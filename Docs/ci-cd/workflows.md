# CI/CD Workflows

ORACLE uses GitHub Actions for continuous integration, calibration quality gating, and Discord notifications.

---

## Workflow Overview

| Workflow | File | Trigger | Purpose |
|---|---|---|---|
| Calibration | `.github/workflows/calibration.yml` | Push / PR to `main` | Run calibration thresholds check |
| Discord Notify | `.github/workflows/discord-notify.yml` | Push to `main`, `develop`, `master` | Post commit info to Discord |

---

## Calibration Workflow

**File:** `.github/workflows/calibration.yml`

### What It Does

1. Sets up Python 3.10 environment
2. Installs backend dependencies
3. Runs the calibration threshold checker
4. Fails the PR if thresholds are not met

### Threshold Modes

| Mode | When Applied |
|---|---|
| **Strict** | Merges to `main` branch |
| **Standard** | All other branches / PRs |

### Running Locally (Before Pushing)

```bash
cd backend
source .venv/bin/activate
python evaluation/check_calibration_thresholds.py
```

Exit `0` = pass. Exit `1` = fail — do NOT merge.

---

## Discord Notification Workflow

**File:** `.github/workflows/discord-notify.yml`

### What It Does

Posts a formatted message to Discord on every push:

```
📝 New Commit Pushed
"Add fairness audit to Phase 3.5"

🔗 Commit: a1b2c3d
👤 Author: rajkoli
🌿 Branch: main
📊 Stats: Files: 5 | +342 | -12
📄 Changed Files:
  • backend/src/agents/oracle/fairness_audit.py
  • Docs/security/overview.md
```

### Setup Instructions

1. Create a Discord webhook in your channel (Settings → Integrations → Webhooks)
2. Copy the webhook URL
3. Add it to GitHub Secrets as `DISCORD_WEBHOOK_URL`
   - Repo → Settings → Secrets → Actions → New secret

> ⚠️ Never paste the webhook URL in code or commit messages. Always use GitHub Secrets.

---

## Adding a New Workflow

1. Create a new YAML file in `.github/workflows/`
2. Define triggers (`on: push`, `on: pull_request`, etc.)
3. Define jobs with `runs-on: ubuntu-latest`
4. Test locally using `act` (optional): `brew install act && act push`

---

## Environment Secrets Required

| Secret | Purpose | Where Used |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | Discord commit notifications | `discord-notify.yml` |
| `GITHUB_TOKEN` | Repo clone access (auto-provided) | All workflows |
| `OPENAI_API_KEY` | LLM calls (if running full analysis) | `calibration.yml` |

---

## Related Docs

- [Discord Bot Setup](./discord-notifications.md) — Full Discord webhook setup guide
- [Calibration Framework](../testing/calibration.md) — What the calibration workflow runs
- [Deployment](../deployment/local-setup.md) — Running the system locally
