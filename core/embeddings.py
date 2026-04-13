# core/embeddings.py
import requests

class Embeddings:
    def __init__(self, model="nomic-embed-text"):
        self.model = model
        self.url = "http://127.0.0.1:11434/api/embeddings"

    def encode(self, text: str):
        r = requests.post(self.url, json={
            "model": self.model,
            "prompt": text
        })
        return r.json()["embedding"]