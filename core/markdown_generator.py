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
        if not items or not isinstance(items, list) or len(items) == 0:
            return "- *(Vazio)*"
        
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
             return "- *(Vazio)*"
             
        return "\n".join(formatted)

    @staticmethod
    def generate(node: dict, depth: int) -> str:
        title = node.get("title", "Untitled")
        definition = node.get("definition", "")
        level = "map-of-content"
        
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        subs = MarkdownGenerator._format_list(node.get("subconcepts", []), is_link=True)

        md = f"""---
tags: [knowledge-engine, {level}]
type: index
generated: {now_iso}
source_depth: {depth}
---

# {title}

> {definition}

## 📚 Roteiro de Estudos (Ramificações)
{subs}
"""
        return md
