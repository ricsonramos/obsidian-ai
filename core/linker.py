import os
import glob
import re

class Linker:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(vault_path)

    def _get_all_titles(self) -> set:
        """Obtém todos os títulos validos e indexados fisicamente no vault."""
        titles = set()
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    match = re.search(r"^#\s+(.+)$", f.read(), re.MULTILINE)
                    if match:
                        titles.add(match.group(1).strip().lower())
            except Exception:
                pass
        return titles

    def run(self):
        """
        Validador de grafos final. O Markdown Generator (através da orientação da engine) já
        converteu conexões sugeridas no JSON e adicionou [[links]] nos bullets certos.
        O Linker foi rebaixado para atuar passivamente evitando poluição transversal:
        Monitorando o surgimento de links fantasmas/projetados para auditoria na tela do motor de observabilidade.
        """
        titles = self._get_all_titles()
        if not titles:
            return

        dead_links_detected = 0
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Conta dead-links que ainda estão pendentes
                links = re.findall(r"\[\[(.*?)\]\]", content)
                for link in links:
                     clean_link = link.lower().strip()
                     if clean_link not in titles:
                          dead_links_detected += 1
                          
            except Exception:
                pass
                
        if dead_links_detected > 0:
             print(f"[AutoLinker | Auditor] Validação de Lacunas: Identificados cerca de {dead_links_detected} Orphan-Links semânticos pre-setados.")
        else:
             print("[AutoLinker | Auditor] O tecido criado é autossuficiente (Sem links fantasmas/pendentes).")
