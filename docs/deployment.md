# 部署说明

本项目在 MVP 阶段按单容器 Docker 部署设计。

## 生产环境检查项

在把面板暴露到内网之外之前，请先完成这些检查：

- 设置强随机 `APP_SECRET`。
- 设置强随机 `CREDENTIAL_SECRET`，并保持稳定。后续实现加密存储后，如果丢失该密钥，将无法解密已保存的凭据。
- 如果需要远程访问，请放在 HTTPS 后面。
- 在内置登录能力完整前，建议通过防火墙或反向代理认证限制访问。
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

## 当前 MVP 限制

当前工程用于验证项目框架和交付方式，还不会执行真实 SSH 操作。界面里的终端和部署区域目前是占位能力，后续需要继续实现 SSH 执行器、WebSocket 终端、任务引擎和 AI 网关。
