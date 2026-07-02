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

type ServerSnapshot = {
  id: number;
  server_id: number;
  status: string;
  cpu_usage: number | null;
  cpu_cores?: number | null;
  memory_usage: number | null;
  memory_total_mb?: number | null;
  memory_used_mb?: number | null;
  disk_usage: number | null;
  disk_total_gb?: number | null;
  disk_used_gb?: number | null;
  os_info: string | null;
  kernel?: string | null;
  ip_addresses?: string | null;
  message: string | null;
  created_at?: string | null;
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
  last_seen_at?: string | null;
  latest_snapshot?: ServerSnapshot | null;
};

const serverStatusLabels: Record<string, string> = {
  online: "在线",
  offline: "离线",
  unknown: "未检测",
  unchecked: "未检测",
  skipped: "未启用",
  failed: "失败",
  ok: "正常"
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

type AiModel = {
  id: number;
  provider_id: number;
  model_id: string;
  display_name: string | null;
  source: string;
  enabled: boolean;
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

type CommandLog = {
  id: number;
  task_id: number | null;
  server_id: number;
  command: string;
  working_directory: string | null;
  stdout: string | null;
  stderr: string | null;
  exit_code: number | null;
  status: string;
  started_at: string | null;
  finished_at: string | null;
};

type DeploymentPlan = {
  summary: string;
  risk_level: string;
  requires_sudo: boolean;
  steps: Array<{ name: string; command: string; working_directory: string }>;
};

type PackageRecord = {
  id: number;
  filename: string;
  size: number;
  sha256: string;
  uploaded_at: string | null;
};

type ProjectAnalysis = {
  id: number;
  package_id: number | null;
  server_id: number | null;
  target_path: string | null;
  detected_type: string;
  summary: string;
  dependencies: string[];
  start_commands: string[];
  file_tree: string[];
  plan: DeploymentPlan;
  created_at: string | null;
};

type DeploymentTask = {
  id: number;
  server_id: number;
  package_id: number | null;
  status: string;
  summary: string | null;
  plan: DeploymentPlan;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string | null;
  logs: CommandLog[];
};

type AssistantState = {
  question: string;
  suggestedCommand: string;
  explanation: string;
  warnings: string[];
  source: string;
  output: string;
  summary: string;
};

type DeployState = {
  targetPath: string;
  packageFile: File | null;
  packageRecord: PackageRecord | null;
  analysis: ProjectAnalysis | null;
  task: DeploymentTask | null;
};

const tokenKey = "ai-agent-ssh-token";

const sections: Array<{ id: SectionId; label: string; icon: React.ReactNode }> = [
  { id: "overview", label: "概览", icon: <Activity size={18} /> },
  { id: "terminal", label: "终端", icon: <TerminalSquare size={18} /> },
  { id: "assistant", label: "AI 助手", icon: <Bot size={18} /> },
  { id: "deploy", label: "服务部署", icon: <UploadCloud size={18} /> },
  { id: "history", label: "历史记录", icon: <History size={18} /> },
  { id: "settings", label: "系统设置", icon: <Settings size={18} /> }
];

const samplePlan: DeploymentPlan = {
  summary: "部署 Node.js 示例服务",
  risk_level: "medium",
  requires_sudo: false,
  steps: [
    { name: "安装依赖", command: "npm install", working_directory: "/opt/apps/demo" },
    { name: "构建服务", command: "npm run build", working_directory: "/opt/apps/demo" }
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

const defaultAssistantState: AssistantState = {
  question: "查询当前服务器配置",
  suggestedCommand: "",
  explanation: "",
  warnings: [],
  source: "",
  output: "",
  summary: ""
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
  const [modelsByProvider, setModelsByProvider] = useState<Record<number, AiModel[]>>({});
  const [packages, setPackages] = useState<PackageRecord[]>([]);
  const [deployments, setDeployments] = useState<DeploymentTask[]>([]);
  const [showServerForm, setShowServerForm] = useState(false);
  const [editingServer, setEditingServer] = useState<ServerRecord | null>(null);
  const [selectedServer, setSelectedServer] = useState<ServerRecord | null>(null);
  const [serverForm, setServerForm] = useState<ServerForm>(emptyServerForm);
  const [providerForm, setProviderForm] = useState<ProviderForm>(emptyProviderForm);
  const [manualModelId, setManualModelId] = useState("");
  const [assistantState, setAssistantState] = useState<AssistantState>(defaultAssistantState);
  const [deployState, setDeployState] = useState<DeployState>({
    targetPath: "/opt/apps/demo",
    packageFile: null,
    packageRecord: null,
    analysis: null,
    task: null
  });

  const currentTitle = useMemo(
    () => sections.find((section) => section.id === activeSection)?.label ?? "概览",
    [activeSection]
  );
  const activeServer = selectedServer ?? servers[0] ?? null;

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
    const [serverItems, providerItems, packageItems, deploymentItems] = await Promise.all([
      apiRequest<ServerRecord[]>("/servers", { token: activeToken }),
      apiRequest<AiProvider[]>("/ai-providers", { token: activeToken }),
      apiRequest<PackageRecord[]>("/packages", { token: activeToken }).catch(() => []),
      apiRequest<DeploymentTask[]>("/deployments", { token: activeToken }).catch(() => [])
    ]);
    setServers(serverItems);
    setProviders(providerItems);
    setPackages(packageItems);
    setDeployments(deploymentItems);
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
    setNotice({ tone: "neutral", message: editingServer ? "正在更新服务器..." : "正在保存服务器..." });
    try {
      const payload = {
        name: serverForm.name,
        host: serverForm.host,
        port: Number(serverForm.port || 22),
        username: serverForm.username,
        auth_type: "password",
        password: serverForm.password,
        remark: serverForm.remark || null
      };
      const saved = await apiRequest<ServerRecord>(editingServer ? `/servers/${editingServer.id}` : "/servers", {
        method: editingServer ? "PUT" : "POST",
        token,
        body: payload
      });
      setServers((items) => (editingServer ? items.map((item) => (item.id === saved.id ? saved : item)) : [...items, saved]));
      setSelectedServer((current) => (current?.id === saved.id ? saved : current));
      setServerForm(emptyServerForm);
      setEditingServer(null);
      setShowServerForm(false);
      setNotice({ tone: "success", message: editingServer ? `服务器已更新：${saved.name}` : `服务器已保存：${saved.name}` });
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
      updateServerInState(updated);
      const fallback = `服务器状态：${formatServerStatus(updated.status)}`;
      setNotice({
        tone: updated.status === "online" ? "success" : "danger",
        message:
          updated.status === "online"
            ? `服务器连接成功：${updated.last_test_message ?? fallback}`
            : `服务器连接失败：${updated.last_test_message ?? fallback}`
      });
    } catch (error) {
      setNotice({ tone: "danger", message: `服务器检查失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshSnapshot(server: ServerRecord) {
    setIsLoading(true);
    try {
      const snapshot = await apiRequest<ServerSnapshot>(`/servers/${server.id}/snapshot`, { method: "POST", token });
      const updated = { ...server, latest_snapshot: snapshot, status: snapshot.status === "ok" ? "online" : server.status };
      updateServerInState(updated);
      setNotice({ tone: snapshot.status === "ok" ? "success" : "danger", message: snapshot.message ?? "资源快照已刷新。" });
    } catch (error) {
      setNotice({ tone: "danger", message: `资源快照刷新失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function deleteServer(server: ServerRecord) {
    setIsLoading(true);
    try {
      await apiRequest<{ ok: boolean }>(`/servers/${server.id}`, { method: "DELETE", token });
      setServers((items) => items.filter((item) => item.id !== server.id));
      setSelectedServer(null);
      setNotice({ tone: "success", message: "服务器已删除。" });
    } catch (error) {
      setNotice({ tone: "danger", message: `服务器删除失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  function editServer(server: ServerRecord) {
    setEditingServer(server);
    setServerForm({
      name: server.name,
      host: server.host,
      port: String(server.port),
      username: server.username,
      password: "",
      remark: server.remark ?? ""
    });
    setShowServerForm(true);
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
      setNotice({ tone: updated.last_test_status === "failed" ? "danger" : "success", message: updated.last_test_message ?? `AI 中转站状态：${formatProviderStatus(updated.last_test_status)}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `AI 中转站检查失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function fetchModels(provider: AiProvider) {
    setIsLoading(true);
    try {
      const models = await apiRequest<AiModel[]>(`/ai-providers/${provider.id}/fetch-models`, { method: "POST", token });
      setModelsByProvider((items) => ({ ...items, [provider.id]: models }));
      setNotice({ tone: "success", message: `模型列表拉取成功，共 ${models.length} 个模型。` });
    } catch (error) {
      setNotice({ tone: "danger", message: `模型拉取失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function addManualModel(provider: AiProvider) {
    if (!manualModelId.trim()) return;
    setIsLoading(true);
    try {
      const model = await apiRequest<AiModel[]>(`/ai-providers/${provider.id}/models`, { method: "GET", token }).then(async () =>
        apiRequest<AiModel>(`/ai-providers/${provider.id}/models`, {
          method: "POST",
          token,
          body: { model_id: manualModelId.trim(), display_name: manualModelId.trim(), enabled: true }
        })
      );
      setModelsByProvider((items) => ({ ...items, [provider.id]: [...(items[provider.id] ?? []), model] }));
      setNotice({ tone: "success", message: `模型已添加：${model.model_id}` });
      setManualModelId("");
    } catch (error) {
      setNotice({ tone: "danger", message: `模型添加失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function setDefaultModel(provider: AiProvider, model: AiModel) {
    setIsLoading(true);
    try {
      const updated = await apiRequest<AiProvider>(`/ai-providers/${provider.id}`, {
        method: "PUT",
        token,
        body: {
          name: provider.name,
          base_url: provider.base_url,
          api_key: "",
          default_model: model.model_id,
          enabled: provider.enabled
        }
      });
      await apiRequest<AiProvider>(`/ai-providers/${provider.id}/set-default`, { method: "POST", token }).catch(() => updated);
      setProviders((items) => items.map((item) => (item.id === provider.id ? updated : item)));
      setNotice({ tone: "success", message: `默认模型已切换：${model.model_id}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `默认模型切换失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function proposeCommand() {
    if (!activeServer) {
      setNotice({ tone: "danger", message: "请先选择服务器。" });
      return;
    }
    setIsLoading(true);
    try {
      const proposal = await apiRequest<{
        command: string;
        explanation: string;
        requires_confirmation: boolean;
        warnings: string[];
        source: string;
      }>(`/servers/${activeServer.id}/assistant/propose-command`, {
        method: "POST",
        token,
        body: {
          question: assistantState.question,
          current_directory: deployState.targetPath,
          recent_output: assistantState.output || null
        }
      });
      setCommand(proposal.command);
      setAssistantState((state) => ({
        ...state,
        suggestedCommand: proposal.command,
        explanation: proposal.explanation,
        warnings: proposal.warnings,
        source: proposal.source,
        output: "",
        summary: ""
      }));
      setNotice({ tone: "success", message: "已生成命令建议，请确认后执行。" });
    } catch (error) {
      setNotice({ tone: "danger", message: `命令建议生成失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function executeSuggestedCommand() {
    if (!activeServer || !assistantState.suggestedCommand) return;
    setIsLoading(true);
    try {
      const log = await apiRequest<CommandLog>(`/servers/${activeServer.id}/commands`, {
        method: "POST",
        token,
        body: { command: assistantState.suggestedCommand, working_directory: null }
      });
      const output = [log.stdout, log.stderr].filter(Boolean).join("\n");
      const summary = await apiRequest<{ status: string; summary: string }>(`/servers/${activeServer.id}/assistant/summarize-output`, {
        method: "POST",
        token,
        body: {
          command: log.command,
          stdout: log.stdout,
          stderr: log.stderr,
          exit_code: log.exit_code
        }
      }).catch(() => ({
        status: log.status === "success" ? "成功" : "失败",
        summary: log.status === "success" ? "命令执行成功，已返回服务器输出。" : "命令执行失败，请查看输出。"
      }));
      setAssistantState((state) => ({
        ...state,
        output,
        summary: summary.summary
      }));
      setNotice({ tone: log.status === "success" ? "success" : "danger", message: "命令执行完成。" });
    } catch (error) {
      setNotice({ tone: "danger", message: `命令执行失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function uploadPackage() {
    if (!deployState.packageFile) {
      setNotice({ tone: "danger", message: "请先选择服务包。" });
      return;
    }
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", deployState.packageFile);
      const uploaded = await apiRequest<PackageRecord>("/packages/upload", { method: "POST", token, body: formData });
      setPackages((items) => [uploaded, ...items]);
      setDeployState((state) => ({ ...state, packageRecord: uploaded }));
      setNotice({ tone: "success", message: `服务包已上传：${uploaded.filename}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `服务包上传失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function analyzePackage() {
    if (!activeServer || !deployState.packageRecord) return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("package_id", String(deployState.packageRecord.id));
      formData.append("target_path", deployState.targetPath);
      const analysis = await apiRequest<ProjectAnalysis>(`/servers/${activeServer.id}/analyze-upload`, {
        method: "POST",
        token,
        body: formData
      });
      setDeployState((state) => ({ ...state, analysis }));
      setNotice({ tone: "success", message: "服务包分析完成。" });
    } catch (error) {
      setNotice({ tone: "danger", message: `服务包分析失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function createDeploymentPlan() {
    if (!activeServer || !deployState.analysis) return;
    setIsLoading(true);
    try {
      const task = await apiRequest<DeploymentTask>("/deployments/plan", {
        method: "POST",
        token,
        body: {
          server_id: activeServer.id,
          package_id: deployState.packageRecord?.id ?? null,
          plan: deployState.analysis.plan
        }
      });
      setDeployState((state) => ({ ...state, task }));
      setDeployments((items) => [task, ...items.filter((item) => item.id !== task.id)]);
      setNotice({ tone: "success", message: "部署计划已创建，请确认后执行。" });
    } catch (error) {
      setNotice({ tone: "danger", message: `部署计划创建失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  async function executeDeployment() {
    if (!deployState.task) return;
    setIsLoading(true);
    try {
      const task = await apiRequest<DeploymentTask>(`/deployments/${deployState.task.id}/execute`, { method: "POST", token });
      setDeployState((state) => ({ ...state, task }));
      setDeployments((items) => [task, ...items.filter((item) => item.id !== task.id)]);
      setNotice({ tone: task.status === "success" ? "success" : "danger", message: `部署执行完成：${task.status}` });
    } catch (error) {
      setNotice({ tone: "danger", message: `部署执行失败：${formatError(error)}` });
    } finally {
      setIsLoading(false);
    }
  }

  function updateServerInState(updated: ServerRecord) {
    setServers((items) => items.map((item) => (item.id === updated.id ? updated : item)));
    setSelectedServer((current) => (current?.id === updated.id ? updated : current));
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
              <input type="password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} />
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
            <button className={activeSection === section.id ? "active" : ""} key={section.id} onClick={() => setActiveSection(section.id)} type="button">
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
          <button
            aria-label={activeSection === "terminal" ? "顶部添加服务器" : "添加服务器"}
            className="primary-action"
            onClick={() => { setEditingServer(null); setServerForm(emptyServerForm); setShowServerForm(true); }}
            type="button"
          >
            <Server size={18} />添加服务器
          </button>
        </header>

        <div className={`notice ${notice.tone}`} role="status">
          {notice.message}
        </div>

        {showServerForm && (
          <ServerFormPanel
            title={editingServer ? "编辑服务器" : "添加服务器"}
            form={serverForm}
            isLoading={isLoading}
            saveLabel={editingServer ? "保存修改" : "保存服务器"}
            onChange={setServerForm}
            onCancel={() => { setShowServerForm(false); setEditingServer(null); }}
            onSave={saveServer}
          />
        )}

        {activeSection === "overview" && (
          <OverviewSection
            isLoading={isLoading}
            providers={providers}
            servers={servers}
            selectedServer={selectedServer}
            onCheckHealth={checkHealth}
            onTestServer={testServer}
            onTestProvider={testProvider}
            onSelectServer={setSelectedServer}
            onRefreshSnapshot={refreshSnapshot}
            onEditServer={editServer}
            onDeleteServer={deleteServer}
          />
        )}
        {activeSection === "terminal" && (
          <TerminalSection
            server={activeServer}
            servers={servers}
            token={token}
            targetPath={deployState.targetPath}
            onSelectServer={setSelectedServer}
            onAddServer={() => {
              setEditingServer(null);
              setServerForm(emptyServerForm);
              setShowServerForm(true);
            }}
          />
        )}
        {activeSection === "assistant" && (
          <AssistantSection
            state={assistantState}
            command={command}
            isLoading={isLoading}
            onChangeState={setAssistantState}
            onChangeCommand={setCommand}
            onCheckCommand={checkCommand}
            onProposeCommand={proposeCommand}
            onExecuteCommand={executeSuggestedCommand}
          />
        )}
        {activeSection === "deploy" && (
          <DeploySection
            state={deployState}
            isLoading={isLoading}
            onChangeState={setDeployState}
            onValidatePlan={validatePlan}
            onUploadPackage={uploadPackage}
            onAnalyzePackage={analyzePackage}
            onCreatePlan={createDeploymentPlan}
            onExecuteDeployment={executeDeployment}
          />
        )}
        {activeSection === "history" && <HistorySection deployments={deployments} packages={packages} />}
        {activeSection === "settings" && (
          <SettingsSection
            form={providerForm}
            isLoading={isLoading}
            providers={providers}
            modelsByProvider={modelsByProvider}
            manualModelId={manualModelId}
            onChange={setProviderForm}
            onChangeManualModelId={setManualModelId}
            onSave={saveProvider}
            onTestProvider={testProvider}
            onFetchModels={fetchModels}
            onAddManualModel={addManualModel}
            onSetDefaultModel={setDefaultModel}
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
  selectedServer,
  onCheckHealth,
  onTestServer,
  onTestProvider,
  onSelectServer,
  onRefreshSnapshot,
  onEditServer,
  onDeleteServer
}: {
  isLoading: boolean;
  providers: AiProvider[];
  servers: ServerRecord[];
  selectedServer: ServerRecord | null;
  onCheckHealth: () => void;
  onTestServer: (server: ServerRecord) => void;
  onTestProvider: (provider: AiProvider) => void;
  onSelectServer: (server: ServerRecord) => void;
  onRefreshSnapshot: (server: ServerRecord) => void;
  onEditServer: (server: ServerRecord) => void;
  onDeleteServer: (server: ServerRecord) => void;
}) {
  const defaultProvider = providers.find((provider) => provider.enabled) ?? providers[0];
  return (
    <>
      <section className="metric-grid" aria-label="系统概览">
        <Metric icon={<Server />} label="服务器" value={String(servers.length)} detail={`${servers.filter((item) => item.status === "online").length} 台在线`} />
        <Metric icon={<Bot />} label="默认模型" value={defaultProvider?.default_model ?? "-"} detail={defaultProvider?.name ?? "未配置"} />
        <Metric icon={<ShieldAlert />} label="安全策略" value="启用" detail="危险命令拦截" />
        <Metric icon={<Database />} label="数据库" value="SQLite" detail="任务和审计可追踪" />
      </section>

      <section className="content-grid">
        <div className="panel server-panel">
          <div className="panel-header">
            <div>
              <h2>服务器列表</h2>
              <p>展示真实连接状态和最近一次资源快照。</p>
            </div>
            <button className="ghost-action" onClick={onCheckHealth} type="button" disabled={isLoading}>
              检查后端
            </button>
          </div>
          <ServerTable servers={servers} isLoading={isLoading} onTestServer={onTestServer} onSelectServer={onSelectServer} />
        </div>

        <AiProviderPanel providers={providers} isLoading={isLoading} onTestProvider={onTestProvider} />
      </section>

      {selectedServer && (
        <ServerDetailPanel
          server={selectedServer}
          isLoading={isLoading}
          onRefreshSnapshot={onRefreshSnapshot}
          onEditServer={onEditServer}
          onDeleteServer={onDeleteServer}
        />
      )}
    </>
  );
}

function ServerFormPanel({
  title,
  form,
  isLoading,
  saveLabel,
  onCancel,
  onChange,
  onSave
}: {
  title: string;
  form: ServerForm;
  isLoading: boolean;
  saveLabel: string;
  onCancel: () => void;
  onChange: (form: ServerForm) => void;
  onSave: () => void;
}) {
  return (
    <section className="panel">
      <div className="panel-header compact">
        <h2>{title}</h2>
        <Server size={18} />
      </div>
      <div className="form-grid">
        <label>服务器名称<input value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} /></label>
        <label>主机地址<input value={form.host} onChange={(event) => onChange({ ...form, host: event.target.value })} /></label>
        <label>SSH 端口<input value={form.port} onChange={(event) => onChange({ ...form, port: event.target.value })} /></label>
        <label>SSH 用户<input value={form.username} onChange={(event) => onChange({ ...form, username: event.target.value })} /></label>
        <label>SSH 密码<input type="password" value={form.password} onChange={(event) => onChange({ ...form, password: event.target.value })} /></label>
        <label>备注<input value={form.remark} onChange={(event) => onChange({ ...form, remark: event.target.value })} /></label>
      </div>
      <div className="button-row">
        <button className="primary-action" onClick={onSave} type="button" disabled={isLoading}>{saveLabel}</button>
        <button className="ghost-action" onClick={onCancel} type="button">取消</button>
      </div>
    </section>
  );
}

function TerminalSection({
  server,
  servers,
  token,
  targetPath,
  onSelectServer,
  onAddServer
}: {
  server: ServerRecord | null;
  servers: ServerRecord[];
  token: string;
  targetPath: string;
  onSelectServer: (server: ServerRecord) => void;
  onAddServer: () => void;
}) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [draft, setDraft] = useState("");
  const [lines, setLines] = useState<string[]>([
    "欢迎进入 SSH 工作台。",
    "在终端直接输入命令并按 Enter 执行，输入 //问题 可让 AI 生成建议命令。"
  ]);
  const [activeRailTab, setActiveRailTab] = useState<"servers" | "audit" | "commands">("servers");
  const [isAiLoading, setIsAiLoading] = useState(false);
  const activeServer = server ?? servers[0] ?? null;
  const promptHost = activeServer?.latest_snapshot?.ip_addresses?.split(",")[0]?.trim() || activeServer?.host;
  const prompt = activeServer ? `${activeServer.username}@${promptHost}:~#` : "未选择服务器:~#";

  function connect(targetServer = activeServer) {
    if (!targetServer) {
      setLines((items) => [...items, "没有可连接的服务器。"]);
      return;
    }
    onSelectServer(targetServer);
    socket?.close();
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/api/servers/${targetServer.id}/terminal?token=${encodeURIComponent(token)}`);
    ws.onopen = () => setLines((items) => [...items, `已连接到 ${targetServer.name}。`]);
    ws.onmessage = (event) => setLines((items) => [...items, String(event.data)]);
    ws.onerror = () => setLines((items) => [...items, "终端连接失败。"]);
    ws.onclose = () => setLines((items) => [...items, "终端已断开。"]);
    setSocket(ws);
  }

  async function askAssistant(question: string) {
    if (!activeServer) {
      setLines((items) => [...items, "请先选择服务器，再使用 AI 助手。"]);
      return;
    }
    setIsAiLoading(true);
    setLines((items) => [...items, `${prompt} //${question}`, "AI 正在分析，请稍候..."]);
    try {
      const proposal = await apiRequest<{
        command: string;
        explanation: string;
        requires_confirmation: boolean;
        warnings: string[];
        source: string;
      }>(`/servers/${activeServer.id}/assistant/propose-command`, {
        method: "POST",
        token,
        body: {
          question,
          current_directory: targetPath,
          recent_output: lines.slice(-12).join("\n") || null
        }
      });
      setLines((items) => [
        ...items.filter((line) => line !== "AI 正在分析，请稍候..."),
        `AI 建议命令：${proposal.command}`,
        `AI 说明：${proposal.explanation}`,
        ...proposal.warnings.map((warning) => `AI 提醒：${warning}`),
        "如需执行，请复制建议命令到终端并按 Enter。"
      ]);
    } catch (error) {
      setLines((items) => [
        ...items.filter((line) => line !== "AI 正在分析，请稍候..."),
        `AI 助手调用失败：${formatError(error)}`
      ]);
    } finally {
      setIsAiLoading(false);
    }
  }

  function submitDraft() {
    const command = draft.trimEnd();
    setDraft("");
    if (!command.trim()) return;
    if (command.trim().startsWith("//")) {
      const question = command.trim().replace(/^\/\/\s*/, "");
      void askAssistant(question || "请根据最近输出给出下一步建议");
      return;
    }
    setLines((items) => [...items, `${prompt} ${command}`]);
    if (!socket) {
      setLines((items) => [...items, "终端尚未连接，请先在右侧选择服务器并连接。"]);
      return;
    }
    socket.send(`${command}\n`);
  }

  function handleTerminalKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.ctrlKey && event.key.toLowerCase() === "l") {
      event.preventDefault();
      setLines(["终端已清屏。"]);
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      submitDraft();
      return;
    }
    if (event.key === "Backspace") {
      event.preventDefault();
      setDraft((value) => value.slice(0, -1));
      return;
    }
    if (event.key === "Tab") {
      event.preventDefault();
      setDraft((value) => `${value}  `);
      return;
    }
    if (event.key.length === 1 && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      setDraft((value) => `${value}${event.key}`);
    }
  }

  return (
    <section className="terminal-workbench" aria-label="SSH 工作台">
      <div className="terminal-stage">
        <div className="terminal-topbar">
          <div>
            <h2>SSH 工作台</h2>
            <span>{activeServer ? `${activeServer.name} · ${activeServer.host}:${activeServer.port}` : "还没有选择服务器"}</span>
          </div>
          <div className="terminal-actions">
            <button className="ghost-action" type="button" onClick={() => connect(activeServer ?? undefined)} disabled={!activeServer}>连接终端</button>
            <button className="ghost-action" type="button" onClick={() => socket?.close()} disabled={!socket}>断开连接</button>
          </div>
        </div>
        <div className="terminal-tabs">
          <button className="active" type="button">本地终端</button>
          <button type="button" onClick={() => setLines((items) => [...items, "新终端会话请先选择服务器连接。"])}>+</button>
        </div>
        <div
          className="terminal-screen"
          role="textbox"
          aria-label="终端窗口"
          tabIndex={0}
          onKeyDown={handleTerminalKeyDown}
        >
          <div className="terminal-output">
            {lines.map((line, index) => (
              <span key={`${line}-${index}`}>{line}</span>
            ))}
            <span className="terminal-input-line">
              <strong>{prompt}</strong>
              <span>{draft}</span>
              <i aria-hidden="true" />
            </span>
          </div>
          {isAiLoading && <div className="terminal-badge">AI 助手处理中</div>}
        </div>
      </div>
      <aside className="terminal-rail">
        <div className="terminal-rail-tabs" role="tablist" aria-label="终端侧栏">
          <button className={activeRailTab === "servers" ? "active" : ""} role="tab" type="button" onClick={() => setActiveRailTab("servers")}>服务器列表</button>
          <button className={activeRailTab === "audit" ? "active" : ""} role="tab" type="button" onClick={() => setActiveRailTab("audit")}>录像审计</button>
          <button className={activeRailTab === "commands" ? "active" : ""} role="tab" type="button" onClick={() => setActiveRailTab("commands")}>常用命令</button>
        </div>
        {activeRailTab === "servers" && (
          <div className="terminal-rail-body">
            <button className="primary-action add-server-action" type="button" onClick={onAddServer}>
              <Server size={17} />添加服务器
            </button>
            <div className="terminal-server-list">
              {servers.map((item) => (
                <div className={activeServer?.id === item.id ? "terminal-server-card active" : "terminal-server-card"} key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.username}@{item.host}:{item.port}</span>
                    <small>{formatServerStatus(item.status)} · {item.remark || "无备注"}</small>
                  </div>
                  <button className="secondary-action" type="button" onClick={() => connect(item)}>
                    连接 {item.name}
                  </button>
                </div>
              ))}
              {servers.length === 0 && <div className="empty-state">暂无服务器，请先添加服务器。</div>}
            </div>
          </div>
        )}
        {activeRailTab === "audit" && (
          <div className="terminal-rail-body">
            <div className="terminal-tip">
              <strong>录像审计</strong>
              <span>当前终端输出会保留在本页面，后续可接入后端审计录像接口。</span>
            </div>
          </div>
        )}
        {activeRailTab === "commands" && (
          <div className="terminal-rail-body command-palette">
            {["pwd", "df -h", "free -h", "docker ps", "systemctl status nginx"].map((command) => (
              <button type="button" key={command} onClick={() => setDraft(command)}>{command}</button>
            ))}
          </div>
        )}
      </aside>
    </section>
  );
}

function AssistantSection({
  state,
  command,
  isLoading,
  onChangeState,
  onChangeCommand,
  onCheckCommand,
  onProposeCommand,
  onExecuteCommand
}: {
  state: AssistantState;
  command: string;
  isLoading: boolean;
  onChangeState: (state: AssistantState) => void;
  onChangeCommand: (value: string) => void;
  onCheckCommand: () => void;
  onProposeCommand: () => void;
  onExecuteCommand: () => void;
}) {
  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="panel-header compact">
          <div>
            <h2>AI 运维助手</h2>
            <p>AI 只生成建议，命令执行前必须确认。</p>
          </div>
          <Bot size={18} />
        </div>
        <div className="settings-list">
          <label>运维问题<input value={state.question} onChange={(event) => onChangeState({ ...state, question: event.target.value })} /></label>
          <label>待检查命令<input value={command} onChange={(event) => onChangeCommand(event.target.value)} /></label>
        </div>
        <div className="button-row">
          <button className="primary-action" onClick={onProposeCommand} type="button" disabled={isLoading}>生成命令建议</button>
          <button className="ghost-action" onClick={onCheckCommand} type="button" disabled={isLoading}><ShieldAlert size={18} />检查命令</button>
        </div>
        {state.suggestedCommand && (
          <div className="result-box">
            <strong>建议命令</strong>
            <code>{state.suggestedCommand}</code>
            {state.explanation && <span>{state.explanation}</span>}
            {state.warnings.map((warning) => <small key={warning}>{warning}</small>)}
            {state.source && <small>来源：{state.source === "ai" ? "AI 中转站" : "内置安全规则"}</small>}
            <button className="secondary-action" onClick={onExecuteCommand} type="button" disabled={isLoading}>确认执行</button>
          </div>
        )}
        {state.output && <pre className="output-box">{state.output}</pre>}
        {state.summary && <div className="risk-box"><CheckCircle2 size={18} /><span>{state.summary}</span></div>}
      </div>
    </section>
  );
}

function DeploySection({
  state,
  isLoading,
  onChangeState,
  onValidatePlan,
  onUploadPackage,
  onAnalyzePackage,
  onCreatePlan,
  onExecuteDeployment
}: {
  state: DeployState;
  isLoading: boolean;
  onChangeState: (state: DeployState) => void;
  onValidatePlan: () => void;
  onUploadPackage: () => void;
  onAnalyzePackage: () => void;
  onCreatePlan: () => void;
  onExecuteDeployment: () => void;
}) {
  return (
    <section className="content-grid lower">
      <div className="panel">
        <div className="panel-header compact"><h2>服务部署</h2><Play size={18} /></div>
        <div className="form-grid">
          <label>服务包<input type="file" onChange={(event) => onChangeState({ ...state, packageFile: event.target.files?.[0] ?? null })} /></label>
          <label>部署目录<input value={state.targetPath} onChange={(event) => onChangeState({ ...state, targetPath: event.target.value })} /></label>
        </div>
        <div className="button-row">
          <button className="primary-action" type="button" onClick={onUploadPackage} disabled={isLoading}>上传服务包</button>
          <button className="ghost-action" type="button" onClick={onAnalyzePackage} disabled={isLoading || !state.packageRecord}>分析上传包</button>
          <button className="ghost-action" type="button" onClick={onValidatePlan} disabled={isLoading}>校验部署计划</button>
        </div>
        {state.packageRecord && <p>服务包：{state.packageRecord.filename}</p>}
        {state.analysis && (
          <div className="result-box">
            <strong>{state.analysis.summary}</strong>
            <span>依赖：{state.analysis.dependencies.join("、") || "未识别"}</span>
            <ol className="step-list">{state.analysis.plan.steps.map((step) => <li key={step.command}>{step.name}：{step.command}</li>)}</ol>
            <button className="secondary-action" type="button" onClick={onCreatePlan} disabled={isLoading}>创建部署计划</button>
          </div>
        )}
      </div>
      <div className="panel">
        <div className="panel-header compact"><h2>部署计划确认</h2><ShieldAlert size={18} /></div>
        {state.task ? (
          <div className="result-box">
            <strong>{state.task.plan.summary}</strong>
            <span>风险：{state.task.plan.risk_level} · sudo：{state.task.plan.requires_sudo ? "需要" : "不需要"}</span>
            <button className="secondary-action" type="button" onClick={onExecuteDeployment} disabled={isLoading}>确认执行部署</button>
          </div>
        ) : (
          <ol className="step-list">
            <li>上传服务包</li>
            <li>分析项目类型</li>
            <li>展示部署计划</li>
            <li>确认后执行</li>
          </ol>
        )}
      </div>
      <div className="panel resource-panel">
        <div className="panel-header compact"><h2>执行日志</h2><History size={18} /></div>
        {state.task?.logs.map((log) => <pre className="output-box" key={log.id}>{log.command}\n{log.stdout}</pre>)}
        {state.task && <span>状态：{state.task.status}</span>}
      </div>
    </section>
  );
}

function HistorySection({ deployments, packages }: { deployments: DeploymentTask[]; packages: PackageRecord[] }) {
  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="panel-header compact">
          <div><h2>历史记录</h2><p>展示部署任务、命令输出和服务包记录。</p></div>
          <History size={18} />
        </div>
        <div className="timeline">
          {deployments.map((task) => (
            <div className="list-card" key={task.id}>
              <strong>部署任务 #{task.id} · {task.status}</strong>
              {task.plan.steps.map((step) => <span key={`${task.id}-${step.command}`}>{step.command}</span>)}
              {task.logs.map((log) => <span key={log.id}>{log.stdout || log.stderr}</span>)}
            </div>
          ))}
          {packages.map((item) => <span key={item.id}>服务包：{item.filename}</span>)}
          {deployments.length === 0 && packages.length === 0 && <span>暂无历史记录。</span>}
        </div>
      </div>
    </section>
  );
}

function SettingsSection({
  form,
  isLoading,
  providers,
  modelsByProvider,
  manualModelId,
  onChange,
  onChangeManualModelId,
  onSave,
  onTestProvider,
  onFetchModels,
  onAddManualModel,
  onSetDefaultModel
}: {
  form: ProviderForm;
  isLoading: boolean;
  providers: AiProvider[];
  modelsByProvider: Record<number, AiModel[]>;
  manualModelId: string;
  onChange: (form: ProviderForm) => void;
  onChangeManualModelId: (value: string) => void;
  onSave: () => void;
  onTestProvider: (provider: AiProvider) => void;
  onFetchModels: (provider: AiProvider) => void;
  onAddManualModel: (provider: AiProvider) => void;
  onSetDefaultModel: (provider: AiProvider, model: AiModel) => void;
}) {
  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="panel-header compact"><h2>AI 中转站配置</h2><KeyRound size={18} /></div>
        <div className="form-grid">
          <label>供应商名称<input value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} /></label>
          <label>接口基础地址<input value={form.base_url} onChange={(event) => onChange({ ...form, base_url: event.target.value })} /></label>
          <label>API 密钥<input type="password" value={form.api_key} onChange={(event) => onChange({ ...form, api_key: event.target.value })} /></label>
          <label>默认模型<input value={form.default_model} onChange={(event) => onChange({ ...form, default_model: event.target.value })} /></label>
        </div>
        <button className="secondary-action" onClick={onSave} type="button" disabled={isLoading}>保存 AI 中转站</button>
        <div className="provider-list">
          {providers.map((provider) => (
            <div className="list-card" key={provider.id}>
              <strong>{provider.name}</strong>
              <span>{provider.base_url}</span>
              <span>{provider.default_model ?? "未设置模型"} · {provider.api_key_mask}</span>
              <div className="button-row">
                <button className="ghost-action" onClick={() => onTestProvider(provider)} type="button" disabled={isLoading}>测试 {provider.name}</button>
                <button className="ghost-action" onClick={() => onFetchModels(provider)} type="button" disabled={isLoading}>拉取模型</button>
              </div>
              <label>手动模型 ID<input value={manualModelId} onChange={(event) => onChangeManualModelId(event.target.value)} /></label>
              <button className="ghost-action" onClick={() => onAddManualModel(provider)} type="button" disabled={isLoading}>添加手动模型</button>
              {(modelsByProvider[provider.id] ?? []).map((model) => (
                <div className="model-row" key={model.id}>
                  <span>{model.model_id} · {model.source === "fetched" ? "拉取" : "手动"} · {model.enabled ? "已启用" : "已禁用"}</span>
                  <button className="ghost-action" onClick={() => onSetDefaultModel(provider, model)} type="button">设为默认模型 {model.model_id}</button>
                </div>
              ))}
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
  onTestServer,
  onSelectServer
}: {
  isLoading: boolean;
  servers: ServerRecord[];
  onTestServer: (server: ServerRecord) => void;
  onSelectServer: (server: ServerRecord) => void;
}) {
  return (
    <div className="server-table">
      <div className="table-row table-head">
        <span>名称</span><span>地址</span><span>系统</span><span>CPU</span><span>内存</span><span>磁盘</span><span>状态</span><span>操作</span>
      </div>
      {servers.map((server) => (
        <div className="table-row" key={server.id}>
          <button className="table-button" type="button" onClick={() => onSelectServer(server)}><strong>{server.name}</strong></button>
          <span>{server.host}:{server.port}</span>
          <span>{server.latest_snapshot?.os_info ?? "-"}</span>
          <span>CPU {formatPercent(server.latest_snapshot?.cpu_usage)}</span>
          <span>内存 {formatPercent(server.latest_snapshot?.memory_usage)}</span>
          <span>磁盘 {formatPercent(server.latest_snapshot?.disk_usage)}</span>
          <span className={`status ${server.status}`}>{formatServerStatus(server.status)}</span>
          <div className="button-row">
            <button className="ghost-action compact-button" onClick={() => onTestServer(server)} type="button" disabled={isLoading}>测试</button>
            <button className="ghost-action compact-button" onClick={() => onSelectServer(server)} type="button">查看 {server.name} 详情</button>
          </div>
          {server.last_test_message && <small className="row-message">{server.last_test_message}</small>}
        </div>
      ))}
      {servers.length === 0 && <div className="empty-state">暂无服务器，请先添加。</div>}
    </div>
  );
}

function ServerDetailPanel({
  server,
  isLoading,
  onRefreshSnapshot,
  onEditServer,
  onDeleteServer
}: {
  server: ServerRecord;
  isLoading: boolean;
  onRefreshSnapshot: (server: ServerRecord) => void;
  onEditServer: (server: ServerRecord) => void;
  onDeleteServer: (server: ServerRecord) => void;
}) {
  const snapshot = server.latest_snapshot;
  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="panel-header">
          <div>
            <h2>{server.name}</h2>
            <p>{server.username}@{server.host}:{server.port} · {formatServerStatus(server.status)}</p>
          </div>
          <div className="button-row">
            <button className="ghost-action" type="button" onClick={() => onRefreshSnapshot(server)} disabled={isLoading}>刷新快照</button>
            <button className="ghost-action" type="button" onClick={() => onEditServer(server)}>编辑服务器</button>
            <button className="ghost-action" type="button" onClick={() => onDeleteServer(server)} disabled={isLoading}>删除服务器</button>
          </div>
        </div>
        <section className="metric-grid">
          <Metric icon={<Cpu />} label="CPU" value={formatPercent(snapshot?.cpu_usage)} detail={`${snapshot?.cpu_cores ?? "-"} 核`} />
          <Metric icon={<Activity />} label="内存" value={formatPercent(snapshot?.memory_usage)} detail={`${snapshot?.memory_used_mb ?? "-"} / ${snapshot?.memory_total_mb ?? "-"} MB`} />
          <Metric icon={<HardDrive />} label="磁盘" value={formatPercent(snapshot?.disk_usage)} detail={`${snapshot?.disk_used_gb ?? "-"} / ${snapshot?.disk_total_gb ?? "-"} GB`} />
          <Metric icon={<Server />} label="系统" value={snapshot?.os_info ?? "-"} detail={snapshot?.kernel ?? "-"} />
        </section>
      </div>
    </section>
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
      <div className="panel-header compact"><h2>AI 中转站</h2><KeyRound size={18} /></div>
      <div className="provider-list compact-list">
        {providers.map((provider) => (
          <div className="list-card" key={provider.id}>
            <strong>{provider.name}</strong>
            <span>{provider.base_url}</span>
            <span>{provider.default_model ?? "未设置模型"}</span>
            <button className="ghost-action" onClick={() => onTestProvider(provider)} type="button" disabled={isLoading}>测试</button>
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

async function apiRequest<T>(path: string, options: { method?: string; token?: string; body?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : options.body instanceof FormData ? options.body : JSON.stringify(options.body)
  });
  if (!response.ok) throw new Error(await readErrorMessage(response));
  return (await response.json()) as T;
}

async function readErrorMessage(response: Response) {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      const first = body.detail[0] as { msg?: string; loc?: string[] };
      const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : "";
      if (field === "password" && first.msg?.includes("8")) return "密码至少需要 8 位。";
      return first.msg ?? `请求失败：后端返回 ${response.status}。`;
    }
  } catch {
    return `请求失败：后端返回 ${response.status}。`;
  }
  return `请求失败：后端返回 ${response.status}。`;
}

function formatError(error: unknown) {
  return error instanceof Error ? error.message : "未知错误";
}

function formatServerStatus(status: string) {
  return serverStatusLabels[status] ?? "未知状态";
}

function formatProviderStatus(status: string | null | undefined) {
  if (!status) return "未检测";
  return { ok: "正常", failed: "失败", skipped: "未启用" }[status] ?? "未知状态";
}

function formatPercent(value: number | null | undefined) {
  return typeof value === "number" ? `${Number.isInteger(value) ? value : value.toFixed(1)}%` : "-";
}

function formatConnectionMode(mode: string) {
  return mode === "ssh" ? "SSH" : mode;
}
