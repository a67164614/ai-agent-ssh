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
- 已有 React 运维面板，并支持菜单切换、后端检查、命令检查和部署计划校验。
- 已有 Docker 单容器部署配置。

## 尚未实现

- 登录和初始化管理员账号。
- AI 中转站 CRUD、模型拉取和加密保存 API Key。
- 服务器 CRUD 和真实 SSH 连接测试。
- WebSocket SSH 终端。
- 服务包上传、项目分析、AI 部署计划生成。
- 部署任务引擎、日志、取消和回滚。

## 注意事项

- `docker-compose.yml` 可能有用户本地端口改动，不能擅自覆盖。
- 当前 Multica 绑定未完成，需求流程先使用本地文档模式。
