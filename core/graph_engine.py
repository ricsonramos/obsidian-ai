import os
import json
import logging
import re
import unicodedata
from typing import List

from pydantic import ValidationError

from core.hybrid_llm import HybridLLM
from core.vault_manager import VaultManager
from core.markdown_generator import MarkdownGenerator
from core.linker import Linker
from core.models import AntigravityResponse, NewNode

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

from core.utils import normalize_title

# Caminho padrão para stop words (relativo ao script)
_DEFAULT_STOP_WORDS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "config", "stop_words.txt"
)

def _load_stop_words(path: str) -> set[str]:
    """Carrega stop words do arquivo de configuração."""
    stop_words = set()
    resolved = os.path.abspath(path)
    if not os.path.exists(resolved):
        logging.warning(f"[StopWords] Arquivo não encontrado: {resolved}. Seguindo sem stop words.")
        return stop_words

    with open(resolved, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Normaliza a stop word para garantir match
                stop_words.add(normalize_title(line))

    logging.info(f"[StopWords] {len(stop_words)} termos carregados de '{resolved}'.")
    return stop_words


class GraphEngine:
    def __init__(
        self,
        dry_run: bool = False,
        resume: bool = False,
        target_stage: str = "all",
        max_tokens_budget: int = 2000,
    ):
        self.dry_run = dry_run
        self.resume = resume
        self.target_stage = str(target_stage).lower()
        self.max_tokens_budget = max_tokens_budget

        vault_path = os.getenv("VAULT_PATH", "./vault")
        self.vault = VaultManager(vault_path)
        self.llm = HybridLLM()
        self.linker = Linker(vault_path)

        self.max_nodes_total = int(os.getenv("MAX_NODES_TOTAL", "30"))
        self.total_nodes_generated = 0
        self._session_titles: set[str] = set()

        # Carrega stop words do arquivo de config
        stop_words_path = os.getenv("STOP_WORDS_PATH", _DEFAULT_STOP_WORDS_PATH)
        self.stop_words = _load_stop_words(stop_words_path)

        # Carrega prompt mestre
        prompt_default = os.path.join(os.path.dirname(__file__), "..", "prompt.txt")
        prompt_path = os.getenv("PROMPT_PATH", prompt_default)
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.master_prompt = f.read()
        except FileNotFoundError:
            self.master_prompt = "Arquiteto Taxonomista Antigravity.\n{title}\n{existing_notes}"

    # ─────────────────────────────────────────────────────────────
    # Ponto de entrada principal
    # ─────────────────────────────────────────────────────────────

    def run(self, topic: str, target_depth: int):
        self.base_topic = topic

        logging.info(f"🧠 Antigravity | Tema: '{topic}' | Profundidade: {target_depth}")

        run_stage_1 = self.target_stage in ["all", "1"]
        run_stage_2 = self.target_stage in ["all", "2"]
        run_stage_3 = self.target_stage in ["all", "3"]
        run_stage_4 = self.target_stage in ["all", "4", "link_all"]
        run_stage_5 = self.target_stage in ["all", "5", "link_all"]

        root_response: AntigravityResponse | None = None

        if run_stage_1:
            logging.info("=== STAGE 1: ANÁLISE TAXONÔMICA (Arquiteto) ===")
            root_response = self._call_architect(topic, depth=1)

            if not root_response:
                logging.error("Falha na chamada ao Arquiteto Taxonomista.")
                return

            self._process_response(root_response, depth=1)

        if run_stage_2 and root_response and target_depth > 1:
            logging.info("=== STAGE 2: EXPANSÃO RECURSIVA ===")
            ready_nodes = root_response.new_nodes
            self._expand_recursive(ready_nodes, current_depth=2, max_depth=target_depth)

        # Relatório final
        self._print_report()

        if run_stage_3:
            logging.info("=== STAGE 3: LINK (wikilinks) ===")
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

    # ─────────────────────────────────────────────────────────────
    # Gap Logic + Processamento da resposta do Arquiteto
    # ─────────────────────────────────────────────────────────────

    def _process_response(self, response: AntigravityResponse, depth: int):
        """
        Processa a resposta do Arquiteto v2 (schema new_nodes).
        - FOUNDATION_FIRST (level 0): cria hub + stubs L0 com backlinks.
        - EXPANSION (level 1+): cria notas de expansao normais.
        """
        ic = response.integrity_check
        nodes = response.new_nodes

        if ic.detected_redundancies:
            logging.info(f"  [MECE] Redundancias detectadas: {ic.detected_redundancies}")
        if ic.missing_foundations:
            logging.info(f"  [GAP] Fundamentos ausentes: {ic.missing_foundations}")

        foundation_nodes = [n for n in nodes if n.level == 0]
        expansion_nodes  = [n for n in nodes if n.level > 0]

        # Cria nota HUB do topico raiz se houver fundamentos
        if foundation_nodes and ic.action_priority == "FOUNDATION_FIRST":
            logging.info(f"  [GAP] FOUNDATION_FIRST — criando hub + {len(foundation_nodes)} nos L0...")
            prereq_links = [f"[[{n.display_name}]]" for n in foundation_nodes]
            self._create_root_hub_note(self.base_topic, "1_Core", prereq_links, depth)

            for node in foundation_nodes:
                self._create_new_node(node, depth, parent_topic=self.base_topic)
        else:
            for node in nodes:
                self._create_new_node(node, depth)

    def _create_root_hub_note(self, topic_title: str, level: str, prereq_links: list, depth: int):
        """Cria a nota MOC (hub) para o tópico raiz, conectando-o aos pré-requisitos."""
        if self._already_exists(topic_title):
            return

        filename = MarkdownGenerator.normalize_filename(topic_title)
        content = MarkdownGenerator.generate_hub_note(topic_title, level, prereq_links, depth)

        self._mark_visited(topic_title)

        if not self.dry_run:
            self.vault.save_node(filename, content, subfolder=self.base_topic)
            logging.info(f"  [HUB] {filename} (raiz com {len(prereq_links)} pré-requisitos)")
        else:
            logging.info(f"  [DRY-HUB] {filename}")

        self.total_nodes_generated += 1

    def _create_prerequisite_note(self, prereq: MissingPrerequisite, depth: int, parent_topic: str = ""):
        """Cria nota stub para pré-requisito faltante (Nível 0 / Foundation)."""
        normalized_name = normalize_title(prereq.name)

        if self._is_stop_word(normalized_name):
            logging.info(f"  [STOP] '{prereq.name}' é stop word — não decomponho mais.")
            return

        if self._already_exists(prereq.name):
            logging.info(f"  [SKIP] Pré-requisito já existe: '{prereq.name}'")
            return

        logging.info(f"  [L0] Criando pré-requisito: {prereq.name}")
        filename = MarkdownGenerator.normalize_filename(prereq.name)
        content = MarkdownGenerator.generate_prerequisite_stub(
            prereq.model_dump(), depth=depth, parent_topic=parent_topic
        )

        self._mark_visited(prereq.name)

        if not self.dry_run:
            self.vault.save_node(filename, content, subfolder=self.base_topic)
            logging.info(f"     [+] {filename}")
        else:
            logging.info(f"     [DRY-RUN] {filename}")

        self.total_nodes_generated += 1

    def _create_new_node(self, node: NewNode, depth: int, parent_topic: str = ""):
        """Cria nota a partir de um NewNode (schema v2)."""
        if self._already_exists(node.display_name) or self._already_exists(node.filename):
            logging.info(f"  [SKIP] Ja existe: '{node.display_name}'")
            return

        if node.filename and self._is_stop_word(normalize_title(node.filename)):
            logging.info(f"  [STOP] '{node.display_name}' e stop word.")
            return

        if self.total_nodes_generated >= self.max_nodes_total:
            logging.warning("[BUDGET] Limite de nos atingido.")
            return

        level_str = ["0_Foundation", "1_Core", "2_Advanced"][min(node.level, 2)]
        logging.info(f"  [NODE] {node.display_name} ({level_str})")

        node_dict = node.model_dump()
        # Injeta parent_topic como conexao se fornecido e ainda nao presente
        if parent_topic:
            parent_link = f"[[{parent_topic}]]"
            if parent_link not in node_dict.get("connections", []):
                node_dict.setdefault("connections", []).insert(0, parent_link)
            node_dict["parent"] = parent_topic

        filename = node.filename + ".md" if not node.filename.endswith(".md") else node.filename

        if node.level == 0:
            content = MarkdownGenerator.generate_prerequisite_stub(
                {"name": node.display_name, "reason": node.brief_definition, "priority": "high"},
                depth=depth,
                parent_topic=parent_topic,
            )
        else:
            content = MarkdownGenerator.generate_from_expansion_node(
                {**node_dict, "display_name": node.display_name}, level=level_str, depth=depth
            )

        self._mark_visited(node.display_name)
        self._mark_visited(node.filename)

        if not self.dry_run:
            self.vault.save_node(filename, content, subfolder=self.base_topic)
            logging.info(f"     [+] {filename}")
        else:
            logging.info(f"     [DRY-RUN] {filename}")

        self.total_nodes_generated += 1

    # ─────────────────────────────────────────────────────────────
    # Chamada ao LLM (Prompt Mestre)
    # ─────────────────────────────────────────────────────────────

    def _call_architect(self, title: str, depth: int) -> AntigravityResponse | None:
        """Chama o LLM com o Prompt Mestre e valida via Pydantic."""
        existing_notes = self.vault.get_existing_notes()
        # Limita a 60 slugs mais curtos para evitar JSON truncado por excesso de contexto
        existing_notes = sorted(existing_notes, key=len)[:60]
        existing_str = json.dumps(existing_notes, ensure_ascii=False)

        prompt = (
            self.master_prompt
            .replace("{title}", title)
            .replace("{existing_notes}", existing_str)
        )

        raw = self.llm.generate(prompt, depth=depth)
        if not raw:
            logging.error(f"LLM retornou vazio para '{title}'.")
            return None

        return self._parse_response(raw, title)

    def _parse_response(self, raw: str, title: str) -> AntigravityResponse | None:
        """Parseia e valida a resposta JSON do LLM com Pydantic."""
        try:
            clean = re.sub(r"```json\s*", "", raw)
            clean = re.sub(r"```\s*$", "", clean, flags=re.MULTILINE)
            start = clean.find("{")
            end = clean.rfind("}")
            if start != -1 and end != -1:
                clean = clean[start:end + 1]

            data = json.loads(clean)
            return AntigravityResponse.model_validate(data)

        except (json.JSONDecodeError, ValidationError) as e:
            logging.warning(f"[Parser] Falha ao validar resposta para '{title}': {e}")

            logging.info("[Parser] Tentando reparo via LLM...")
            schema_ref = (
                '{"integrity_check":{"detected_redundancies":[],"missing_foundations":[],'
                '"action_priority":"FOUNDATION_FIRST"},'
                '"new_nodes":[{"filename":"snake_case","display_name":"Nome","level":0,'
                '"brief_definition":"...","search_queries":["q1","q2"],"connections":["[[pai]]"]}]}'
            )
            repair = self.llm.generate(
                raw, depth=1,
                system_instruction=(
                    f"Fix this into valid JSON matching this schema exactly, no markdown:\n{schema_ref}"
                ),
            )
            try:
                r_start = repair.find("{")
                r_end = repair.rfind("}")
                if r_start != -1 and r_end != -1:
                    repair = repair[r_start:r_end + 1]
                data = json.loads(repair)
                return AntigravityResponse.model_validate(data)
            except Exception:
                logging.error(f"[Parser] Reparo falhou para '{title}'. Pulando no.")
                return None

    # ─────────────────────────────────────────────────────────────
    # Expansão recursiva
    # ─────────────────────────────────────────────────────────────

    def _expand_recursive(self, nodes: List[NewNode], current_depth: int, max_depth: int):
        if current_depth > max_depth:
            return

        if self.total_nodes_generated >= self.max_nodes_total:
            logging.warning("[BUDGET] Limite de nos atingido — abortando recursao.")
            return

        if not self._check_budget():
            logging.warning("\U0001f6d1 Orcamento de tokens esgotado — abortando recursao.")
            return

        limit = self._get_depth_decay_limit(current_depth)
        # Expande apenas nos de nivel 1+ (fundamentos nao precisam ser expandidos)
        nodes_to_expand = [n for n in nodes if n.level >= 1][:limit]

        next_layer: List[NewNode] = []

        for node in nodes_to_expand:
            if self._is_stop_word(normalize_title(node.display_name)):
                logging.info(f"  [STOP] '{node.display_name}' e stop word.")
                continue

            if self.total_nodes_generated >= self.max_nodes_total:
                break

            logging.info(f"  → Expandindo [L{current_depth}]: {node.display_name}")
            child_response = self._call_architect(node.display_name, depth=current_depth)

            if child_response:
                self._process_response(child_response, depth=current_depth)
                next_layer.extend(child_response.new_nodes)

        if next_layer:
            self._expand_recursive(next_layer, current_depth + 1, max_depth)

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────

    def _is_stop_word(self, normalized_title: str) -> bool:
        return normalized_title in self.stop_words

    def _already_exists(self, title: str) -> bool:
        normalized = normalize_title(title)
        return (
            normalized in self._session_titles
            or self.vault.has_visited(title)
        )

    def _mark_visited(self, title: str):
        normalized = normalize_title(title)
        self._session_titles.add(normalized)
        self.vault.add_visited(title)

    def _check_budget(self) -> bool:
        return self.llm.session_tokens < self.max_tokens_budget

    def _get_depth_decay_limit(self, current_depth: int) -> int:
        decay_str = os.getenv("DEPTH_DECAY_LIMITS", "5,3,2")
        try:
            limits = [int(x.strip()) for x in decay_str.split(",")]
        except ValueError:
            limits = [5, 3, 2]

        if current_depth == 1:
            return limits[0] if limits else 5
        elif current_depth == 2:
            return limits[1] if len(limits) > 1 else 3
        else:
            return limits[2] if len(limits) > 2 else 2

    def _print_report(self):
        logging.info("═══════════════════════════════════════")
        logging.info("📊 ANTIGRAVITY — RELATÓRIO DA SESSÃO")
        logging.info(f"  → Nós gerados       : {self.total_nodes_generated}")
        logging.info(f"  → Tokens consumidos : ~{int(self.llm.session_tokens)} / {self.max_tokens_budget}")
        logging.info(f"  → Chamadas ao LLM   : {self.llm._gemini_calls}")
        logging.info("═══════════════════════════════════════")