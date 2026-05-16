# ORACLE Validation Lab UI

This directory contains the testing and validation dashboard for the ORACLE Engineering Intelligence Agent. It is designed to visualize the deterministic AST inferences, execution graphs, and explainability evidence extracted by the backend.

## How to Run

To test the full-stack integration, you need to run both the frontend UI and the FastAPI backend server.

### 1. Start the Frontend UI

Open a terminal in the `backend/testing_oracle_ui` directory and start a local Python HTTP server:
```bash
cd backend/testing_oracle_ui
python3 -m http.server 8000
```
Then navigate to `http://localhost:8000` in your web browser.

### 2. Start the FastAPI Intelligence Engine

The UI communicates with the real ORACLE agent via a FastAPI server. You must start this server on port **8001** to avoid port conflicts with the frontend.

Open a **new** terminal window, navigate to the `backend/` directory, and run:
```bash
cd backend
PYTHONPATH=$PYTHONPATH:. venv/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

Once both are running, you can click **"Initialize Analysis Agent"** in the UI to perform a live intelligence extraction.
