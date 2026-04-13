import sys
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
# 🧠 JSON SAFE PARSER (LLM RESILIENT)
# =========================================================
def extract_json(text: str) -> str:
    """
    Extrai JSON limpo mesmo se o LLM devolver markdown ou texto extra.
    """
    if not text:
        return "{}"

    # remove blocos markdown
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # tenta capturar primeiro objeto JSON válido
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return text.strip()


# =========================================================
# 🧠 GRAPH GENERATOR CORE (RECURSIVO + SAFE)
# =========================================================
class GraphEngine:
    def __init__(self, llm, manager, linker):
        self.llm = llm
        self.manager = manager
        self.linker = linker
        self.visited = set()

    def generate_nodes(self, title, content, depth=1):
        """
        Gera grafo recursivo controlado.
        """
        if depth <= 0:
            return []

        if title.lower() in self.visited:
            return []

        self.visited.add(title.lower())

        prompt = f"""
Você é um sistema de geração de conhecimento.

Crie 5 a 7 subconceitos do tema abaixo:

TEMA:
{title}: {content}

REGRAS:
- Responda SOMENTE JSON válido
- Sem markdown
- Sem texto extra

FORMATO:
{{
  "nodes": [
    {{
      "title": "string",
      "content": "string"
    }}
  ]
}}
"""

        raw = self.llm.generate(prompt)

        try:
            clean = extract_json(raw)
            data = json.loads(clean)
        except Exception:
            print(f"[!] Falha JSON em: {title}")
            return []

        nodes = data.get("nodes", [])
        all_created = []

        # salva nó principal
        main_md = MarkdownGenerator.generate_concept_stub(
            title,
            content,
            "Gerado via GRAPH ENGINE 2.0"
        )
        self.manager.save_concept(title, main_md)
        all_created.append(title)

        # processa filhos
        for node in nodes:
            child_title = node.get("title")
            child_content = node.get("content")

            if not child_title or not child_content:
                continue

            linked_content = f"{child_content}\n\n🔗 Relacionado a: [[{title}]]"

            md = MarkdownGenerator.generate_concept_stub(
                child_title,
                child_content,
                linked_content
            )

            self.manager.save_concept(child_title, md)
            all_created.append(child_title)

            # RECURSÃO CONTROLADA
            if depth > 1:
                self.generate_nodes(child_title, child_content, depth - 1)

        return all_created


# =========================================================
# 🚀 MAIN CLI
# =========================================================
def main():
    parser = argparse.ArgumentParser(description="Second Brain AI (Graph Engine 2.0)")
    subparsers = parser.add_subparsers(dest="command")

    # INBOX
    inbox_parser = subparsers.add_parser("inbox")
    inbox_parser.add_argument("content")

    # CONCEPT NORMAL
    concept_parser = subparsers.add_parser("concept")
    concept_parser.add_argument("title")
    concept_parser.add_argument("content")

    # DAILY
    subparsers.add_parser("daily")

    # GRAPH ENGINE 2.0
    graph_parser = subparsers.add_parser("graph")
    graph_parser.add_argument("title")
    graph_parser.add_argument("content")
    graph_parser.add_argument("--depth", type=int, default=1)

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    vault_path = os.path.abspath(os.path.join(script_dir, "..", ".."))

    manager = VaultManager(vault_path)
    llm = LocalLLM()
    linker = AutoLinker(manager)
    graph = GraphEngine(llm, manager, linker)

    # =========================
    # INBOX
    # =========================
    if args.command == "inbox":
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        manager.save_inbox(f"inbox_{date_str}", args.content)
        print("[+] Inbox salvo")

    # =========================
    # CONCEPT NORMAL
    # =========================
    elif args.command == "concept":
        prompt = f"""
Explique o conceito: {args.title}
Base: {args.content}

## 📖 Definição Simples
## 🔬 Explicação Técnica
## ⚡ Exemplos Práticos
"""

        raw = llm.generate(prompt)
        linked = linker.apply_semi_auto_links(raw)

        md = MarkdownGenerator.generate_concept_stub(
            args.title,
            args.content,
            linked
        )

        manager.save_concept(args.title, md)
        print("[+] Concept salvo")

    # =========================
    # DAILY
    # =========================
    elif args.command == "daily":
        inbox = manager.get_inbox_content()

        if not inbox.strip():
            print("[-] Inbox vazio")
            return

        prompt = f"Resuma em bullets:\n{inbox}"

        raw = llm.generate(prompt)
        linked = linker.apply_semi_auto_links(raw)

        date_str = datetime.now().strftime("%Y-%m-%d")

        md = MarkdownGenerator.generate_daily_note(date_str, linked)
        manager.save_daily(f"daily_{date_str}", md)

        print("[+] Daily salvo")

    # =========================
    # GRAPH ENGINE 2.0
    # =========================
    elif args.command == "graph":
        print(f"[*] GRAPH ENGINE 2.0: {args.title} (depth={args.depth})")

        created = graph.generate_nodes(
            args.title,
            args.content,
            args.depth
        )

        print(f"[+] Grafo criado: {len(created)} nós")
        print(created)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()