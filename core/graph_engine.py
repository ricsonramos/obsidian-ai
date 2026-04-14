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
    def __init__(self, dry_run: bool = False, resume: bool = False, target_stage: str = "all", max_tokens_budget: int = 2000):
        self.dry_run = dry_run
        self.resume = resume
        self.target_stage = str(target_stage).lower()
        self.max_tokens_budget = max_tokens_budget

        vault_path = os.getenv("VAULT_PATH", "./vault")
        self.vault = VaultManager(vault_path)
        self.llm = HybridLLM()
        self.linker = Linker(vault_path)

        # Controle Estrito Exponencial
        self.max_nodes_total = int(os.getenv("MAX_NODES_TOTAL", "25"))
        self.total_nodes_generated = 0
        self.total_children_accumulated = 0
        self._session_titles = set()
        
        prompt_default = os.path.join(os.path.dirname(__file__), "..", "prompt.txt")
        prompt_path = os.getenv("PROMPT_PATH", prompt_default)
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.master_prompt = f.read()
        except FileNotFoundError:
            self.master_prompt = "Gerador de Sumário Skeleton.\n{json_schema}"

    def run(self, topic: str, target_depth: int):
        self.base_topic = topic

        logging.info(f"Modo Esqueleto (Indexador) | Alvo: '{topic}' | Dep: {target_depth} | Orçamento: {self.max_tokens_budget}")

        run_stage_1 = self.target_stage in ["all", "1"]
        run_stage_2 = self.target_stage in ["all", "2"]
        run_stage_3 = self.target_stage in ["all", "3"]
        run_stage_4 = self.target_stage in ["all", "4", "link_all"]
        run_stage_5 = self.target_stage in ["all", "5", "link_all"]

        root_nodes = []

        if run_stage_1:
            logging.info("=== STAGE 1: ANCORAGEM RAIZ ===")
            root_nodes = self._process_node(topic, generation_depth=1)
            
            if not root_nodes:
                logging.error("Falha na geração taxonômica.")
                return

            self._save_nodes(root_nodes, 1)
            self.total_nodes_generated += len(root_nodes)

        if run_stage_2:
            logging.info("=== STAGE 2: DESDOBRAMENTO EM ÁRVORE ===")
            if not root_nodes:
                 return
                 
            if target_depth > 1:
                self._expand_recursive(root_nodes, current_depth=2, max_depth=target_depth)

        # Relatorio Final do Orçamento
        if self.total_nodes_generated > 0:
             avg_branch = self.total_children_accumulated / self.total_nodes_generated
        else:
             avg_branch = 0.0
             
        logging.info("=======================================")
        logging.info("📊 BUDGET & TAXONOMY REPORT")
        logging.info(f"-> [Índices extraídos] : {self.total_nodes_generated}")
        logging.info(f"-> [Branch factor]     : {avg_branch:.1f} subtemas por pasta")
        logging.info(f"-> [Tokens Consumidos] : ~{int(self.llm.session_tokens)} / {self.max_tokens_budget} Limit")
        logging.info("=======================================")

        if run_stage_3:
            logging.info("=== STAGE 3: LINK ===")
            if not self.dry_run:
                self.linker.run()
                
        if run_stage_4:
            logging.info("=== STAGE 4: ACTIVE CROSS-LINK ===")
            if not self.dry_run:
                self.linker.cross_link_vault()
                
        if run_stage_5:
            logging.info("=== STAGE 5: SEMANTIC VECTOR BRIDGE ===")
            if not self.dry_run:
                self.linker.semantic_link_vault(self.llm)
                 
    def _rank_nodes(self, nodes: List[Dict], limit: int) -> List[Dict]:
        """Num fluxo puro de esqueleto, a relevância repousa em quantos braços válidos a árvore apresentou."""
        for n in nodes:
            score = len(n.get("subconcepts", [])) * 2
            n["_importance_score"] = score
            
        return sorted(nodes, key=lambda x: x.get("_importance_score", 0), reverse=True)[:limit]

    def _get_depth_decay_limit(self, current_depth: int) -> int:
        decay_str = os.getenv("DEPTH_DECAY_LIMITS", "5,3,2")
        try:
             limits = [int(x.strip()) for x in decay_str.split(',')]
        except ValueError:
             limits = [5, 3, 2]
             
        if current_depth == 1:
            return limits[0] if len(limits) > 0 else 5
        elif current_depth == 2:
            return limits[1] if len(limits) > 1 else 3
        elif current_depth >= 3:
            return limits[2] if len(limits) > 2 else 2
        return 0
        
    def _check_budget(self) -> bool:
        if self.llm.session_tokens >= self.max_tokens_budget:
             return False
        return True
        
    def _expand_recursive(self, parent_nodes: List[Dict], current_depth: int, max_depth: int):
        if current_depth > max_depth or self.total_nodes_generated >= self.max_nodes_total:
             return
             
        if not self._check_budget():
             logging.warning(f"🛑 Expansão barrada! Orçamento esgotado.")
             return
             
        # Limita pros top ramos 
        rank_limit = int(os.getenv("RANK_NODES_LIMIT", "5"))
        parents_ranked = self._rank_nodes(parent_nodes, limit=rank_limit)
        max_branching_rate = self._get_depth_decay_limit(current_depth)
        
        queue_subconcepts = []
        for p in parents_ranked:
             subs = p.get("subconcepts", [])
             queue_subconcepts.extend(subs)

        queue_subconcepts = queue_subconcepts[:max_branching_rate]
        
        if not queue_subconcepts:
             return
             
        self.total_children_accumulated += len(queue_subconcepts)
        new_layer_nodes = []
        
        for sub_topic in queue_subconcepts:
            if self.total_nodes_generated >= self.max_nodes_total:
                break
                
            if not self._check_budget():
                 break
                
            if self._already_exists(sub_topic):
                continue
                
            logging.info(f"-> Indexando folha [L{current_depth}]: {sub_topic}")
            subs_nodes = self._process_node(sub_topic, current_depth)
            
            if subs_nodes:
                self._save_nodes(subs_nodes, current_depth)
                self.total_nodes_generated += len(subs_nodes)
                new_layer_nodes.extend(subs_nodes)
                
        if new_layer_nodes:
             self._expand_recursive(new_layer_nodes, current_depth + 1, max_depth)

    def _already_exists(self, title: str) -> bool:
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
                logging.info(f"     [+] Mapa gerado: {filename}")
            else:
                logging.info(f"     [DRY-RUN] Roteirizado: {node.get('title', '')}")

    def _process_node(self, topic: str, generation_depth: int) -> List[Dict]:
        schema_skeleton = '''{
  "nodes": [
    {
      "title": "string",
      "definition": "1 frase crua (o que é estritamente)",
      "subconcepts": ["sub-area pertinente 1", "sub-area pertinente 2", "etc"]
    }
  ]
}'''
        prompt = self.master_prompt.replace("{title}", topic).replace("{depth}", str(generation_depth)).replace("{json_schema}", schema_skeleton)
        resp = self.llm.generate(prompt, depth=1)
        data = self._extract_json(resp)
        
        raw_nodes = data.get("nodes", [])
        
        # Num mapeador raiz, o teto de 5 indices de arvore direta é satisfatório
        raw_nodes = raw_nodes[:5]
        
        valid_nodes = []
        for n in raw_nodes:
            title = n.get("title", "")
            if not title:
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
            logging.warning("JSON reparo fallback (Map Mode)...")
            repair = self.llm.generate(f"{response}", depth=1, system_instruction="Fix into valid rigid JSON schema with no markdown.")
            try:
                r_start = repair.find("{")
                r_end = repair.rfind("}")
                if r_start != -1 and r_end != -1:
                     repair = repair[r_start:r_end+1]
                return json.loads(repair)
            except Exception:
                return {}