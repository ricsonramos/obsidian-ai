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
    def generate_from_expansion_node(node: dict, level: str, depth: int, parent_topic: str = "") -> str:
        """
        Gera nota Obsidian com suporte a RAG para expansão de conceitos.
        """
        display_name = node.get("display_name", node.get("filename", "Untitled"))
        related = node.get("connections", [])
        
        source_path = os.getenv("PDF_SOURCE_PATH", "G:\\Meu Drive\\Vault 101\\02-Direito Penal\\Livros")
        
        md_lines = ["---"]
        md_lines.append(f'title: "{display_name}"')
        md_lines.append(f'level: "{level}"')
        md_lines.append('subject: "Direito Penal"')
        md_lines.append(f'source_path: "{source_path}"')
        md_lines.append(f'search_query: "Definição e doutrina sobre {display_name} no contexto de {parent_topic}"')
        md_lines.append('status: "waiting_ollama_rag"')
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"# {display_name}")
        md_lines.append("")
        md_lines.append("## 📝 Resumo da Doutrina")
        md_lines.append("(Aguardando processamento RAG via Ollama...)")
        md_lines.append("")
        md_lines.append("## 🔍 Perguntas para o Modelo Local (Passo 3):")
        md_lines.append(f"1. Quais os elementos constitutivos de {display_name} segundo a fonte?")
        md_lines.append("2. Existe divergência doutrinária relevante neste ponto?")
        md_lines.append(f"3. Como este conceito se aplica na atividade operacional da PMMG?")
        md_lines.append("")
        
        footer = []
        if parent_topic:
            footer.append(f"[[{parent_topic}]]")
        for r in related:
            footer.append(r)
            
        md_lines.append(" | ".join(footer))
        
        return "\n".join(md_lines)

    @staticmethod
    def generate_prerequisite_stub(prereq: dict, depth: int, parent_topic: str = "") -> str:
        """
        Gera nota Obsidian com suporte a RAG para pré-requisitos (Nível 0).
        """
        name = prereq.get("name", "Pre-requisito")
        source_path = os.getenv("PDF_SOURCE_PATH", "G:\\Meu Drive\\Vault 101\\02-Direito Penal\\Livros")

        md_lines = ["---"]
        md_lines.append(f'title: "{name}"')
        md_lines.append('level: "0_Foundation"')
        md_lines.append('subject: "Direito Penal"')
        md_lines.append(f'source_path: "{source_path}"')
        md_lines.append(f'search_query: "Conceitos fundamentais de {name} aplicados ao Direito Penal"')
        md_lines.append('status: "waiting_ollama_rag"')
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"# {name}")
        md_lines.append("")
        md_lines.append("## 📝 Resumo da Doutrina")
        md_lines.append("(Aguardando processamento RAG via Ollama...)")
        md_lines.append("")
        md_lines.append("## 🔍 Perguntas para o Modelo Local (Passo 3):")
        md_lines.append(f"1. Quais os elementos constitutivos de {name} segundo a fonte?")
        md_lines.append("2. Existe divergência doutrinária relevante neste ponto?")
        md_lines.append(f"3. Como este conceito se aplica na atividade operacional da PMMG?")
        md_lines.append("")
        
        if parent_topic:
            md_lines.append(f"[[{parent_topic}]]")
            
        return "\n".join(md_lines)

    @staticmethod
    def generate_hub_note(topic_title: str, level: str, prereq_links: list, depth: int) -> str:
        """
        Gera nota MOC (hub/raiz) para o tópico principal.
        """
        md_lines = ["---"]
        md_lines.append(f'title: "{topic_title}"')
        md_lines.append('status: "hub"')
        md_lines.append(f'level: "{level}"')
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
