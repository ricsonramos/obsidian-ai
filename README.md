# 🌌 Antigravity: Autonomous Knowledge Management Engine

**Antigravity** is a sophisticated autonomous system designed to transform a single thematic query into a structured, interconnected, and academically grounded knowledge base within Obsidian. It acts as an **Autonomous Curriculum Architect**, ensuring that learners никогда do not encounter advanced concepts without a solid grasp of their foundation.

---

## 🎯 Context: The Learning Entropy Problem
In traditional self-directed study, learners often face two major hurdles:
1.  **The Prerequisite Gap**: Diving into "Machine Learning" without "Linear Algebra" leads to shallow understanding and frustration.
2.  **Information Fragmentation (Islands)**: Notes are often created as isolated entities, failing to reflect the interconnected nature of knowledge.

Antigravity solves this by applying **Autonomous Taxonomy Decomposition** and **Graph-Based Connectivity**.

---

## 🚀 The Solution: 5-Stage Knowledge Synthesis

Antigravity operates through a deterministic 5-stage pipeline:

### Stage 1: Taxonomic Analysis (The Architect)
Utilizes LLM reasoning (Gemini Flash) to decompose a topic. 
- **Backtracking Logic**: Identifies missing L0 (Fundamental) prerequisites. 
- **MECE Strategy**: Ensures notes are Mutuamente Exclusivos e Coletivamente Exaustivos (no overlaps).

### Stage 2: Recursive Expansion (The Builder)
Recursively expands the graph based on the target depth.
- **Tree-to-Graph Transition**: Each node generates sub-nodes, building a hierarchy from L0 (Foundation) to L2+ (Advanced).

### Stage 3: Wikilink Audit (The Auditor)
A local validation layer that scans the generated content to ensure all internal `[[wikilinks]]` point to existing or planned files, preventing "ghost links."

### Stage 4: Active Cross-Link (The Librarian)
Scans the entire vault using **Universal Normalization**. It identifies mentions of existing topics within new text and automatically creates backlinks, ensuring the graph is densely populated.

### Stage 5: Semantic Vector Bridge (The Neural Linker)
The apex of the system. It uses **Mathematical Vector Embeddings** (RAG) to "understand" the meaning of notes.
- **Cosine Similarity**: If two notes share high semantic proximity (>0.82) but aren't linked, Antigravity forces a connection.

---

## 🎨 Antigravity Dashboard (The Command Center) [NEW]

The system now features a modern, real-time dashboard built with **Next.js** and **FastAPI**. 
- **Motivo**: Centralizar o controle de um sistema autônomo complexo, permitindo monitoramento visual de logs e configurações "on-the-fly".
- **Real-time Logs**: Integração via WebSocket para acompanhar cada passo do motor (Taxonomia, RAG e Linking).
- **Gerenciamento de Vault**: Alteração dinâmica de temas e caminhos de biblioteca sem reiniciar o serviço.

---

## 🧠 Local RAG Engine (Ollama Integration) [NEW]

A key evolution in the Antigravity ecosystem is the **Selective Local RAG**. Instead of relying on cloud synthesis, it uses local models (via Ollama) to process authoritative PDF sources (books).
- **Motivo (Privacidade & Custo)**: Garantir que a síntese doutrinária seja 100% offline e gratuita, protegendo o conhecimento acadêmico do usuário.
- **Hardware-Aware (CPU Optimized)**: Projetado para rodar em hardware limitado (CPUs sem GPUs potentes).
  - **Otimização de Contexto**: Janelas de contexto dinâmicas (4k-6k chars) para evitar gargalos.
  - **Throttling Inteligente**: Controle de threads e limites de tokens para manter o sistema responsivo durante a síntese.
- **Controle Granular**: Escolha qual livro específico deve servir de base para cada matéria no Dashboard.
- **Selo de Integridade**: Sistema de "tags" e status no YAML (`status: enriched_ollama`) para evitar re-processamento desnecessário.

---

## 🛠️ Implementation Details

### Universal Normalization Engine
To prevent duplication (e.g., "Álgebra" vs "algebra"), Antigravity uses a custom normalization layer:
- **Accent Stripping**: Accents and special characters are removed for comparison.
- **Slugification**: Consistent snake_case for filenames.
- **Root-Word Comparison**: The engine compares the "essence" of titles to enforce MECE principles.

### Integrity Check Schema (v2)
Every LLM call is validated against a strict Pydantic schema:
- `detected_redundancies`: Active monitoring of existing vault nodes.
- `missing_foundations`: Hard requirement for L0 nodes before L1+ expansion.
- `action_priority`: Decides between `FOUNDATION_FIRST` or `EXPANSION`.

---

## 💻 Technology Stack

- **Backend**: FastAPI / Python 3.10+
- **Frontend**: Next.js 14+ (Dashboard Interativo)
- **Local Brain (RAG)**: [Ollama](https://ollama.com/) (Models: `llama3`, `phi3`, `gemma`).
- **Cloud Brain (Logic)**: [Google Gemini 1.5 Flash](https://aistudio.google.com/).
- **Persistence**: Obsidian Markdown (YAML Frontmatter + Wikilinks).
- **Hardware Management**: Custom thread-throttling & context windowing.

---

## ⚙️ Configuration (.env)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `VAULT_PATH` | Absolute path to your Obsidian vault. | Required |
| `PDF_SOURCE_PATH` | Path to your local library (Books/PDFs). | Required |
| `OLLAMA_MODEL` | Local model for RAG synthesis. | `llama3` |
| `SEMANTIC_THRESHOLD` | Sensitivity of Stage 5 linking (0.0 to 1.0). | 0.82 |

---

## 🏃 Quick Start (Dashboard Mode)

1.  **Clone & Install**:
    ```bash
    git clone https://github.com/RicsonRamos/obsidian-ai.git
    pip install -r requirements.txt
    ```
2.  **Configure**: Add your `GEMINI_API_KEY` to `.env` and configure `VAULT_PATH`.
3.  **Launch Ecosystem**:
    ```bash
    # Starts both FastAPI and Next.js Dashboard
    python run_dashboard.py
    ```
4.  **Enrich**: Select your book in the Sidebar and click **Brain: Enrich Notes** to start the local RAG.

---

## 🔮 Expectations & Roadmap

Antigravity aims to be the definitive "Artificial Librarian" for Obsidian:
- **Auto-Image Generation**: Inserção automática de diagramas gerados por AI nas notas.
- **Cross-Vault Synergy**: Inteligência para carregar conceitos de diferentes vaults (ex: Direito e Sociologia) para síntese transdisciplinar.
- **Persistent Memory**: Memória de longo prazo para o motor não repetir explicações já dadas em outras notas.

---

## 📜 Research License
This tool is built for students, researchers, and knowledge workers who wish to automate the **scaffolding** of their learning, allowing them to focus on active synthesis rather than manual organization.
