# ORACLE Engineering Intelligence Platform

ORACLE is a deterministic, AST-driven repository intelligence system designed for professional technical analysis, adversarial robust flow detection, and Viva questioning generation.

It moves beyond simple "technology detection" and vector database retrieval, acting as an evidence-based engine that infers structural architecture, request lifecycles, execution graphs, and runtime risks directly from source code.

## Key Capabilities

1. **AST-Driven Architecture Inference**: Deep parsing of frameworks (FastAPI, Express) to detect modular wrappers, dynamic routes, and middleware chains without executing the code.
2. **Implementation Intelligence (The Viva Engine)**: Synthesizes intelligent engineering questions focusing on architectural tradeoffs and failure paths, avoiding generic textbook definitions.
3. **Execution Flow Debugging**: Automatically generates Mermaid diagrams tracking the request lifecycle and detecting anomalies like orphan nodes or disconnected authentication flows.
4. **Adversarial Robustness**: Validates that dependencies listed in configurations (e.g., `requirements.txt`) are actively used in the codebase before making structural claims.
5. **Weighted Confidence Scoring**: Calculates evidence-based confidence levels prioritizing strong signals (explicit imports) over weak signals (indirect references).
6. **Evaluation Pipeline**: Built-in deterministic benchmarking suite to test Precision/Recall against predefined ground-truth project configurations.

## System Requirements

- Python 3.10+
- `pydantic` (V2)

## Installation & Setup

1. Create a virtual environment:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage (CLI)

The ORACLE CLI is the primary interface for repository analysis.

**Important:** You must execute the CLI from the `backend` virtual environment with the correct `PYTHONPATH`.

```bash
# Export the Python path to resolve src modules
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

# 1. Analyze a repository and generate an HTML report
backend/venv/bin/python3 -m src.cli analyze https://github.com/user/repo --report

# 2. Evaluate accuracy against a ground-truth benchmark
backend/venv/bin/python3 -m src.cli evaluate https://github.com/user/repo --expected backend/evaluation/expected_outputs/project_el.json

# 3. Explain an ORACLE claim with specific code evidence
backend/venv/bin/python3 -m src.cli explain "tech_stack"

# 4. Debug the ExecutionGraph for anomalies
backend/venv/bin/python3 -m src.cli debug https://github.com/user/repo
```

## Running the Validation Suite

To verify that the ORACLE core, evaluation pipelines, and report generators are functioning correctly:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
backend/venv/bin/python3 backend/tests/validation_suite.py
```

## Directory Structure

```text
/backend
├── evaluation/                 # Ground truth JSONs and benchmark runners
├── src/
│   ├── agents/                 # Orchestrators (oracle.py)
│   ├── core/                   # Event emitters and core logic
│   ├── models/                 # Pydantic Context, Evidence, and Flow models
│   ├── services/
│   │   ├── debug_visualizer/   # Mermaid and HTML report builders
│   │   ├── github/             # Repo cloner, struct analyzer, tech detector
│   │   ├── intelligence/       # AST adapters, flow analyzers, graph engines
│   ├── cli.py                  # CLI entry point
├── tests/                      # Validation suites and pipeline tests
```

## Design Philosophy

- **Deterministic**: Heuristic rules and AST traversal replace stochastic generation.
- **Explainable**: Every claim requires a confidence score and a traceable line of code evidence.
- **Production-Grade**: Built with scalability (ExclusionEngine) and robust failure handling.
