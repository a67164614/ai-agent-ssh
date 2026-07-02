# 部署说明

本项目按单容器 Docker 部署设计。前端会在镜像构建阶段编译成静态资源，由 FastAPI 统一托管，运行时只需要启动一个服务容器。

## 生产环境检查项

在把面板暴露到内网之外之前，请先完成这些检查：

- 设置强随机 `APP_SECRET`。
- 设置强随机 `CREDENTIAL_SECRET`，并保持稳定。如果丢失或修改该密钥，将无法解密已保存的 AI API Key 和 SSH 凭据。
- 如果需要远程访问，请放在 HTTPS 反向代理后面。
- 通过防火墙、Cloudflare Tunnel 或反向代理限制访问来源。
- 定期备份 Docker 数据卷，尤其是 `/app/data/ai_agent_ssh.db`。
- 不要把 `.env`、SSH 私钥、AI API Key 或服务器密码提交到 Git 仓库。

## Docker Compose 启动

创建 `.env`：

```powershell
copy .env.example .env
```

编辑 `.env`：

```text
APP_SECRET=replace-with-random-secret
CREDENTIAL_SECRET=replace-with-random-secret
AI_BASE_URL=https://example.com/v1
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

Compose 文件的默认端口映射：

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

## Ubuntu 首次部署

如果服务器可以访问 GitHub：

```bash
cd /opt/ops-agent
git clone git@github.com:a67164614/ai-agent-ssh.git ai-agent-ssh
cd ai-agent-ssh
cp .env.example .env
nano .env
docker compose up -d --build
docker compose logs -f ai-agent-ssh
```

如果服务器无法稳定拉取 GitHub，可以在本地打包上传：

```powershell
cd E:\工作数据\ai-agents
Compress-Archive -Path .\ai-agent-ssh\* -DestinationPath .\ai-agent-ssh.zip -Force
scp .\ai-agent-ssh.zip cbc@你的服务器IP:/home/cbc/
```

服务器上解压并启动：

```bash
mkdir -p /home/cbc/ai-agents-ssh
unzip -o /home/cbc/ai-agent-ssh.zip -d /home/cbc/ai-agents-ssh
cd /home/cbc/ai-agents-ssh
cp -n .env.example .env
nano .env
docker compose up -d --build
docker compose logs -f ai-agent-ssh
```

## 更新部署

如果服务器目录是 Git 仓库：

```bash
cd /home/cbc/ai-agents-ssh
git pull
docker compose up -d --build
docker compose logs -f ai-agent-ssh
```

如果服务器目录是直接上传的代码包：

```powershell
cd E:\工作数据\ai-agents
Compress-Archive -Path .\ai-agent-ssh\* -DestinationPath .\ai-agent-ssh.zip -Force
scp .\ai-agent-ssh.zip cbc@你的服务器IP:/home/cbc/
```

```bash
cd /home/cbc/ai-agents-ssh
unzip -o /home/cbc/ai-agent-ssh.zip -d /home/cbc/ai-agents-ssh
docker compose up -d --build
docker compose logs -f ai-agent-ssh
```

只改前端或后端代码时，也执行 `docker compose up -d --build`。Dockerfile 已调整缓存层，后端依赖安装会尽量复用缓存。

## 数据库和升级

当前后端使用 SQLAlchemy `create_all` 初始化表结构，并在应用启动时对 SQLite 旧库执行轻量升级，自动补齐当前已知新增字段，并创建缺失的新表。这个过程不会删除已有管理员、服务器或 AI 中转站数据。

更新前建议备份数据库：

```bash
docker compose exec ai-agent-ssh sh -lc 'cp /app/data/ai_agent_ssh.db /app/data/ai_agent_ssh.db.bak.$(date +%Y%m%d%H%M%S)'
```

如果更新后接口返回 500，请先查看容器日志：

```bash
docker compose logs -f ai-agent-ssh
```

开发环境可以在备份后重建数据卷；生产环境不要直接删除数据卷，应先保留 `/app/data/ai_agent_ssh.db` 并根据日志处理迁移问题。

## 功能检查清单

部署完成后建议按顺序检查：

1. 打开 `http://服务器IP:8088`。
2. 首次进入时初始化管理员账号。
3. 登录后刷新页面，确认不会回到初始化页。
4. 新增 AI 中转站，执行连接测试并拉取模型。
5. 新增服务器，执行 SSH 连接测试。
6. 刷新服务器资源快照，确认 CPU、内存、磁盘和系统信息可见。
7. 打开 Web 终端，确认可以连接到目标服务器。
8. 上传服务包，分析项目类型，创建部署计划并确认执行。

## 常见问题

### GitHub 私有仓库拉取失败

优先确认服务器上的 SSH Key 已添加到 GitHub，并能通过：

```bash
ssh -T git@github.com
```

如果服务器网络或 GitHub 权限不稳定，使用本地打包上传流程。

### HTTP/2 framing layer 错误

可以临时关闭 Git 的 HTTP/2：

```bash
git config --global http.version HTTP/1.1
```

如果仍不稳定，改用 SSH clone 或本地打包上传。

### 页面能打开但接口 500

查看后端日志：

```bash
docker compose logs -f ai-agent-ssh
```

重点检查 `.env`、数据库文件权限、`CREDENTIAL_SECRET` 是否变化，以及 SQLite 轻量升级日志。
