import os

class VaultManager:
    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.inbox_path = os.path.join(vault_path, "00_Inbox")
        self.concepts_path = os.path.join(vault_path, "01_Concepts")
        self.daily_path = os.path.join(vault_path, "04_Daily")

    def save_file(self, folder, filename, content):
        if not filename.endswith(".md"):
            filename += ".md"
        path = os.path.join(folder, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def save_inbox(self, filename, content):
        return self.save_file(self.inbox_path, filename, content)

    def save_concept(self, filename, content, parent_folder=None):
        base_dir = self.concepts_path
        if parent_folder:
            base_dir = os.path.join(base_dir, parent_folder)
            
        os.makedirs(base_dir, exist_ok=True)
        
        if not filename.endswith(".md"):
            filename += ".md"
            
        path = os.path.join(base_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
        
    def save_daily(self, filename, content):
        return self.save_file(self.daily_path, filename, content)

    def get_whitelist_concepts(self):
        """Retorna a lista (whitelist) de conceitos existentes (busca recursiva)."""
        concepts = set()
        if os.path.exists(self.concepts_path):
            for root, dirs, files in os.walk(self.concepts_path):
                for file in files:
                    if file.endswith(".md"):
                        concepts.add(file.replace(".md", ""))
        return concepts

    def get_inbox_content(self):
        """Retorna e limpa opcionalmente os inputs do Inbox para sumarização."""
        content = []
        if os.path.exists(self.inbox_path):
            for file in os.listdir(self.inbox_path):
                if file.endswith(".md"):
                    filepath = os.path.join(self.inbox_path, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content.append(f"[{file}] {f.read().strip()}")
        return "\n".join(content)
    
    def build_index(self):
        self.index = {}

        for root, _, files in os.walk(self.vault_path):
            for f in files:
                if f.endswith(".md"):
                    name = f[:-3].lower()
                    self.index[name] = os.path.join(root, f)

    def find_note_path(self, title: str):
        if not hasattr(self, "index"):
            self.build_index()

        return self.index.get(title.lower())