# 部署说明

本项目在 MVP 阶段按单容器 Docker 部署设计。

## 生产环境检查项

在把面板暴露到内网之外之前，请先完成这些检查：

- 设置强随机 `APP_SECRET`。
- 设置强随机 `CREDENTIAL_SECRET`，并保持稳定。如果丢失或修改该密钥，将无法解密已保存的 AI API Key 和 SSH 凭据。
- 如果需要远程访问，请放在 HTTPS 后面。
- 当前已有单管理员登录，但仍建议通过防火墙或反向代理限制访问来源。
- 定期备份 Docker 数据卷。

## Docker Compose

创建 `.env`：

```powershell
copy .env.example .env
```

编辑 `.env`：

```text
APP_SECRET=replace-with-random-secret
CREDENTIAL_SECRET=replace-with-random-secret
AI_BASE_URL=https://cdn.coderelay.cn/v1
AI_API_KEY=your-key
AI_MODEL=deepseek-chat
```

启动服务：

```powershell
docker compose up -d --build
```

查看日志：

```powershell
docker compose logs -f ai-agent-ssh
```

停止服务：

```powershell
docker compose down
```

只有在确认要删除本地状态时，才删除数据卷：

```powershell
docker compose down -v
```

## 端口和数据卷

Compose 文件的端口映射：

```text
宿主机 8088 -> 容器 8080
```

数据卷：

```text
ai_agent_ssh_data    -> /app/data
ai_agent_ssh_uploads -> /app/uploads
```

## API 冒烟测试

```powershell
curl http://localhost:8088/api/health
```

预期响应：

```json
{"status":"ok","service":"ai-agent-ssh"}
```

## 更新部署

如果服务器上目录是直接上传的代码包，而不是 Git 仓库，更新流程如下：

```bash
cd /home/cbc/ai-agents-ssh
docker compose down
docker compose up -d --build
docker compose logs -f ai-agent-ssh
```

如果服务器上目录是 Git 仓库，更新流程如下：

```bash
cd /home/cbc/ai-agents-ssh
git pull
docker compose up -d --build
docker compose logs -f ai-agent-ssh
```

如果只改前端或后端代码，也仍然执行 `docker compose up -d --build`。Dockerfile 已调整缓存层，后端依赖安装会尽量复用缓存。

## 数据库变更注意

当前后端使用 SQLAlchemy `create_all` 初始化表结构，尚未引入 Alembic 迁移。应用启动时会对 SQLite 旧库执行轻量升级，自动补齐当前已知新增字段，并创建缺失的新表。这个过程不会删除已有管理员、服务器或 AI 中转站数据。

如果更新后 `/api/servers` 或 `/api/ai-providers` 仍然返回 500，请先查看容器日志：

```bash
docker compose logs -f ai-agent-ssh
```

开发环境可先备份再重建数据卷；生产环境不要直接删除数据卷。应先备份 `/app/data/ai_agent_ssh.db`，再按日志补充迁移脚本。

## 当前 MVP 限制

当前工程已经支持登录、AI 中转站保存、服务器保存和安全检查，但还不会执行真实 SSH 操作。界面里的终端、真实连接测试、真实快照和部署区域目前是占位能力，后续需要继续实现 SSH 执行器、WebSocket 终端、任务引擎和 AI 网关。
