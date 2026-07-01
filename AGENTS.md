# AI Agent SSH 项目智能体规则

## 项目结构

- `backend/`：FastAPI 后端，包含 API 路由、配置、数据库模型、Pydantic schema 和 pytest 测试。
- `frontend/`：React/Vite/TypeScript 前端，包含运维面板界面、交互测试和构建配置。
- `docs/`：部署说明、实施计划、项目上下文、需求模板和智能体协作规则。
- `.codex/`：Codex 项目流程配置。
- `Dockerfile`、`docker-compose.yml`：单容器构建和部署入口。

本仓库前后端在同一个 Git 仓库内管理，默认使用根目录 `AGENTS.md` 作为唯一项目规则。处理任务前必须先查看根目录 `git status --short`。如果出现用户未提交改动，必须保留并绕开，不能擅自还原。

## 构建和测试命令

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

如果没有虚拟环境：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -v
```

前端：

```powershell
cd frontend
npm install
npm test
npm run build
```

Docker：

```powershell
docker compose up -d --build
```

当前本地环境可能没有 Docker 命令。无法运行 Docker 验证时，必须在交付说明中明确写出。

## 编码规则

- 后端新增接口、schema、命令安全规则、任务规则时必须先写测试，再实现。
- 前端新增交互必须至少覆盖菜单切换、接口调用或关键状态变化测试。
- 业务含义不明显的类、函数、字段和校验规则要写中文注释。
- 不写只复述语法的注释。
- API 返回结构、字段命名、部署计划 JSON 和危险命令规则必须与文档保持一致。
- 不提交 `.env`、真实 API Key、SSH 密码、私钥、服务器真实凭据。
- 不提交 `.venv/`、`node_modules/`、`backend/static/`、构建临时目录。

## 文档规则

需求、功能、接口、流程、字段或数据规则发生变化时，必须同步更新文档。默认位置：

- 跨端需求：`docs/需求/<需求名称>/`
- 后端专项：`docs/需求/<需求名称>/backend/`
- 前端专项：`docs/需求/<需求名称>/frontend/`

每个需求至少包含：

- `prd.md`：背景、目标、范围、非目标、业务规则、接口/字段影响、验收标准。
- `architecture.md`：架构设计、数据流、状态流、关键约束；有流程时使用 Mermaid 图。
- `todo.md`：后端、前端、测试、文档、部署检查清单。
- `plan.md`：实现顺序、影响文件、验证命令、回滚说明。

所有生成文档默认使用中文。

## 项目上下文规则

维护这些文件：

- `docs/项目上下文/current-context.md`
- `docs/项目上下文/session-log.md`
- `docs/项目上下文/open-items.md`

每次较完整的开发会话结束时，更新 `session-log.md`，记录用户目标、改动文件、验证命令、结果、风险和后续事项。

如果用户说“恢复当前项目上下文”，必须先读取：

- `AGENTS.md`
- `.codex/project-binding.json`
- `.codex/requirement-dev-flow.json`
- `docs/项目上下文/current-context.md`
- `docs/项目上下文/session-log.md`
- `docs/项目上下文/open-items.md`

## 需求研发流程

默认使用需求文档驱动流程：

1. 读取 PRD 或用户需求。
2. 提炼目标、范围、非目标、业务规则、接口和验收标准。
3. 先产出 `architecture.md`，再拆任务。
4. 按前端、后端、测试、文档、部署拆成可独立执行任务。
5. 默认只同步看板，不自动派单。
6. 用户明确说“自动派单”“让 agent 执行”“触发智能体执行”时，才进入自动执行。
7. 实现后先规格审查，再代码质量审查。
8. 审查问题修复后重新测试和复审。
9. 交付前更新架构、上下文和交付摘要。

## 智能体角色

默认角色见 `docs/智能体协作/agent-roles.md`。使用角色时只传递任务必要上下文、相关需求片段、允许改动范围和验证要求，不把整个仓库无差别交给子智能体。

## Multica 规则

当前项目尚未完成 Multica 绑定。缺少：

- `workspaceId`
- `projectId`
- `projectUrl`
- `issueUrlTemplate`

在绑定完成前：

- 不创建 Multica issue。
- 不自动派单。
- 只在本地文档中记录需求拆解和任务状态。

绑定完成后，需求类任务默认创建或更新 Multica 父子 issue，但仍不自动派单，除非用户明确要求。

## 验证和 Git 安全

- 完成前必须运行受影响范围验证命令，或明确说明无法运行的原因。
- 不自动 push、部署、amend、reset、clean 或删除用户改动。
- 不擅自提交用户未请求的改动；若需要提交，先确认范围。
- 不还原用户本地未提交改动。
- 发现 `docker-compose.yml`、`.env` 等环境相关本地改动时，默认视为用户配置，不能覆盖。
