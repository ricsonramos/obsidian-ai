import os
import json
import logging
import re
from typing import List, Dict

from core.hybrid_llm import HybridLLM
from core.vault_manager import VaultManager
from core.markdown_generator import MarkdownGenerator
from core.linker import Linker

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

class GraphEngine:
    def __init__(self, dry_run: bool = False, resume: bool = False, target_stage: str = "all"):
        self.dry_run = dry_run
        self.resume = resume
        self.target_stage = str(target_stage).lower()

        vault_path = os.getenv("VAULT_PATH", "./vault")
        self.vault = VaultManager(vault_path)
        self.llm = HybridLLM()
        self.linker = Linker(vault_path)

        # Controle de Crescimento Exponencial
        self.max_nodes_total = int(os.getenv("MAX_NODES_TOTAL", "25"))
        self.total_nodes_generated = 0
        self.total_children_accumulated = 0
        self._session_titles = set()
        
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.master_prompt = f.read()
        except FileNotFoundError:
            self.master_prompt = "Vocês gera JSON estrito. Output schema:\n{json_schema}"

    def run(self, topic: str, target_depth: int):
        self.base_topic = topic
        logging.info(f"Geometria Acionada | Alvo: '{topic}' | Dep: {target_depth} | Limite Global: {self.max_nodes_total} nós")

        run_stage_1 = self.target_stage in ["all", "1"]
        run_stage_2 = self.target_stage in ["all", "2"]
        run_stage_3 = self.target_stage in ["all", "3"]

        root_nodes = []

        # =========================
        # ESTÁGIO 1 — ÁRVORE RAIZ
        # =========================
        if run_stage_1:
            logging.info("=== STAGE 1: DECOMPOSE (ROOT) ===")
            root_nodes = self._process_node(topic, generation_depth=1)
            
            if not root_nodes:
                logging.error("Falha na geração do nó raiz.")
                return

            self._save_nodes(root_nodes, 1)
            self.total_nodes_generated += len(root_nodes)

        # =========================
        # ESTÁGIO 2 — EXPANSÃO RECURSIVA (Subconcepts)
        # =========================
        if run_stage_2:
            logging.info("=== STAGE 2: EXPAND (RECURSION) ===")
            if not root_nodes:
                 logging.error("Sem nós base para iniciar recursividade.")
                 return
                 
            if target_depth > 1:
                self._expand_recursive(root_nodes, current_depth=2, max_depth=target_depth)

        # =========================
        # LOGGING E OBSERVABILIDADE
        # =========================
        if self.total_nodes_generated > 0:
             avg_branch = self.total_children_accumulated / self.total_nodes_generated
        else:
             avg_branch = 0.0
             
        logging.info("=======================================")
        logging.info("📊 RELATÓRIO DO MOTOR DE CONHECIMENTO")
        logging.info(f"-> [total_nodes_generated]: {self.total_nodes_generated}")
        logging.info(f"-> [branching_factor_avg] : {avg_branch:.1f}")
        logging.info(f"-> [tokens_estimated]     : [Registrados e contidos via HybridLLM]")
        logging.info("=======================================")

        # =========================
        # ESTÁGIO 3 — AUTOLINKER / VALIDADOR
        # =========================
        if run_stage_3:
            logging.info("=== STAGE 3: LINK ===")
            if not self.dry_run:
                self.linker.run()
            else:
                 logging.info("[DRY-RUN] Modificações locais do Linker evitadas.")
                 
    def _get_depth_decay_limit(self, current_depth: int) -> int:
        """Função crítica: Depth Decay (Atrofia progressiva da curva recursiva combinatória)"""
        if current_depth == 1:
            return 6  # Nível 1 - Amplo
        elif current_depth == 2:
            return 3  # Nível 2 - Retração agressiva  (~50%)
        elif current_depth == 3:
            return 1  # Nível 3 - Visão ultra direcional sem espalhamento
        return 0      # Depth 4+ cortado preventivamente
        
    def _expand_recursive(self, parent_nodes: List[Dict], current_depth: int, max_depth: int):
        if current_depth > max_depth or self.total_nodes_generated >= self.max_nodes_total:
             return
             
        max_branching_rate = self._get_depth_decay_limit(current_depth)
        
        # Puxa APENAS subconcepts dos nós pai para expandir (Geração Vertical Pura)
        queue_subconcepts = []
        for p in parent_nodes:
             subs = p.get("subconcepts", [])
             queue_subconcepts.extend(subs)

        # Trunca para manter estrito o escopo da expansão combinatória (Poda)
        queue_subconcepts = queue_subconcepts[:max_branching_rate]
        
        if not queue_subconcepts:
             return
             
        self.total_children_accumulated += len(queue_subconcepts)
        new_layer_nodes = []
        
        for sub_topic in queue_subconcepts:
            if self.total_nodes_generated >= self.max_nodes_total:
                logging.warning("⚠️ Limite max_nodes_total atingido (Explosion Prevent).")
                break
                
            if self._already_exists(sub_topic):
                continue
                
            logging.info(f"-> Recursividade de expansão [L{current_depth}]: {sub_topic}")
            subs_nodes = self._process_node(sub_topic, current_depth)
            
            if subs_nodes:
                self._save_nodes(subs_nodes, current_depth)
                self.total_nodes_generated += len(subs_nodes)
                new_layer_nodes.extend(subs_nodes)
                
        # Mantém escavando os próximos níveis...
        if new_layer_nodes:
             self._expand_recursive(new_layer_nodes, current_depth + 1, max_depth)

    def _already_exists(self, title: str) -> bool:
        """Centraliza validação entre arquivos locais de outras sessões e o andamento em memória."""
        normalized = title.lower().strip()
        if normalized in self._session_titles:
             return True
        if self.vault.has_visited(title):
             return True
        return False

    def _save_nodes(self, nodes: List[Dict], depth: int):
        for node in nodes:
            self._session_titles.add(node.get("title", "").lower().strip())
            self.vault.add_visited(node.get("title", ""))
            
            if not self.dry_run:
                md_text = MarkdownGenerator.generate(node, depth)
                filename = MarkdownGenerator.normalize_filename(node.get("title", "Untitled"))
                filepath = self.vault.save_node(filename, md_text, subfolder=self.base_topic)
                logging.info(f"     [+] Gravado: {filename}")
            else:
                logging.info(f"     [DRY-RUN] Processado nó: {node.get('title', '')}")

    def _process_node(self, topic: str, generation_depth: int) -> List[Dict]:
        """Faz requisição manipulando os Schemas variando Nível (Ligthweight Level 1 vs Expanded)"""
        
        schema_level_1 = '''{
  "nodes": [
    {
      "title": "string",
      "definition": "1 frase curta rigorosa",
      "core": ["até 3 itens chaves fundamentais"],
      "connections": ["links (associações semânticas laterais)"],
      "subconcepts": ["links (sugestões parciais para expansão vertical)"]
    }
  ]
}'''

        schema_level_full = '''{
  "nodes": [
    {
      "title": "string",
      "definition": "1 frase curta rigorosa",
      "core": ["até 3 itens principais"],
      "mechanism": ["até 3 passos dinâmicos curtos"],
      "examples": ["até 2 nomes de exemplo"],
      "applications": ["até 3 usos"],
      "connections": ["links (grafo lateral)"],
      "subconcepts": ["links (ramos estruturais diretos)"],
      "level": "foundational | intermediate | advanced"
    }
  ]
}'''
        target_schema = schema_level_1 if generation_depth == 1 else schema_level_full
        
        prompt = self.master_prompt.replace("{title}", topic).replace("{depth}", str(generation_depth)).replace("{json_schema}", target_schema)
        resp = self.llm.generate(prompt, depth=1)
        data = self._extract_json(resp)
        
        raw_nodes = data.get("nodes", [])
        
        # CORTA FORÇADO SE LLM NÃO RESPEITOU MAX_CHILDREN
        raw_nodes = raw_nodes[:5]
        
        valid_nodes = []
        for n in raw_nodes:
            title = n.get("title", "")
            definition = n.get("definition", "")
            
            if not title or not definition:
                continue
                
            if len(definition) < 10:
                continue
                
            valid_nodes.append(n)
            
        return valid_nodes

    def _extract_json(self, response: str) -> dict:
        if not response or not response.strip():
            return {}
        try:
            clean = re.sub(r"```json\s*", "", response)
            clean = re.sub(r"```\s*$", "", clean)
            
            start = clean.find("{")
            end = clean.rfind("}")
            if start != -1 and end != -1:
                clean = clean[start:end+1]
            return json.loads(clean)
        except json.JSONDecodeError:
            logging.warning("JSON Corrompido. Instanciando reparo...")
            repair = self.llm.generate(f"JSON Original:\n\n{response}", depth=1, system_instruction="Você retorna um único objeto JSON funcional válido contendo apenas formatação com chaves adequadas.")
            try:
                r_start = repair.find("{")
                r_end = repair.rfind("}")
                if r_start != -1 and r_end != -1:
                     repair = repair[r_start:r_end+1]
                return json.loads(repair)
            except Exception:
                return {}