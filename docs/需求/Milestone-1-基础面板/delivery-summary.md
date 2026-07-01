# Milestone 1：基础面板交付摘要

## 交付范围

本阶段已把静态运维面板推进到可登录、可保存配置、可管理服务器基础信息的可用版本。Multica 流程未启用，所有需求研发记录保留在本仓库中文文档内。

## 已完成

- 管理员初始化、登录、登出占位、当前用户查询。
- Bearer token 认证保护 AI Provider 和 Server 接口。
- 密码哈希、应用 token 签名、凭据加密和掩码显示。
- AI Provider CRUD、默认 Provider、连接测试占位、模型手动管理、按默认模型创建记录。
- Server CRUD、SSH 密码/私钥加密保存、响应不泄露凭据。
- Server 连接测试占位接口，返回 `unchecked` 和明确提示。
- ServerSnapshot 表和快照占位接口，返回 `skipped` 和明确提示。
- 管理员初始化/登录、AI Provider 创建/更新/删除、Server 创建/更新/删除/测试/快照写入 `AuditLog`。
- 前端初始化/登录页面、真实服务器列表、添加服务器表单、AI Provider 配置表单。
- 前端命令安全检查、部署计划校验、后端健康检查继续可用。
- Dockerfile 缓存层优化：后端 `pip install` 在复制前端静态资源之前执行。

## 未完成和后续项

- 真实 AI HTTP 连接测试和 `/models` 拉取尚未接入。
- 真实 SSH executor、AsyncSSH mock 测试、连接成功/失败状态更新尚未接入。
- 服务器快照还未执行真实只读命令和资源解析。
- 前端暂未拆分 `api.ts`、`types.ts` 和独立页面组件。
- 前端服务器编辑/删除、快照刷新、服务器详情页、模型完整管理尚未完成。
- Web SSH、AI 助手、上传分析、部署任务引擎和回滚仍在后续 Milestone。
- SQLite 仍使用 `create_all`，生产演进前应引入 Alembic 迁移。

## 验证结果

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

结果：31 个测试通过，1 个 Starlette/httpx 兼容性警告。

```powershell
cd frontend
npm test
```

结果：7 个测试通过。当前系统默认 Node 为 12.22.12，验证时使用临时 Node 22.13.1。

```powershell
cd frontend
npm run build
```

结果：TypeScript 和 Vite 构建通过，静态产物输出到 `backend/static/`，该目录被 `.gitignore` 忽略。

## 部署注意

- 生产环境必须设置稳定的 `APP_SECRET` 和 `CREDENTIAL_SECRET`。
- `CREDENTIAL_SECRET` 一旦用于保存 API Key 或 SSH 凭据，后续不能随意更换，否则旧凭据无法解密。
- 如果已有旧 SQLite 数据库，新增字段和表不会通过迁移自动补齐；开发环境可备份后删除数据卷重建，生产环境应先补 Alembic 迁移。
- 本地 Windows 前端验证需要 Node 20+，当前项目依赖的 Vite 7/Vitest 4 不支持 Node 12。
