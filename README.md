# Retail Analytics AI Agent

A local AI agent built with **DSPy**, **LangGraph**, and **llama-cpp-python** for answering retail analytics questions using hybrid RAG + SQL approaches.

---

## Graph Design

The agent uses a **stateful LangGraph workflow** with the following flow:

- **Router Node**: Analyzes the question and routes to appropriate tools (`rag`, `sql`, or `hybrid`)
- **Retrieval Node**: Retrieves relevant documentation chunks using BM25 (for RAG or hybrid routes)
- **Planner Node**: Extracts constraints from retrieved docs to guide SQL generation
- **SQL Generator Node**: Generates SQLite queries using DSPy with schema awareness and error feedback
- **Executor Node**: Executes SQL queries against the Northwind database
- **SQL Repair Loop**: If SQL execution fails, the error is fed back to the generator (max 2 retries)
- **Synthesizer Node**: Combines SQL results and/or RAG context to generate final answer with citations

**Flow**: Entry → Router → [Retrieval → Planner] → SQL Generator ⇄ Executor (repair loop) → Synthesizer → END

---

## DSPy Impact

**Optimized Module**: SQLGenerator

**Metric Delta**: [Fill in your results here, e.g., 60% → 80% valid SQL execution]

DSPy's `BootstrapFewShot` optimizer was used to refine the SQL Generator module with 5 training examples. The optimization improves SQL validity and reduces retry attempts by learning from successful query patterns.

---

## Trade-offs & Assumptions

### Assumptions
- **CostOfGoods**: Approximated as `0.7 * UnitPrice` if missing from the database
- **Local Model**: Using local GGUF model (`phi3.5:3.8b-mini-instruct-q4_K_M`) via `llama-cpp-python` due to local constraints and to avoid external API dependencies

### Trade-offs
- **Model Size**: Using quantized 4-bit model (2.3GB) balances performance with hardware constraints
- **CPU Inference**: Running on CPU (`n_gpu_layers=0`) for compatibility; GPU would improve speed
- **Retry Limit**: SQL repair loop limited to 2 retries to prevent infinite loops
- **Date Handling**: SQLite requires `strftime('%Y', date)` instead of standard SQL `YEAR()` function

---

## Setup & Run

### Prerequisites
- Python 3.8+
- 4GB+ RAM (8GB+ recommended for smooth inference)

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download the model**:
   - Download `phi3.5:3.8b-mini-instruct-q4_K_M` GGUF model (~2.3GB)
   - Place it in: `models/phi3.5.gguf`

3. **Run the agent**:
   ```bash
   python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out outputs_hybrid.jsonl
   ```
