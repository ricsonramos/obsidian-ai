# Knowledge Engine — Claude Code Context

## Visão geral do projeto
CLI Python que recebe um conceito (ex: "redes neurais"), usa um router híbrido
Gemini API + Ollama local, e gera um grafo de conhecimento interligado salvo como
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
│   ├── hybrid_llm.py            # router: Gemini depth=1 → Ollama depth 2+
│   ├── graph_engine.py          # pipeline 3 estágios: decompose → expand → link
│   ├── vault_manager.py         # salva .md no vault do Obsidian
│   ├── markdown_generator.py    # formata conteúdo como Markdown compatível com Obsidian
│   └── linker.py                # AutoLinker: injeta [[wikilinks]] entre nós
└── vault/                       # output do vault Obsidian (conteúdo no .gitignore)
```

---

## Como rodar

```bash
# gerar grafo com depth 2 (raiz via Gemini, filhos via Ollama)
python main.py graph "redes neurais" --depth 2

# sobrescrever modelo Ollama para essa execução
python main.py graph "transformers" --depth 3 --ollama-model deepseek-r1:14b

# dry run: imprime nós sem salvar no vault
python main.py graph "backpropagation" --dry-run
```

---

## Variáveis de ambiente (.env)

```
GEMINI_API_KEY=your_key_here
GEMINI_DAILY_LIMIT=40
OLLAMA_MODEL=qwen3:8b
OLLAMA_URL=http://localhost:11434/api/generate
VAULT_PATH=./vault
```

---

## Stack de LLMs

### Gemini 2.0 Flash (API remota)
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
- Usado SOMENTE em depth=1 (decomposição do conceito raiz)
- Quota rastreada por sessão via `self._gemini_calls` e `GEMINI_DAILY_LIMIT`
- Fallback automático para Ollama se quota esgotada ou se a chamada falhar
- Temperature: 0.4, maxOutputTokens: 8192

### Ollama (local)
- Endpoint: `http://localhost:11434/api/generate`
- Modelo padrão: configurável via env (recomendado: `qwen3:8b` ou `deepseek-r1:14b`)
- Usado para: depth 2+, repair de JSON inválido, passagem do AutoLinker
- Sempre usar `"stream": false` e timeout de 120s

### Lógica do HybridLLM router
```
depth == 1 AND quota_disponivel AND gemini_key presente → Gemini
caso contrário → Ollama
falha no Gemini → fallback Ollama (sem lançar exceção)
```

---

## Pipeline do GraphEngine (3 estágios obrigatoriamente separados)

### Estágio 1 — DECOMPOSE
- LLM gera apenas o mapa conceitual: títulos + relações (sem conteúdo ainda)
- Entrada: conceito raiz + profundidade
- Saída: lista de `{ title, relations[] }`

### Estágio 2 — EXPAND
- Para cada título gerado no estágio 1, chamada LLM isolada gera conteúdo rico
- Mínimo 150 palavras por nó
- Cada chamada é independente das outras (sem contexto compartilhado entre filhos)

### Estágio 3 — LINK
- AutoLinker varre todos os nós gerados
- Injeta `[[wikilinks]]` onde títulos de outros nós são mencionados no conteúdo
- Atualiza os arquivos já salvos no vault

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

### Extração de JSON
- Usar contagem de profundidade de colchetes (não regex) para lidar com estruturas aninhadas
- Se parse falhar: chamada secundária ao Ollama para repair do JSON quebrado
- Se repair também falhar: logar erro e pular o nó (nunca travar o pipeline)

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

### Regras para nomes de arquivo
- Lowercase
- Espaços → underscores
- Remover caracteres especiais (acentos, pontuação)
- Exemplo: "Redes Neurais Convolucionais" → `redes_neurais_convolucionais.md`

---

## Regras de desenvolvimento (nunca violar)

1. NUNCA acoplar os 3 estágios do pipeline — cada um deve ser método separado
2. NUNCA salvar nó no vault antes de passar por `is_valid_node()`
3. SEMPRE passar `depth` ao `HybridLLM.generate()` para o router funcionar corretamente
4. SEMPRE usar caminhos absolutos para escrita de arquivos no vault
5. O `prompt.txt` é lido em runtime por `load_prompt()` — nunca hardcodar o prompt no código
6. O set `self.visited` usa `.lower()` para deduplicação — títulos no vault preservam o case original
7. Nós rejeitados por `is_valid_node()` devem ser logados com `[REJECTED]` prefix

---

## Gates de qualidade — is_valid_node()

Um nó é rejeitado se qualquer condição abaixo for verdadeira:
- `title` vazio ou None
- `content` vazio ou None
- `len(content) < 100`
- título já existe em `self.visited` (case-insensitive)
- content é substring ou cópia de outro nó já processado

---

## Checklist de validação (rodar antes de considerar tarefa concluída)

- [ ] `python main.py graph "redes neurais" --depth 2` roda sem erros
- [ ] Mínimo 5 arquivos `.md` criados em `./vault/`
- [ ] Cada arquivo tem frontmatter YAML válido
- [ ] `[[wikilinks]]` aparecem nas seções de relações
- [ ] Gemini é chamado apenas 1 vez (depth=1), Ollama faz o resto
- [ ] Rodar o mesmo comando duas vezes não cria nós duplicados
- [ ] `--dry-run` não cria nenhum arquivo
- [ ] Google Search ativo: saída do Gemini contém citações de fontes reais
- [ ] Modelo Gemini: confirmar que NÃO está usando gemini-2.0-flash
- [ ] Retry funcionando: forçar 429 e verificar espera de 2s/5s/9s nos logs
- [ ] Custo logado após cada chamada Gemini bem-sucedida

---

## Ordem sugerida de implementação

1. Estrutura de pastas + `.env.example` + `requirements.txt`
2. `core/hybrid_llm.py` — HybridLLM com Gemini + Ollama + fallback
3. `prompt.txt` — prompt mestre para knowledge graphs (em português)
4. `core/graph_engine.py` — GraphEngine com 3 estágios separados
5. `core/vault_manager.py` + `core/markdown_generator.py` + `core/linker.py`
6. `main.py` — CLI com argparse
7. Rodar checklist de validação completo