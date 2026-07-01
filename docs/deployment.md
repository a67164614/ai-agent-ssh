# Deployment Guide

This project is designed for single-container Docker deployment in the MVP phase.

## Production Checklist

Before exposing the panel beyond a local network:

- Set a strong `APP_SECRET`.
- Set a strong `CREDENTIAL_SECRET` and keep it stable. Losing it will prevent decrypting saved credentials once encryption-backed settings are implemented.
- Put the service behind HTTPS if accessed remotely.
- Restrict access with a firewall or reverse proxy authentication until built-in auth is complete.
- Back up the Docker data volume.

## Docker Compose

Create `.env`:

```powershell
copy .env.example .env
```

Edit `.env`:

```text
APP_SECRET=replace-with-random-secret
CREDENTIAL_SECRET=replace-with-random-secret
AI_BASE_URL=https://cdn.coderelay.cn/v1
AI_API_KEY=your-key
AI_MODEL=deepseek-chat
```

Start:

```powershell
docker compose up -d --build
```

View logs:

```powershell
docker compose logs -f ai-agent-ssh
```

Stop:

```powershell
docker compose down
```

Remove data volumes only when you intentionally want to delete local state:

```powershell
docker compose down -v
```

## Ports And Volumes

The compose file maps:

```text
host 8088 -> container 8080
```

Volumes:

```text
ai_agent_ssh_data    -> /app/data
ai_agent_ssh_uploads -> /app/uploads
```

## API Smoke Test

```powershell
curl http://localhost:8088/api/health
```

Expected response:

```json
{"status":"ok","service":"ai-agent-ssh"}
```

## Current MVP Limitations

This scaffold validates the selected project framework and delivery shape. It does not yet perform real SSH operations. Treat the UI terminal and deployment sections as placeholders until the SSH executor, WebSocket terminal, task engine, and AI gateway are implemented.
