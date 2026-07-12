# GitHub-to-Discord Bot Setup Guide

This workflow automatically posts commit information to Discord whenever you push code to GitHub.

## What It Does

✅ Posts commit details to Discord on every push  
✅ Shows commit message, author, branch, and file changes  
✅ Displays stats (files changed, insertions, deletions)  
✅ Provides clickable link to the commit on GitHub  
✅ Formatted with emojis and colors for easy reading  

## Setup Instructions

### Step 1: Create a Discord Channel (if you don't have one)
1. Go to your Discord server
2. Create a new channel (e.g., `#github-notifications`)
3. Make sure the bot will have permission to post messages

### Step 2: Create a Discord Webhook

1. **In Discord**, right-click on the channel where you want notifications
2. Click **"Edit Channel"**
3. Go to **"Integrations"** → **"Webhooks"**
4. Click **"New Webhook"**
5. Give it a name (e.g., "GitHub Bot")
6. Copy the **Webhook URL**

### Step 3: Add Webhook URL to GitHub Secrets

1. Go to your GitHub repository: https://github.com/Project-XI/Project-EL
2. Click **Settings** (top right)
3. Go to **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Name: `DISCORD_WEBHOOK_URL`
6. Paste the webhook URL you copied from Discord
7. Click **Add secret**

### Step 4: Test It

1. Make a commit and push to `main`, `develop`, or `master` branch
2. The GitHub Action will automatically run
3. You should see a formatted message in your Discord channel within 30 seconds

## Example Discord Message

The bot posts messages that look like:

```
📝 New Commit Pushed
"Refine ORACLE analysis and testing UI"

🔗 Commit: c2c1c7d
👤 Author: rajkoli
🌿 Branch: main
📊 Stats: Files: 18 | +2442 | -271
📄 Changed Files:
• Docs/index.html
• backend/.env.example
• backend/src/agents/oracle.py
• backend/src/main.py
• backend/src/cli.py
```

## Customization

You can edit `.github/workflows/discord-notify.yml` to:
- Change which branches trigger notifications (currently: `main`, `develop`, `master`)
- Modify the message format and colors
- Add additional fields or remove some
- Change the webhook timeout or retry logic

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No message in Discord | Check that `DISCORD_WEBHOOK_URL` secret is set in GitHub Settings |
| Webhook URL error | Make sure the webhook URL is correct and not expired |
| Action fails | Check the GitHub Actions logs: Go to repo → Actions → find the failed run |
| Webhook URL shows as empty | The secret may have been corrupted; delete and recreate it |

## Security Note

⚠️ **Never** paste your Discord webhook URL in code or commit messages.  
⚠️ Always use GitHub Secrets to store sensitive URLs.  
⚠️ If you accidentally expose a webhook URL, delete it and create a new one in Discord.

---

Once set up, every commit push will automatically notify your team on Discord! 🚀
