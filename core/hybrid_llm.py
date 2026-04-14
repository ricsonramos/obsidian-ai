import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

class HybridLLM:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Migração do modelo
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.search_enabled = os.getenv("GEMINI_SEARCH_ENABLED", "false").lower() == "true"
        self._gemini_calls = 0

    def generate(self, prompt: str, depth: int, system_instruction: str = "") -> str:
        """Roteador principal: usa exclusivamente o Gemini para economizar tempo e processamento."""
        if not self.gemini_key:
            logging.error("GEMINI_API_KEY não configurada.")
            return ""

        try:
            response = self._call_gemini_with_retry(prompt, system_instruction)
            if response:
                self._gemini_calls += 1
                self._log_gemini_usage(prompt, response)
                return response
        except Exception as e:
            logging.error(f"Falha generalizada no Gemini: {e}")
            
        return ""

    def _log_gemini_usage(self, input_text: str, output_text: str):
        # Estimativa grosseira: 1 token ≈ 4 caracteres
        input_tokens = len(input_text) / 4
        output_tokens = len(output_text) / 4

        # Preço Gemini 2.5 Flash-Lite: $0.10/1M input, $0.40/1M output
        input_cost = (input_tokens / 1_000_000) * 0.10
        output_cost = (output_tokens / 1_000_000) * 0.40
        total = input_cost + output_cost

        print(f"[Gemini] tokens estimados: {int(input_tokens)} in / {int(output_tokens)} out")
        print(f"[Gemini] custo estimado: ${total:.6f} USD")
        print(f"[Gemini] total de chamadas nesta sessão: {self._gemini_calls}")

    def _call_gemini_with_retry(self, prompt: str, system_instruction: str, max_retries: int = 3) -> str | None:
        import time
        for attempt in range(max_retries):
            try:
                result = self._call_gemini(prompt, system_instruction)
                if result is not None:
                    return result
            except requests.exceptions.RequestException as e:
                # Tratar possivel 429 status
                if hasattr(e, 'response') and e.response is not None and getattr(e.response, "status_code", 0) == 429:
                     pass
                else:
                    error_details = getattr(e, 'response', None)
                    err_text = error_details.text if error_details is not None else str(e)
                    logging.error(f"[Gemini API Error] {err_text}")
                    return None # falha real sem ser 429

            if attempt < max_retries - 1:
                wait = (2 ** attempt) + 1  # 2s, 5s, 9s
                print(f"[Gemini] Rate limit — aguardando {wait}s antes de retry {attempt + 2}/{max_retries}")
                time.sleep(wait)

        print("[Gemini] Esgotou retries — falha na geração do conteúdo.")
        return None

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 8192
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
            
        if self.search_enabled:
            payload["tools"] = [{"google_search": {}}]
            
        response = requests.post(url, json=payload, timeout=60)
        if not response.ok:
            error_message = response.text
            response.raise_for_status()
            
        data = response.json()
        
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Formato inesperado na resposta do Gemini: {data}") from e
