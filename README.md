# AI Agent SSH

AI Agent SSH is the foundation for a lightweight AI-assisted SSH operations panel. The first scaffold uses a React/Vite frontend and a FastAPI backend packaged into a single Docker service.

Current scope:

- FastAPI app shell with health check.
- Dangerous command detection.
- Deployment plan validation before execution.
- SQLite persistence foundation for users, servers, AI providers, models, and audit logs.
- React operations dashboard scaffold.
- Docker Compose deployment.

Not implemented yet:

- Real SSH connection testing and command execution.
- Web SSH terminal proxy.
- AI provider CRUD and model fetching.
- Package upload and real deployment execution.
- Authentication UI and session handling.

## Tech Stack

- Frontend: React, Vite, TypeScript, lucide-react, @xterm/xterm-ready dependency.
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite.
- Future backend integrations: AsyncSSH, OpenAI-compatible AI gateway, Redis-backed task queue.
- Deployment: Docker and Docker Compose.

## Local Development

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8080 --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api` requests to `http://127.0.0.1:8080`.

## Docker Deployment

```powershell
copy .env.example .env
docker compose up -d --build
```

Open:

```text
http://localhost:8088
```

Health check:

```powershell
curl http://localhost:8088/api/health
```

## Environment Variables

| Name | Required | Description |
| --- | --- | --- |
| `APP_SECRET` | yes | Application secret used for future session signing. Change in production. |
| `CREDENTIAL_SECRET` | yes | Secret for encrypting SSH credentials and AI API keys. Change in production. |
| `DATABASE_URL` | no | Defaults to SQLite at `/app/data/ai_agent_ssh.db` in Docker. |
| `AI_BASE_URL` | no | Initial OpenAI-compatible base URL. Use a `/v1` URL, not `/chat/completions`. |
| `AI_API_KEY` | no | Initial AI API key. |
| `AI_MODEL` | no | Initial default model name. |

## Repository Layout

```text
backend/
  app/
    api/          FastAPI routes
    core/         config and command safety logic
    db/           SQLAlchemy models and session setup
    schemas/      Pydantic request and domain schemas
  tests/          pytest coverage
frontend/
  src/            React app shell
docs/
  deployment.md   deployment notes
  plans/          implementation plans
```

## Roadmap

1. Add single-admin authentication and first-run setup.
2. Add AI provider settings CRUD and encrypted API key storage.
3. Add server CRUD and SSH connection testing with AsyncSSH.
4. Add WebSocket SSH terminal using @xterm/xterm.
5. Add package upload, project analyzer, and AI deployment planning.
6. Add deployment task engine, logs, cancellation, and rollback records.
