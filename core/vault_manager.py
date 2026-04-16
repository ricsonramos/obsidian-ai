import os
import glob
import re
import shutil
from core.utils import normalize_title

class VaultManager:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(vault_path)
        self.visited = set()

        if not os.path.exists(self.vault_path):
            os.makedirs(self.vault_path)

        self._load_existing_titles()

    def _load_existing_titles(self):
        """Varre o vault e indexa TUDO de forma normalizada para o cache de memória."""
        self.visited = set()  # Reseta o set para evitar acúmulo de sujeira
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        for file_path in md_files:
            try:
                # 1. Indexa pelo nome do arquivo físico
                base = os.path.basename(file_path)
                name = os.path.splitext(base)[0]
                self.visited.add(normalize_title(name))
                
                # 2. Indexa pelo título H1 interno (backup de redundância)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if match:
                        title = match.group(1).strip()
                        self.visited.add(normalize_title(title))
            except Exception:
                continue

    def get_existing_notes(self) -> list[str]:
        """Injeta a lista no prompt para que a IA saiba o que NÃO repetir."""
        return sorted(list(self.visited))

    def has_visited(self, title: str) -> bool:
        """Checagem estrita para evitar gastos desnecessários com a API."""
        return normalize_title(title) in self.visited

    def add_visited(self, title: str):
        """Adiciona manualmente um título ao cache de visitados."""
        self.visited.add(normalize_title(title))

    def save_node(self, title: str, content: str, subfolder: str = ""):
        """Garante persistência física usando apenas o padrão snake_case."""
        from core.utils import title_to_slug
        clean_title = normalize_title(title)
        filename = f"{title_to_slug(title)}.md"

        target_dir = self.vault_path
        if subfolder:
            # Força pastas a também seguirem o padrão normalizado
            safe_subfolder = normalize_title(subfolder)
            target_dir = os.path.join(self.vault_path, safe_subfolder)

        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.visited.add(clean_title)
        return filepath

    def sanitize_vault(self, log_callback: callable = None):
        """
        Faxina Geral: Renomeia arquivos fora do padrão e isola duplicatas.
        Execute isso para 'limpar o terreno' antes de novas expansões.
        """
        def _log(msg):
            if log_callback:
                log_callback(msg, "info")
            else:
                print(msg)

        _log("🧹 Iniciando sanitização física do Vault...")
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        
        backup_dir = os.path.join(self.vault_path, "_duplicates_backup")
        
        for file_path in md_files:
            # Ignora o diretório de backup
            if "_duplicates_backup" in file_path:
                continue

            current_dir = os.path.dirname(file_path)
            current_filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(current_filename)[0]
            
            # Gera o padrão snake_case
            standard_name = normalize_title(name_without_ext)
            if not standard_name: continue
            
            new_filename = f"{standard_name}.md"
            new_path = os.path.join(current_dir, new_filename)

            if current_filename != new_filename:
                if os.path.exists(new_path):
                    _log(f"  [CONFLITO] '{current_filename}' -> movendo para backup.")
                    os.makedirs(backup_dir, exist_ok=True)
                    try:
                        shutil.move(file_path, os.path.join(backup_dir, current_filename))
                    except: pass
                else:
                    os.rename(file_path, new_path)
                    _log(f"  [PADRÃO] '{current_filename}' -> '{new_filename}'")
        
        # Recarrega o inventário após as mudanças físicas
        self._load_existing_titles()
        _log(f"✨ Vault sanitizado! {len(self.visited)} conceitos únicos indexados.")