# nocobot - Dokploy Deployment Guide

## Overview

Deploy nocobot (Telegram bot + NocoDB MCP agent) to Dokploy as a standalone service.

**Architecture:**
```
┌─────────────────┐       Telegram API      ┌──────────────────┐
│  Telegram User  │ ◄────────────────────► │    nocobot       │
└─────────────────┘                         │  (Dokploy)       │
                                            └────────┬─────────┘
                                                     │
                                                     │ HTTP (MCP)
                                                     ▼
                                            ┌──────────────────┐
                                            │  NocoDB MCP      │
                                            │  Server          │
                                            └────────┬─────────┘
                                                     │
                                                     │ HTTPS
                                                     ▼
                                            ┌──────────────────┐
                                            │  NocoDB Instance │
                                            └──────────────────┘
```

## Prerequisites

1. **Dokploy instance** running
2. **NocoDB MCP Server** deployed and accessible (e.g., `http://your-mcp-server/mcp`)
3. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
4. **OpenRouter API Key** from [openrouter.ai](https://openrouter.ai)

---

## Step 1: Create Project in Dokploy

1. Go to **Projects** → **Create Project**
2. Name: `nocobot` or similar
3. Click **Create**

---

## Step 2: Add Application

1. Inside the project, click **+ Add Service** → **Application**
2. Choose **GitHub** as source
3. Select repository: `your-username/NocoBot`
4. Branch: `master` (or feature branch)
5. Build Path: `/` (repo root - required for monorepo)

---

## Step 3: Configure Build Settings

Go to **General** tab:

| Setting | Value |
|---------|-------|
| Build Type | Dockerfile |
| Docker File | `nocobot/Dockerfile` |
| Docker Context Path | `nocobot` |

**Important:** This is a monorepo. Build Path stays at `/` while Docker File and Context point to the `nocobot/` subdirectory.

---

## Step 4: Configure Environment Variables

Go to **Environment** tab and add these **Runtime Environment Variables**:

```
TELEGRAM_TOKEN=your-telegram-bot-token
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=anthropic/claude-sonnet-4
NOCODB_MCP_URL=http://your-mcp-server/mcp
```

**Optional:**
```
TELEGRAM_ALLOW_FROM=["user_id_1","username"]
```

**IMPORTANT:**
- Do NOT include `export` prefix
- Do NOT put quotes around values (except for JSON arrays)
- Each variable on its own line

---

## Step 5: No Domain/Port Configuration Needed

Unlike the MCP server, nocobot is a **client** that:
- Connects OUT to Telegram's API (long polling)
- Connects OUT to MCP server

It does NOT expose any ports or need a domain.

---

## Step 6: Deploy

1. Click **Deploy** button
2. Watch the build logs
3. Verify container starts successfully

### Expected Build Output

```
COPY pyproject.toml LICENSE ./
COPY __init__.py __main__.py main.py ... ratelimit.py ./nocobot/
COPY bus/ ./nocobot/bus/
COPY channels/ ./nocobot/channels/
COPY providers/ ./nocobot/providers/
RUN uv pip install --system --no-cache .
```

### Expected Runtime Output

```
Configuration loaded
Connecting to MCP server at http://your-mcp-server/mcp...
Discovered 62 MCP tools
Cached 2 MCP resources
Starting Telegram bot (polling mode)...
Telegram bot @your_bot_name connected
Nocobot started - press Ctrl+C to stop
```

---

## Step 7: Verify Deployment

1. Open Telegram
2. Find your bot and send `/start`
3. Send a message like "List all tables"
4. Verify bot responds with NocoDB data

---

## Troubleshooting

### "Configuration validation error"

**Symptom:** Container crashes with pydantic validation error

**Fix:**
1. Check all required env vars are set (TELEGRAM_TOKEN, OPENROUTER_API_KEY)
2. No typos in variable names
3. Redeploy after fixing

### "Error connecting to MCP server"

**Symptom:** Bot starts but can't reach MCP

**Check:**
1. Is `NOCODB_MCP_URL` correct?
2. Is MCP server running and accessible from Dokploy network?
3. Try: `curl http://your-mcp-server/health` from Dokploy server

### "Telegram bot token invalid"

**Symptom:** `telegram.error.InvalidToken`

**Fix:**
1. Get fresh token from @BotFather
2. Update `TELEGRAM_TOKEN` in Dokploy
3. Redeploy

### Bot starts but doesn't respond

**Check:**
1. Is `TELEGRAM_ALLOW_FROM` set? If so, is your user ID in the list?
2. Check container logs for errors
3. Verify OpenRouter API key is valid

---

## Updating the Deployment

After pushing changes to GitHub:

1. Go to project in Dokploy
2. Click **Deploy** to rebuild
3. Or enable **Auto Deploy** for automatic deploys on push

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_TOKEN` | Yes | - | Bot token from @BotFather |
| `OPENROUTER_API_KEY` | Yes | - | API key from OpenRouter |
| `OPENROUTER_MODEL` | No | `anthropic/claude-sonnet-4` | LLM model to use |
| `NOCODB_MCP_URL` | No | `http://your-mcp-server/mcp` | MCP server URL |
| `TELEGRAM_ALLOW_FROM` | No | `[]` | JSON array of allowed user IDs/usernames |
| `MAX_MESSAGE_LENGTH` | No | `4096` | Max characters per message |
| `RATE_LIMIT_MESSAGES` | No | `10` | Messages allowed per window (0 to disable) |
| `RATE_LIMIT_WINDOW` | No | `60.0` | Rate limit window in seconds |

---

## Security Considerations

1. **Telegram Token**: Stored in Dokploy's encrypted environment storage
2. **OpenRouter Key**: Same - never logged or exposed
3. **Allow List**: Restrict bot access to specific users if needed
4. **Network**: nocobot only makes outbound connections, no inbound ports exposed
