# AI Agent SSH

AI Agent SSH 是一个轻量级 AI SSH 运维面板的基础工程。当前版本采用 React/Vite 前端和 FastAPI 后端，并支持打包成单个 Docker 服务。

当前已包含：

- FastAPI 应用骨架和健康检查接口。
- 危险命令检测。
- 部署计划执行前校验。
- SQLite 持久化基础，包含用户、服务器、AI 中转站、模型和审计日志表结构。
- React 运维面板界面骨架。
- Docker Compose 部署配置。

当前尚未实现：

- 真实 SSH 连接测试和命令执行。
- Web SSH 终端代理。
- AI 中转站增删改查和模型拉取。
- 服务包上传和真实部署执行。
- 登录界面和会话管理。

## 技术栈

- 前端：React、Vite、TypeScript、lucide-react、@xterm/xterm。
- 后端：FastAPI、Pydantic、SQLAlchemy、SQLite。
- 后续后端集成：AsyncSSH、OpenAI-compatible AI 网关、Redis 任务队列。
- 部署：Docker、Docker Compose。

## 本地开发

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8080 --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

前端开发服务会把 `/api` 请求代理到 `http://127.0.0.1:8080`。

## Docker 部署

```powershell
copy .env.example .env
docker compose up -d --build
```

访问地址：

```text
http://localhost:8088
```

健康检查：

```powershell
curl http://localhost:8088/api/health
```

## 环境变量

| 名称 | 必填 | 说明 |
| --- | --- | --- |
| `APP_SECRET` | 是 | 应用密钥，后续用于会话签名。生产环境必须修改。 |
| `CREDENTIAL_SECRET` | 是 | SSH 凭据和 AI API Key 的加密密钥。生产环境必须修改。 |
| `DATABASE_URL` | 否 | Docker 中默认使用 `/app/data/ai_agent_ssh.db` 作为 SQLite 数据库。 |
| `AI_BASE_URL` | 否 | 首次初始化使用的 OpenAI-compatible Base URL。填写到 `/v1`，不要填写 `/chat/completions`。 |
| `AI_API_KEY` | 否 | 首次初始化使用的 AI API Key。 |
| `AI_MODEL` | 否 | 首次初始化使用的默认模型。 |

## 仓库结构

```text
backend/
  app/
    api/          FastAPI 路由
    core/         配置和命令安全逻辑
    db/           SQLAlchemy 模型和会话配置
    schemas/      Pydantic 请求和领域模型
  tests/          pytest 测试
frontend/
  src/            React 应用界面
docs/
  deployment.md   部署说明
  plans/          实施计划
```

## 后续路线

1. 增加单管理员登录和首次初始化。
2. 增加 AI 中转站配置管理，并加密保存 API Key。
3. 增加服务器管理和基于 AsyncSSH 的连接测试。
4. 增加基于 @xterm/xterm 的 WebSocket SSH 终端。
5. 增加服务包上传、项目分析器和 AI 部署计划生成。
6. 增加部署任务引擎、日志、取消任务和回滚记录。
