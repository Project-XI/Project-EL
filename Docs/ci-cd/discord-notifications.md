# Discord Commit Notifications Setup

This workflow automatically posts commit information to Discord whenever code is pushed to GitHub.

---

## What It Posts

Every push triggers a formatted Discord message with:

- ✅ Commit message and short hash
- ✅ Author name and branch
- ✅ Files changed count, lines added/deleted
- ✅ List of changed files (up to 10)
- ✅ Clickable link to the commit on GitHub

---

## Step 1: Create a Discord Webhook

1. Go to your Discord server
2. Right-click the channel where you want notifications
3. Click **Edit Channel** → **Integrations** → **Webhooks**
4. Click **New Webhook**, give it a name (e.g. "GitHub Bot")
5. Copy the **Webhook URL**

---

## Step 2: Add the Secret to GitHub

1. Go to `https://github.com/Project-XI/Project-EL/settings/secrets/actions`
2. Click **New repository secret**
3. Name: `DISCORD_WEBHOOK_URL`
4. Value: (paste the webhook URL)
5. Click **Add secret**

---

## Step 3: Verify the Workflow File

The workflow is at `.github/workflows/discord-notify.yml`. It triggers on pushes to:
- `main`
- `develop`
- `master`

To change which branches trigger it, edit the `on.push.branches` field.

---

## Customising the Message

Edit `.github/workflows/discord-notify.yml` to:
- Change message colours (embed `color` field)
- Add or remove fields (repo URL, PR links, etc.)
- Adjust the max number of files shown
- Change the webhook timeout

---

## Troubleshooting

| Issue | Solution |
|---|---|
| No message in Discord | Confirm `DISCORD_WEBHOOK_URL` is set correctly in GitHub Secrets |
| Webhook error | Check that the webhook URL hasn't expired — recreate if needed |
| Action fails | Check Actions logs: Repo → Actions → Find the failed run |
| Secret appears empty | Delete and recreate the secret |

---

## Security

> ⚠️ **Never** put the Discord webhook URL directly in code or commit messages.  
> ⚠️ If you accidentally expose it, delete it in Discord and create a new one.  
> ⚠️ Always use GitHub Secrets for any sensitive URLs or tokens.

---

## Related Docs

- [CI/CD Workflows Overview](./workflows.md)
- [Environment Variables](../deployment/environment-variables.md)
