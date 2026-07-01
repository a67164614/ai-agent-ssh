import { useMemo, useState } from "react";
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

type SectionId = "overview" | "terminal" | "assistant" | "deploy" | "history" | "settings";
type NoticeTone = "neutral" | "success" | "danger";

type Notice = {
  tone: NoticeTone;
  message: string;
};

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

const sections: Array<{ id: SectionId; label: string; icon: React.ReactNode }> = [
  { id: "overview", label: "概览", icon: <Activity size={18} /> },
  { id: "terminal", label: "终端", icon: <TerminalSquare size={18} /> },
  { id: "assistant", label: "AI 助手", icon: <Bot size={18} /> },
  { id: "deploy", label: "服务部署", icon: <UploadCloud size={18} /> },
  { id: "history", label: "历史记录", icon: <History size={18} /> },
  { id: "settings", label: "系统设置", icon: <Settings size={18} /> }
];

const samplePlan = {
  summary: "部署 Node.js 示例服务",
  risk_level: "medium",
  requires_sudo: false,
  steps: [
    {
      name: "安装依赖",
      command: "npm install",
      working_directory: "/opt/apps/demo"
    },
    {
      name: "构建服务",
      command: "npm run build",
      working_directory: "/opt/apps/demo"
    }
  ]
};

export function App() {
  const [activeSection, setActiveSection] = useState<SectionId>("overview");
  const [notice, setNotice] = useState<Notice>({ tone: "neutral", message: "等待操作。" });
  const [command, setCommand] = useState("systemctl status nginx");
  const [isLoading, setIsLoading] = useState(false);

  const currentTitle = useMemo(
    () => sections.find((section) => section.id === activeSection)?.label ?? "概览",
    [activeSection]
  );

  async function checkHealth() {
    setIsLoading(true);
    setNotice({ tone: "neutral", message: "正在检查后端连接..." });
    try {
      const response = await fetch("/api/health");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const body = (await response.json()) as { service: string };
      setNotice({ tone: "success", message: `后端连接正常：${body.service}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `后端连接失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function checkCommand() {
    setIsLoading(true);
    setNotice({ tone: "neutral", message: "正在检查命令风险..." });
    try {
      const response = await fetch("/api/commands/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command })
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const body = (await response.json()) as { allowed: boolean; reason: string | null; warnings: string[] };
      if (!body.allowed) {
        setNotice({ tone: "danger", message: `已拦截：${body.reason}` });
        return;
      }
      const warnings = body.warnings.length > 0 ? `，提示：${body.warnings.join(", ")}` : "";
      setNotice({ tone: "success", message: `命令允许执行${warnings}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `命令检查失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function validatePlan() {
    setIsLoading(true);
    setNotice({ tone: "neutral", message: "正在校验部署计划..." });
    try {
      const response = await fetch("/api/deployments/validate-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(samplePlan)
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const body = (await response.json()) as { valid: boolean; plan: { steps: unknown[] } };
      setNotice({ tone: "success", message: `部署计划校验通过，共 ${body.plan.steps.length} 个步骤。` });
    } catch (error) {
      setNotice({ tone: "danger", message: `部署计划校验失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Server size={22} />
          <div>
            <strong>AI Agent SSH</strong>
            <span>运维面板</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="主导航">
          {sections.map((section) => (
            <button
              className={activeSection === section.id ? "active" : ""}
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              type="button"
            >
              {section.icon}
              {section.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>{currentTitle}</h1>
            <p>通过 SSH 管理多台服务器，AI 只生成计划，执行前必须确认。</p>
          </div>
          <button className="primary-action" onClick={() => setNotice({ tone: "neutral", message: "添加服务器功能将在服务器管理接口完成后启用。" })} type="button">
            <Server size={18} />添加服务器
          </button>
        </header>

        <div className={`notice ${notice.tone}`} role="status">
          {notice.message}
        </div>

        {activeSection === "overview" && <OverviewSection isLoading={isLoading} onCheckHealth={checkHealth} />}
        {activeSection === "terminal" && <TerminalSection />}
        {activeSection === "assistant" && (
          <AssistantSection command={command} isLoading={isLoading} onChangeCommand={setCommand} onCheckCommand={checkCommand} />
        )}
        {activeSection === "deploy" && <DeploySection isLoading={isLoading} onValidatePlan={validatePlan} />}
        {activeSection === "history" && <HistorySection />}
        {activeSection === "settings" && <SettingsSection isLoading={isLoading} onCheckHealth={checkHealth} />}
      </main>
    </div>
  );
}

function OverviewSection({ isLoading, onCheckHealth }: { isLoading: boolean; onCheckHealth: () => void }) {
  return (
    <>
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
            <button className="ghost-action" onClick={onCheckHealth} type="button" disabled={isLoading}>
              检查后端
            </button>
          </div>
          <ServerTable />
        </div>

        <AiProviderPanel isLoading={isLoading} onCheckHealth={onCheckHealth} />
      </section>
    </>
  );
}

function TerminalSection() {
  return (
    <section className="content-grid single">
      <div className="panel terminal-panel">
        <div className="panel-header compact">
          <div>
            <h2>Web SSH 终端</h2>
            <p>真实终端代理将在 WebSocket SSH 功能完成后启用。</p>
          </div>
          <TerminalSquare size={18} />
        </div>
        <div className="terminal">
          <span>$ systemctl status demo.service</span>
          <span>● demo.service - managed by AI Agent SSH</span>
          <span>Active: waiting for WebSocket SSH executor</span>
        </div>
      </div>
    </section>
  );
}

function AssistantSection({
  command,
  isLoading,
  onChangeCommand,
  onCheckCommand
}: {
  command: string;
  isLoading: boolean;
  onChangeCommand: (value: string) => void;
  onCheckCommand: () => void;
}) {
  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="panel-header compact">
          <div>
            <h2>AI 命令安全检查</h2>
            <p>当前先接入后端危险命令检测，后续再接 AI 生成命令。</p>
          </div>
          <Bot size={18} />
        </div>
        <div className="settings-list">
          <label>
            待检查命令
            <input value={command} onChange={(event) => onChangeCommand(event.target.value)} />
          </label>
        </div>
        <button className="secondary-action" onClick={onCheckCommand} type="button" disabled={isLoading}>
          <ShieldAlert size={18} />检查命令
        </button>
      </div>
    </section>
  );
}

function DeploySection({ isLoading, onValidatePlan }: { isLoading: boolean; onValidatePlan: () => void }) {
  return (
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
        <button className="secondary-action spaced" onClick={onValidatePlan} type="button" disabled={isLoading}>
          <CheckCircle2 size={18} />校验部署计划
        </button>
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
  );
}

function HistorySection() {
  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="panel-header compact">
          <div>
            <h2>历史记录</h2>
            <p>部署任务、命令输出和审计日志接口完成后会在这里展示。</p>
          </div>
          <History size={18} />
        </div>
        <div className="timeline">
          <span>已完成：后端健康检查接口</span>
          <span>已完成：命令安全检查接口</span>
          <span>已完成：部署计划校验接口</span>
        </div>
      </div>
    </section>
  );
}

function SettingsSection({ isLoading, onCheckHealth }: { isLoading: boolean; onCheckHealth: () => void }) {
  return (
    <section className="content-grid single">
      <AiProviderPanel isLoading={isLoading} onCheckHealth={onCheckHealth} />
    </section>
  );
}

function ServerTable() {
  return (
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
        <button className="table-row table-button" key={server.host} type="button">
          <strong>{server.name}</strong>
          <span>{server.host}</span>
          <span>{server.os}</span>
          <span>{server.cpu}</span>
          <span>{server.memory}</span>
          <span>{server.disk}</span>
          <span className={`status ${server.status}`}>{server.status}</span>
        </button>
      ))}
    </div>
  );
}

function AiProviderPanel({ isLoading, onCheckHealth }: { isLoading: boolean; onCheckHealth: () => void }) {
  return (
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
      <button className="secondary-action" onClick={onCheckHealth} type="button" disabled={isLoading}>
        <CheckCircle2 size={18} />检查后端
      </button>
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

function formatError(error: unknown) {
  return error instanceof Error ? error.message : "未知错误";
}
