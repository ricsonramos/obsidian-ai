import os
import sys
import re
from core.brain import Brain


# =========================================================
# 🧠 CHAT CLI — GRAPH ONLY MODE
# =========================================================
class ChatCLI:
    def __init__(self):
        vault_path = os.path.abspath(os.getcwd())
        self.brain = Brain(vault_path)

        self.stopwords = {
            "de","da","do","das","dos","e","o","a",
            "um","uma","para","com","em","no","na",
            "que","é","os","as"
        }

    # =========================================================
    # 🧠 DUPLICATA SEMÂNTICA SIMPLES
    # =========================================================
    def normalize(self, text):
        text = re.sub(r"[^a-z0-9\s]", "", text.lower())
        return [t for t in text.split() if t not in self.stopwords]

    def similarity(self, a, b):
        a = set(self.normalize(a))
        b = set(self.normalize(b))
        if not a or not b:
            return 0
        return len(a & b) / len(a | b)

    def is_duplicate(self, title):
        try:
            existing = self.brain.manager.get_whitelist_concepts()
        except:
            return None

        for t in existing:
            if self.similarity(title, t) > 0.75:
                return t
        return None

    # =========================================================
    # 🧠 PROCESSAMENTO (GRAPH ONLY)
    # =========================================================
    def process_input(self, user_input):

        title = user_input.strip()
        depth = 3  # 🔥 FIXO SEMPRE

        dup = self.is_duplicate(title)
        
        if dup:
            print(f"\n🔗 Nó '{dup}' já existe no Cofre. Vamos expandi-lo e interligá-lo.")
            title = dup
            content = "Gerado previamente"
        else:
            print(f"\n🧠 Definindo conceito principal: '{title}'...")
            prompt_def = f"Forneça uma explicação técnica e objetiva em 1 parágrafo sobre '{title}'."
            content = self.brain.llm.generate(prompt_def)
            print(f"   ✓ Definição concluída.")

        print(f"\n🧠 Gerando grafo automático (depth={depth})...")

        # 🚀 SEM IA DECIDINDO FLUXO
        self.brain.graph(title, content, depth)
        result = self.brain.process()

        print("\n✅ Fluxo finalizado com sucesso!")
        print(result)

    # =========================================================
    # 🧠 LOOP
    # =========================================================
    def run(self):

        print("\n============================================================")
        print("🧠 OBSIDIAN AI — GRAPH EXPANSION MODE")
        print("============================================================")
        print("💡 Tudo vira grafo automaticamente")
        print("📊 Profundidade fixa: 3 níveis")
        print("🚀 Digite qualquer conceito e pressione ENTER")
        print("❌ exit para sair")
        print("============================================================\n")

        while True:
            try:
                user_input = input("🧠 Você > ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "sair"]:
                    break

                self.process_input(user_input)

            except KeyboardInterrupt:
                break


# =========================================================
if __name__ == "__main__":
    ChatCLI().run()