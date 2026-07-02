# Milestone 1：基础面板任务拆解

## 任务 1：安全与认证基础

角色：后端业务智能体、后端接口智能体

范围：

- `backend/app/core/crypto.py`
- `backend/app/core/auth.py`
- `backend/app/schemas/auth.py`
- `backend/app/api/routes.py`
- `backend/tests/test_crypto.py`
- `backend/tests/test_auth.py`

验收：

- 凭据可加密/解密。
- 密码哈希可校验。
- 可以初始化管理员。
- 已有管理员时不能重复初始化。
- 登录成功返回 token。
- `/api/auth/me` 可返回当前用户。
- 未认证访问受保护接口返回 401。

状态：已完成。

## 任务 2：AI Provider 后端

角色：后端接口智能体、后端业务智能体、后端数据智能体

范围：

- `backend/app/db/models.py`
- `backend/app/schemas/ai_provider.py`
- `backend/app/services/ai_gateway.py`
- `backend/app/api/routes.py`
- `backend/tests/test_ai_providers.py`
- `backend/tests/test_ai_gateway.py`

验收：

- Provider CRUD 可用。
- API Key 加密保存。
- 响应只返回掩码和 `has_api_key`。
- 设置默认 Provider 后其他 Provider 取消默认。
- 可手动添加、编辑、删除模型。
- 连接测试调用 OpenAI-compatible `/chat/completions`。
- 模型拉取调用 OpenAI-compatible `/models` 并落库。

状态：已完成。

## 任务 3：服务器管理后端

角色：后端接口智能体、后端业务智能体、后端数据智能体

范围：

- `backend/app/db/models.py`
- `backend/app/schemas/server.py`
- `backend/app/services/ssh_command.py`
- `backend/app/services/server_snapshot.py`
- `backend/app/api/routes.py`
- `backend/tests/test_servers.py`
- `backend/tests/test_server_snapshot.py`

验收：

- Server CRUD 可用。
- SSH 密码和私钥加密保存。
- 响应不泄露凭据。
- SSH 测试成功/失败更新状态。
- 快照接口保存并返回 CPU、内存、磁盘、系统、内核和 IP 信息。
- 受控命令执行前进行危险命令校验，并记录命令日志。
- WebSocket 终端可代理到目标 SSH 服务器。

状态：已完成。

## 任务 4：服务包分析和部署执行

角色：后端业务智能体、后端接口智能体、测试验证智能体

范围：

- `backend/app/db/models.py`
- `backend/app/services/project_analyzer.py`
- `backend/app/services/ssh_command.py`
- `backend/app/api/routes.py`
- `backend/tests/test_project_analyzer.py`
- `backend/tests/test_operations_api.py`

验收：

- 可上传服务包并记录 SHA256。
- 可安全解压 zip 和 tar，拒绝路径穿越。
- 可识别 Docker、Java、Node.js、Python、Go、静态站点等项目类型。
- 可生成部署计划。
- 可创建、执行、取消和查询部署任务。
- 部署执行会上传关联服务包并记录每一步日志。

状态：已完成。

## 任务 5：前端基础架构和认证页

角色：管理后台智能体

范围：

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/styles.css`

验收：

- 可显示初始化/登录状态。
- 登录后进入面板。
- 刷新后保留有效登录态。
- 未登录不展示管理页面。
- 登录页布局清晰，提示全部为中文。

状态：已完成。

## 任务 6：AI 设置前端

角色：管理后台智能体

范围：

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`

验收：

- 可列出 Provider。
- 可新增、更新、删除 Provider。
- API Key 只显示掩码。
- 可测试连接。
- 可拉取模型，失败时可手动新增模型。
- 可设置默认 Provider 和默认模型。

状态：已完成。

## 任务 7：服务器管理和终端前端

角色：管理后台智能体

范围：

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`

验收：

- 首页服务器列表来自 API。
- 可新增、编辑、删除服务器。
- 可测试 SSH 并展示中文结果。
- 可刷新快照并展示资源信息。
- 点击服务器可查看详情。
- 终端页可通过 WebSocket 连接服务器。

状态：已完成。

## 任务 8：AI 助手、服务部署和历史前端

角色：管理后台智能体

范围：

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`

验收：

- AI 助手调用后端生成命令建议。
- 命令执行后可调用后端总结输出。
- 服务包可上传、分析并生成部署计划。
- 可创建、确认执行和取消部署任务。
- 历史记录展示命令日志和部署任务。

状态：已完成。

## 任务 9：文档、部署和验证

角色：文档交付智能体、测试验证智能体

范围：

- `README.md`
- `docs/deployment.md`
- `docs/项目上下文/*`
- `docs/需求/Milestone-1-基础面板/*`
- `Dockerfile`

验收：

- 中文文档与当前实现一致。
- Dockerfile 缓存层优化。
- 后端测试、前端测试、类型检查和构建通过。
- 用户可见文案与当前实现一致。

状态：已完成。
