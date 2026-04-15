import os
import glob
import re
from core.utils import normalize_title

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
            try:
                base = os.path.basename(file_path)
                name = os.path.splitext(base)[0]
                # Indexa pelo slug do nome do arquivo (já normalizado)
                self.visited.add(normalize_title(name))
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Tenta extrair título do H1 e normaliza
                    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if match:
                        title = match.group(1).strip()
                        self.visited.add(normalize_title(title))
            except Exception:
                pass

    def get_existing_notes(self) -> list[str]:
        """
        Retorna lista ordenada de títulos normalizados para injetar
        no prompt como {existing_notes}.
        """
        return sorted(list(self.visited))

    def add_visited(self, title: str):
        self.visited.add(normalize_title(title))

    def has_visited(self, title: str) -> bool:
        return normalize_title(title) in self.visited

    def save_node(self, filename: str, content: str, subfolder: str = ""):
        target_dir = self.vault_path
        if subfolder:
            # Remove caracteres proibidos no Windows: < > : " / \ | ? *
            safe_subfolder = re.sub(r'[<>:\"\/\\|\?\*]', '', subfolder)
            safe_subfolder = safe_subfolder.strip().title()
            target_dir = os.path.join(self.vault_path, safe_subfolder)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        filepath = os.path.join(target_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
