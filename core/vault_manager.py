import os
import glob
import re

class VaultManager:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(vault_path)
        self.visited = set()
        
        if not os.path.exists(self.vault_path):
            os.makedirs(self.vault_path)
            
        self._load_existing_titles()

    def _load_existing_titles(self):
        """Lê os arquivos existentes no vault para popular a lista self.visited."""
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        for file_path in md_files:
            # Tentar extrair o título real do Heading 1 "# Title"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if match:
                        title = match.group(1).strip()
                        self.visited.add(title.lower())
                    else:
                        # Fallback pro nome do arquivo caso nao tenha H1 padrão
                        base = os.path.basename(file_path)
                        name = os.path.splitext(base)[0].replace("_", " ")
                        self.visited.add(name.lower())
            except Exception:
                pass

    def add_visited(self, title: str):
        self.visited.add(title.lower())

    def has_visited(self, title: str) -> bool:
        return title.lower() in self.visited

    def save_node(self, filename: str, content: str, subfolder: str = ""):
        target_dir = self.vault_path
        if subfolder:
            safe_subfolder = subfolder.replace('"', '').title()
            target_dir = os.path.join(self.vault_path, safe_subfolder)
            
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
