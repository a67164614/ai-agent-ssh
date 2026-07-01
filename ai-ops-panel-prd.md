# AI 运维面板 PRD

## 1. 背景

用户希望构建一个类似宝塔面板的轻量运维系统，但核心能力不是传统固定菜单，而是通过 AI 辅助完成服务器查询、服务识别、部署、日志分析和故障排查。

系统第一版采用中心面板通过 SSH 管理多台服务器的方式实现，后续预留 Agent 模式。最终目标是将系统打包为 Docker 镜像并发布到 GitHub，用户更换机器时可以直接拉取镜像部署。

## 2. 问题陈述

当前通用 AI 聊天面板只能根据文字生成命令，不能真正读取目标服务器状态，也不能自动完成部署。用户需要的是一个可操作的运维平台：

- 能管理多台服务器。
- 能查看服务器基础配置和状态。
- 能进入指定服务器的 Web 终端。
- 能上传任意服务包或项目目录。
- 能让 AI 分析当前目录里的服务是什么、如何启动、需要什么环境。
- 能在用户确认后自动部署服务。
- 能记录部署历史、执行日志和操作结果。
- 能用 Docker 一键部署整套系统。

## 3. 产品目标

第一版目标是做出一个可用的多服务器 AI 运维面板：

1. 用户可以通过 Web 页面添加多台服务器。
2. 用户可以看到服务器列表、在线状态和基础资源信息。
3. 用户可以点击某台服务器进入详情页。
4. 用户可以在详情页打开 Web SSH 终端。
5. 用户可以上传服务包或选择远程目录。
6. AI 可以分析服务类型、启动方式、依赖环境、端口和部署建议。
7. 系统在执行任何命令前展示部署计划和命令确认。
8. 用户确认后，系统通过 SSH 在目标服务器执行部署。
9. 系统记录任务日志、执行输出和部署历史。
10. 系统可以通过 Docker Compose 一键部署。
11. 用户可以在 Web 页面中配置和切换 AI 中转站，而不是只能通过环境变量或配置文件修改。

## 4. 非目标

第一版不做完整宝塔替代品，不覆盖所有 Linux 管理能力。

不在 MVP 中实现：

- 多租户 SaaS。
- 复杂 RBAC 权限模型。
- Kubernetes 管理。
- 大规模批量任务编排。
- 完整 CMDB。
- 云厂商资源管理。
- 自动修复生产故障。
- AI 无确认直接执行高危命令。
- 每台服务器 Agent 安装模式。

## 5. 推荐方案

采用方案 C：先 SSH，后续支持 Agent。

第一阶段：

```text
浏览器
  -> AI 运维面板后端
  -> 数据库保存服务器信息和任务记录
  -> 后端通过 SSH 连接目标服务器
  -> 执行查询、上传、部署、日志读取等操作
  -> 调用中转站 AI API 分析和总结
```

后续阶段：

```text
浏览器
  -> 中心面板
  -> 目标服务器 Agent
  -> Agent 在本机执行受控操作
```

选择该方案的原因：

- SSH 方案落地最快，不需要先给每台机器安装 Agent。
- 能满足 3 台服务器这类初期使用场景。
- Docker 部署简单。
- 后续可以平滑增加 Agent，提高稳定性和安全边界。

## 6. 用户角色

### 6.1 管理员

系统拥有者，可以配置 AI 中转站、添加服务器、上传服务、执行部署、查看所有任务日志。

### 6.2 运维用户

可以查看服务器、使用终端、执行已授权的部署和查询任务。

第一版可以只做管理员单用户模式，后续再扩展多用户权限。

## 7. 核心用户故事

1. 作为管理员，我想通过 Docker 快速启动系统，以便换机器时可以快速恢复运维面板。
2. 作为管理员，我想在 Web 页面配置中转站 API 地址、Key 和模型名，以便系统可以调用云端 AI。
3. 作为管理员，我想在页面上测试中转站连接，以便确认 API Key、Base URL 和模型可用。
4. 作为管理员，我想在页面上拉取中转站模型列表，以便选择真实可用的模型。
5. 作为管理员，我想在页面上切换当前默认模型，以便根据任务选择不同模型。
6. 作为管理员，我想让系统加密保存中转站 API Key，以便避免密钥明文泄露。
7. 作为管理员，我想添加服务器 IP、SSH 端口、用户名和认证信息，以便系统可以管理目标服务器。
8. 作为管理员，我想在服务器列表看到所有服务器，以便快速选择要操作的机器。
9. 作为管理员，我想看到服务器在线状态，以便知道哪些服务器当前可连接。
10. 作为管理员，我想看到 CPU、内存、磁盘、系统版本等基础信息，以便快速了解服务器状态。
11. 作为管理员，我想点击服务器进入详情页，以便查看该服务器的完整信息。
12. 作为管理员，我想在页面里打开 Web SSH 终端，以便直接操作目标服务器。
13. 作为管理员，我想上传一个服务压缩包，以便让系统分析并部署它。
14. 作为管理员，我想选择目标服务器上的一个目录，以便让 AI 分析已有服务。
15. 作为管理员，我想让 AI 判断当前目录是什么项目，以便知道它的技术栈和启动方式。
16. 作为管理员，我想让 AI 识别 Java、Node.js、Python、Go、Dockerfile、docker-compose 和静态站点项目，以便处理常见服务类型。
17. 作为管理员，我想看到 AI 给出的部署计划，以便在执行前确认它是否合理。
18. 作为管理员，我想看到即将执行的命令，以便避免误操作。
19. 作为管理员，我想点击确认后才执行部署，以便控制风险。
20. 作为管理员，我想拒绝 AI 生成的部署方案，以便阻止不合理操作。
21. 作为管理员，我想让系统自动安装必要依赖前先询问我，以便避免改变服务器环境。
22. 作为管理员，我想部署完成后看到服务状态，以便确认服务是否启动成功。
23. 作为管理员，我想查看服务日志，以便排查启动失败原因。
24. 作为管理员，我想保存每次部署记录，以便未来回溯。
25. 作为管理员，我想一键回滚上一个版本，以便部署失败时恢复服务。
26. 作为管理员，我想让 AI 总结错误日志，以便更快定位问题。
27. 作为管理员，我想让 AI 解释某个项目怎么启动，以便减少阅读 README 的时间。
28. 作为管理员，我想批量查询多台服务器状态，以便快速巡检。
29. 作为管理员，我想限制危险命令，以便 AI 不会执行破坏性操作。

## 8. MVP 功能范围

### 8.1 登录与系统配置

- 单管理员登录。
- 初始化管理员账号。
- 页面配置 AI 中转站：
  - Base URL
  - API Key
  - 默认模型
  - 接口类型，默认 OpenAI-compatible Chat Completions
  - 是否启用
- 支持新增、编辑、删除中转站连接。
- 支持配置多个中转站连接，但 MVP 只需要一个默认启用连接。
- 支持从中转站拉取模型列表。
- 支持手动添加模型 ID，处理 /models 接口不可用的中转站。
- 支持在页面上切换默认模型。
- 测试 AI 连接。
- Docker 环境变量只作为首次初始化默认值；系统启动后，管理员可以在页面覆盖配置。
- API Key 必须加密保存，页面再次打开时只展示掩码，不展示完整明文。

### 8.2 服务器管理

- 添加服务器：
  - 名称
  - 主机地址
  - SSH 端口
  - 用户名
  - 密码或私钥
  - 备注
- 编辑服务器。
- 删除服务器。
- 测试 SSH 连接。
- 获取服务器基础信息。
- 服务器列表展示：
  - 名称
  - IP
  - 在线状态
  - 系统版本
  - CPU 核数
  - 内存使用率
  - 磁盘使用率
  - 最近连接时间

### 8.3 服务器详情页

- 基础信息面板。
- CPU、内存、磁盘、网络概要。
- 常用操作入口：
  - 查询配置
  - 查看进程
  - 查看端口
  - 查看磁盘
  - 打开终端
  - 上传服务
  - AI 分析目录

### 8.4 Web SSH 终端

- 使用 xterm.js 展示终端。
- 后端通过 WebSocket 代理 SSH 会话。
- 支持输入、输出、窗口尺寸变化。
- 支持断开连接。
- 第一版不需要多人共享终端。

### 8.5 服务上传与项目分析

用户可以：

- 上传 zip、tar.gz、jar、二进制文件或项目目录压缩包。
- 选择目标服务器。
- 选择部署目录。
- 让 AI 分析上传内容。

系统分析文件时收集：

- 文件树。
- README。
- package.json。
- pom.xml。
- build.gradle。
- requirements.txt。
- pyproject.toml。
- go.mod。
- Dockerfile。
- docker-compose.yml。
- application.yml。
- .env.example。
- 启动脚本。

AI 输出：

- 项目类型。
- 依赖环境。
- 构建命令。
- 启动命令。
- 端口推测。
- 日志位置推测。
- 推荐托管方式：
  - systemd
  - pm2
  - docker compose
  - nginx
  - 直接二进制

### 8.6 部署计划确认

部署前必须展示：

- 目标服务器。
- 目标目录。
- 项目类型。
- 需要执行的步骤。
- 每一步命令。
- 风险提示。
- 是否需要 sudo。
- 是否会安装依赖。
- 是否会覆盖已有文件。
- 是否会重启服务。

用户操作：

- 执行。
- 拒绝。
- 复制命令。
- 只应用到终端。

### 8.7 部署执行

部署任务通过后端任务系统执行。

能力：

- 上传文件到目标服务器。
- 解压服务包。
- 备份旧版本。
- 执行构建命令。
- 创建或更新 systemd 服务。
- 启动或重启服务。
- 检查服务状态。
- 拉取最近日志。
- 记录完整输出。

### 8.8 AI 运维助手

AI 助手上下文必须包含：

- 当前选中的服务器。
- 当前目录。
- 最近一次命令输出。
- 服务器基础信息。
- 项目分析结果。
- 可用工具列表。

AI 不能直接执行任意命令。它只能产生：

- 查询类建议。
- 部署计划。
- 白名单工具调用。
- 等待用户确认的命令草案。

## 9. 支持的服务类型

MVP 优先支持：

### 9.1 Java

识别依据：

- jar 文件。
- pom.xml。
- build.gradle。
- application.yml。

部署方式：

- java -jar。
- systemd 托管。

### 9.2 Node.js

识别依据：

- package.json。
- pnpm-lock.yaml。
- yarn.lock。

部署方式：

- npm install / pnpm install。
- npm run build。
- npm run start。
- pm2 托管。

### 9.3 Python

识别依据：

- requirements.txt。
- pyproject.toml。
- app.py。
- main.py。
- manage.py。

部署方式：

- venv。
- pip install。
- uvicorn / gunicorn / python main.py。
- systemd 托管。

### 9.4 Go

识别依据：

- go.mod。
- main.go。
- Linux 可执行文件。

部署方式：

- go build。
- systemd 托管。

### 9.5 Docker

识别依据：

- Dockerfile。
- docker-compose.yml。

部署方式：

- docker build。
- docker compose up -d。

### 9.6 静态站点

识别依据：

- index.html。
- dist。
- build。
- nginx.conf。

部署方式：

- Nginx 静态目录。

## 10. 安全要求

### 10.1 SSH 凭据

- SSH 密码和私钥必须加密保存。
- 加密密钥通过环境变量传入容器。
- 不在日志中输出密码、私钥、API Key。

### 10.2 命令执行

- AI 不允许绕过确认直接执行命令。
- 高危命令必须拦截。
- 高危模式包括：
  - rm -rf /
  - mkfs
  - dd
  - shutdown
  - reboot
  - chmod -R 777
  - chown -R /
  - curl | bash
  - wget | sh
  - userdel
  - iptables flush
- 涉及 sudo 的命令必须标记风险。

### 10.3 审计

每次操作记录：

- 用户。
- 目标服务器。
- 时间。
- 操作类型。
- AI 生成内容。
- 用户确认动作。
- 实际执行命令。
- 命令输出。
- 执行状态。

### 10.4 默认安全策略

- 默认只允许当前用户添加的服务器。
- 默认不允许批量执行危险操作。
- 默认不允许 AI 自动安装系统包，必须用户确认。
- 默认不暴露公网，建议放在内网或反向代理后。

## 11. 系统架构

### 11.1 组件

```text
Frontend
  Web UI, xterm.js, server list, deployment wizard

Backend API
  Auth, server management, AI orchestration, deployment tasks

SSH Executor
  SSH command, SFTP upload, WebSocket terminal proxy

Project Analyzer
  File tree scanner, manifest parser, AI prompt builder

AI Gateway
  OpenAI-compatible client for relay API

Task Engine
  Async jobs, logs, status, cancellation

Database
  Users, servers, credentials, tasks, deployments, settings
```

### 11.2 推荐技术栈

MVP 推荐：

```text
Frontend: React or Vue 3
Terminal: xterm.js
Backend: FastAPI
SSH: Paramiko or AsyncSSH
Database: SQLite for MVP, PostgreSQL for production
Task: BackgroundTasks or Celery later
Container: Docker + Docker Compose
```

如果团队更偏 Java，可替代为：

```text
Backend: Spring Boot
SSH: Apache MINA SSHD or JSch
Database: MySQL/PostgreSQL
WebSocket: Spring WebSocket
```

第一版建议 FastAPI，原因是 AI 编排、文件分析、SSH 自动化开发速度更快。

## 12. 数据模型

### 12.1 User

- id
- username
- password_hash
- role
- created_at

### 12.2 Server

- id
- name
- host
- port
- username
- auth_type
- encrypted_password
- encrypted_private_key
- remark
- status
- last_seen_at
- created_at
- updated_at

### 12.3 ServerSnapshot

- id
- server_id
- os
- kernel
- cpu
- memory_total
- memory_used
- disk_total
- disk_used
- ip_addresses
- collected_at

### 12.4 AppPackage

- id
- filename
- storage_path
- size
- sha256
- uploaded_by
- uploaded_at

### 12.5 ProjectAnalysis

- id
- package_id
- server_id
- target_path
- detected_type
- summary
- dependencies
- start_commands
- deploy_plan
- raw_ai_response
- created_at

### 12.6 DeploymentTask

- id
- server_id
- package_id
- status
- plan_json
- started_at
- finished_at
- created_by

### 12.7 CommandLog

- id
- task_id
- server_id
- command
- stdout
- stderr
- exit_code
- started_at
- finished_at

### 12.8 AuditLog

- id
- user_id
- action
- target_type
- target_id
- detail_json
- created_at

### 12.9 AiProvider

- id
- name
- provider_type
- base_url
- encrypted_api_key
- default_model
- api_mode
- enabled
- last_test_status
- last_test_message
- last_test_at
- created_at
- updated_at

说明：

- provider_type MVP 固定支持 openai-compatible。
- api_mode MVP 固定支持 chat_completions。
- encrypted_api_key 必须加密保存。
- 系统可以保存多个 AiProvider，但同一时间只需要一个默认启用 provider。

### 12.10 AiModel

- id
- provider_id
- model_id
- display_name
- source
- enabled
- created_at
- updated_at

说明：

- source 可为 fetched 或 manual。
- fetched 表示从中转站 /models 接口拉取。
- manual 表示管理员手动添加。

## 13. API 草案

### 13.1 Auth

- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me

### 13.2 Settings

- GET /api/settings/ai
- PUT /api/settings/ai
- POST /api/settings/ai/test
- GET /api/ai-providers
- POST /api/ai-providers
- GET /api/ai-providers/{id}
- PUT /api/ai-providers/{id}
- DELETE /api/ai-providers/{id}
- POST /api/ai-providers/{id}/test
- POST /api/ai-providers/{id}/fetch-models
- GET /api/ai-providers/{id}/models
- POST /api/ai-providers/{id}/models
- PUT /api/ai-providers/{id}/models/{model_id}
- DELETE /api/ai-providers/{id}/models/{model_id}
- POST /api/ai-providers/{id}/set-default

### 13.3 Servers

- GET /api/servers
- POST /api/servers
- GET /api/servers/{id}
- PUT /api/servers/{id}
- DELETE /api/servers/{id}
- POST /api/servers/{id}/test
- POST /api/servers/{id}/snapshot

### 13.4 Terminal

- WS /api/servers/{id}/terminal

### 13.5 Packages

- POST /api/packages/upload
- GET /api/packages
- DELETE /api/packages/{id}

### 13.6 Analysis

- POST /api/servers/{id}/analyze-upload
- POST /api/servers/{id}/analyze-path

### 13.7 Deployment

- POST /api/deployments/plan
- POST /api/deployments/{id}/execute
- POST /api/deployments/{id}/cancel
- GET /api/deployments/{id}
- GET /api/deployments

### 13.8 AI Assistant

- POST /api/servers/{id}/assistant/chat
- POST /api/servers/{id}/assistant/propose-command
- POST /api/servers/{id}/assistant/summarize-output

## 14. Docker 交付要求

### 14.1 镜像

发布镜像：

```text
ghcr.io/<owner>/ai-ops-panel:latest
```

### 14.2 Docker Compose

最小部署：

```yaml
services:
  ai-ops-panel:
    image: ghcr.io/<owner>/ai-ops-panel:latest
    ports:
      - "8088:8080"
    volumes:
      - ai_ops_data:/app/data
      - ai_ops_uploads:/app/uploads
    environment:
      - APP_SECRET=change-me
      - CREDENTIAL_SECRET=change-me
      - AI_BASE_URL=https://cdn.coderelay.cn/v1
      - AI_API_KEY=
      - AI_MODEL=deepseek-chat
    restart: always

volumes:
  ai_ops_data:
  ai_ops_uploads:
```

环境变量说明：

- AI_BASE_URL、AI_API_KEY、AI_MODEL 只用于首次初始化默认中转站连接。
- 如果数据库里已有 AiProvider，系统不得用环境变量覆盖页面配置。
- 管理员可以在页面修改、测试和切换中转站配置。
- CREDENTIAL_SECRET 用于加密 SSH 凭据和 AI API Key，生产环境必须显式设置。

### 14.3 GitHub Actions

需要自动执行：

- 后端测试。
- 前端构建。
- Docker 镜像构建。
- 推送 GHCR。

触发条件：

- main 分支 push。
- tag 发布。

## 15. 页面设计

### 15.1 首页

包含：

- 服务器列表。
- 添加服务器按钮。
- 批量操作入口。
- 常用命令入口。
- AI 设置入口。

列表字段：

- 选择框。
- 服务器名称。
- IP。
- 状态。
- 系统。
- CPU。
- 内存。
- 磁盘。
- 操作。

### 15.2 服务器详情

Tabs：

- 概览。
- 终端。
- AI 助手。
- 服务部署。
- 日志。
- 历史记录。

### 15.3 AI 设置页

字段：

- 连接名称。
- Base URL。
- API Key。
- 默认模型。
- 接口类型。
- 启用状态。

操作：

- 新增连接。
- 编辑连接。
- 删除连接。
- 测试连接。
- 拉取模型列表。
- 手动添加模型 ID。
- 设置默认连接。
- 设置默认模型。

展示要求：

- API Key 输入后保存为密文。
- 已保存的 API Key 在页面中只显示掩码。
- 测试连接时展示成功或失败原因。
- 拉取模型失败时允许手动添加模型 ID。
- Base URL 输入提示必须说明只填写到 /v1，不填写 /chat/completions。

### 15.4 AI 助手交互

对话区域显示：

- 用户问题。
- AI 思考状态。
- 建议命令卡片。
- 部署计划卡片。
- 执行按钮。
- 应用到终端按钮。
- 拒绝按钮。
- 执行输出。
- AI 总结。

### 15.5 服务部署页

流程：

1. 选择服务器。
2. 上传服务包或填写远程目录。
3. AI 分析。
4. 展示部署计划。
5. 用户确认。
6. 执行部署。
7. 查看结果和日志。

## 16. AI 行为约束

AI 输出应分为两类：

### 16.1 分析结果

用于解释服务类型、依赖、启动方式。

### 16.2 操作计划

必须是结构化 JSON：

```json
{
  "summary": "这是一个 Node.js 服务",
  "risk_level": "medium",
  "requires_sudo": false,
  "steps": [
    {
      "name": "安装依赖",
      "command": "npm install",
      "working_directory": "/opt/apps/demo"
    },
    {
      "name": "启动服务",
      "command": "npm run start",
      "working_directory": "/opt/apps/demo"
    }
  ]
}
```

后端必须校验该 JSON，不允许直接信任 AI。

## 17. 错误处理

必须处理：

- SSH 连接失败。
- SSH 认证失败。
- 目标目录不存在。
- 上传失败。
- 解压失败。
- AI 调用失败。
- AI 返回格式错误。
- 命令执行超时。
- 命令退出码非 0。
- 服务启动失败。
- 日志为空。

错误展示要求：

- 给用户可读的错误摘要。
- 保留原始日志。
- 支持复制错误信息。
- 支持让 AI 分析错误。

## 18. 测试要求

### 18.1 单元测试

必须覆盖：

- 项目类型识别。
- AI 输出 JSON 解析。
- 危险命令检测。
- 部署计划校验。
- SSH 命令构造。
- 配置读取。

### 18.2 集成测试

必须覆盖：

- 添加服务器。
- 测试 SSH 连接。
- 获取服务器快照。
- 上传服务包。
- 生成部署计划。
- 执行模拟部署。

### 18.3 端到端测试

必须覆盖：

- 登录。
- 添加服务器。
- 打开详情。
- 查询配置。
- AI 生成命令。
- 用户确认执行。
- 查看执行结果。

## 19. 里程碑

### Milestone 1: 基础面板

- 登录。
- 页面 AI 中转站设置。
- 中转站连接测试。
- 模型列表拉取和手动模型配置。
- 添加服务器。
- 服务器列表。
- SSH 连接测试。
- 获取服务器配置。

### Milestone 2: Web 终端

- xterm.js 页面。
- SSH WebSocket 代理。
- 终端输入输出。

### Milestone 3: AI 查询助手

- AI 生成查询命令。
- 命令确认卡片。
- 执行后总结。
- 危险命令拦截。

### Milestone 4: 服务分析

- 上传服务包。
- 文件树分析。
- 常见项目类型识别。
- AI 输出部署建议。

### Milestone 5: 自动部署

- 部署计划确认。
- SSH 上传和执行。
- systemd / pm2 / docker compose 基础支持。
- 日志查看。
- 部署历史。

### Milestone 6: Docker 发布

- Dockerfile。
- docker-compose.yml。
- GitHub Actions。
- GHCR 镜像发布。
- 安装文档。

## 20. 后续 Agent 模式

后续可以在目标服务器安装轻量 Agent。

Agent 能力：

- 本机命令白名单执行。
- 文件上传接收。
- 服务状态查询。
- 日志流式返回。
- 资源指标上报。
- 任务执行心跳。

中心面板能力：

- 选择 SSH 模式或 Agent 模式。
- 批量安装 Agent。
- 管理 Agent 在线状态。
- 使用 Agent 替代 SSH 执行高频操作。

Agent 模式不进入 MVP，但数据模型和架构要预留 server.connection_mode 字段。

## 21. 成功标准

MVP 成功标准：

1. 可以用 Docker Compose 启动系统。
2. 可以在 Web 页面配置中转站 API 并测试成功。
3. 可以添加 3 台服务器。
4. 可以看到服务器列表和基础资源状态。
5. 可以打开任意一台服务器的 Web 终端。
6. 可以输入“查询当前服务器配置”，系统真实执行命令并总结。
7. 可以上传一个常见服务包，让 AI 判断服务类型和启动方式。
8. 可以展示部署计划并等待用户确认。
9. 用户确认后可以在目标服务器完成一次部署。
10. 可以查看执行日志和部署历史。
11. 可以在页面修改默认模型，不需要重启 Docker 容器。
