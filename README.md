# AI Agent SSH

AI Agent SSH 是一个面向个人服务器和小团队内网环境的 AI SSH 运维面板。项目采用 React/Vite 前端、FastAPI 后端和 SQLite 持久化，支持打包成单个 Docker 服务部署。

当前版本已经打通基础运维闭环：

- 单管理员初始化、登录、登出和 Bearer token 认证。
- SSH 凭据、AI API Key 加密保存，接口只返回脱敏状态。
- AI 中转站管理、真实连接测试、`/models` 模型拉取、手动模型维护和默认模型设置。
- 服务器新增、编辑、删除、列表、详情、真实 SSH 连接测试和资源快照刷新。
- Web SSH 终端代理，前端通过 WebSocket 连接目标服务器。
- AI 助手接口，支持命令建议、命令输出总结和基础对话。
- 受控命令执行，执行前进行危险命令拦截，执行结果写入命令日志。
- 服务包上传、SHA256 记录、压缩包安全解压、项目类型识别和部署计划生成。
- 部署任务创建、确认执行、取消、历史查询和步骤日志记录。
- 基础审计日志，记录管理员、AI 中转站和服务器关键操作。
- SQLite 持久化基础，启动时会对旧库执行轻量字段补齐。
- React 运维面板，支持首页概览、服务器管理、终端、AI 助手、服务部署、历史记录和系统设置。
- Docker Compose 单容器部署配置。

## 技术栈

- 前端：React、Vite、TypeScript、lucide-react、@xterm/xterm。
- 后端：FastAPI、Pydantic、SQLAlchemy、SQLite、AsyncSSH。
- AI 接入：OpenAI-compatible API。
- 测试：pytest、Vitest、Testing Library。
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

前端依赖 Vite 7 和 Vitest 4，建议使用 Node 20 或更高版本。Node 12/14 会因为无法解析现代 ESM 语法导致测试或构建失败。

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

服务器部署和更新步骤见 `docs/deployment.md`。

## 环境变量

| 名称 | 必填 | 说明 |
| --- | --- | --- |
| `APP_SECRET` | 是 | 应用 token 签名密钥，生产环境必须修改为强随机值。 |
| `CREDENTIAL_SECRET` | 是 | SSH 凭据和 AI API Key 的加密密钥，生产环境必须修改并长期保持稳定。 |
| `DATABASE_URL` | 否 | Docker 中默认使用 `/app/data/ai_agent_ssh.db` 作为 SQLite 数据库。 |
| `AI_BASE_URL` | 否 | 首次初始化使用的 OpenAI-compatible Base URL。填写到 `/v1`，不要填写 `/chat/completions`。 |
| `AI_API_KEY` | 否 | 首次初始化使用的 AI API Key。 |
| `AI_MODEL` | 否 | 首次初始化使用的默认模型。 |

## 仓库结构

```text
backend/
  app/
    api/          FastAPI 路由
    core/         配置、认证、加密和命令安全逻辑
    db/           SQLAlchemy 模型、会话和轻量升级逻辑
    schemas/      Pydantic 请求和响应模型
    services/     AI、SSH、快照和项目分析服务
  tests/          pytest 测试
frontend/
  src/            React 运维面板和交互测试
docs/
  deployment.md   部署说明
  需求/           PRD、架构、任务拆解和交付摘要
  项目上下文/     当前上下文、会话日志和遗留事项
```

## 当前边界

- 当前认证适合个人或内网面板，公网长期暴露前建议加 HTTPS、反向代理访问控制和更严格的 token 过期策略。
- SQLite 适合单机轻量部署；多用户、高并发或长期生产演进建议迁移到 PostgreSQL 并引入 Alembic。
- 部署任务为同步执行模型，适合小型服务部署；大量长任务建议接入独立任务队列和更完整的回滚策略。
