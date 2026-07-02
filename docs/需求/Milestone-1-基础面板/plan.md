# Milestone 1：基础面板实施计划

> 本计划跳过 Multica，只使用多角色本地协作流程。实现必须遵守测试先行。

## 1. 阶段拆分

### 阶段 A：后端安全与认证基础

角色：后端业务智能体、后端接口智能体、测试验证智能体

目标：

- 凭据加密/解密。
- 密码哈希。
- Token 签发和校验。
- 管理员初始化、登录、登出、当前用户。

验证：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_crypto.py -v
```

### 阶段 B：AI Provider 和模型管理

角色：后端接口智能体、后端业务智能体、管理后台智能体

目标：

- Provider CRUD。
- API Key 掩码。
- 默认 Provider。
- 连接测试。
- 拉取模型和手动模型管理。
- 前端设置页接真实 API。

验证：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_ai_providers.py -v
```

```powershell
cd frontend
npm test
```

### 阶段 C：服务器管理和 SSH 快照

角色：后端接口智能体、后端业务智能体、后端数据智能体、管理后台智能体

目标：

- Server CRUD。
- SSH 凭据加密。
- SSH 测试。
- ServerSnapshot。
- 首页列表和详情页接真实 API。

验证：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_servers.py -v
```

```powershell
cd frontend
npm test
npm run build
```

### 阶段 D：审计、文档和部署体验

角色：文档交付智能体、测试验证智能体、代码质量审查智能体

目标：

- 写入关键审计日志。
- 优化 Dockerfile 缓存层。
- 更新 README、部署说明、上下文和交付摘要。

验证：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

```powershell
cd frontend
npm test
npm run build
```

## 2. 影响文件

| 类型 | 文件 | 说明 |
| --- | --- | --- |
| 后端 | `backend/app/core/crypto.py` | 凭据加密工具 |
| 后端 | `backend/app/core/auth.py` | 密码哈希和 token |
| 后端 | `backend/app/api/routes.py` 或拆分路由 | Auth、Provider、Server API |
| 后端 | `backend/app/db/models.py` | 补字段、新增快照模型 |
| 后端 | `backend/app/schemas/*.py` | 请求响应模型 |
| 后端 | `backend/app/services/*.py` | 业务服务 |
| 前端 | `frontend/src/App.tsx` | 临时接入页面，后续可拆分 |
| 前端 | `frontend/src/api.ts` | API client |
| 前端 | `frontend/src/types.ts` | 前端类型 |
| 测试 | `backend/tests/*.py` | 后端测试 |
| 测试 | `frontend/src/*.test.tsx` | 前端交互测试 |
| 文档 | `docs/需求/Milestone-1-基础面板/*` | 本需求文档 |

## 3. 实施约束

- 不改动用户本地未提交的 `docker-compose.yml` 端口配置，除非用户明确要求。
- 不启用 Multica，不创建 issue。
- 不做 Web SSH、AI 聊天、服务包上传和部署执行。
- 本次交付提供真实 SSH 测试、资源快照、受控命令执行和 Web 终端接口；自动化测试使用 mock，不依赖用户服务器。
- 前端 UI 所有主链路按钮接入真实接口；危险操作需要用户确认并展示中文结果。

## 4. 多子智能体分工

- 业务分析智能体：维护 PRD 和验收标准。
- 后端接口智能体：Auth、AI Provider、Server API。
- 后端业务智能体：加密、AI 测试、SSH 执行器、快照解析。
- 后端数据智能体：模型字段、快照表、审计表使用。
- 管理后台智能体：AI 设置页、服务器列表、服务器表单、详情基础页。
- 测试验证智能体：运行 pytest、npm test、npm build。
- 规格审查智能体：对照本阶段 PRD 检查功能完整性。
- 代码质量审查智能体：检查安全、泄密、边界和可维护性。

## 5. 风险

- 认证实现需要在简单和安全之间取舍；第一阶段建议使用 Bearer token，后续可换 session/cookie。
- SQLite `create_all` 不适合长期迁移管理；后续应引入 Alembic。
- 服务器快照命令对不同 Linux 发行版兼容性有限，需要保留原始错误。
- `CREDENTIAL_SECRET` 变更会导致旧凭据无法解密，需在部署文档强调。
- 当前前端依赖 Vite 7/Vitest 4，需要 Node 20+；Windows 当前默认 Node 12 不能直接运行前端验证。
- 当前缺少 Alembic，旧 SQLite 数据库不会自动补新增字段，部署升级前需要备份和迁移方案。

## 6. 回滚

- 还原本阶段提交。
- 保留旧 SQLite 数据文件备份。
- 如果数据模型变更导致旧库问题，删除开发环境数据库重建；生产环境后续需迁移脚本。
