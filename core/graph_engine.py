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
from core.models import AntigravityResponse, ExpansionNode, MissingPrerequisite

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
            ready_nodes = root_response.expansion_nodes
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
        Implementa a Gap Logic:
          1. Se status == 'missing_prerequisites', cria PRIMEIRO a nota raiz do tópico
             (que age como hub), listando todos os pré-requisitos como links.
          2. Cria os stubs L0 (com backlink para o hub).
          3. Cria os expansion_nodes normais.
        """
        status = response.subject_info.status
        level = response.subject_info.level
        topic_title = response.subject_info.title or self.base_topic

        if status == "missing_prerequisites" and response.missing_prerequisites:
            logging.info(f"  ⚠️  Pré-requisitos faltantes detectados — criando nota raiz e stubs L0...")

            # Cria a nota raiz do tópico (o HUB do grafo)
            prereq_links = [f"[[{p.name}]]" for p in response.missing_prerequisites]
            self._create_root_hub_note(topic_title, level, prereq_links, depth)

            # Cria as notas L0 com backlink para o tópico raiz
            for prereq in response.missing_prerequisites:
                self._create_prerequisite_note(prereq, depth, parent_topic=topic_title)

        for node in response.expansion_nodes:
            self._create_expansion_note(node, level=level, depth=depth)

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

    def _create_expansion_note(self, node: ExpansionNode, level: str, depth: int):
        """Cria nota de expansão para um conceito mapeado."""
        if self._already_exists(node.display_name) or self._already_exists(node.filename):
            logging.info(f"  [SKIP] Já existe: '{node.display_name}'")
            return

        if self.total_nodes_generated >= self.max_nodes_total:
            logging.warning("[BUDGET] Limite de nós atingido — abortando expansão.")
            return

        logging.info(f"  [NODE] {node.display_name} ({level})")
        filename = node.filename + ".md" if not node.filename.endswith(".md") else node.filename
        content = MarkdownGenerator.generate_from_expansion_node(
            node.model_dump(), level=level, depth=depth
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
            # Limpa eventuais wrappers de markdown mesmo com response_mime_type
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

            # Tentativa de reparo via LLM
            logging.info("[Parser] Tentando reparo via LLM...")
            repair = self.llm.generate(
                raw,
                depth=1,
                system_instruction=(
                    "Fix the following into a valid JSON object matching this schema exactly, "
                    "no markdown, no extra text:\n"
                    '{"subject_info":{"title":"...","level":"0_Foundation|1_Core|2_Advanced",'
                    '"status":"missing_prerequisites|ready_to_expand"},'
                    '"missing_prerequisites":[{"name":"...","reason":"...","priority":"high"}],'
                    '"expansion_nodes":[{"filename":"snake_case","display_name":"...","brief_definition":"...",'
                    '"search_queries":["...","..."],"connections":[]}]}'
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
                logging.error(f"[Parser] Reparo falhou para '{title}'. Pulando nó.")
                return None

    # ─────────────────────────────────────────────────────────────
    # Expansão recursiva
    # ─────────────────────────────────────────────────────────────

    def _expand_recursive(self, nodes: List[ExpansionNode], current_depth: int, max_depth: int):
        if current_depth > max_depth:
            return

        if self.total_nodes_generated >= self.max_nodes_total:
            logging.warning("[BUDGET] Limite de nós atingido — abortando recursão.")
            return

        if not self._check_budget():
            logging.warning("🛑 Orçamento de tokens esgotado — abortando recursão.")
            return

        limit = self._get_depth_decay_limit(current_depth)
        nodes_to_expand = nodes[:limit]

        next_layer: List[ExpansionNode] = []

        for node in nodes_to_expand:
            if self._is_stop_word(normalize_title(node.display_name)):
                logging.info(f"  [STOP] '{node.display_name}' é stop word — não decompõe mais.")
                continue

            if self.total_nodes_generated >= self.max_nodes_total:
                break

            logging.info(f"  → Expandindo [L{current_depth}]: {node.display_name}")
            child_response = self._call_architect(node.display_name, depth=current_depth)

            if child_response:
                self._process_response(child_response, depth=current_depth)
                next_layer.extend(child_response.expansion_nodes)

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