# 当前项目上下文

## 项目概述

AI Agent SSH 是一个轻量 AI SSH 运维面板。目标是通过 Web 面板管理多台服务器，后端通过 SSH 执行受控查询、终端代理、项目分析和部署任务，AI 只生成建议和部署计划，执行前必须由用户确认。

## 当前技术栈

- 前端：React、Vite、TypeScript、lucide-react、@xterm/xterm。
- 后端：FastAPI、Pydantic、SQLAlchemy、SQLite、AsyncSSH。
- AI 接入：OpenAI-compatible API。
- 测试：pytest、Vitest、Testing Library。
- 部署：Docker、Docker Compose。

## 当前实现状态

- 已有健康检查接口：`GET /api/health`。
- 已有命令安全检查接口：`POST /api/commands/check`。
- 已有管理员初始化、登录、登出、当前用户和初始化状态接口。
- 已有 AI 中转站接口：`/api/ai-providers` 和模型管理子接口，已接入 OpenAI-compatible `/chat/completions` 真实测试和 `/models` 拉取。
- 已有服务器管理接口：`/api/servers`，支持新增、编辑、删除、详情、真实 SSH 连接测试和资源快照采集。
- 已有 WebSocket SSH 终端代理：`/api/servers/{server_id}/terminal`。
- 已有受控命令执行接口：`POST /api/servers/{id}/commands`，会先执行危险命令校验并记录 `CommandLog`。
- 已有服务包上传、压缩包安全解压、基础项目类型识别、部署计划生成、部署任务执行、取消、日志和历史查询接口。
- 已有 AI 助手接口，支持命令建议、命令输出总结和基础对话。
- 已有 React 运维面板，支持登录、菜单切换、服务器管理、资源快照、Web 终端、AI 设置、AI 助手、服务部署和历史记录。
- 已有 Docker 单容器部署配置。
- 已将总 PRD 纳入仓库根目录：`ai-ops-panel-prd.md`。
- 已完成 Milestone 1 本地需求拆解和交付记录：`docs/需求/Milestone-1-基础面板/`。

## 当前工程边界

- 当前 Multica 绑定未配置，需求流程使用本地中文文档模式。
- 用户已明确要求不用管 Multica，只关注多子智能体流程交互和完整落地开发。
- `docker-compose.yml` 可能有用户本地端口改动，不能擅自覆盖。
- 不要提交 `.env`、真实 SSH 凭据、AI API Key 或私钥。
- 当前认证适合个人或内网面板，公网长期暴露前建议加 HTTPS、访问来源限制和更严格的 token 过期策略。
- SQLite 适合单机轻量部署；多用户、高并发或长期生产演进建议迁移到 PostgreSQL 并引入 Alembic。
- 部署任务当前为同步执行模型；大量长任务建议接入任务队列和更完整的回滚策略。

## 最近验证

- 后端：`.\backend\.venv\Scripts\python.exe -m pytest -q`。
- 前端测试：使用临时 Node 22 执行 Vitest。
- 前端类型检查：`tsc -b`。
- 前端构建：`vite build`。
