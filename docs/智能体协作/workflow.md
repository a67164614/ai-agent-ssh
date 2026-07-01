# 需求研发工作流

## 1. 需求进入

输入可以是 PRD、用户描述、Bug 反馈或优化目标。

主控协调智能体先读取：

- `AGENTS.md`
- `.codex/project-binding.json`
- `.codex/requirement-dev-flow.json`
- `docs/项目上下文/current-context.md`
- `docs/项目上下文/open-items.md`

## 2. 需求分析

业务分析智能体输出：

- 背景和目标。
- 用户角色。
- 范围和非目标。
- 业务规则。
- 边界和异常场景。
- 验收标准。

输出到 `docs/需求/<需求名称>/prd.md`。

## 3. 架构设计

规划设计智能体输出：

- 当前系统影响面。
- 前后端模块划分。
- API 和数据模型变化。
- 流程图、时序图或状态图。
- 风险和回滚方案。

输出到 `docs/需求/<需求名称>/architecture.md`。

## 4. 任务拆解

按角色拆分任务：

- 后端接口任务。
- 后端业务任务。
- 后端数据任务。
- 前端任务。
- 测试验证任务。
- 文档交付任务。

输出到 `todo.md` 和 `plan.md`。

## 5. 看板同步

当前项目 Multica 未绑定，跳过 issue 创建。

绑定完成后：

- 创建一个父 issue。
- 创建多个可独立执行的子 issue。
- 默认不分配执行人。
- 只有用户明确要求自动派单时才触发执行。

## 6. 实现

实现必须遵循测试先行：

- 后端新增行为先写 pytest。
- 前端新增交互先写 Vitest/Testing Library 测试。
- Docker 或文档变更至少运行可行的构建或配置检查。

## 7. 审查

先做规格审查，再做代码质量审查。

规格审查检查是否符合 PRD 和验收标准。代码质量审查检查安全、可维护性、边界和测试缺口。

## 8. 交付

交付前更新：

- `architecture.md`
- `delivery-summary.md`
- `docs/项目上下文/session-log.md`
- `docs/项目上下文/open-items.md`

最终回复必须列出验证命令和结果。
