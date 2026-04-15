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

### NotebookLM Workflow
Generates specialized search manifests (`research_list.txt`) optimized for **Google NotebookLM**. It provides:
- **Academic Queries**: Specific technical strings (ArXiv/Scholar optimized) to feed the researcher.
- **Context Stubs**: Temporary notes that wait for human/AI content insertion after deeper research.

---

## 💻 Technology Stack

- **Core Engine**: Python 3.10+
- **Brain**: [Google Gemini 2.5 Flash](https://aistudio.google.com/) (Superior speed/cost ratio).
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/) (Strict JSON data contracts).
- **Persistence**: Obsidian Markdown (YAML Frontmatter + Wikilinks).
- **NLP**: Sentence Transformers / Gemini Embedding API for Stage 5 link forging.
- **Environment**: `.env` based configuration for pathing and budgets.

---

## ⚙️ Configuration (.env)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `VAULT_PATH` | Absolute path to your Obsidian vault. | Required |
| `MAX_NODES_TOTAL` | Safety limit for node generation per session. | 50 |
| `MAX_TOKENS_BUDGET` | Token budget per recursive branch. | 8000 |
| `SEMANTIC_THRESHOLD` | Sensitivity of Stage 5 linking (0.0 to 1.0). | 0.82 |
| `GEMINI_MODEL` | The model used for reasoning and decomposition. | `gemini-2.5-flash` |

---

## 🏃 Quick Start

1.  **Clone & Install**:
    ```bash
    git clone https://github.com/RicsonRamos/obsidian-ai.git
    pip install -r requirements.txt
    ```
2.  **Configure**: Add your `GEMINI_API_KEY` to the `.env` file.
3.  **Generate**:
    ```bash
    # Map a complex topic with foundation backtracking
    python main.py graph "Quantum Computing" --depth 2
    ```
4.  **Link**:
    ```bash
    # Run a full semantic audit and cross-link session
    python main.py link --semantic
    ```

---

## 📜 Research License
This tool is built for students, researchers, and knowledge workers who wish to automate the **scaffolding** of their learning, allowing them to focus on active synthesis rather than manual organization.
