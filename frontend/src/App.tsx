import {
  Activity,
  Bot,
  CheckCircle2,
  Cpu,
  Database,
  HardDrive,
  History,
  KeyRound,
  Play,
  Server,
  Settings,
  ShieldAlert,
  TerminalSquare,
  UploadCloud
} from "lucide-react";

const servers = [
  {
    name: "prod-app-01",
    host: "10.0.12.21",
    status: "online",
    os: "Ubuntu 24.04",
    cpu: "8 cores",
    memory: "61%",
    disk: "48%"
  },
  {
    name: "staging-web",
    host: "10.0.12.33",
    status: "online",
    os: "Debian 12",
    cpu: "4 cores",
    memory: "42%",
    disk: "35%"
  },
  {
    name: "legacy-api",
    host: "172.16.4.8",
    status: "unknown",
    os: "CentOS Stream",
    cpu: "2 cores",
    memory: "-",
    disk: "-"
  }
];

const deploymentSteps = [
  "上传并解压服务包到 /opt/apps/demo",
  "识别 package.json 并安装依赖",
  "执行 npm run build",
  "生成 systemd 服务草案",
  "等待管理员确认后启动服务"
];

export function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Server size={22} />
          <div>
            <strong>AI Agent SSH</strong>
            <span>Operations Panel</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="主导航">
          <button className="active"><Activity size={18} />概览</button>
          <button><TerminalSquare size={18} />终端</button>
          <button><Bot size={18} />AI 助手</button>
          <button><UploadCloud size={18} />服务部署</button>
          <button><History size={18} />历史记录</button>
          <button><Settings size={18} />系统设置</button>
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>服务器运维面板</h1>
            <p>通过 SSH 管理多台服务器，AI 只生成计划，执行前必须确认。</p>
          </div>
          <button className="primary-action"><Server size={18} />添加服务器</button>
        </header>

        <section className="metric-grid" aria-label="系统概览">
          <Metric icon={<Server />} label="服务器" value="3" detail="2 online" />
          <Metric icon={<Bot />} label="默认模型" value="deepseek-chat" detail="OpenAI compatible" />
          <Metric icon={<ShieldAlert />} label="安全策略" value="启用" detail="危险命令拦截" />
          <Metric icon={<Database />} label="数据库" value="SQLite" detail="可迁移 PostgreSQL" />
        </section>

        <section className="content-grid">
          <div className="panel server-panel">
            <div className="panel-header">
              <div>
                <h2>服务器列表</h2>
                <p>在线状态和资源信息会由后端 SSH 快照刷新。</p>
              </div>
              <button className="ghost-action">批量巡检</button>
            </div>
            <div className="server-table">
              <div className="table-row table-head">
                <span>名称</span>
                <span>地址</span>
                <span>系统</span>
                <span>CPU</span>
                <span>内存</span>
                <span>磁盘</span>
                <span>状态</span>
              </div>
              {servers.map((server) => (
                <div className="table-row" key={server.host}>
                  <strong>{server.name}</strong>
                  <span>{server.host}</span>
                  <span>{server.os}</span>
                  <span>{server.cpu}</span>
                  <span>{server.memory}</span>
                  <span>{server.disk}</span>
                  <span className={`status ${server.status}`}>{server.status}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header compact">
              <h2>AI 中转站</h2>
              <KeyRound size={18} />
            </div>
            <div className="settings-list">
              <label>
                Base URL
                <input value="https://cdn.coderelay.cn/v1" readOnly />
              </label>
              <label>
                API Key
                <input value="sk-***************" readOnly />
              </label>
              <label>
                默认模型
                <input value="deepseek-chat" readOnly />
              </label>
            </div>
            <button className="secondary-action"><CheckCircle2 size={18} />测试连接</button>
          </div>
        </section>

        <section className="content-grid lower">
          <div className="panel">
            <div className="panel-header compact">
              <h2>部署计划确认</h2>
              <Play size={18} />
            </div>
            <ol className="step-list">
              {deploymentSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <div className="risk-box">
              <ShieldAlert size={18} />
              <span>涉及 sudo、覆盖文件或安装依赖时，后端会标记风险并要求确认。</span>
            </div>
          </div>

          <div className="panel terminal-panel">
            <div className="panel-header compact">
              <h2>Web SSH 终端</h2>
              <TerminalSquare size={18} />
            </div>
            <div className="terminal">
              <span>$ systemctl status demo.service</span>
              <span>● demo.service - managed by AI Agent SSH</span>
              <span>Active: waiting for connection</span>
            </div>
          </div>

          <div className="panel resource-panel">
            <div className="panel-header compact">
              <h2>资源快照</h2>
              <Cpu size={18} />
            </div>
            <Resource label="CPU" value="37%" />
            <Resource label="Memory" value="61%" />
            <Resource label="Disk" value="48%" icon={<HardDrive size={16} />} />
          </div>
        </section>
      </main>
    </div>
  );
}

function Metric({ icon, label, value, detail }: { icon: React.ReactNode; label: string; value: string; detail: string }) {
  return (
    <div className="metric">
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function Resource({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="resource">
      <div>
        {icon}
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
      <meter value={Number.parseInt(value, 10)} min="0" max="100" />
    </div>
  );
}
