"""
Pydantic models para validação da resposta do LLM (schema Arquiteto Taxonomista Antigravity).
"""
import re
import unicodedata
from typing import Literal, List

from pydantic import BaseModel, field_validator


def _sanitize_filename(value: str) -> str:
    """Enforcement de snake_case ASCII puro para nomes de arquivo."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("utf-8")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9_\s-]", "", normalized)
    normalized = re.sub(r"[\s\-]+", "_", normalized).strip("_")
    return normalized


class SubjectInfo(BaseModel):
    title: str
    level: Literal["0_Foundation", "1_Core", "2_Advanced"]
    status: Literal["missing_prerequisites", "ready_to_expand"]


class MissingPrerequisite(BaseModel):
    name: str
    reason: str
    priority: Literal["high", "medium", "low"] = "high"


class ExpansionNode(BaseModel):
    filename: str
    display_name: str
    brief_definition: str
    search_queries: List[str]
    connections: List[str] = []

    @field_validator("filename", mode="before")
    @classmethod
    def sanitize_filename(cls, v: str) -> str:
        sanitized = _sanitize_filename(str(v))
        if not sanitized:
            raise ValueError(f"filename inválido após sanitização: '{v}'")
        return sanitized


class AntigravityResponse(BaseModel):
    subject_info: SubjectInfo
    missing_prerequisites: List[MissingPrerequisite] = []
    expansion_nodes: List[ExpansionNode] = []
