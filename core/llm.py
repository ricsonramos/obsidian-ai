import requests

class LocalLLM:
    def __init__(self, model="llama3.2:3b", base_url="http://127.0.0.1:11434/api/generate"):
        self.model = model
        self.base_url = base_url
    
    def generate(self, prompt, system_prompt="Você é um assistente acadêmico conciso. Responda estruturadamente em Português do Brasil."):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2, # Muito conservador, reduz alucinação  
                "num_ctx": 2048     # Limitado para i5 3rd gen
            }
        }
        
        try:
            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.exceptions.ConnectionError:
            print("[Erro da API] Falha na conexão. O Ollama está rodando?")
            return "[Erro de Conexão]"
        except Exception as e:
            print(f"[Erro da API] Erro: {e}")
            return "[Erro Interno]"
