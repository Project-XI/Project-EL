# Environment Variables Reference

All sensitive configuration must be set via environment variables. Never hardcode secrets in source files.

---

## Setup

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your values.

---

## Variables Reference

### LLM / AI

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for LLM-powered question generation and scoring |

---

### GitHub

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | ✅ Yes | Personal Access Token for cloning repositories |

**Required scope:** `repo:read` (for public repos) or `repo` (for private repos)

To create a token: GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens

---

### Server

| Variable | Required | Default | Description |
|---|---|---|---|
| `HOST` | ❌ No | `localhost` | Bind host for FastAPI server |
| `PORT` | ❌ No | `8001` | Port for FastAPI WebSocket server |

---

### Discord (CI/CD only)

| Variable | Set In | Description |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | GitHub Secrets | Discord webhook URL for commit notifications |

**Never put this in `.env`** — use GitHub Secrets only.

---

## Example `.env.example`

```env
# LLM
OPENAI_API_KEY=sk-...your-key-here...

# GitHub (for repo cloning)
GITHUB_TOKEN=ghp_...your-token-here...

# Server
HOST=localhost
PORT=8001
```

---

## Security Rules

1. `.env` is in `.gitignore` — **never commit it**
2. If you accidentally expose `OPENAI_API_KEY` or `GITHUB_TOKEN`, revoke them immediately
3. For production, use a secrets manager (e.g. AWS Secrets Manager, HashiCorp Vault) — not `.env` files
4. For CI/CD, all secrets must be in GitHub repository Secrets, not workflow YAML files

---

## Related Docs

- [Installation Guide](../getting-started/installation.md)
- [CI/CD Workflows](../ci-cd/workflows.md) — GitHub Secrets setup
- [Discord Notifications](../ci-cd/discord-notifications.md) — DISCORD_WEBHOOK_URL setup
