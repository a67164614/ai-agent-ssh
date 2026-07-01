# Milestone 1：基础面板任务拆解

## 任务 1：安全与认证基础（已完成）

角色：后端业务智能体、后端接口智能体

范围：

- `backend/app/core/crypto.py`
- `backend/app/core/auth.py`
- `backend/app/schemas/auth.py`
- `backend/app/api/routes.py` 或 `backend/app/api/auth.py`
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

## 任务 2：AI Provider 后端

角色：后端接口智能体、后端业务智能体、后端数据智能体

范围：

- `backend/app/db/models.py`
- `backend/app/schemas/ai_provider.py`
- `backend/app/services/ai_provider_service.py`
- `backend/app/api/routes.py` 或 `backend/app/api/ai_providers.py`
- `backend/tests/test_ai_providers.py`

状态：基础管理已完成，真实 AI HTTP 测试和真实模型拉取未完成。

验收：

- Provider CRUD 可用。
- API Key 加密保存。
- 响应只返回掩码和 `has_api_key`。
- 设置默认 Provider 后其他 Provider 取消默认。
- 可手动添加、编辑、删除模型。
- 模型拉取和连接测试可 mock 成功/失败。（未完成，当前为占位实现）

## 任务 3：服务器管理后端（基础 CRUD 已完成）

角色：后端接口智能体、后端业务智能体、后端数据智能体

范围：

- `backend/app/db/models.py`
- `backend/app/schemas/server.py`
- `backend/app/services/server_service.py`
- `backend/app/services/ssh_service.py`
- `backend/app/api/routes.py` 或 `backend/app/api/servers.py`
- `backend/tests/test_servers.py`

状态：Server CRUD、凭据加密、快照表和占位接口已完成；真实 SSH executor 未完成。

验收：

- Server CRUD 可用。
- SSH 密码和私钥加密保存。
- 响应不泄露凭据。
- SSH 测试成功/失败更新状态。（未完成，当前返回 `unchecked`）
- 快照接口保存并返回基础资源信息。（未完成，当前返回 `skipped` 占位快照）

## 任务 4：前端基础架构和认证页（部分完成）

角色：管理后台智能体

范围：

- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`

状态：认证页和登录态已完成；统一 API client 和类型文件尚未拆分。

验收：

- 有统一 API client。（未完成，当前集中在 `App.tsx`）
- 可显示初始化/登录状态。
- 登录后进入面板。
- 未登录不展示管理页面。

## 任务 5：AI 设置前端（部分完成）

角色：管理后台智能体

范围：

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- 可按需要新增组件文件。

状态：Provider 列表和新增已完成；编辑、删除、模型完整管理、设置默认交互尚未完成。

验收：

- 可列出 Provider。
- 可新增/编辑/删除 Provider。（新增已完成，编辑/删除未完成）
- API Key 只显示掩码。
- 可测试连接。（当前调用占位接口）
- 可拉取模型，失败时可手动新增模型。（前端未完成）
- 可设置默认 Provider/模型。（前端未完成）

## 任务 6：服务器管理前端（部分完成）

角色：管理后台智能体

范围：

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- 可按需要新增组件文件。

状态：首页列表和新增服务器已完成；编辑、删除、详情和快照刷新未完成。

验收：

- 首页服务器列表来自 API。
- 可新增/编辑/删除服务器。（新增已完成，编辑/删除未完成）
- 可测试 SSH。（当前调用占位接口）
- 可刷新快照。（未完成）
- 点击服务器进入详情页。（未完成）

## 任务 7：审计、文档和部署体验（已完成基础版）

角色：文档交付智能体、测试验证智能体

范围：

- `backend/app/api/routes.py`
- `Dockerfile`
- `README.md`
- `docs/deployment.md`
- `docs/项目上下文/*`
- `docs/需求/Milestone-1-基础面板/delivery-summary.md`

验收：

- 关键操作写审计。
- Dockerfile 缓存层优化。
- 交付文档更新。
- 后端和前端验证通过。
