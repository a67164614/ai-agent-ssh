# AI 运维面板基础工程实施计划

> **给 Claude 的要求：** 按任务逐步执行，不要跳过验证步骤。

**目标：** 构建一个可运行的 AI SSH 运维面板 MVP 基础工程。

**架构：** 开发阶段前端和后端分别运行；Docker 构建阶段把 React/Vite 前端编译成静态资源，并由 FastAPI 后端统一托管。后端负责登录、配置、服务器记录、部署计划校验、命令安全检查，并为后续 SSH/WebSocket 编排预留结构。第一版保持单容器友好，使用 SQLite 存储，并保留迁移到 PostgreSQL 和后台任务队列的空间。

**技术栈：** React、Vite、TypeScript、FastAPI、Pydantic、SQLAlchemy、SQLite、pytest、Docker Compose。

---

### 任务 1：后端命令安全领域

**文件：**
- 创建：`backend/app/core/security.py`
- 创建：`backend/tests/test_command_safety.py`

**步骤：**
1. 为危险命令检测编写 pytest 测试。
2. 运行 `python -m pytest backend/tests/test_command_safety.py -v`，确认因为模块缺失而失败。
3. 实现 `is_dangerous_command` 和命令安全检查结果。
4. 重新运行测试，确认通过。

### 任务 2：部署计划校验

**文件：**
- 创建：`backend/app/schemas/deployment.py`
- 创建：`backend/tests/test_deployment_plan.py`

**步骤：**
1. 为合法部署计划和危险步骤拦截编写 pytest 测试。
2. 运行目标测试，确认失败。
3. 实现 Pydantic 模型和校验逻辑。
4. 重新运行目标测试和完整后端测试。

### 任务 3：FastAPI 应用骨架

**文件：**
- 创建：`backend/app/main.py`
- 创建：`backend/app/api/routes.py`
- 创建：`backend/app/core/config.py`
- 创建：`backend/tests/test_api.py`

**步骤：**
1. 为 `/api/health`、`/api/commands/check`、`/api/deployments/validate-plan` 编写 API 测试。
2. 运行测试，确认失败。
3. 实现路由。
4. 重新运行 API 测试。

### 任务 4：持久化基础

**文件：**
- 创建：`backend/app/db/session.py`
- 创建：`backend/app/db/models.py`
- 创建：`backend/app/db/init_db.py`

**步骤：**
1. 添加用户、服务器、AI 中转站和审计日志的 SQLAlchemy 模型。
2. 应用启动时初始化 SQLite 表。
3. 保持 API 端点简洁，本阶段不实现真实 SSH 执行。

### 任务 5：前端界面骨架

**文件：**
- 创建：`frontend/package.json`
- 创建：`frontend/src/App.tsx`
- 创建：`frontend/src/main.tsx`
- 创建：`frontend/src/styles.css`

**步骤：**
1. 创建 TypeScript Vite 应用骨架。
2. 添加服务器列表、AI 设置、部署流程、终端占位和历史记录等面板区域。
3. 添加类型检查和构建命令。

### 任务 6：Docker 和文档

**文件：**
- 创建：`Dockerfile`
- 创建：`docker-compose.yml`
- 创建：`.dockerignore`
- 创建：`README.md`
- 创建：`docs/deployment.md`

**步骤：**
1. 在 Docker 构建阶段编译前端资源。
2. 安装后端依赖，并在 8080 端口运行 FastAPI。
3. 文档说明本地开发、Docker Compose 部署、环境变量和首次启动注意事项。
4. 运行后端测试、前端构建和 Docker 配置验证。
5. 提交基础工程。
