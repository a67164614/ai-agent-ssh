# 遗留事项

## Multica 绑定

- 缺少 `workspaceId` 和 `projectId`。
- 绑定前不能创建 Multica issue，也不能自动派单。
- 需要用户提供 Multica 服务地址、workspaceId、projectId，或允许通过 CLI 查询/创建项目。

## 产品功能

- 真实 AI 供应商测试和 `/models` 拉取未实现；当前返回“未启用”或基于默认模型创建记录。
- 真实服务器快照采集未实现；当前只落库 `ServerSnapshot` 占位记录。
- 网页 SSH 终端和部署任务引擎未实现。
- 前端服务器编辑/删除、详情页、快照刷新、AI 模型完整管理未完成。
- 当前下一步优先级：实现真实 AI HTTP 客户端、服务器资源快照和受控命令执行，然后拆分前端 API/client 类型与页面组件。

## 部署体验

- 当前 Ubuntu 更新流程可以使用 Git 拉取，也可以本地打包上传后执行 `docker compose up -d --build`。
- 可以后续补 GitHub Actions 构建 GHCR 镜像，减少服务器本地构建耗时。
- Dockerfile 已把后端 `pip install` 放在复制前端静态资源之前，减少前端改动导致的 pip 重装。
