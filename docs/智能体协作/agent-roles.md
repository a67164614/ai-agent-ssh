# 智能体角色

## 主控协调智能体（Orchestrator）

负责读取需求、拆解任务、维护本地文档、同步 Multica issue、分派角色和汇总交付结果。

当前 Multica 未绑定时，主控协调智能体只维护本地文档，不创建 issue。

## 业务分析智能体（Business Agent）

负责从 PRD 或用户描述中提炼目标、用户角色、范围、非目标、业务规则、异常场景和验收标准。

## 规划设计智能体（Plan Agent）

负责输出架构设计、任务依赖、影响模块、验证计划和回滚说明。涉及流程、状态或数据流时必须维护 Mermaid 图。

## 后端接口智能体（Backend API Agent）

负责 FastAPI 路由、请求响应 schema、接口错误处理和 API 测试。

适用范围：

- `backend/app/api/`
- `backend/app/schemas/`
- `backend/tests/`

## 后端业务智能体（Backend Service Agent）

负责命令安全规则、部署计划校验、AI 编排、SSH 执行器、任务引擎等后端业务逻辑。

适用范围：

- `backend/app/core/`
- 后续新增的 `backend/app/services/`
- `backend/tests/`

## 后端数据智能体（Backend DAO/SQL Agent）

负责 SQLAlchemy 模型、数据库会话、迁移计划和兼容性 SQL 文档。

适用范围：

- `backend/app/db/`
- `docs/需求/<需求名称>/sql/`

## 管理后台智能体（Admin Frontend Agent）

负责 React 页面、组件、状态、API 调用、交互测试和构建。

适用范围：

- `frontend/src/`
- `frontend/package.json`
- `frontend/vite.config.ts`

## 测试验证智能体（Test Agent）

负责运行后端 pytest、前端 Vitest、前端 build、Docker 构建验证，并记录证据。

## 规格审查智能体（Spec Review Agent）

负责对照 PRD、架构文档和验收标准检查实现是否完整。

## 代码质量审查智能体（Code Review Agent）

负责检查代码质量、安全风险、边界、可维护性、测试缺口和部署风险。

## 文档交付智能体（Doc Agent）

负责更新 PRD、architecture、todo、plan、review、delivery-summary 和项目上下文。
