import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { App } from "./App";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  window.localStorage.clear();
});

describe("App interactions", () => {
  test("shows a clear validation message for short admin password", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Not authenticated" })
    });

    render(<App />);
    await userEvent.type(screen.getByLabelText("账号"), "admin");
    await userEvent.type(screen.getByLabelText("密码"), "123456");
    await userEvent.click(screen.getByRole("button", { name: "初始化管理员" }));

    expect(screen.getByText("认证失败：密码至少需要 8 位。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  test("initializes an admin and loads protected resources", async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Not authenticated" })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: "token-1", user: { id: 1, username: "admin", role: "admin" } })
      })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<App />);
    await userEvent.type(screen.getByLabelText("账号"), "admin");
    await userEvent.type(screen.getByLabelText("密码"), "strong-password");
    await userEvent.click(screen.getByRole("button", { name: "初始化管理员" }));

    await waitFor(() => {
      expect(screen.getAllByText("登录用户：admin").length).toBeGreaterThan(0);
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/init", expect.objectContaining({ method: "POST" }));
  });

  test("renders server data from the API and creates a server", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1, username: "admin", role: "admin" })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            id: 1,
            name: "prod-app-01",
            host: "10.0.12.21",
            port: 22,
            username: "root",
            auth_type: "password",
            remark: null,
            status: "unknown",
            connection_mode: "ssh",
            has_password: true,
            has_private_key: false
          }
        ]
      })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
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
        })
      });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByText("prod-app-01")).toBeInTheDocument();
    });

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

  test("creates an AI provider through the API", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, username: "admin", role: "admin" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          name: "Relay",
          provider_type: "openai-compatible",
          base_url: "https://relay.example/v1",
          default_model: "deepseek-chat",
          api_mode: "chat_completions",
          enabled: true,
          has_api_key: true,
          api_key_mask: "sk-t********test"
        })
      });

    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: /系统设置/ }));
    await userEvent.clear(screen.getByLabelText("供应商名称"));
    await userEvent.type(screen.getByLabelText("供应商名称"), "Relay");
    await userEvent.clear(screen.getByLabelText("Base URL"));
    await userEvent.type(screen.getByLabelText("Base URL"), "https://relay.example/v1");
    await userEvent.type(screen.getByLabelText("API Key"), "sk-test");
    await userEvent.clear(screen.getByLabelText("默认模型"));
    await userEvent.type(screen.getByLabelText("默认模型"), "deepseek-chat");
    await userEvent.click(screen.getByRole("button", { name: "保存 AI 中转站" }));

    await waitFor(() => {
      expect(screen.getByText("AI 中转站已保存：Relay")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenLastCalledWith("/api/ai-providers", expect.objectContaining({ method: "POST" }));
  });

  test("switches sidebar sections", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, username: "admin", role: "admin" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: /终端/ }));

    expect(screen.getByRole("heading", { name: "Web SSH 终端" })).toBeInTheDocument();
    expect(screen.getByText("真实终端代理将在 WebSocket SSH 功能完成后启用。")).toBeInTheDocument();
  });

  test("checks backend health through the API", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, username: "admin", role: "admin" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "ok", service: "ai-agent-ssh" })
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
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, username: "admin", role: "admin" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          allowed: false,
          reason: "rm -rf / style deletion",
          requires_confirmation: false,
          warnings: []
        })
      });

    render(<App />);
    const navigation = await screen.findByRole("navigation", { name: "主导航" });
    await userEvent.click(within(navigation).getByRole("button", { name: /AI 助手/ }));
    await userEvent.clear(screen.getByLabelText("待检查命令"));
    await userEvent.type(screen.getByLabelText("待检查命令"), "rm -rf /");
    await userEvent.click(screen.getByRole("button", { name: /检查命令/ }));

    await waitFor(() => {
      expect(screen.getByText("已拦截：rm -rf / style deletion")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/commands/check",
      expect.objectContaining({ method: "POST" })
    );
  });

  test("validates deployment plan through the API", async () => {
    window.localStorage.setItem("ai-agent-ssh-token", "token-1");
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, username: "admin", role: "admin" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true, plan: { steps: [{ name: "构建" }] } })
      });

    render(<App />);
    const navigation = await screen.findByRole("navigation", { name: "主导航" });
    await userEvent.click(within(navigation).getByRole("button", { name: /服务部署/ }));
    await userEvent.click(screen.getByRole("button", { name: /校验部署计划/ }));

    await waitFor(() => {
      expect(screen.getByText("部署计划校验通过，共 1 个步骤。")).toBeInTheDocument();
    });
  });
});
