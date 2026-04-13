# Second Brain AI (Local Offline) Llama 3.2 3B Edition

A infraestrutura completa do seu Second Brain foi estabelecida e o MVP funcional encontra-se na pasta `d:\Documentos\VsCode\projetos_git\obsidian-ai`!

## O que foi construído 🏗️

> [!CAUTION]
> **O MODO FULL AUTO FOI BLOQUEADO COMO PEDIDO**. A IA só vai apontar links Markdown (`[[ ]]`) para conceitos **se e somente se** o conceito já existir na pasta `01_Concepts` como arquivo. Foi aplicado proteção usando Whitelisting do Os.path e detecção regex para impedir "explosão de notas vazias".

1. **Vault Structure**: As pastas raízes `00_Inbox`, `01_Concepts`, `02_Skills`, `03_Projects` e `04_Daily` foram mapeadas e preparadas para você apontar o Obsidian em cima.
2. **Local AI Engine (`core/llm.py`)**: Ligação direta com Ollama usando restrições essenciais para um i5 3rd gen. O `num_ctx` está capado para não engasgar o hardware e o prompt força a linguagem em Português BR e a resposta ser unicamente os subtítulos da nota.
3. **Structured Stubs (`core/markdown_generator.py`)**: A IA é envolvida em um Wrapper Python que sempre entrega blocos predefinidos na nota e aplica um **Callout explícito na nota** avisando que veio do Llama para controle humano da integridade.

## Como Usar o Cérebro 🧠🚀

### 1. Setup Técnico
Abra seu terminal pelo próprio VSCode e certifique-se que o Ollama está habilitado.
```bash
cd 99_System/python_core
pip install -r requirements.txt
# Certifique-se que o ollama ligue o daemon primeiro
ollama serve 
```

### 2. Função 1: Inbox (Captura Fast-Thought)
Quando quiser registrar sem gastar CPU/Tempo do modelo:
```bash
python brain.py inbox "Vi hoje um conceito legal chamado Agentic RAG, pesquisar mais."
```
Nenhuma IA roda aqui. Ele simplesmente joga um registro em Markdown no `00_Inbox` com Timestamp.

### 3. Função 2: Geração de Conceito (Processamento Deep)
Quando achar pertinente solidificar conhecimento:
```bash
python brain.py concept "Redes Neurais" "São sistemas da computação inspirados na mente biológica com pesos e viés."
```
Aqui o sistema brilha. O Llama 3.2 3B vai traduzir sua linha boba numa nota completa com "Definição Simples" e "Explicação Técnica", buscar se alguma palavra escrita cruza com **Conceitos já criados antes baseados na Whitelist** (SEMI-AUTO) e vai exportar para `01_Concepts/Redes Neurais.md`.

### 4. Função 3: Auto-Daily Notes
Reunir seus pensamentos do Inbox no fim do dia:
```bash
python brain.py daily
```
Todo o texto que estava largado no Inbox vai ser compilado via IA, resumido em bullet-points analíticos ligados pelo Semi-Auto Linker e armazenado em `04_Daily` com a data atual.

> [!TIP]
> **Adicione atalhos de terminal**: Posteriormente será muito útil adicionar Alias no Windows ou um Hotkey nativo no Obsidian para acionar esses sub-comandos Python sem precisar abrir terminal.
