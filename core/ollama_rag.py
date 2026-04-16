import os
import json
import requests
import re
from pypdf import PdfReader
from typing import List, Dict, Optional

class OllamaRAG:
    """
    Motor RAG Seletivo (Just-in-Time) para hardware limitado.
    Indexa apenas o sumário e extrai páginas sob demanda.
    """
    def __init__(self, host: str, model: str, log_callback: callable = None):
        self.host = host.rstrip("/")
        self.model = model
        self.log_callback = log_callback
        self._pdf_cache = {} # path -> {chapters: [{title: str, page: int}]}

    def _log(self, msg, level="info"):
        if self.log_callback:
            self.log_callback(msg, level)
        else:
            print(msg)

    def _get_pdf_outline(self, pdf_path: str) -> List[Dict]:
        """Extrai o sumário do PDF."""
        if pdf_path in self._pdf_cache:
            return self._pdf_cache[pdf_path]["chapters"]

        try:
            reader = PdfReader(pdf_path)
            outline = reader.outline
            chapters = []

            def process_outline(item):
                if isinstance(item, list):
                    for sub in item: process_outline(sub)
                else:
                    try:
                        page_num = reader.get_destination_page_number(item)
                        chapters.append({"title": item.title, "page": page_num})
                    except: pass

            process_outline(outline)
            
            # Se não houver sumário, tenta detectar capítulos nas primeiras 15 páginas
            if not chapters:
                chapters = self._fallback_chapter_detection(reader)

            self._pdf_cache[pdf_path] = {"chapters": chapters}
            return chapters
        except Exception as e:
            self._log(f"Erro ao ler PDF {pdf_path}: {e}", "error")
            return []

    def _fallback_chapter_detection(self, reader: PdfReader) -> List[Dict]:
        """Tenta detectar capítulos por palavras-chave se o outline falhar."""
        chapters = []
        # Tenta varrer as primeiras 15 páginas em busca de "SUMÁRIO" ou "ÍNDICE"
        for i in range(min(15, len(reader.pages))):
            text = reader.pages[i].extract_text()
            # Busca linhas que parecem capítulos: "Capítulo X", "1. Introdução ... 45"
            matches = re.finditer(r"(.*)\.{2,}\s*(\d+)$", text, re.MULTILINE)
            for m in matches:
                chapters.append({"title": m.group(1).strip(), "page": int(m.group(2)) - 1})
        return chapters

    def find_relevant_pages(self, pdf_path: str, topic: str) -> List[int]:
        """Identifica as páginas prováveis para um tema baseado no sumário."""
        chapters = self._get_pdf_outline(pdf_path)
        if not chapters:
            return [0, 1, 2, 3, 4] # Fallback: primeiras páginas

        best_match_idx = -1
        topic_clean = topic.lower()

        for i, ch in enumerate(chapters):
            if topic_clean in ch["title"].lower():
                best_match_idx = i
                break

        if best_match_idx != -1:
            start_page = chapters[best_match_idx]["page"]
            # Pega até a próxima entrada no sumário ou +15 páginas
            end_page = chapters[best_match_idx + 1]["page"] if best_match_idx + 1 < len(chapters) else start_page + 15
            # Garante limites
            return list(range(max(0, start_page), min(start_page + 20, end_page + 1)))
        
        return [0, 5, 10, 15] # Fallback

    def build_summary(self, topic: str, context: str) -> str:
        """Sintetiza via Ollama com limite de recursos."""
        prompt = f"""
Você é um especialista em Direito Penal acadêmico.
Resuma "{topic}" usando o CONTEXTO abaixo.

REGRAS:
1. Seja direto e use linguagem jurídica.
2. Máximo 2 parágrafos.
3. Se não encontrar no contexto, diga apenas "Informação não localizada".

CONTEXTO:
{context[:4000]}

SÍNTESE:
"""
        try:
            # Opções para aliviar o hardware
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "system": "Você sintetiza Direito Penal de forma direta e granular.",
                    "options": {
                        "num_thread": 4,
                        "num_predict": 400,
                        "temperature": 0.2
                    }
                },
                timeout=300
            )
            return response.json().get("response", "Erro na síntese.")
        except Exception as e:
            return f"Erro ao conectar com Ollama: {e}"

    def extract_text(self, pdf_path: str, pages: List[int]) -> str:
        """Extrai texto e limpa referências para economizar RAM."""
        text = ""
        try:
            reader = PdfReader(pdf_path)
            for p in pages:
                if p < len(reader.pages):
                    text += reader.pages[p].extract_text() + "\n"
            # Força limpeza do objeto reader
            del reader
        except Exception as e:
            self._log(f"Erro na extração de texto: {e}", "error")
        return text

    def enrich_note(self, filepath: str, forced_pdf_path: str = None, ignore_status: bool = False):
        """Lê nota, busca no PDF e atualiza com selos de segurança."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 🧹 LIMPEZA DE CABEÇALHO CORROMPIDO (Versões anteriores)
        if content.startswith('rag: "done"') or content.startswith('rag: done'):
            content = re.sub(r'^rag:.*?\nrag_date:.*?\n', '', content, flags=re.MULTILINE)
            content = re.sub(r'^---\s*\n---\s*\n', '---\n', content)

        fm_match = re.search(r"^---\s*(.*?)\s*---", content, re.DOTALL)
        if not fm_match: return
        
        import yaml
        import datetime
        metadata = yaml.safe_load(fm_match.group(1)) or {}
        
        # 🛡️ VERIFICAÇÃO DE SEGURANÇA (PULOS)
        status = metadata.get("status")
        if not ignore_status:
            if status == "enriched_ollama" or metadata.get("rag") == "done" or metadata.get("rag") == "skip":
                self._log(f"⏩ Pulando '{os.path.basename(filepath)}' (Já processada).")
                return
            
        if status not in ["waiting_ollama_rag", "research"]:
            if not ignore_status: return

        title = metadata.get("title") or os.path.basename(filepath).replace(".md", "")
        
        # 📚 DEFINIÇÃO DO LIVRO (PDF)
        if forced_pdf_path and os.path.exists(forced_pdf_path):
            pdf_path = forced_pdf_path
        else:
            source_dir = metadata.get("source_path") or os.getenv("PDF_SOURCE_PATH", "G:\\Meu Drive\\Vault 101\\02-Direito Penal\\Livros")
            pdfs = [f for f in os.listdir(source_dir) if f.endswith(".pdf")] if os.path.exists(source_dir) else []
            if not pdfs:
                self._log(f"⚠️ Nenhum PDF em {source_dir}", "warning")
                return
            pdf_path = os.path.join(source_dir, pdfs[0])

        pdf_name = os.path.basename(pdf_path)
        self._log(f"🔍 Usando {pdf_name} para '{title}'...")

        pages = self.find_relevant_pages(pdf_path, title)
        context = self.extract_text(pdf_path, pages)
        
        self._log(f"🧠 Ollama sintetizando '{title}' (Contexto otimizado)...")
        summary = self.build_summary(title, context)
        
        # ── ATUALIZAÇÃO INTELIGENTE DO CONTEÚDO ──
        placeholder = "(Aguardando processamento RAG via Ollama...)"
        new_section = f"## 📝 Resumo da Doutrina (RAG)\n{summary}\n\n#antigravity/rag-enriched"
        
        # Se já existe uma seção RAG (mesmo com erro), substitui ela inteira
        rag_pattern = r"## 📝 Resumo da Doutrina \(RAG\).*?#antigravity/rag-enriched"
        if re.search(rag_pattern, content, re.DOTALL):
            new_content = re.sub(rag_pattern, new_section, content, flags=re.DOTALL)
        elif placeholder in content:
            new_content = content.replace(placeholder, new_section)
        else:
            new_content = content.strip() + f"\n\n{new_section}\n"

        # 🛑 VERIFICAÇÃO DE ERROS NO SUMÁRIO
        if summary.startswith("Erro"):
            self._log(f"❌ Falha no enriquecimento de '{title}'. Tente novamente.", "error")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            return

        # ── INJEÇÃO DE SELOS NO YAML (SEGURO) ──
        # Atualiza status e adiciona metadados de controle
        new_content = re.sub(r"status:\s*['\"]?(\w+)['\"]?", 'status: "enriched_ollama"', new_content)
        
        # Injeção robusta: Insere logo após o primeiro ---
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if 'rag: "done"' in new_content:
            new_content = re.sub(r"rag:\s*.*", 'rag: "done"', new_content)
        else:
            # Garante que insere DENTRO do bloco YAML (após o primeiro ---)
            new_content = re.sub(r"^---\s*", f"---\nrag: \"done\"\nrag_date: \"{now_str}\"\n", new_content, count=1)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        self._log(f"✅ Nota '{title}' selada e enriquecida!")
