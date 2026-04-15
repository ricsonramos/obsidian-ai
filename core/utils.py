import re
import unicodedata


def normalize_title(title: str) -> str:
    """
    Normalização para COMPARAÇÃO de títulos (verificar se já existe):
    - Remove acentos
    - Lowercase
    - Substitui _ e - por espaço (para comparar "algebra_linear" == "Álgebra Linear")
    - Remove caracteres especiais exceto espaços e alfanuméricos
    - Colapsa múltiplos espaços
    """
    if not title:
        return ""
    # Remove acentos
    nfkd = unicodedata.normalize("NFKD", title)
    only_ascii = nfkd.encode("ASCII", "ignore").decode("utf-8")
    t = only_ascii.lower()
    # Normaliza separadores: _ e - viram espaço para comparação
    t = t.replace("_", " ").replace("-", " ")
    # Remove caracteres especiais exceto espaços e alfanuméricos
    t = re.sub(r"[^a-z0-9\s]", "", t)
    # Colapsa múltiplos espaços
    t = re.sub(r"\s+", " ", t).strip()
    return t


def title_to_slug(title: str) -> str:
    """
    Converte título para snake_case ASCII sanitizado (nome de arquivo).
    Ex: "Álgebra Linear" → "algebra_linear"
        "Cálculo Diferencial e Integral" → "calculo_diferencial_e_integral"
    """
    # Remove acentos
    nfkd = unicodedata.normalize("NFKD", title)
    only_ascii = nfkd.encode("ASCII", "ignore").decode("utf-8")
    t = only_ascii.lower()
    # Substitui espaços, hifens e underscores por espaço único primeiro
    t = re.sub(r"[\s\-_]+", " ", t)
    # Remove chars especiais
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = t.strip().replace(" ", "_")
    # Colapsa underscores múltiplos
    t = re.sub(r"_+", "_", t)
    return t
