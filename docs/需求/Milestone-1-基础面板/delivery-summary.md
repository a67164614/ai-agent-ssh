# Milestone 1：基础面板交付摘要

## 交付范围

本阶段已把静态运维面板推进到核心闭环可用版本：可登录、可保存配置、可管理服务器、可真实测试 AI 和 SSH、可采集资源快照、可进入 Web SSH 终端、可执行受控命令、可上传分析服务包并执行部署计划。Multica 流程未启用，所有需求研发记录保留在本仓库中文文档内。

## 已完成

- 管理员初始化、登录、登出、当前用户查询和初始化状态查询。
- Bearer token 认证保护 AI Provider、Server、Package、Deployment 和命令执行接口。
- 密码哈希、应用 token 签名、凭据加密和掩码显示。
- AI Provider CRUD、默认 Provider、真实连接测试、真实 `/models` 拉取、模型手动管理和默认模型切换。
- Server CRUD、SSH 密码/私钥加密保存、响应不泄露凭据。
- Server 真实 SSH 连接测试接口，成功标记 `online`，失败标记 `offline` 并返回中文失败原因。
- ServerSnapshot 通过 SSH 只读命令采集 CPU、内存、磁盘、系统、内核和 IP 信息并落库。
- WebSocket SSH 终端代理，前端可连接目标服务器并进行交互式操作。
- AI 助手接口，支持命令建议、命令输出总结和基础对话。
- 受控命令执行接口，执行前校验危险命令，执行结果写入 `CommandLog`。
- 服务包上传接口，保存 `AppPackage`，记录大小和 SHA256。
- 上传包分析接口，支持 zip、tar 和单文件安全解压，识别 Docker、Java、Node.js、Python、Go、静态站点等类型并生成部署计划。
- 部署任务接口，支持创建、执行、取消、查询任务；执行时记录上传日志和每一步命令日志。
- 命令日志查询接口，支持按服务器查看历史执行输出。
- 管理员初始化/登录、AI Provider 创建/更新/删除、Server 创建/更新/删除/测试/快照写入 `AuditLog`。
- 前端初始化/登录页面、服务器列表、服务器详情、编辑删除、快照刷新、终端、AI 设置、AI 助手、服务部署和历史记录。
- 前端命令安全检查、部署计划校验、后端健康检查继续可用。
- Dockerfile 缓存层优化：后端 `pip install` 在复制前端静态资源之前执行。

## 工程边界

- 前端仍集中在 `App.tsx`，可以在功能稳定后拆分 API client、类型文件和页面组件。
- SQLite 仍使用 `create_all` 和启动时轻量升级逻辑，生产长期演进建议引入 Alembic。
- 当前部署任务为同步执行模型，适合小型服务；大量长任务建议接入任务队列。
- 部署回滚已保留任务状态和日志基础，自动回滚策略可按真实发布流程继续增强。

## 验证结果

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q
```

结果：49 个测试通过，1 个 Starlette/httpx 兼容性警告。

```powershell
cd frontend
npm test
```

结果：15 个测试通过。当前系统默认 Node 为 12.22.12，验证时使用临时 Node 22.13.1。

```powershell
cd frontend
npm run build
```

结果：TypeScript 和 Vite 构建通过，静态产物输出到 `backend/static/`，该目录被 `.gitignore` 忽略。

## 部署注意

- 生产环境必须设置稳定的 `APP_SECRET` 和 `CREDENTIAL_SECRET`。
- `CREDENTIAL_SECRET` 一旦用于保存 API Key 或 SSH 凭据，不能随意更换，否则旧凭据无法解密。
- 如果已有旧 SQLite 数据库，应用启动会补齐当前已知新增字段和表；更新前仍建议备份 `/app/data/ai_agent_ssh.db`。
- 本地 Windows 前端验证需要 Node 20+，当前项目依赖的 Vite 7/Vitest 4 不支持 Node 12。
