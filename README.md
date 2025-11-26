# Retail Analytics AI Agent

A local AI agent built with DSPy, LangGraph, and Ollama for retail analytics on the Northwind database.

## Graph Design

- **Entry → Router**: Routes questions to RAG, SQL, or Hybrid pathways based on question type
- **Dual Pathways**: 
  - RAG path: Router → Retriever → Synthesizer
  - SQL path: Router → Planner → SQL Gen → Executor → Synthesizer (with error repair loop)
  - Hybrid: Retriever → Planner → SQL Gen → Executor → Synthesizer
- **Repair Loop**: SQL errors trigger retry at SQL Gen node (max 2 attempts) with error feedback
- **Convergence**: All paths merge at Synthesizer → END, producing final answer with citations

## DSPy Optimization

**Component Optimized**: `SQLGeneratorModule`

**Method**: BootstrapFewShot with 5 training examples covering JOINs, aggregations, and filters

**Metric**: `validate_sql` - validates SQL execution against actual database

**Before vs After**:
```
[Manual fill-in after running evaluation]
Before optimization: X% success rate
After optimization:  Y% success rate
```

## Trade-offs & Assumptions

- **CostOfGoods Assumption**: When CostOfGoods column is missing, it is approximated as `0.7 * UnitPrice`
- **Retry Limit**: SQL error repair is limited to 2 attempts to prevent infinite loops
- **Local LLM**: Uses Ollama (phi3.5) for complete local execution - no external API calls
- **Simple BM25 Retrieval**: Uses rank-bm25 instead of embeddings for faster, dependency-light retrieval

## Setup & Usage

### Prerequisites
```bash
# Install Ollama from https://ollama.com/download
# Download the model
ollama pull phi3.5
```

### Installation
```bash
pip install -r requirements.txt
```

### (Optional) Optimize SQL Generator
```bash
python agent/optimize_refine.py
```

### Run Agent
```bash
python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out outputs_hybrid.jsonl
```

## Project Structure

```
.
├── agent/
│   ├── dspy_signatures.py      # DSPy signatures and modules
│   ├── graph_hybrid.py          # LangGraph state machine
│   ├── optimize_refine.py       # DSPy optimization script
│   └── rag/
│       ├── retrieval.py         # BM25-based retriever
│       └── tools/
│           └── sqlite_tool.py   # Database interface
├── data/
│   └── northwind.sqlite         # Northwind database
├── docs/
│   └── *.md                     # Documentation files (4 required)
├── requirements.txt
└── run_agent_hybrid.py          # Main entry point
```

## Environment Validation

Check your setup:
```bash
python check_env.py
```