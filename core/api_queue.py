import json
import os
import time
import uuid


class APIQueue:
    def __init__(self, filepath="queue.json", max_retries=5, base_delay=5, max_delay=60):
        self.filepath = filepath
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        self.queue = self._load()

    # =========================
    # PERSISTÊNCIA
    # =========================
    def _load(self):
        if not os.path.exists(self.filepath):
            return []

        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.queue, f, indent=2, ensure_ascii=False)

    # =========================
    # ➕ ADICIONAR TASK
    # =========================
    def add(self, payload):
        task = {
            "id": str(uuid.uuid4()),
            "payload": payload,
            "status": "pending",
            "retries": 0,
            "last_error": None
        }

        self.queue.append(task)
        self._save()
        return task["id"]

    # =========================
    # PROCESSAR FILA
    # =========================
    def process(self, handler):
        for task in self.queue:
            if task["status"] == "done":
                continue

            delay = min(self.base_delay * (2 ** task["retries"]), self.max_delay)

            try:
                print(f"Processando...: {task['payload']['title']}")

                handler(task["payload"])

                task["status"] = "done"
                self._save()

            except Exception as e:
                task["retries"] += 1
                task["last_error"] = str(e)

                print(f" Erro: {e}")
                print(f" Retry {task['retries']} em {delay}s")

                self._save()

                if task["retries"] >= self.max_retries:
                    task["status"] = "failed"
                    print(f"Falhou definitivamente: {task['payload']['title']}")
                    self._save()
                    continue

                time.sleep(delay)