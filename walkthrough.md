# Refatoração Finalizada: Knowledge Engine Architecture

A refatoração agressiva do Knowledge Graph Engine foi integralmente concluída, estabelecendo proteções físicas e comportamentais para torná-lo rápido, minimalista e altamente escalável para o Obsidian.

## 🛠️ Mudanças no Núcleo

### O Motor Anti-Explosão (`core/graph_engine.py`)
- **Implementada Árvore Vertical Genuína**: A expansão 2.0 agora flui extraindo e varrendo iterativamente apenas o atributo estrito `subconcepts` retornado pelo LLM em vez de transbordar listas aleatórias, respeitando a separação de semântica vertical x horizontal.
- **Limites Físicos Adicionados**: Foram integrados o `max_nodes_total` via Variável de Ambiente (com trava padrão de 25 nós) e o fatiamento absoluto da API `queue_subconcepts[:max_branching_rate]`.
- **Lógica de `Depth Decay`**: O escopo recursivo perde força progressivamente. Nível 1 espalha até 6 ramos, Nível 2 reduz para 3, Nível 3 é asfixiado para 1 (freio brusco de redundâncias desnecessárias).

### O Roteador Semântico Avançado
- **Split Modding Prompt**: O script instiga o LLM dinamicamente dependendo da sua posição na árvore geradora. Tópicos RAIZ exigem apenas um mini-JSON `(title, definition, core, connections)` e Tópicos FOLHAS abarcam as referências expandidas, impedindo gasto de tokens na etapa inicial.
- As restrições de formatações (`definition: 1 frase rigorosa`) foram injetadas nos parsers JSON dinâmicos.

### Gerador Passivo (`core/markdown_generator.py`) e Validação (`core/linker.py`)
- O Markdown Generator não sofre mais com a quebra de estrutura quando a API omite referências (Ex: Omissões de `mechanism` viram omissões ou strings perfeitamente controladas ao invés de lançar chaves estouradas).
- O antigo `Linker` abandonou as substituições ineficientes (`Regex` pesados no corpo inteiro do texto) e agora funciona apenas como um "Auditor" (STAGE 3) — Ele cruza as conexões semânticas montadas no YAML `[[ ]]` com os arquivos que existem no Vault, indicando se algum nó criado é Fantasma (Dead-link), garantindo que as lacunas sigam à risca sua restrição técnica!

## 🧪 Como Testar

A profundidade padrão (Default) no `main.py` foi atualizada de 1 para 2 como requisitado. Logo:

```bash
python main.py graph "machine learning" --dry-run
```

A flag de teste listará precisamente a taxa de decaimento via log, a média paramétrica formatada e o impedidor natural de limites. Se estiver satisfeito, basta retirar o flag.
