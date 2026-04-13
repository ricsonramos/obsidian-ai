import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# 🧠 OLLAMA LOCAL LLM (ROBUSTO)
# =========================================================
class LocalLLM:
    def __init__(self, model="mistral", base_url="http://127.0.0.1:11434/api/generate"):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt, system_prompt="Você é um assistente acadêmico estruturado."):
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{prompt}",
            "stream": False,  # 🔥 MUITO MAIS ESTÁVEL QUE STREAM
            "format": "json", # 🔥 FORÇA OLLAMA A RETORNAR APENAS JSON VÁLIDO
            "options": {
                "temperature": 0.3,
                "top_p": 0.8,
                "num_predict": 8192 # 🔥 GIGANTE para evitar cortar o JSON no meio
            }
        }

        try:
            res = requests.post(self.base_url, json=payload, timeout=120)

            if res.status_code != 200:
                raise Exception(res.text)

            data = res.json()
            return data.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            print("[Erro Ollama] servidor não está acessível")
            return "[Erro Conexão Ollama]"

        except Exception as e:
            print(f"[Erro Ollama] {e}")
            return "[Erro Interno Ollama]"


# =========================================================
# 🧠 GEMINI (OPCIONAL / FALLBACK)
# =========================================================
class GeminiLLM:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        self.client = None

        try:
            import google.generativeai as genai

            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                print("[!] GEMINI_API_KEY não encontrada")
                return

            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model_name)

        except ImportError:
            print("[!] google-generativeai não instalado (ignorado)")
        except Exception as e:
            print(f"[!] Gemini init erro: {e}")

    def generate(self, prompt, system_prompt="Você é um assistente acadêmico."):
        if not self.client:
            return "[Gemini indisponível]"

        try:
            full_prompt = f"{system_prompt}\n\n{prompt}"

            response = self.client.generate_content(
                full_prompt,
                generation_config={"temperature": 0.2}
            )

            return response.text.strip()

        except Exception as e:
            print(f"[Erro Gemini] {e}")
            return "[Erro Gemini]"