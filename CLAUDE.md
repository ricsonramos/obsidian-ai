# Knowledge Engine — Claude Code Context

## Visão geral do projeto
CLI Python que recebe um conceito (ex: "redes neurais"), usa o Gemini API e gera um grafo de conhecimento interligado salvo como
arquivos Markdown num vault do Obsidian.

---

## Estrutura do projeto

```
knowledge-engine/
├── CLAUDE.md                    # este arquivo
├── main.py                      # CLI entrypoint (argparse)
├── prompt.txt                   # prompt externo (lido em runtime pelo load_prompt())
├── .env                         # variáveis de ambiente (nunca commitar)
├── .env.example                 # template público das variáveis
├── requirements.txt
├── core/
│   ├── hybrid_llm.py            # router: Exclusivo Gemini API (Chat + Embeddings)
│   ├── graph_engine.py          # pipeline 5 estágios: decompose → expand → link → regex_link → semantic_link
│   ├── vault_manager.py         # salva .md no vault do Obsidian
│   ├── markdown_generator.py    # formata conteúdo como Markdown compatível com Obsidian
│   └── linker.py                # AutoLinker: Auditor, Regex Linker e Semantic Linker
└── vault/                       # output do vault Obsidian (conteúdo no .gitignore)
```

---

## Como rodar

```bash
# gerar grafo completo com todos os 5 estágios
python main.py graph "redes neurais" --depth 2

# rodar apenas a manutenção de links (Estágios 4 e 5)
python main.py link

# rodar apenas um estágio específico de links
python main.py link --stage 4  # Apenas Regex Lexical
python main.py link --stage 5  # Apenas Semantic Vector
```

---

## Variáveis de ambiente (.env)

```
GEMINI_API_KEY=your_key_here
GEMINI_DAILY_LIMIT=40
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_SEARCH_ENABLED=true
GEMINI_INPUT_COST=0.10
GEMINI_OUTPUT_COST=0.40

LLM_MAX_RETRIES=3
LLM_TIMEOUT=60
LLM_TEMPERATURE=0.4
LLM_MAX_OUTPUT_TOKENS=8192

VAULT_PATH=./vault
DEFAULT_DEPTH=2
MAX_TOKENS_BUDGET=2000
PROMPT_PATH=./prompt.txt
DEPTH_DECAY_LIMITS=5,3,2
RANK_NODES_LIMIT=5
SEMANTIC_THRESHOLD=0.82
```

---

## Stack de LLMs

### Gemini 2.x (API remota)
- **Chat**: Usado para todas as queries de desdobramento (decomposição e expansão estruturada).
- **Embeddings**: Usado o modelo `gemini-embedding-001` para o Estágio 5.

### Lógica do LLM router
O router `HybridLLM` gerencia unicamente a API remota de cloud configurada via `GEMINI_API_KEY`. Possui cache local para embeddings para evitar chamadas redundantes.

---

## Pipeline do GraphEngine (5 estágios)

### Estágio 1 — DECOMPOSE
- LLM gera apenas o mapa conceitual: títulos + relações.

### Estágio 2 — EXPAND
- LLM gera conteúdo rico para cada título (mínimo 150 palavras).

### Estágio 3 — LINK (Auditor)
- AutoLinker varre nós gerados e valida links estruturais reportados pelo LLM.

### Estágio 4 — REGEX LINK (Lexical)
- Scraper local que injeta `[[wikilinks]]` no corpo do texto usando Regex (Zero API cost).
- Ordena por tamanho de título para evitar colisões.

### Estágio 5 — SEMANTIC LINK (Vector Bridge)
- Usa Embeddings e Similiaridade de Cosseno para unir "ilhas" de conhecimento.
- Cache local em `.embeddings_cache.json` baseado em `mtime`.

---

## JSON contract — todas as respostas LLM devem seguir este schema

```json
{
  "nodes": [
    {
      "title": "string",
      "content": "string (mínimo 150 caracteres)",
      "level": "foundational | intermediate | advanced",
      "relations": ["Título do nó relacionado"]
    }
  ]
}
```

---

## Formato de saída no vault Obsidian

Cada arquivo `.md` deve ter exatamente esta estrutura:

```markdown
---
tags: [knowledge-engine, {level}]
relations: [[Nó A]], [[Nó B]]
generated: {ISO datetime}
source_depth: {depth}
---

# {Title}

{content}

## 🔗 Relações
- [[Nó Relacionado 1]]
- [[Nó Relacionado 2]]
```

---

## Regras de desenvolvimento (nunca violar)

1. NUNCA salvar nó no vault antes de passar por `is_valid_node()`.
2. SEMPRE usar `gemini-embedding-001` para Stage 5 (v1beta endpoint).
3. O cache `.embeddings_cache.json` DEVE ser respeitado para economizar API.
4. O `SEMANTIC_THRESHOLD` controla a agressividade das pontes do Stage 5.

---

## Checklist de validação

- [ ] `python main.py graph "redes neurais" --depth 2` roda com Stage 4 e 5.
- [ ] `python main.py link` atualiza conexões sem chamar Chat API.
- [ ] `.embeddings_cache.json` é criado no vault.
- [ ] Diferentes grafos (ilhas) são unidos na aba "Relações".