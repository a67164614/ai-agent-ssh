import { useEffect, useMemo, useState } from "react";
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

type User = {
  id: number;
  username: string;
  role: string;
};

type AuthResponse = {
  access_token: string;
  user: User;
};

type AuthStatus = {
  initialized: boolean;
};

type ServerRecord = {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string;
  auth_type: string;
  remark: string | null;
  status: string;
  connection_mode: string;
  has_password: boolean;
  has_private_key: boolean;
  last_test_message?: string | null;
};

type AiProvider = {
  id: number;
  name: string;
  provider_type: string;
  base_url: string;
  default_model: string | null;
  api_mode: string;
  enabled: boolean;
  has_api_key: boolean;
  api_key_mask: string;
  last_test_status?: string | null;
  last_test_message?: string | null;
};

type ServerForm = {
  name: string;
  host: string;
  port: string;
  username: string;
  password: string;
  remark: string;
};

type ProviderForm = {
  name: string;
  base_url: string;
  api_key: string;
  default_model: string;
};

const tokenKey = "ai-agent-ssh-token";

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

const emptyServerForm: ServerForm = {
  name: "",
  host: "",
  port: "22",
  username: "root",
  password: "",
  remark: ""
};

const emptyProviderForm: ProviderForm = {
  name: "",
  base_url: "https://",
  api_key: "",
  default_model: ""
};

export function App() {
  const [activeSection, setActiveSection] = useState<SectionId>("overview");
  const [notice, setNotice] = useState<Notice>({ tone: "neutral", message: "等待操作。" });
  const [command, setCommand] = useState("systemctl status nginx");
  const [isLoading, setIsLoading] = useState(false);
  const [token, setToken] = useState(() => window.localStorage.getItem(tokenKey) ?? "");
  const [user, setUser] = useState<User | null>(null);
  const [isAdminInitialized, setIsAdminInitialized] = useState(false);
  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [authForm, setAuthForm] = useState({ username: "", password: "" });
  const [servers, setServers] = useState<ServerRecord[]>([]);
  const [providers, setProviders] = useState<AiProvider[]>([]);
  const [showServerForm, setShowServerForm] = useState(false);
  const [serverForm, setServerForm] = useState<ServerForm>(emptyServerForm);
  const [providerForm, setProviderForm] = useState<ProviderForm>(emptyProviderForm);

  const currentTitle = useMemo(
    () => sections.find((section) => section.id === activeSection)?.label ?? "概览",
    [activeSection]
  );

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      try {
        if (token) {
          const me = await apiRequest<User>("/auth/me", { token });
          if (cancelled) return;
          setUser(me);
          setIsAdminInitialized(true);
          try {
            await loadResources(token);
          } catch (error) {
            if (!cancelled) {
              setNotice({ tone: "danger", message: `资源加载失败：${formatError(error)}` });
            }
          }
          return;
        }
      } catch {
        if (!cancelled) {
          window.localStorage.removeItem(tokenKey);
          setToken("");
          setUser(null);
        }
      } finally {
        try {
          const status = await apiRequest<AuthStatus>("/auth/status");
          if (!cancelled) {
            setIsAdminInitialized(status.initialized);
          }
        } catch {
          if (!cancelled) {
            setIsAdminInitialized(true);
            setNotice({ tone: "danger", message: "认证状态检查失败，请确认后端服务是否正常。" });
          }
        }
        if (!cancelled) {
          setIsAuthChecked(true);
        }
      }
    }
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  async function loadResources(activeToken: string) {
    const [serverItems, providerItems] = await Promise.all([
      apiRequest<ServerRecord[]>("/servers", { token: activeToken }),
      apiRequest<AiProvider[]>("/ai-providers", { token: activeToken })
    ]);
    setServers(serverItems);
    setProviders(providerItems);
  }

  async function submitAuth(mode: "init" | "login") {
    if (authForm.password.length < 8) {
      setNotice({ tone: "danger", message: "认证失败：密码至少需要 8 位。" });
      return;
    }
    setIsLoading(true);
    setNotice({ tone: "neutral", message: mode === "init" ? "正在初始化管理员..." : "正在登录..." });
    try {
      const body = await apiRequest<AuthResponse>(`/auth/${mode}`, {
        method: "POST",
        body: authForm
      });
      window.localStorage.setItem(tokenKey, body.access_token);
      setToken(body.access_token);
      setUser(body.user);
      setIsAdminInitialized(true);
      await loadResources(body.access_token);
      setNotice({ tone: "success", message: `登录用户：${body.user.username}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `认证失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function checkHealth() {
    setIsLoading(true);
    setNotice({ tone: "neutral", message: "正在检查后端连接..." });
    try {
      const body = await apiRequest<{ service: string }>("/health", { token });
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
      const body = await apiRequest<{ allowed: boolean; reason: string | null; warnings: string[] }>("/commands/check", {
        method: "POST",
        token,
        body: { command }
      });
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
      const body = await apiRequest<{ valid: boolean; plan: { steps: unknown[] } }>("/deployments/validate-plan", {
        method: "POST",
        token,
        body: samplePlan
      });
      setNotice({ tone: "success", message: `部署计划校验通过，共 ${body.plan.steps.length} 个步骤。` });
    } catch (error) {
      setNotice({ tone: "danger", message: `部署计划校验失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function saveServer() {
    setIsLoading(true);
    setNotice({ tone: "neutral", message: "正在保存服务器..." });
    try {
      const saved = await apiRequest<ServerRecord>("/servers", {
        method: "POST",
        token,
        body: {
          name: serverForm.name,
          host: serverForm.host,
          port: Number(serverForm.port || 22),
          username: serverForm.username,
          auth_type: "password",
          password: serverForm.password,
          remark: serverForm.remark || null
        }
      });
      setServers((items) => [...items, saved]);
      setServerForm(emptyServerForm);
      setShowServerForm(false);
      setNotice({ tone: "success", message: `服务器已保存：${saved.name}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `服务器保存失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function testServer(server: ServerRecord) {
    setIsLoading(true);
    setNotice({ tone: "neutral", message: `正在检查 ${server.name}...` });
    try {
      const updated = await apiRequest<ServerRecord>(`/servers/${server.id}/test`, { method: "POST", token });
      setServers((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setNotice({ tone: "success", message: updated.last_test_message ?? `${updated.name} 检查完成。` });
    } catch (error) {
      setNotice({ tone: "danger", message: `服务器检查失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function saveProvider() {
    setIsLoading(true);
    setNotice({ tone: "neutral", message: "正在保存 AI 中转站..." });
    try {
      const saved = await apiRequest<AiProvider>("/ai-providers", {
        method: "POST",
        token,
        body: {
          name: providerForm.name,
          base_url: providerForm.base_url,
          api_key: providerForm.api_key,
          default_model: providerForm.default_model || null,
          enabled: true
        }
      });
      setProviders((items) => [...items, saved]);
      setProviderForm(emptyProviderForm);
      setNotice({ tone: "success", message: `AI 中转站已保存：${saved.name}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `AI 中转站保存失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function testProvider(provider: AiProvider) {
    setIsLoading(true);
    try {
      const updated = await apiRequest<AiProvider>(`/ai-providers/${provider.id}/test`, { method: "POST", token });
      setProviders((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setNotice({ tone: "success", message: updated.last_test_message ?? `${updated.name} 检查完成。` });
    } catch (error) {
      setNotice({ tone: "danger", message: `AI 中转站检查失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  if (!user) {
    return (
      <main className="auth-screen">
        <section className="panel auth-panel">
          <div className="brand auth-brand">
            <Server size={24} />
            <div>
              <strong>AI Agent SSH</strong>
              <span>管理员入口</span>
            </div>
          </div>
          <div className="settings-list">
            <label>
              账号
              <input value={authForm.username} onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })} />
            </label>
            <label>
              密码
              <input
                type="password"
                value={authForm.password}
                onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })}
              />
            </label>
          </div>
          <div className="button-row">
            {!isAdminInitialized && isAuthChecked && (
              <button className="primary-action" onClick={() => void submitAuth("init")} type="button" disabled={isLoading}>
                初始化管理员
              </button>
            )}
            <button className="ghost-action" onClick={() => void submitAuth("login")} type="button" disabled={isLoading}>
              登录
            </button>
          </div>
          <div className={`notice ${notice.tone}`} role="status">
            {notice.message}
          </div>
        </section>
      </main>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Server size={22} />
          <div>
            <strong>AI Agent SSH</strong>
            <span>登录用户：{user.username}</span>
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
          <button className="primary-action" onClick={() => setShowServerForm(true)} type="button">
            <Server size={18} />添加服务器
          </button>
        </header>

        <div className={`notice ${notice.tone}`} role="status">
          {notice.message}
        </div>

        {showServerForm && (
          <ServerFormPanel
            form={serverForm}
            isLoading={isLoading}
            onChange={setServerForm}
            onCancel={() => setShowServerForm(false)}
            onSave={saveServer}
          />
        )}

        {activeSection === "overview" && (
          <OverviewSection
            isLoading={isLoading}
            providers={providers}
            servers={servers}
            onCheckHealth={checkHealth}
            onTestServer={testServer}
            onTestProvider={testProvider}
          />
        )}
        {activeSection === "terminal" && <TerminalSection />}
        {activeSection === "assistant" && (
          <AssistantSection command={command} isLoading={isLoading} onChangeCommand={setCommand} onCheckCommand={checkCommand} />
        )}
        {activeSection === "deploy" && <DeploySection isLoading={isLoading} onValidatePlan={validatePlan} />}
        {activeSection === "history" && <HistorySection />}
        {activeSection === "settings" && (
          <SettingsSection
            form={providerForm}
            isLoading={isLoading}
            providers={providers}
            onChange={setProviderForm}
            onSave={saveProvider}
            onTestProvider={testProvider}
          />
        )}
      </main>
    </div>
  );
}

function OverviewSection({
  isLoading,
  providers,
  servers,
  onCheckHealth,
  onTestServer,
  onTestProvider
}: {
  isLoading: boolean;
  providers: AiProvider[];
  servers: ServerRecord[];
  onCheckHealth: () => void;
  onTestServer: (server: ServerRecord) => void;
  onTestProvider: (provider: AiProvider) => void;
}) {
  const defaultProvider = providers.find((provider) => provider.enabled) ?? providers[0];
  return (
    <>
      <section className="metric-grid" aria-label="系统概览">
        <Metric icon={<Server />} label="服务器" value={String(servers.length)} detail={`${servers.filter((item) => item.status === "online").length} online`} />
        <Metric icon={<Bot />} label="默认模型" value={defaultProvider?.default_model ?? "-"} detail={defaultProvider?.name ?? "未配置"} />
        <Metric icon={<ShieldAlert />} label="安全策略" value="启用" detail="危险命令拦截" />
        <Metric icon={<Database />} label="数据库" value="SQLite" detail="可迁移 PostgreSQL" />
      </section>

      <section className="content-grid">
        <div className="panel server-panel">
          <div className="panel-header">
            <div>
              <h2>服务器列表</h2>
              <p>状态和资源快照由后端服务器接口维护。</p>
            </div>
            <button className="ghost-action" onClick={onCheckHealth} type="button" disabled={isLoading}>
              检查后端
            </button>
          </div>
          <ServerTable servers={servers} isLoading={isLoading} onTestServer={onTestServer} />
        </div>

        <AiProviderPanel providers={providers} isLoading={isLoading} onTestProvider={onTestProvider} />
      </section>
    </>
  );
}

function ServerFormPanel({
  form,
  isLoading,
  onCancel,
  onChange,
  onSave
}: {
  form: ServerForm;
  isLoading: boolean;
  onCancel: () => void;
  onChange: (form: ServerForm) => void;
  onSave: () => void;
}) {
  return (
    <section className="panel">
      <div className="panel-header compact">
        <h2>添加服务器</h2>
        <Server size={18} />
      </div>
      <div className="form-grid">
        <label>
          服务器名称
          <input value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} />
        </label>
        <label>
          主机地址
          <input value={form.host} onChange={(event) => onChange({ ...form, host: event.target.value })} />
        </label>
        <label>
          SSH 端口
          <input value={form.port} onChange={(event) => onChange({ ...form, port: event.target.value })} />
        </label>
        <label>
          SSH 用户
          <input value={form.username} onChange={(event) => onChange({ ...form, username: event.target.value })} />
        </label>
        <label>
          SSH 密码
          <input type="password" value={form.password} onChange={(event) => onChange({ ...form, password: event.target.value })} />
        </label>
        <label>
          备注
          <input value={form.remark} onChange={(event) => onChange({ ...form, remark: event.target.value })} />
        </label>
      </div>
      <div className="button-row">
        <button className="primary-action" onClick={onSave} type="button" disabled={isLoading}>
          保存服务器
        </button>
        <button className="ghost-action" onClick={onCancel} type="button">
          取消
        </button>
      </div>
    </section>
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
        <Resource label="CPU" value="-" />
        <Resource label="Memory" value="-" />
        <Resource label="Disk" value="-" icon={<HardDrive size={16} />} />
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
            <p>部署任务、命令输出和审计日志列表会在下一阶段展示。</p>
          </div>
          <History size={18} />
        </div>
        <div className="timeline">
          <span>已完成：管理员初始化和登录</span>
          <span>已完成：AI 中转站配置保存</span>
          <span>已完成：服务器保存和连接检查入口</span>
        </div>
      </div>
    </section>
  );
}

function SettingsSection({
  form,
  isLoading,
  providers,
  onChange,
  onSave,
  onTestProvider
}: {
  form: ProviderForm;
  isLoading: boolean;
  providers: AiProvider[];
  onChange: (form: ProviderForm) => void;
  onSave: () => void;
  onTestProvider: (provider: AiProvider) => void;
}) {
  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="panel-header compact">
          <h2>AI 中转站配置</h2>
          <KeyRound size={18} />
        </div>
        <div className="form-grid">
          <label>
            供应商名称
            <input value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} />
          </label>
          <label>
            Base URL
            <input value={form.base_url} onChange={(event) => onChange({ ...form, base_url: event.target.value })} />
          </label>
          <label>
            API Key
            <input type="password" value={form.api_key} onChange={(event) => onChange({ ...form, api_key: event.target.value })} />
          </label>
          <label>
            默认模型
            <input value={form.default_model} onChange={(event) => onChange({ ...form, default_model: event.target.value })} />
          </label>
        </div>
        <button className="secondary-action" onClick={onSave} type="button" disabled={isLoading}>
          保存 AI 中转站
        </button>
        <div className="provider-list">
          {providers.map((provider) => (
            <div className="list-card" key={provider.id}>
              <strong>{provider.name}</strong>
              <span>{provider.base_url}</span>
              <span>{provider.default_model ?? "未设置模型"} · {provider.api_key_mask}</span>
              <button className="ghost-action" onClick={() => onTestProvider(provider)} type="button" disabled={isLoading}>
                测试
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ServerTable({
  isLoading,
  servers,
  onTestServer
}: {
  isLoading: boolean;
  servers: ServerRecord[];
  onTestServer: (server: ServerRecord) => void;
}) {
  return (
    <div className="server-table">
      <div className="table-row table-head">
        <span>名称</span>
        <span>地址</span>
        <span>用户</span>
        <span>认证</span>
        <span>模式</span>
        <span>状态</span>
        <span>操作</span>
      </div>
      {servers.map((server) => (
        <div className="table-row" key={server.id}>
          <strong>{server.name}</strong>
          <span>{server.host}:{server.port}</span>
          <span>{server.username}</span>
          <span>{server.has_private_key ? "私钥" : "密码"}</span>
          <span>{server.connection_mode}</span>
          <span className={`status ${server.status}`}>{server.status}</span>
          <button className="ghost-action compact-button" onClick={() => onTestServer(server)} type="button" disabled={isLoading}>
            测试
          </button>
        </div>
      ))}
      {servers.length === 0 && <div className="empty-state">暂无服务器，请先添加。</div>}
    </div>
  );
}

function AiProviderPanel({
  isLoading,
  providers,
  onTestProvider
}: {
  isLoading: boolean;
  providers: AiProvider[];
  onTestProvider: (provider: AiProvider) => void;
}) {
  return (
    <div className="panel">
      <div className="panel-header compact">
        <h2>AI 中转站</h2>
        <KeyRound size={18} />
      </div>
      <div className="provider-list compact-list">
        {providers.map((provider) => (
          <div className="list-card" key={provider.id}>
            <strong>{provider.name}</strong>
            <span>{provider.base_url}</span>
            <span>{provider.default_model ?? "未设置模型"}</span>
            <button className="ghost-action" onClick={() => onTestProvider(provider)} type="button" disabled={isLoading}>
              测试
            </button>
          </div>
        ))}
        {providers.length === 0 && <div className="empty-state">暂无 AI 中转站配置。</div>}
      </div>
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
  const numericValue = Number.parseInt(value, 10);
  return (
    <div className="resource">
      <div>
        {icon}
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
      <meter value={Number.isFinite(numericValue) ? numericValue : 0} min="0" max="100" />
    </div>
  );
}

async function apiRequest<T>(
  path: string,
  options: { method?: string; token?: string; body?: unknown } = {}
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body)
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return (await response.json()) as T;
}

async function readErrorMessage(response: Response) {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      const first = body.detail[0] as { msg?: string; loc?: string[] };
      const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : "";
      if (field === "password" && first.msg?.includes("8")) {
        return "密码至少需要 8 位。";
      }
      return first.msg ?? `HTTP ${response.status}`;
    }
  } catch {
    return `HTTP ${response.status}`;
  }
  return `HTTP ${response.status}`;
}

function formatError(error: unknown) {
  return error instanceof Error ? error.message : "未知错误";
}
