# 遗留事项

## Multica 绑定

- 缺少 `workspaceId` 和 `projectId`。
- 绑定前不能创建 Multica issue，也不能自动派单。
- 需要用户提供 Multica 服务地址、workspaceId、projectId，或允许通过 CLI 查询/创建项目。

## 产品功能

- 登录和初始化管理员账号未实现。
- AI 中转站配置页面仍是占位，未接真实 CRUD。
- 服务器管理未接真实数据库 CRUD。
- SSH 连接测试、Web SSH 终端和部署任务引擎未实现。

## 部署体验

- 当前 Ubuntu 更新流程主要依赖 `git archive` 干净包上传。
- 可以后续补 GitHub Actions 构建 GHCR 镜像，减少服务器本地构建耗时。
- Dockerfile 可继续优化 pip/npm 缓存层，降低每次更新构建时间。
