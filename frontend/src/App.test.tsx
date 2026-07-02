import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { App } from "./App";

const fetchMock = vi.fn();

type MockApiReply = {
  body: unknown;
  ok?: boolean;
  status?: number;
};

type MockApiRoutes = Record<string, MockApiReply | ((init?: RequestInit) => MockApiReply)>;

const adminUser = { id: 1, username: "admin", role: "admin" };

const serverRecord = {
  id: 1,
  name: "prod-app-01",
  host: "10.0.12.21",
  port: 22,
  username: "root",
  auth_type: "password",
  remark: null,
  status: "offline",
  connection_mode: "ssh",
  has_password: true,
  has_private_key: false,
  last_test_message: "SSH 连接失败：认证失败。",
  latest_snapshot: {
    id: 9,
    server_id: 1,
    status: "ok",
    cpu_usage: 12.5,
    cpu_cores: 4,
    memory_usage: 25.8,
    memory_total_mb: 7936,
    memory_used_mb: 2048,
    disk_usage: 37,
    disk_total_gb: 98.3,
    disk_used_gb: 36.4,
    os_info: "Ubuntu 22.04.4 LTS",
    kernel: "6.5.0-35-generic",
    ip_addresses: "10.0.12.21",
    message: "资源快照采集成功。",
    created_at: "2026-07-02T08:00:00Z"
  },
  last_seen_at: "2026-07-02T08:00:00Z"
};

const providerRecord = {
  id: 1,
  name: "Relay",
  provider_type: "openai-compatible",
  base_url: "https://relay.example/v1",
  default_model: "deepseek-chat",
  api_mode: "chat_completions",
  enabled: true,
  has_api_key: true,
  api_key_mask: "sk-t********test",
  last_test_status: "ok",
  last_test_message: "AI 中转站连接正常。"
};

const modelRecord = {
  id: 10,
  provider_id: 1,
  model_id: "deepseek-chat",
  display_name: "deepseek-chat",
  source: "fetched",
  enabled: true
};

const packageRecord = {
  id: 7,
  filename: "demo.zip",
  size: 1024,
  sha256: "abc123",
  uploaded_at: "2026-07-02T08:10:00Z"
};

const plan = {
  summary: "这是一个 Node.js 服务",
  risk_level: "medium",
  requires_sudo: false,
  steps: [
    {
      name: "安装依赖",
      command: "npm install",
      working_directory: "/opt/apps/demo"
    },
    {
      name: "启动服务",
      command: "npm run start",
      working_directory: "/opt/apps/demo"
    }
  ]
};

const analysisRecord = {
  id: 3,
  package_id: 7,
  server_id: 1,
  target_path: "/opt/apps/demo",
  detected_type: "node",
  summary: "这是一个 Node.js 服务，建议使用 pm2 或 systemd 托管。",
  dependencies: ["Node.js", "npm"],
  start_commands: ["npm run start"],
  file_tree: ["package.json", "src/main.ts"],
  plan,
  created_at: "2026-07-02T08:20:00Z"
};

const deploymentRecord = {
  id: 5,
  server_id: 1,
  package_id: 7,
  status: "success",
  summary: "这是一个 Node.js 服务",
  plan,
  error_message: null,
  started_at: "2026-07-02T08:30:00Z",
  finished_at: "2026-07-02T08:31:00Z",
  created_at: "2026-07-02T08:25:00Z",
  logs: [
    {
      id: 11,
      task_id: 5,
      server_id: 1,
      command: "npm run start",
      working_directory: "/opt/apps/demo",
      stdout: "服务已启动",
      stderr: "",
      exit_code: 0,
      status: "success",
      started_at: "2026-07-02T08:30:00Z",
      finished_at: "2026-07-02T08:31:00Z"
    }
  ]
};

function mockApi(routes: MockApiRoutes = {}) {
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = input.toString();
    const route = routes[path] ?? {
      "/api/auth/status": { body: { initialized: false } },
      "/api/auth/me": { body: { detail: "请先登录。" }, ok: false, status: 401 },
      "/api/servers": { body: [] },
      "/api/ai-providers": { body: [] },
      "/api/packages": { body: [] },
      "/api/deployments": { body: [] }
    }[path];

    if (!route) {
      throw new Error(`No mock response for ${path}`);
    }

    const reply = typeof route === "function" ? route(init) : route;
    return {
      ok: reply.ok ?? true,
      status: reply.status ?? (reply.ok === false ? 500 : 200),
      json: async () => reply.body
    };
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  window.localStorage.clear();
});

describe("App interactions", () => {
  test("shows login mode after admin has already been initialized", async () => {
    mockApi({
      "/api/auth/status": { body: { initialized: true } }
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "初始化管理员" })).not.toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "登录" })).toBeInTheDocument();
  });

  test("shows a clear validation message for short admin password", async () => {
    mockApi();

    render(<App />);
    await userEvent.type(screen.getByLabelText("账号"), "admin");
    await userEvent.type(screen.getByLabelText("密码"), "123456");
    await userEvent.click(await screen.findByRole("button", { name: "初始化管理员" }));

    expect(screen.getByText("认证失败：密码至少需要 8 位。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  test("initializes an admin and loads protected resources", async () => {
    mockApi({
      "/api/auth/init": { body: { access_token: "token-1", user: adminUser } }
    });

    render(<App />);
    await userEvent.type(screen.getByLabelText("账号"), "admin");
    await userEvent.type(screen.getByLabelText("密码"), "strong-password");
    await userEvent.click(await screen.findByRole("button", { name: "初始化管理员" }));

    await waitFor(() => {
      expect(screen.getAllByText("登录用户：admin").length).toBeGreaterThan(0);
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/init", expect.objectContaining({ method: "POST" }));
  });

  test("renders server data from the API and creates a server", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": (init) => ({
        body:
          init?.method === "POST"
            ? {
          id: 2,
          name: "staging-web",
          host: "10.0.12.33",
          port: 22,
          username: "ubuntu",
          auth_type: "password",
          remark: null,
          status: "unknown",
          connection_mode: "ssh",
          has_password: true,
          has_private_key: false
              }
            : [serverRecord]
      }),
      "/api/ai-providers": { body: [] }
    });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByText("prod-app-01")).toBeInTheDocument();
    });
    expect(screen.getByText("Ubuntu 22.04.4 LTS")).toBeInTheDocument();
    expect(screen.getByText("CPU 12.5%")).toBeInTheDocument();
    expect(screen.getByText("内存 25.8%")).toBeInTheDocument();
    expect(screen.getByText("磁盘 37%")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /添加服务器/ }));
    await userEvent.clear(screen.getByLabelText("服务器名称"));
    await userEvent.type(screen.getByLabelText("服务器名称"), "staging-web");
    await userEvent.clear(screen.getByLabelText("主机地址"));
    await userEvent.type(screen.getByLabelText("主机地址"), "10.0.12.33");
    await userEvent.clear(screen.getByLabelText("SSH 用户"));
    await userEvent.type(screen.getByLabelText("SSH 用户"), "ubuntu");
    await userEvent.type(screen.getByLabelText("SSH 密码"), "secret");
    await userEvent.click(screen.getByRole("button", { name: "保存服务器" }));

    await waitFor(() => {
      expect(screen.getByText("服务器已保存：staging-web")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/servers",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ Authorization: "Bearer token-1" })
      })
    );
  });

  test("shows Chinese server status and connection test result", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": { body: [serverRecord] },
      "/api/servers/1/test": {
        body: {
          ...serverRecord,
          status: "online",
          last_test_message: "SSH 连接成功。"
        }
      }
    });

    render(<App />);

    expect(await screen.findByText("离线")).toBeInTheDocument();
    expect(screen.getByText("SSH 连接失败：认证失败。")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "测试" }));

    await waitFor(() => {
      expect(screen.getByText("服务器连接成功：SSH 连接成功。")).toBeInTheDocument();
    });
    expect(screen.getByText("在线")).toBeInTheDocument();
  });

  test("creates an AI provider through the API", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/ai-providers": (init) => ({ body: init?.method === "POST" ? providerRecord : [] })
    });

    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: /系统设置/ }));
    await userEvent.clear(screen.getByLabelText("供应商名称"));
    await userEvent.type(screen.getByLabelText("供应商名称"), "Relay");
    await userEvent.clear(screen.getByLabelText("接口基础地址"));
    await userEvent.type(screen.getByLabelText("接口基础地址"), "https://relay.example/v1");
    await userEvent.type(screen.getByLabelText("API 密钥"), "sk-test");
    await userEvent.clear(screen.getByLabelText("默认模型"));
    await userEvent.type(screen.getByLabelText("默认模型"), "deepseek-chat");
    await userEvent.click(screen.getByRole("button", { name: "保存 AI 中转站" }));

    await waitFor(() => {
      expect(screen.getByText("AI 中转站已保存：Relay")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenLastCalledWith("/api/ai-providers", expect.objectContaining({ method: "POST" }));
  });

  test("runs commands from the terminal surface and shows the server rail", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    const instances: Array<{
      url: string;
      sent: string[];
      onopen: null | (() => void);
      onmessage: null | ((event: { data: string }) => void);
      onclose: null | (() => void);
      onerror: null | (() => void);
      send: (value: string) => void;
      close: () => void;
    }> = [];
    class MockWebSocket {
      url: string;
      sent: string[] = [];
      onopen: null | (() => void) = null;
      onmessage: null | ((event: { data: string }) => void) = null;
      onclose: null | (() => void) = null;
      onerror: null | (() => void) = null;

      constructor(url: string) {
        this.url = url;
        instances.push(this);
        setTimeout(() => this.onopen?.(), 0);
      }

      send(value: string) {
        this.sent.push(value);
        this.onmessage?.({ data: `已发送：${value}` });
      }

      close() {
        this.onclose?.();
      }
    }
    vi.stubGlobal("WebSocket", MockWebSocket);
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": { body: [serverRecord] }
    });

    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: /终端/ }));

    expect(screen.getByRole("heading", { name: "SSH 工作台" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "服务器列表" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "添加服务器" })).toBeInTheDocument();
    expect(screen.queryByLabelText("终端输入")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "连接 prod-app-01" }));
    await waitFor(() => {
      expect(screen.getByText("已连接到 prod-app-01。")).toBeInTheDocument();
    });

    screen.getByRole("textbox", { name: "终端窗口" }).focus();
    await userEvent.keyboard("pwd{Enter}");

    expect(instances[0].url).toContain("/api/servers/1/terminal");
    expect(instances[0].sent).toContain("pwd\n");
    expect(screen.getByText("root@prod-app-01:~# pwd")).toBeInTheDocument();
  });

  test("routes double-slash terminal input to the AI assistant", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": { body: [serverRecord] },
      "/api/servers/1/assistant/propose-command": {
        body: {
          command: "df -h && free -h",
          explanation: "查看磁盘和内存使用情况。",
          requires_confirmation: true,
          warnings: ["只读查询命令。"],
          source: "ai"
        }
      }
    });

    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: /终端/ }));
    screen.getByRole("textbox", { name: "终端窗口" }).focus();
    await userEvent.keyboard("//查看磁盘和内存{Enter}");

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/servers/1/assistant/propose-command",
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(await screen.findByText("AI 建议命令：df -h && free -h")).toBeInTheDocument();
    expect(screen.getByText("AI 说明：查看磁盘和内存使用情况。")).toBeInTheDocument();
  });

  test("supports Chinese input, paste, copy and compact prompt in the terminal", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": { body: [serverRecord] }
    });

    const writeText = vi.fn();
    Object.assign(navigator, { clipboard: { writeText } });
    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: /终端/ }));
    expect(screen.queryByRole("status", { name: "" })).not.toBeInTheDocument();

    const terminal = screen.getByRole("textbox", { name: "终端窗口" });
    terminal.focus();
    fireEvent.compositionStart(terminal);
    fireEvent.compositionUpdate(terminal, { data: "//查看日志" });
    fireEvent.compositionEnd(terminal, { data: "//查看日志" });
    expect(screen.getByText(/root@prod-app-01:~#/)).toBeInTheDocument();
    expect(screen.getByText("//查看日志")).toBeInTheDocument();

    fireEvent.paste(terminal, {
      clipboardData: {
        getData: () => " && tail -n 50 /var/log/syslog"
      }
    });
    expect(screen.getByText("//查看日志 && tail -n 50 /var/log/syslog")).toBeInTheDocument();

    await userEvent.keyboard("{Control>}c{/Control}");
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("//查看日志 && tail -n 50 /var/log/syslog"));
  });

  test("opens server detail and supports snapshot refresh, edit and delete", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": { body: [serverRecord] },
      "/api/servers/1/snapshot": {
        body: { ...serverRecord.latest_snapshot, cpu_usage: 18.2, message: "资源快照已刷新。" }
      },
      "/api/servers/1": (init) => ({
        body: init?.method === "DELETE" ? { ok: true } : { ...serverRecord, name: "prod-app-renamed" }
      })
    });

    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: "查看 prod-app-01 详情" }));
    expect(screen.getByRole("heading", { name: "prod-app-01" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "刷新快照" }));
    await waitFor(() => {
      expect(screen.getAllByText("资源快照已刷新。").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("CPU 18.2%")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "编辑服务器" }));
    await userEvent.clear(screen.getByLabelText("服务器名称"));
    await userEvent.type(screen.getByLabelText("服务器名称"), "prod-app-renamed");
    await userEvent.click(screen.getByRole("button", { name: "保存修改" }));
    await waitFor(() => {
      expect(screen.getByText("服务器已更新：prod-app-renamed")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "删除服务器" }));
    await waitFor(() => {
      expect(screen.getByText("服务器已删除。")).toBeInTheDocument();
    });
  });

  test("manages AI provider testing, model fetching, manual model and default model", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/ai-providers": { body: [providerRecord] },
      "/api/ai-providers/1/test": { body: { ...providerRecord, last_test_message: "AI 中转站连接正常。" } },
      "/api/ai-providers/1/fetch-models": { body: [modelRecord] },
      "/api/ai-providers/1/models": (init) => ({
        body:
          init?.method === "POST"
            ? { id: 12, provider_id: 1, model_id: "qwen-max", display_name: "qwen-max", source: "manual", enabled: true }
            : [modelRecord]
      }),
      "/api/ai-providers/1": { body: { ...providerRecord, default_model: "qwen-max" } },
      "/api/ai-providers/1/set-default": { body: providerRecord }
    });

    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: /系统设置/ }));
    await userEvent.click(screen.getByRole("button", { name: "测试 Relay" }));
    await waitFor(() => {
      expect(screen.getByText("AI 中转站连接正常。")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "拉取模型" }));
    expect(await screen.findByText("deepseek-chat · 拉取 · 已启用")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("手动模型 ID"), "qwen-max");
    await userEvent.click(screen.getByRole("button", { name: "添加手动模型" }));
    await waitFor(() => {
      expect(screen.getByText("模型已添加：qwen-max")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "设为默认模型 qwen-max" }));
    await waitFor(() => {
      expect(screen.getByText("默认模型已切换：qwen-max")).toBeInTheDocument();
    });
  });

  test("proposes a command, confirms execution and summarizes output", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": { body: [serverRecord] },
      "/api/servers/1/assistant/propose-command": {
        body: {
          command: "uname -a && lscpu && free -h && df -h /",
          explanation: "查询系统、CPU、内存和磁盘信息。",
          requires_confirmation: true,
          warnings: ["包含系统查询命令。"],
          source: "ai"
        }
      },
      "/api/servers/1/commands": {
        body: {
          id: 20,
          task_id: null,
          server_id: 1,
          command: "uname -a && lscpu && free -h && df -h /",
          working_directory: null,
          stdout: "Ubuntu 22.04\nCPU(s): 4\nMem: 7.8Gi\n/dev/sda1 37%",
          stderr: "",
          exit_code: 0,
          status: "success",
          started_at: "2026-07-02T08:40:00Z",
          finished_at: "2026-07-02T08:40:01Z"
        }
      },
      "/api/servers/1/assistant/summarize-output": {
        body: {
          status: "成功",
          summary: "命令执行成功，服务器为 Ubuntu 22.04，CPU 4 核，根分区使用率 37%。"
        }
      }
    });

    render(<App />);

    const navigation = await screen.findByRole("navigation", { name: "主导航" });
    await userEvent.click(within(navigation).getByRole("button", { name: /AI 助手/ }));
    await userEvent.clear(screen.getByLabelText("运维问题"));
    await userEvent.type(screen.getByLabelText("运维问题"), "查询当前服务器配置");
    await userEvent.click(screen.getByRole("button", { name: "生成命令建议" }));

    expect(await screen.findByText("建议命令")).toBeInTheDocument();
    expect(screen.getByText("uname -a && lscpu && free -h && df -h /")).toBeInTheDocument();
    expect(screen.getByText("查询系统、CPU、内存和磁盘信息。")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "确认执行" }));
    await waitFor(() => {
      expect(screen.getByText("命令执行完成。")).toBeInTheDocument();
    });
    expect(screen.getAllByText(/Ubuntu 22.04/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/CPU 4 核/)).toBeInTheDocument();
  });

  test("uploads package, analyzes project, creates plan, executes deployment and shows history", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": { body: [serverRecord] },
      "/api/packages/upload": { body: packageRecord },
      "/api/servers/1/analyze-upload": { body: analysisRecord },
      "/api/deployments/plan": { body: { ...deploymentRecord, status: "pending", logs: [] } },
      "/api/deployments/5/execute": { body: deploymentRecord },
      "/api/deployments": { body: [deploymentRecord] }
    });

    render(<App />);

    const navigation = await screen.findByRole("navigation", { name: "主导航" });
    await userEvent.click(within(navigation).getByRole("button", { name: /服务部署/ }));
    await userEvent.upload(screen.getByLabelText("服务包"), new File(["demo"], "demo.zip", { type: "application/zip" }));
    await userEvent.clear(screen.getByLabelText("部署目录"));
    await userEvent.type(screen.getByLabelText("部署目录"), "/opt/apps/demo");
    await userEvent.click(screen.getByRole("button", { name: "上传服务包" }));

    await waitFor(() => {
      expect(screen.getByText("服务包已上传：demo.zip")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "分析上传包" }));
    expect(await screen.findByText("这是一个 Node.js 服务，建议使用 pm2 或 systemd 托管。")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "创建部署计划" }));
    await waitFor(() => {
      expect(screen.getByText("部署计划已创建，请确认后执行。")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "确认执行部署" }));
    await waitFor(() => {
      expect(screen.getByText("部署执行完成：success")).toBeInTheDocument();
    });

    await userEvent.click(within(navigation).getByRole("button", { name: /历史记录/ }));
    expect(await screen.findByText("npm run start")).toBeInTheDocument();
    expect(screen.getByText("服务已启动")).toBeInTheDocument();
  });

  test("checks backend health through the API", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/health": { body: { status: "ok", service: "ai-agent-ssh" } }
    });

    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: /检查后端/ }));

    await waitFor(() => {
      expect(screen.getByText("后端连接正常：ai-agent-ssh")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/health", expect.objectContaining({ method: "GET" }));
  });

  test("checks a dangerous command through the API", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/commands/check": {
        body: {
          allowed: false,
          reason: "检测到危险的递归强制删除命令。",
          requires_confirmation: false,
          warnings: []
        }
      }
    });

    render(<App />);
    const navigation = await screen.findByRole("navigation", { name: "主导航" });
    await userEvent.click(within(navigation).getByRole("button", { name: /AI 助手/ }));
    await userEvent.clear(screen.getByLabelText("待检查命令"));
    await userEvent.type(screen.getByLabelText("待检查命令"), "rm -rf /");
    await userEvent.click(screen.getByRole("button", { name: /检查命令/ }));

    await waitFor(() => {
      expect(screen.getByText("已拦截：检测到危险的递归强制删除命令。")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/commands/check",
      expect.objectContaining({ method: "POST" })
    );
  });

  test("validates deployment plan through the API", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/deployments/validate-plan": { body: { valid: true, plan: { steps: [{ name: "构建" }] } } }
    });

    render(<App />);
    const navigation = await screen.findByRole("navigation", { name: "主导航" });
    await userEvent.click(within(navigation).getByRole("button", { name: /服务部署/ }));
    await userEvent.click(screen.getByRole("button", { name: /校验部署计划/ }));

    await waitFor(() => {
      expect(screen.getByText("部署计划校验通过，共 1 个步骤。")).toBeInTheDocument();
    });
  });

  test("keeps authenticated session when resource loading fails during refresh", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    mockApi({
      "/api/auth/status": { body: { initialized: true } },
      "/api/auth/me": { body: adminUser },
      "/api/servers": {
        body: { detail: "no such column: servers.last_test_message" },
        ok: false,
        status: 500
      }
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "概览" })).toBeInTheDocument();
    });
    expect(window.localStorage.getItem("ai-agent-ssh-token")).toBe("token-1");
    expect(screen.getByText("资源加载失败：no such column: servers.last_test_message")).toBeInTheDocument();
  });
});
