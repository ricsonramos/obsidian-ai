import re
from datetime import datetime
from core.utils import title_to_slug

class MarkdownGenerator:
    @staticmethod
    def normalize_filename(title: str) -> str:
        """
        Gera nome de arquivo snake_case ASCII puro usando utility universal.
        """
        filename = title_to_slug(title)
        if not filename.endswith(".md"):
            filename += ".md"
        return filename

    @staticmethod
    def generate_from_expansion_node(node: dict, level: str, depth: int) -> str:
        """
        Gera nota Obsidian a partir de um ExpansionNode do schema Antigravity.
        Campos: filename, display_name, brief_definition, search_queries, connections
        """
        display_name = node.get("display_name", node.get("filename", "Untitled"))
        brief_def = node.get("brief_definition", "")
        search_queries = node.get("search_queries", [])
        connections = node.get("connections", [])
        now = datetime.now().isoformat(timespec="seconds")

        md_lines = ["---"]
        md_lines.append(f'title: "{display_name}"')
        md_lines.append("status: research")
        md_lines.append(f"hierarchy_level: {level}")

        if search_queries:
            md_lines.append("primary_queries:")
            for q in search_queries:
                md_lines.append(f'  - "{q}"')

        if connections:
            conn_str = ", ".join(connections)
            md_lines.append(f"connections: [{conn_str}]")

        md_lines.append(f"generated: {now}")
        md_lines.append(f"source_depth: {depth}")
        tag = level.replace("|", "_").replace(" ", "_")
        md_lines.append(f"tags: [knowledge-engine, {tag}]")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"# {display_name}")
        md_lines.append("")

        if brief_def:
            md_lines.append(f"> {brief_def}")
            md_lines.append("")

        if search_queries:
            md_lines.append("## Queries de Pesquisa (NotebookLM)")
            for q in search_queries:
                md_lines.append(f"- {q}")
            md_lines.append("")

        if connections:
            md_lines.append("## Conexoes")
            for c in connections:
                md_lines.append(f"- {c}")

        return "\n".join(md_lines)

    @staticmethod
    def generate_prerequisite_stub(prereq: dict, depth: int, parent_topic: str = "") -> str:
        """
        Gera stub de nota L0 para pré-requisito faltante.
        Campos: name, reason, priority
        Inclui backlink para o tópico pai (parent_topic) na seção Conexoes.
        """
        name = prereq.get("name", "Pre-requisito")
        reason = prereq.get("reason", "")
        now = datetime.now().isoformat(timespec="seconds")

        md_lines = ["---"]
        md_lines.append(f'title: "{name}"')
        md_lines.append("status: research")
        md_lines.append("hierarchy_level: 0_Foundation")
        if parent_topic:
            md_lines.append(f'parent: "{parent_topic}"')
        md_lines.append(f"generated: {now}")
        md_lines.append(f"source_depth: {depth}")
        md_lines.append("tags: [knowledge-engine, 0_Foundation, prerequisite]")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"# {name}")
        md_lines.append("")

        if reason:
            md_lines.append(f"> **Por que estudar isso primeiro:** {reason}")
            md_lines.append("")

        md_lines.append("## Notas de Estudo")
        md_lines.append("_Adicione aqui o resumo do NotebookLM apos concluir a pesquisa._")
        md_lines.append("")

        if parent_topic:
            md_lines.append("## Conexoes")
            md_lines.append(f"- [[{parent_topic}]]")

        return "\n".join(md_lines)

    @staticmethod
    def generate_hub_note(topic_title: str, level: str, prereq_links: list, depth: int) -> str:
        """
        Gera nota MOC (hub/raiz) para o tópico principal.
        Inclui links para todos os pré-requisitos na seção Prerequisitos.
        """
        now = datetime.now().isoformat(timespec="seconds")
        tag = level.replace("|", "_").replace(" ", "_")

        md_lines = ["---"]
        md_lines.append(f'title: "{topic_title}"')
        md_lines.append("status: hub")
        md_lines.append(f"hierarchy_level: {level}")
        md_lines.append(f"generated: {now}")
        md_lines.append(f"source_depth: {depth}")
        md_lines.append(f"tags: [knowledge-engine, {tag}, hub]")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"# {topic_title}")
        md_lines.append("")
        md_lines.append("> Nota raiz (MOC). Estude os pre-requisitos antes de avancar.")
        md_lines.append("")
        md_lines.append("## Pre-Requisitos Identificados")
        for link in prereq_links:
            md_lines.append(f"- {link}")
        md_lines.append("")
        md_lines.append("## Subconceitos")
        md_lines.append("_Sera populado nas proximas expansoes pelo Antigravity Engine._")

        return "\n".join(md_lines)

    @staticmethod
    def generate(node: dict, depth: int) -> str:
        """
        Compatibilidade com o fluxo antigo (schema nodes[]).
        Mantido para não quebrar linker.py e outros módulos legados.
        """
        title = node.get("title", "Untitled")
        content = node.get("content", node.get("definition", ""))
        level = node.get("level", "intermediate")

        relations = node.get("relations", [])
        subconcepts = node.get("subconcepts", [])
        all_relations = [r.strip() for r in (relations + subconcepts) if isinstance(r, str) and r.strip()]

        now = datetime.now().isoformat(timespec="seconds")

        md_lines = ["---"]
        md_lines.append(f"tags: [knowledge-engine, {level}]")

        if all_relations:
            relations_str = ", ".join([f"[[{r}]]" for r in all_relations])
            md_lines.append(f"relations: {relations_str}")

        md_lines.append(f"generated: {now}")
        md_lines.append(f"source_depth: {depth}")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"# {title}")
        md_lines.append("")

        if content:
            md_lines.append(content)
            md_lines.append("")

        if all_relations:
            md_lines.append("## Relacoes")
            for r in all_relations:
                md_lines.append(f"- [[{r}]]")

        return "\n".join(md_lines)
