import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { App } from "./App";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

describe("App interactions", () => {
  test("switches sidebar sections", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: /终端/ }));

    expect(screen.getByRole("heading", { name: "Web SSH 终端" })).toBeInTheDocument();
    expect(screen.getByText("真实终端代理将在 WebSocket SSH 功能完成后启用。")).toBeInTheDocument();
  });

  test("checks backend health through the API", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "ok", service: "ai-agent-ssh" })
    });

    render(<App />);
    await userEvent.click(screen.getAllByRole("button", { name: /检查后端/ })[0]);

    await waitFor(() => {
      expect(screen.getByText("后端连接正常：ai-agent-ssh")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/health");
  });

  test("checks a dangerous command through the API", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        allowed: false,
        reason: "rm -rf / style deletion",
        requires_confirmation: false,
        warnings: []
      })
    });

    render(<App />);
    await userEvent.click(within(screen.getByRole("navigation", { name: "主导航" })).getByRole("button", { name: /AI 助手/ }));
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
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ valid: true, plan: { steps: [{ name: "构建" }] } })
    });

    render(<App />);
    await userEvent.click(within(screen.getByRole("navigation", { name: "主导航" })).getByRole("button", { name: /服务部署/ }));
    await userEvent.click(screen.getByRole("button", { name: /校验部署计划/ }));

    await waitFor(() => {
      expect(screen.getByText("部署计划校验通过，共 1 个步骤。")).toBeInTheDocument();
    });
  });
});
