# 🧠 Obsidian AI — Second Brain Local (Llama + Graph Engine)

Sistema de Second Brain local baseado em IA, integrado ao Obsidian, com geração automática de conhecimento estruturado, grafo de conceitos e suporte a LLMs locais (Ollama) e cloud (Gemini API).

---

## 🚀 Visão Geral

O **Obsidian AI** é um sistema de memória cognitiva aumentada que transforma notas simples em uma **rede semântica de conhecimento vivo**.

Ele combina:

- 🧠 LLM local (Ollama + Llama 3.2 3B)
- ☁️ LLM cloud (Google Gemini API opcional)
- 🕸 Graph Engine (expansão recursiva de conceitos)
- 📁 Vault estruturado no padrão Obsidian
- 🔗 Auto-linking semântico controlado (whitelist)

---

## 🧱 Arquitetura do Sistema

```

obsidian-ai/
│
├── 00_Inbox/         # Captura rápida de ideias (raw input)
├── 01_Concepts/      # Conhecimento estruturado (IA)
├── 02_Skills/        # Habilidades em desenvolvimento
├── 03_Projects/      # Projetos ativos
├── 04_Daily/         # Resumos diários gerados por IA
│
├── 99_System/
│   ├── python_core/
│   │   ├── brain.py
│   │   ├── core/
│   │   │   ├── llm.py
│   │   │   ├── vault_manager.py
│   │   │   ├── markdown_generator.py
│   │   │   ├── linker.py

````

---

## 🧠 Módulos Principais

### 1. Inbox (Captura rápida)
Registro de ideias sem processamento de IA.

```bash
python brain.py inbox "Ideia bruta"
````

✔ rápido
✔ sem custo de LLM
✔ armazenamento imediato

---

### 2. Concept Engine (IA estruturada)

Transforma ideias em conhecimento organizado:

```bash
python brain.py concept "Redes Neurais" "Sistema inspirado no cérebro humano"
```

Gera automaticamente:

* Definição simples
* Explicação técnica
* Exemplos práticos
* Auto-linking para conceitos existentes

---

### 3. Graph Engine (Knowledge Graph Generator)

Sistema avançado de expansão de conhecimento.

```bash
python brain.py graph "Redes Neurais" "Sistema inspirado no cérebro humano" --depth 2
```

Gera:

* Rede de conceitos interligados
* Subconceitos automaticamente criados
* Links bidirecionais no Obsidian
* Expansão recursiva controlada

Exemplo:

```
Redes Neurais
 ├── Neurônio Artificial
 ├── Backpropagation
 ├── Gradient Descent
 ├── Função de Ativação
```

---

### 4. Daily Engine

Resumo automático de aprendizado diário:

```bash
python brain.py daily
```

* Consolida Inbox
* Remove redundâncias
* Gera insights estruturados

---

## 🤖 Modelos de IA Suportados

### 🟢 Local (default)

* Ollama
* Llama 3.2 3B
* Offline-first
* Baixo consumo de hardware

### ☁️ Cloud (opcional)

* Google Gemini API
* Modelos: gemini-1.5-flash
* Ideal para expansão pesada de grafo

---

## ⚙️ Graph Engine (Core Feature)

O sistema utiliza um **Graph Expansion Engine** com:

* Parsing resiliente de JSON
* Fallback automático para outputs quebrados
* Proteção contra loops
* Depth control (recursão limitada)
* Deduplicação básica de nós

### Exemplo de saída:

```json
{
  "nodes": [
    {
      "title": "Backpropagation",
      "content": "Algoritmo de ajuste de pesos..."
    }
  ]
}
```

---

## 🧠 Características Técnicas

* Python 3.10+
* Arquitetura modular (core separated)
* Obsidian-first design
* LLM-agnostic (local + cloud)
* Safe JSON parser para LLMs não determinísticos
* Auto-linking controlado por whitelist
* Vault-based knowledge storage

---

## 🔗 Auto-Linking Inteligente

O sistema conecta automaticamente conceitos existentes:

```
[[Redes Neurais]] ↔ [[Backpropagation]]
```

Mas apenas se o conceito já existir no vault.

---

## ⚠️ Limitações

* Modelos pequenos podem gerar JSON inconsistente
* Graph recursion deve ser controlada (`--depth`)
* Performance depende do backend LLM (local ou cloud)

---

## 🚀 Roadmap

* [ ] Graph Engine 3.0 (recursão avançada)
* [ ] Deduplicação semântica (embeddings)
* [ ] Visual graph export
* [ ] UI dashboard (Obsidian plugin)
* [ ] Multi-agent reasoning system
* [ ] Hybrid routing (local vs cloud LLM)

---

## 🧠 Filosofia do Projeto

> “Transformar conhecimento passivo em uma rede viva de aprendizado contínuo.”

O sistema não apenas armazena notas — ele **expande conhecimento automaticamente**.

---

## 📦 Setup

```bash
cd 99_System/python_core
pip install -r requirements.txt
python brain.py inbox "test"
```

---

## 🤝 Tecnologias

* Python
* Ollama
* Llama 3.2 3B
* Google Gemini API
* Obsidian Vault
* Markdown Knowledge Graph

---

## 🧠 Autor

Sistema experimental de Second Brain AI com foco em:

* IA local
* graph-based knowledge
* augmentation of human cognition

---

## 📌 Status

🚧 Em desenvolvimento ativo (MVP funcional)
