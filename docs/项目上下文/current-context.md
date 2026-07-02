# 当前项目上下文

## 项目概述

AI Agent SSH 是一个轻量 AI SSH 运维面板。目标是通过 Web 面板管理多台服务器，后端通过 SSH 执行受控查询、终端代理、项目分析和部署任务，AI 只生成建议和部署计划，执行前必须由用户确认。

## 当前技术栈

- 前端：React、Vite、TypeScript、lucide-react、@xterm/xterm。
- 后端：FastAPI、Pydantic、SQLAlchemy、SQLite。
- 测试：pytest、Vitest、Testing Library。
- 部署：Docker、Docker Compose。

## 当前实现状态

- 已有 FastAPI 应用骨架。
- 已有命令安全检查接口：`POST /api/commands/check`。
- 已有部署计划校验接口：`POST /api/deployments/validate-plan`。
- 已有健康检查接口：`GET /api/health`。
- 已有管理员初始化/登录接口：`POST /api/auth/init`、`POST /api/auth/login`、`GET /api/auth/me`。
- 已有 AI 中转站接口：`/api/ai-providers` 和模型管理子接口。
- 已有服务器管理接口：`/api/servers`、真实 SSH 连接测试和快照占位。
- 已有 React 运维面板，并支持登录、菜单切换、服务器新增、AI 中转站新增、后端检查、命令检查和部署计划校验。
- 已有 Docker 单容器部署配置。
- 已将总 PRD 纳入仓库根目录：`ai-ops-panel-prd.md`。
- 已完成 Milestone 1 本地需求拆解：`docs/需求/Milestone-1-基础面板/`。

## 尚未实现

- 真实 AI 连接测试和模型拉取。
- 只读资源快照采集。
- WebSocket SSH 终端。
- 服务包上传、项目分析、AI 部署计划生成。
- 部署任务引擎、日志、取消和回滚。
- 前端服务器编辑/删除、详情页、快照刷新和模型完整管理。

## 注意事项

- `docker-compose.yml` 可能有用户本地端口改动，不能擅自覆盖。
- 当前 Multica 绑定未完成，需求流程先使用本地文档模式。
- 用户已明确要求不用管 Multica，只关注多子智能体流程交互和完整落地开发。
- 第一阶段已完成基础管理闭环；服务器连通性已接入真实 SSH 探测，真实 AI HTTP 调用、资源快照和受控命令执行仍是下一阶段重点。
