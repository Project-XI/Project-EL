# Installation Guide

This guide walks you through setting up ORACLE locally from scratch.

---

## Prerequisites

- Python 3.10+
- `pip` and `venv`
- Git

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/Project-XI/Project-EL.git
cd Project-EL
```

---

## Step 2: Set Up Python Environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
# LLM Configuration
OPENAI_API_KEY=your_key_here

# GitHub (for private repo access)
GITHUB_TOKEN=your_github_pat

# WebSocket Server
HOST=localhost
PORT=8001
```

---

## Step 4: Run the Backend Server

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

The WebSocket endpoint will be live at:
```
ws://localhost:8001/ws/analyze
```

---

## Step 5: Open the ORACLE UI

Open `frontend/index.html` (or `Docs/index.html`) directly in your browser — no build step required.

Enter a GitHub repository URL and click **Analyze** to start a session.

---

## Step 6: (Optional) Run Calibration

```bash
cd backend
python -m evaluation.calibration.calibration_runner
```

Or use the threshold checker:

```bash
python evaluation/check_calibration_thresholds.py
```

---

## Verifying the Setup

If the setup is correct:
- The browser UI shows the ORACLE dashboard
- Entering a GitHub repo URL starts the analysis
- WebSocket logs stream in the terminal panel
- The execution graph and viva questions appear after ~30 seconds

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Activate virtualenv: `source .venv/bin/activate` |
| `Connection refused` on WebSocket | Make sure backend is running on port 8001 |
| Empty execution graph | Check `GITHUB_TOKEN` has `repo` read permissions |
| Calibration fails | Ensure all evaluation fixtures exist in `backend/evaluation/` |

---

## Next Steps

- [Understanding the Architecture](../architecture/system-overview.md)
- [Running a Viva Session](../viva-intelligence/session-flow.md)
- [Setting Up CI/CD](../ci-cd/workflows.md)
