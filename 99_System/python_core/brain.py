import os
import argparse
import json
import re
from datetime import datetime

from core.llm import LocalLLM
from core.markdown_generator import MarkdownGenerator
from core.vault_manager import VaultManager
from core.linker import AutoLinker


# =========================================================
# 🧠 PROMPT LOADER (CÉREBRO EXTERNO)
# =========================================================
def load_prompt():
    path = os.path.join(os.path.dirname(__file__), "prompt.txt")

    if not os.path.exists(path):
        raise FileNotFoundError("prompt.txt não encontrado (sistema depende dele).")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# =========================================================
# 🧠 JSON EXTRACTOR ROBUSTO
# =========================================================
def extract_json(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    if start == -1:
        return ""

    depth = 0

    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1

        if depth == 0:
            return text[start:i + 1]

    return ""


# =========================================================
# 🧠 QUALITY FILTER (ANTI LIXO)
# =========================================================
def is_valid_node(node):
    if not isinstance(node, dict):
        return False

    title = node.get("title", "")
    content = node.get("content", "")

    if not title or not content:
        return False

    if len(content) < 40:
        return False

    return True


# =========================================================
# 🧠 GRAPH ENGINE (MOTOR COGNITIVO)
# =========================================================
class GraphEngine:
    def __init__(self, llm, manager, linker):
        self.llm = llm
        self.manager = manager
        self.linker = linker
        self.visited = set()

    def llm_call(self, prompt):
        return self.llm.generate(
            prompt,
            system_prompt="Você é um arquiteto de conhecimento rigoroso."
        )

    # =====================================================
    # 🧠 STAGE 1 - GENERATION
    # =====================================================
    def generate_raw(self, title, content, depth):
        base_prompt = load_prompt()

        return base_prompt.format(
            title=title,
            content=content,
            depth=depth,
            json_schema="""
{
  "nodes": [
    {
      "title": "string",
      "content": "string",
      "relations": ["string"]
    }
  ]
}
"""
        )

    # =====================================================
    # 🧠 STAGE 2 - SELF REPAIR
    # =====================================================
    def repair_json(self, broken_json):
        repair_prompt = f"""
Você é um validador e corretor de JSON.

Corrija e melhore este grafo de conhecimento:

{broken_json}

REGRAS:
- remover nós vazios
- melhorar textos superficiais
- manter estrutura válida
- enriquecer conteúdo quando possível

Responda SOMENTE JSON válido.
"""
        return self.llm_call(repair_prompt)

    # =====================================================
    # 🧠 PARSER PIPELINE
    # =====================================================
    def parse_json(self, raw):
        clean = extract_json(raw)

        if not clean:
            return None

        try:
            return json.loads(clean)
        except:
            repaired = self.repair_json(clean)
            cleaned_repair = extract_json(repaired)

            try:
                return json.loads(cleaned_repair)
            except:
                return None

    # =====================================================
    # 🧠 MAIN ENGINE
    # =====================================================
    def generate_nodes(self, title, content, depth=1):
        if depth <= 0:
            return []

        if title.lower() in self.visited:
            return []

        self.visited.add(title.lower())

        # STAGE 1
        prompt = self.generate_raw(title, content, depth)
        raw = self.llm_call(prompt)

        # PARSE PIPELINE
        data = self.parse_json(raw)

        if not data:
            print(f"[!] Falha total em: {title}")
            print(raw)
            return []

        nodes = data.get("nodes", [])
        all_created = []

        # =====================================================
        # 📌 NODE PRINCIPAL
        # =====================================================
        main_md = MarkdownGenerator.generate_concept_stub(
            title,
            content,
            "Gerado via Knowledge Engine v2"
        )

        self.manager.save_concept(title, main_md)
        all_created.append(title)

        # =====================================================
        # 📌 CHILD NODES
        # =====================================================
        for node in nodes:
            if not is_valid_node(node):
                continue

            child_title = node["title"]
            child_content = node["content"]

            relations = node.get("relations", [])
            relations_md = "\n".join([f"- [[{r}]]" for r in relations])

            linked_content = f"""{child_content}

## 🔗 Relações
{relations_md}
"""

            md = MarkdownGenerator.generate_concept_stub(
                child_title,
                child_content,
                linked_content
            )

            self.manager.save_concept(child_title, md)
            all_created.append(child_title)

            # RECURSÃO INTELIGENTE
            if depth > 1 and len(child_content) > 60:
                self.generate_nodes(child_title, child_content, depth - 1)

        return all_created


# =========================================================
# 🚀 CLI
# =========================================================
def main():
    parser = argparse.ArgumentParser(description="Knowledge Engine v2")
    subparsers = parser.add_subparsers(dest="command")

    graph_parser = subparsers.add_parser("graph")
    graph_parser.add_argument("title")
    graph_parser.add_argument("content")
    graph_parser.add_argument("--depth", type=int, default=1)

    args = parser.parse_args()

    vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    manager = VaultManager(vault_path)
    llm = LocalLLM()
    linker = AutoLinker(manager)

    engine = GraphEngine(llm, manager, linker)

    if args.command == "graph":
        print(f"[*] Knowledge Engine v2: {args.title} (depth={args.depth})")

        result = engine.generate_nodes(
            args.title,
            args.content,
            args.depth
        )

        print(f"[+] Nodes criados: {len(result)}")
        print(result)


if __name__ == "__main__":
    main()