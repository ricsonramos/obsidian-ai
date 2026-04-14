import re
from datetime import datetime, timezone

class MarkdownGenerator:
    @staticmethod
    def normalize_filename(title: str) -> str:
        name = title.lower()
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"[\s-]+", "_", name)
        return f"{name}.md"

    @staticmethod
    def _format_list(items, is_link=False):
        """Montador infalível para a ausência de geração garantindo legibilidade caso o LLM falhe na chave."""
        if not items or not isinstance(items, list) or len(items) == 0:
            return "- *(Nenhuma informação consolidada fornecida)*"
        
        formatted = []
        for item in items:
            clean_item = str(item).strip()
            if not clean_item:
                 continue
                 
            if is_link:
                clean_item = clean_item.replace("[", "").replace("]", "")
                formatted.append(f"- [[{clean_item}]]")
            else:
                 formatted.append(f"- {clean_item}")
                 
        if not formatted:
             return "- *(Nenhuma informação consolidada fornecida)*"
             
        return "\n".join(formatted)

    @staticmethod
    def generate(node: dict, depth: int) -> str:
        title = node.get("title", "Untitled")
        definition = node.get("definition", "Indefinido")
        level = node.get("level", "intermediate")
        
        core_list = MarkdownGenerator._format_list(node.get("core", []), is_link=False)
        connections_list = MarkdownGenerator._format_list(node.get("connections", []), is_link=True)
        
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        md = f"""---
tags: [knowledge-engine, {level}]
type: concept
generated: {now_iso}
source_depth: {depth}
---

# {title}

## 🧩 Definição
{definition}

## 🔑 Núcleo
{core_list}
"""
        
        # INJEÇÃO CONDICIONAL DE SEÇÕES COMPLETAS
        if "mechanism" in node or depth > 1:
            mechanism_list = MarkdownGenerator._format_list(node.get("mechanism", []))
            md += f"\n## ⚙️ Funcionamento\n{mechanism_list}\n"
            
        if "examples" in node or depth > 1:
            examples_list = MarkdownGenerator._format_list(node.get("examples", []))
            md += f"\n## 📊 Exemplos\n{examples_list}\n"
            
        if "applications" in node or depth > 1:
             app_list = MarkdownGenerator._format_list(node.get("applications", []))
             md += f"\n## 🚀 Aplicações\n{app_list}\n"
             
        # REDES HORIZONTAIS
        md += f"\n## 🔗 Conexões\n{connections_list}\n"
        
        # VERTICAIS 
        if "subconcepts" in node or depth > 1:
             subs = MarkdownGenerator._format_list(node.get("subconcepts", []), is_link=True)
             md += f"\n## 🧱 Subconceitos\n{subs}\n"
             
        return md
