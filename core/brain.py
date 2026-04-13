import os
import json
import re
import hashlib
from datetime import datetime

from core.llm import LocalLLM
from core.markdown_generator import MarkdownGenerator
from core.vault_manager import VaultManager
from core.linker import AutoLinker


# =========================================================
# 🧠 JSON SAFE PARSER
# =========================================================
def extract_json(text: str) -> str:
    if not text:
        return "{}"

    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text.strip()


# =========================================================
# 🧠 GRAPH ENGINE 2.1 (ESTÁVEL + FIXED)
# =========================================================
class GraphEngine:
    def __init__(self, llm, manager, linker):
        self.llm = llm
        self.manager = manager
        self.linker = linker

        self.visited = set()
        self.cache = {}

    # -------------------------
    # util
    # -------------------------
    def _norm(self, text):
        return (text or "").strip().lower()

    def _hash(self, title, content):
        return hashlib.md5((title + content).encode("utf-8")).hexdigest()

    # -------------------------
    # geração LLM (FIX PRINCIPAL)
    # -------------------------
    def _generate(self, title, content):
        key = self._hash(title, content)

        if key in self.cache:
            return self.cache[key]

        prompt = f"""
VOCÊ É UM GERADOR ESTRITO DE JSON.

REGRAS IMPORTANTES:
- NÃO escreva texto fora do JSON
- NÃO explique nada
- NÃO use markdown
- RETORNE APENAS JSON VÁLIDO

TEMA:
{title}: {content}

FORMATO OBRIGATÓRIO:

{{
  "nodes": [
    {{"title": "conceito curto", "content": "explicação técnica objetiva"}},
    {{"title": "conceito curto", "content": "explicação técnica objetiva"}},
    {{"title": "conceito curto", "content": "explicação técnica objetiva"}}
  ]
}}
"""

        raw = self.llm.generate(prompt)
        cleaned = extract_json(raw)

        try:
            data = json.loads(cleaned)
            nodes = data.get("nodes", [])
        except Exception:
            print(f"\n[!] JSON inválido em: {title}")
            print("[DEBUG RAW LLM OUTPUT]\n", raw)
            return []

        if not isinstance(nodes, list):
            return []

        self.cache[key] = nodes
        return nodes

    # -------------------------
    # MAIN RECURSIVO (CORRIGIDO)
    # -------------------------
    def generate_nodes(self, title, content, depth=1):
        if depth <= 0:
            return []

        norm = self._norm(title)
        if norm in self.visited:
            return []

        self.visited.add(norm)

        nodes = self._generate(title, content)

        created = []

        # =====================
        # NÓ PRINCIPAL
        # =====================
        if not self.manager.find_note_path(title):
            md = MarkdownGenerator.generate_concept_stub(
                title,
                f"Gerado automaticamente - Raiz (Depth {depth})",
                content
            )
            self.manager.save_concept(title, md)

        created.append(title)

        # se LLM falhou mas ainda queremos progressão
        if not nodes:
            return created

        # =====================
        # FILHOS
        # =====================
        for node in nodes:
            t = node.get("title")
            c = node.get("content")

            if not t or not c:
                continue

            existing = self.manager.find_note_path(t)

            if existing:
                self.linker.create_link(title, t)
                created.append(f"{t} (linked)")
                continue

            md = MarkdownGenerator.generate_concept_stub(
                t,
                f"Gerado a partir de [[{title}]]",
                f"{c}\n\n🔗 [[{title}]]"
            )

            self.manager.save_concept(t, md)
            created.append(t)

            # recursion REAL
            if depth > 1:
                sub_nodes = self.generate_nodes(t, c, depth - 1)
                created.extend(sub_nodes)

        return created


# =========================================================
# 🧠 BRAIN
# =========================================================
class Brain:
    def __init__(self, vault_path):
        self.manager = VaultManager(vault_path)
        self.llm = LocalLLM()
        self.linker = AutoLinker(self.manager)

        self.graph_engine = GraphEngine(self.llm, self.manager, self.linker)

    # -------------------------
    # inbox
    # -------------------------
    def inbox(self, content):
        date = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.manager.save_inbox(f"inbox_{date}", content)
        return "[+] inbox salvo"

    # -------------------------
    # daily
    # -------------------------
    def daily(self):
        inbox = self.manager.get_inbox_content()

        if not inbox.strip():
            return "[-] inbox vazio"

        raw = self.llm.generate(f"Resuma em bullets:\n{inbox}")
        linked = self.linker.apply_semi_auto_links(raw)

        date = datetime.now().strftime("%Y-%m-%d")

        md = MarkdownGenerator.generate_daily_note(date, linked)
        self.manager.save_daily(f"daily_{date}", md)

        return "[+] daily salvo"

    # -------------------------
    # GRAPH ENTRYPOINT
    # -------------------------
    def graph(self, title, content, depth=1):
        created = self.graph_engine.generate_nodes(title, content, depth)
        return f"[+] grafo criado: {len(created)} nós", created

    # -------------------------
    # PROCESS (compat)
    # -------------------------
    def process(self):
        return "[+] sistema Graph Engine 2.1 ativo (sem fila)"