import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class HybridLLM:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._gemini_calls = 0
        self.session_tokens = 0

    def generate(self, prompt: str, depth: int = 1, system_instruction: str = "") -> str:
        """Roteador principal: usa Gemini Flash com resposta JSON nativa."""
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
        # Estimativa: 1 token ≈ 4 caracteres
        input_tokens = len(input_text) / 4
        output_tokens = len(output_text) / 4

        self.session_tokens += input_tokens + output_tokens

        gemini_in_cost = float(os.getenv("GEMINI_INPUT_COST", "0.10"))
        gemini_out_cost = float(os.getenv("GEMINI_OUTPUT_COST", "0.40"))

        input_cost = (input_tokens / 1_000_000) * gemini_in_cost
        output_cost = (output_tokens / 1_000_000) * gemini_out_cost
        total = input_cost + output_cost

        print(f"[Gemini] tokens: {int(input_tokens)}in / {int(output_tokens)}out")
        print(f"[Gemini] acumulado: ~{int(self.session_tokens)} tokens | custo sessão: ${total:.6f} USD")

    def _call_gemini_with_retry(self, prompt: str, system_instruction: str) -> str | None:
        import time
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

        for attempt in range(max_retries):
            try:
                result = self._call_gemini(prompt, system_instruction)
                if result is not None:
                    return result
            except requests.exceptions.RequestException as e:
                if hasattr(e, "response") and e.response is not None and getattr(e.response, "status_code", 0) == 429:
                    pass  # Rate limit — vai para retry
                else:
                    err_text = getattr(getattr(e, "response", None), "text", str(e))
                    logging.error(f"[Gemini API Error] {err_text}")
                    return None

            if attempt < max_retries - 1:
                wait = (2 ** attempt) + 1  # 2s, 5s, 9s
                print(f"[Gemini] Rate limit — aguardando {wait}s (retry {attempt + 2}/{max_retries})")
                time.sleep(wait)

        print("[Gemini] Esgotou retries — falha na geração.")
        return None

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent?key={self.gemini_key}"
        )

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.4")),
                "maxOutputTokens": int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "8192")),
                "response_mime_type": "application/json",  # JSON nativo — sem markdown wrapper
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        timeout = int(os.getenv("LLM_TIMEOUT", "60"))
        response = requests.post(url, json=payload, timeout=timeout)

        if not response.ok:
            response.raise_for_status()

        data = response.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Formato inesperado na resposta do Gemini: {data}") from e

    def get_embedding(self, text: str) -> list[float]:
        """Representação vetorial 768-D via gemini-embedding-001 (para Semantic Link)."""
        if not self.gemini_key:
            return []

        clean_text = text.replace("\n", " ").strip()
        if not clean_text:
            return []

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-embedding-001:embedContent?key={self.gemini_key}"
        )

        payload = {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": clean_text}]},
        }

        import time
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=payload, timeout=int(os.getenv("LLM_TIMEOUT", "60")))
                if resp.ok:
                    return resp.json().get("embedding", {}).get("values", [])
                if resp.status_code != 429:
                    logging.error(f"[Embeddings] API Error: {resp.text}")
                    return []
            except requests.exceptions.RequestException as e:
                logging.error(f"[Embeddings] Exceção de Rede: {e}")

            if attempt < max_retries - 1:
                wait = (2 ** attempt) + 1
                time.sleep(wait)

        return []
