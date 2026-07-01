# Milestone 1：基础面板待办清单

## 文档

- [x] 读取根 PRD 和当前项目上下文。
- [x] 汇总业务、后端、前端三个分析结果。
- [x] 创建本阶段 PRD。
- [x] 创建本阶段架构设计。
- [x] 实现后更新交付摘要。
- [x] 更新项目上下文和遗留事项。

## 后端

- [x] 新增凭据加密工具和测试。
- [x] 新增密码哈希和 token 工具及测试。
- [x] 新增 Auth API：初始化、登录、登出、当前用户。
- [x] 为受保护接口增加认证依赖。
- [x] 新增 AI Provider schema、route 和测试。
- [x] 新增 AI Model 管理接口和测试。
- [ ] 新增真实 AI 连接测试和模型拉取，测试中 mock HTTP。
- [x] 补 `AiProvider` 测试状态字段。
- [x] 新增 `ServerSnapshot` 模型。
- [x] 新增 Server schema、route 和测试。
- [ ] 新增真实 SSH 执行器抽象，测试中 mock AsyncSSH。
- [x] 新增 SSH 连接测试接口和快照接口占位状态。
- [x] 关键操作写入 AuditLog。

## 前端

- [ ] 拆分 API client 和类型定义。
- [x] 新增登录/初始化页面状态。
- [x] AI 设置页接真实 Provider API。
- [ ] AI 设置页接模型管理完整交互。
- [x] Server 列表接真实 API。
- [x] 新增服务器新增表单。
- [ ] 新增服务器编辑/删除表单。
- [x] 新增 SSH 测试交互占位。
- [ ] 新增快照刷新交互。
- [ ] 新增服务器详情基础信息页。
- [x] 扩展前端交互测试。

## 测试

- [x] 后端运行 `pytest -v`。
- [x] 前端运行 `npm test`。
- [x] 前端运行 `npm run build`。
- [ ] Docker 构建如本地不可用，需要在交付说明中记录。

## 部署

- [x] 优化 Dockerfile 缓存层，减少前端更新导致后端 pip 重装。
- [x] 更新 Ubuntu 手动上传部署说明。
