import re
from datetime import datetime

class MarkdownGenerator:
    @staticmethod
    def normalize_filename(title: str) -> str:
        """
        Gera um nome de arquivo válido protegido: lowercase, sem acentos, 
        com underscores no lugar de espaços, e garante a extensão .md.
        """
        import unicodedata
        
        # Remove acentos
        normalized = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
        # Converte para lowercase
        normalized = normalized.lower()
        # Remove caracteres especiais que não são alfanuméricos ou espaços/hifens
        normalized = re.sub(r'[^a-z0-9\s-]', '', normalized)
        # Substitui espaços e hifens por underscores
        normalized = re.sub(r'[\s\-]+', '_', normalized).strip('_')
        
        if not normalized.endswith(".md"):
            normalized += ".md"
            
        return normalized

    @staticmethod
    def generate(node: dict, depth: int) -> str:
        """
        Formata o nó no padrão do Vault do Obsidian contendo Frontmatter YAML e wikilinks.
        """
        title = node.get("title", "Untitled")
        content = node.get("content", node.get("definition", ""))
        level = node.get("level", "intermediate")
        
        # Suporta tanto "relations" do padrão antigo quanto "subconcepts" do padrão novo
        relations = node.get("relations", [])
        subconcepts = node.get("subconcepts", [])
        
        all_relations = []
        for rel in relations + subconcepts:
            if isinstance(rel, str) and rel.strip():
                all_relations.append(rel.strip())
                
        now = datetime.now().isoformat()
        
        # Cria a string inicial (Frontmatter + Titulo + Conteudo Base)
        md_lines = []
        md_lines.append("---")
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
            md_lines.append("## 🔗 Relações")
            for r in all_relations:
                md_lines.append(f"- [[{r}]]")
                
        return "\n".join(md_lines)
