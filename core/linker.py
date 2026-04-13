import re
import os

class AutoLinker:
    def __init__(self, vault_manager):
        self.vault_manager = vault_manager

    def apply_semi_auto_links(self, text):
        """
        SEMI-AUTO: Aplica links APENAS para palavras que já existem no Cofre (Whitelist).
        Impede explosão descontrolada de novas notas vazias criadas pela IA.
        """
        whitelist = self.vault_manager.get_whitelist_concepts()
        if not whitelist:
            return text
            
        # Ordenar os conceitos do mais longo para o mais curto evita overlap
        # (ex: "Machine Learning" vs "Learning")
        sorted_concepts = sorted(list(whitelist), key=len, reverse=True)
        
        linked_text = text
        for concept in sorted_concepts:
            # Usar regex para casar a palavra isolada (!\w) que não esteja já em um link (!\[)
            # Match exato em repetição de termos
            pattern = re.compile(rf'(?<!\[)({re.escape(concept)})(?!\])(?!\w)', re.IGNORECASE)
            
            def replace_match(match):
                matched_text = match.group(1)
                # O Obsidian permite aliasing: [[Nota|texto na frase]]
                return f"[[{concept}|{matched_text}]]"

            linked_text = pattern.sub(replace_match, linked_text)

        return linked_text

    def create_link(self, source_title, target_title):
        """Adiciona um link manualmente em uma nota existente se o nó for detectado como duplicado"""
        source_path = self.vault_manager.find_note_path(source_title)
        if source_path and os.path.exists(source_path):
            with open(source_path, "a", encoding="utf-8") as f:
                f.write(f"\n🔗 [[{target_title}]]\n")
