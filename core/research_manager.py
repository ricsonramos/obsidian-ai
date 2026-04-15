"""
ResearchManager — Gerador de Manifesto para NotebookLM.

Escaneia o vault buscando notas com `status: research` no frontmatter YAML
e consolida todas as `primary_queries` em um arquivo research_list.txt.

Fluxo esperado pelo usuário:
  1. python main.py research  → gera research_list.txt
  2. Usuário usa as queries para encontrar PDFs no ArXiv / Google Scholar
  3. Usuário faz upload no NotebookLM, cola o resumo gerado na nota
  4. Usuário muda status: research → status: learned na nota do Obsidian
"""
import os
import glob
import re
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _extract_frontmatter(content: str) -> dict:
    """Extrai campos simples do frontmatter YAML sem dependência pesada."""
    result = {}
    # Detecta bloco --- ... ---
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return result

    block = match.group(1)

    # status: valor simples
    for key in ["status", "title", "hierarchy_level"]:
        m = re.search(rf"^{key}:\s*[\"']?(.+?)[\"']?\s*$", block, re.MULTILINE)
        if m:
            result[key] = m.group(1).strip()

    # primary_queries: lista YAML
    m_list = re.search(r"primary_queries:\s*\n((?:\s+-\s+.+\n?)+)", block)
    if m_list:
        raw_items = m_list.group(1)
        queries = re.findall(r'-\s+"?(.+?)"?\s*$', raw_items, re.MULTILINE)
        result["primary_queries"] = [q.strip() for q in queries]

    return result


class ResearchManager:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(vault_path)

    def generate_manifest(self) -> str:
        """
        Gera research_list.txt consolidando todas as primary_queries
        de notas com status: research no vault.

        Retorna o caminho absoluto do arquivo gerado.
        """
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)

        sections = []
        total_queries = 0

        for file_path in sorted(md_files):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            fm = _extract_frontmatter(content)

            if fm.get("status") != "research":
                continue

            title = fm.get("title", os.path.splitext(os.path.basename(file_path))[0])
            queries = fm.get("primary_queries", [])
            level = fm.get("hierarchy_level", "")

            if not queries:
                logging.warning(f"[Research] Nota sem queries: {file_path}")
                continue

            block = [f"## {title}", f"_Nível: {level}_"]
            for q in queries:
                block.append(f"- {q}")

            sections.append("\n".join(block))
            total_queries += len(queries)

        output_path = os.path.join(self.vault_path, "research_list.txt")

        header = (
            "# Antigravity — Research Manifest\n"
            "# Use estas queries para buscar PDFs no ArXiv, Google Scholar ou Z-Library.\n"
            "# Após estudar e colar o resumo do NotebookLM na nota, altere `status: research` → `status: learned`.\n"
            f"# Total de consultas: {total_queries}\n"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + "\n\n" + "\n\n".join(sections) + "\n")

        logging.info(f"[Research] Manifest gerado: {output_path} ({total_queries} queries de {len(sections)} notas)")
        return output_path
