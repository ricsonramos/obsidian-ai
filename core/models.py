"""
Pydantic models para validação da resposta do LLM (schema v2 Antigravity).
Novo schema com integrity_check para deduplicação MECE e backtracking.
"""
from typing import Literal, List
from pydantic import BaseModel, field_validator
from core.utils import title_to_slug


class IntegrityCheck(BaseModel):
    detected_redundancies: List[str] = []
    missing_foundations: List[str] = []
    action_priority: Literal["FOUNDATION_FIRST", "EXPANSION"] = "EXPANSION"


class NewNode(BaseModel):
    filename: str
    display_name: str
    level: int  # 0 = Foundation, 1 = Core, 2 = Advanced
    search_queries: List[str]
    connections: List[str] = []
    brief_definition: str = ""

    @field_validator("filename", mode="before")
    @classmethod
    def sanitize_filename(cls, v: str) -> str:
        sanitized = title_to_slug(str(v))
        if not sanitized:
            raise ValueError(f"filename inválido após sanitização: '{v}'")
        return sanitized


class AntigravityResponse(BaseModel):
    integrity_check: IntegrityCheck = IntegrityCheck()
    new_nodes: List[NewNode] = []

    # ── Compatibilidade reversa com schema v1 ──────────────────────
    # Se o LLM ainda retornar o schema antigo, esses campos são aceitos
    # e convertidos internamente pelo GraphEngine.
    subject_info: dict = {}
    missing_prerequisites: List[dict] = []
    expansion_nodes: List[dict] = []
