import os
import asyncio
import logging
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv, set_key

from core.graph_engine import GraphEngine
from core.research_manager import ResearchManager
from core.vault_manager import VaultManager

# Configuração básica
load_dotenv()
app = FastAPI(title="Antigravity API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Gerenciador de WebSocket (Logs em Tempo Real) ──────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str, level: str = "info"):
        data = {"message": message, "level": level}
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                pass

manager = ConnectionManager()

# ── Modelos de Dados ───────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str

class ConfigUpdate(BaseModel):
    vault_path: Optional[str] = None
    theme: Optional[str] = None

# ── Utilitários de Engine ──────────────────────────────────────────

async def run_graph_task(topic: str, depth: int, vault_path: str):
    loop = asyncio.get_running_loop()
    await manager.broadcast(f"🚀 Iniciando mapeamento: '{topic}' em {vault_path}", level="info")
    
    def log_callback(message: str, level: str = "info"):
        # Forma robusta de agendar uma corrotina a partir de uma thread externa
        asyncio.run_coroutine_threadsafe(manager.broadcast(message, level), loop)

    try:
        engine = GraphEngine(
            dry_run=False,
            resume=False,
            target_stage="all",
            max_tokens_budget=int(os.getenv("MAX_TOKENS_BUDGET", "2000")),
            log_callback=log_callback,
            vault_path=vault_path
        )
        await loop.run_in_executor(None, engine.run, topic, depth)
        await manager.broadcast(f"✅ Mapeamento de '{topic}' concluído!", level="info")
    except Exception as e:
        await manager.broadcast(f"❌ Erro no motor: {str(e)}", level="error")

class EnrichRequest(BaseModel):
    pdf_name: Optional[str] = None
    force_all: bool = False
    vault_path: Optional[str] = None
    note_paths: Optional[List[str]] = None

async def run_enrich_task(vault_path: str, pdf_name: str = None, force_all: bool = False, note_paths: List[str] = None):
    loop = asyncio.get_running_loop()
    await manager.broadcast("🔍 Iniciando processo RAG seletivo...", level="info")
    
    from core.ollama_rag import OllamaRAG
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    
    def log_callback(msg, level="info"):
        asyncio.run_coroutine_threadsafe(manager.broadcast(msg, level), loop)

    try:
        rag = OllamaRAG(host, model, log_callback=log_callback)
        vpath = os.path.abspath(vault_path)
        
        forced_pdf_path = None
        if pdf_name:
            source_dir = os.getenv("PDF_SOURCE_PATH", "G:\\Meu Drive\\Vault 101\\02-Direito Penal\\Livros")
            forced_pdf_path = os.path.join(source_dir, pdf_name)

        # Se o usuário selecionou notas específicas, usamos apenas elas
        if note_paths:
            md_files = [os.path.join(vpath, p) if not os.path.isabs(p) else p for p in note_paths]
        else:
            # Caso contrário, varremos o vault
            md_files = []
            for root, dirs, files in os.walk(vpath):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.endswith(".md"):
                        md_files.append(os.path.join(root, file))
        
        await manager.broadcast(f"📂 Processando {len(md_files)} alvos selecionados.", level="info")
        
        count = 0
        for f in md_files:
            try:
                if not os.path.exists(f): continue
                
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                    
                    if force_all or note_paths: # Se foi selecionado manualmente, forçamos o processamento
                        if 'rag: "skip"' in content or "rag: skip" in content:
                            continue
                        is_pending = True
                    else:
                        is_pending = any(s in content for s in [
                            'status: "waiting_ollama_rag"', "status: 'waiting_ollama_rag'", "status: waiting_ollama_rag",
                            'status: "research"', "status: 'research'", "status: research"
                        ])
                    
                    if is_pending:
                        count += 1
                        await loop.run_in_executor(None, rag.enrich_note, f, forced_pdf_path, force_all)
            except Exception as e:
                print(f"Erro em {f}: {e}")
                continue
            
        await manager.broadcast(f"✨ Concluído! {count} notas atualizadas.", level="info")
    except Exception as e:
        await manager.broadcast(f"❌ Erro no RAG: {str(e)}", level="error")

# ── Endpoints ──────────────────────────────────────────────────────

@app.get("/api/config")
async def get_config():
    return {
        "vault_path": os.getenv("VAULT_PATH", "./vault"),
        "theme": os.getenv("APP_THEME", "obsidian"),
        "depth": int(os.getenv("DEFAULT_DEPTH", "2")),
    }

@app.get("/api/pdfs")
async def list_pdfs():
    source_dir = os.getenv("PDF_SOURCE_PATH", "G:\\Meu Drive\\Vault 101\\02-Direito Penal\\Livros")
    if not os.path.exists(source_dir):
        return {"pdfs": []}
    pdfs = [f for f in os.listdir(source_dir) if f.endswith(".pdf")]
    return {"pdfs": sorted(pdfs)}

@app.get("/api/notes/pending")
async def list_pending_notes():
    vault_path = os.getenv("VAULT_PATH", "./vault")
    vpath = os.path.abspath(vault_path)
    pending = []
    
    if not os.path.exists(vpath):
        return {"notes": []}
        
    for root, dirs, files in os.walk(vpath):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".md"):
                fpath = os.path.join(root, file)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                        is_pending = any(s in content for s in [
                            'status: "waiting_ollama_rag"', "status: 'waiting_ollama_rag'", "status: waiting_ollama_rag",
                            'status: "research"', "status: 'research'", "status: research"
                        ])
                        if is_pending:
                            # Retorna o caminho relativo para facilitar na UI
                            rel_path = os.path.relpath(fpath, vpath)
                            pending.append({"name": file, "path": rel_path})
                except: continue
    return {"notes": pending[:50]} # Limita a 50 para não sobrecarregar a UI

@app.post("/api/enrich")
async def start_enrichment(req: EnrichRequest, background_tasks: BackgroundTasks):
    current_vault = req.vault_path or os.getenv("VAULT_PATH", "./vault")
    background_tasks.add_task(run_enrich_task, current_vault, req.pdf_name, req.force_all, req.note_paths)
    return {"status": "started", "message": "Motor RAG iniciado."}

@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    env_path = ".env"
    if config.vault_path:
        clean_path = config.vault_path.strip().strip("'").strip('"')
        os.environ["VAULT_PATH"] = clean_path
        set_key(env_path, "VAULT_PATH", clean_path)
    if config.theme:
        os.environ["APP_THEME"] = config.theme
        set_key(env_path, "APP_THEME", config.theme)
    return {"status": "updated"}

@app.get("/api/fs/list")
async def list_folders(path: str = "."):
    try:
        abs_path = os.path.abspath(path)
        items = []
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            for entry in os.scandir(abs_path):
                if entry.is_dir() and not entry.name.startswith("."):
                    items.append({"name": entry.name, "path": entry.path})
        return {
            "current_path": abs_path,
            "parent_path": os.path.dirname(abs_path),
            "folders": sorted(items, key=lambda x: x["name"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_interaction(msg: ChatMessage, background_tasks: BackgroundTasks):
    text = msg.message.lower()
    current_vault = os.getenv("VAULT_PATH", "./vault")
    
    if "gerar" in text or "mapear" in text or "graph" in text:
        topic = text.replace("gerar", "").replace("mapear", "").replace("graph", "").replace("sobre", "").strip()
        if not topic:
            return {"response": "Por favor, informe o tópico que deseja mapear."}
        
        background_tasks.add_task(run_graph_task, topic, int(os.getenv("DEFAULT_DEPTH", "2")), current_vault)
        return {"response": f"Entendido! Iniciei o mapeamento de '{topic}' no vault: {current_vault}"}

    elif "enriquecer" in text or "rag" in text or "sintetizar" in text:
        background_tasks.add_task(run_enrich_task, current_vault)
        return {"response": "Iniciando motor RAG local via Ollama. Vou ler os PDFs e preencher os resumos das notas pendentes."}

    elif "link" in text or "conectar" in text:
        return {"response": "Ainda estou aprendendo a linkar via chat, mas você pode usar o comando 'graph' para tudo!"}

    return {"response": "Olá! Eu sou o Antigravity. O que vamos mapear ou enriquecer hoje?"}

@app.websocket("/api/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Mantém a conexão viva
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
