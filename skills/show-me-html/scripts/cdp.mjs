// 共用的无头 Chrome 连接：CDP，Node 22+ 内置 WebSocket，无第三方依赖。render.mjs 与 probe_round.mjs 共用。
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// 无头 Chrome 不读 HTTP(S)_PROXY 环境变量：配了代理就显式传，否则每次直连 Google Fonts。测试见 tests/test_build.py 的 test_cdp_proxy_args_follow_proxy_env
export function proxyArgs(env = process.env) {
  const pick = (...names) =>
    names.map((n) => (env[n] || "").trim()).find(Boolean) || "";
  const proxy = pick(
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "ALL_PROXY",
    "all_proxy"
  );
  const bypass = pick("NO_PROXY", "no_proxy")
    .split(",")
    .map((h) => h.trim())
    .filter(Boolean);
  if (!proxy || bypass.includes("*")) return [];
  const args = [`--proxy-server=${proxy.replace(/\/$/, "")}`];
  if (bypass.length)
    args.push(
      `--proxy-bypass-list=${bypass.map((h) => (h.startsWith(".") ? "*" + h : h)).join(";")}`
    );
  return args;
}

// 启动一个无头 Chrome 并连上。返回 send(方法, 参数, sessionId)、until(事件名, {sessionId, timeout})、on(监听)、close()。
// close() 返回 Promise：结束 Chrome，等它退出后删掉这次的配置目录（每次几 MB 到几十 MB）。
// 启动失败时先收拾干净再抛错，不留 Chrome 进程和目录。
export async function launch(chromePath, prefix = "show-me-cdp-") {
  if (typeof WebSocket === "undefined")
    throw new Error("这个 node 没有内置 WebSocket，需要 Node 22 或更新版本");
  const dir = mkdtempSync(join(tmpdir(), prefix));
  const chrome = spawn(chromePath, [
    "--headless=new",
    "--remote-debugging-port=0",
    "--hide-scrollbars",
    // --no-sandbox：macOS 与普通用户下不需要，Linux 容器里以 root 跑 Chrome 时不加会直接退出
    "--no-sandbox",
    `--user-data-dir=${dir}`,
    ...proxyArgs(),
    "about:blank",
  ]);
  const exited = new Promise((r) => {
    chrome.once("exit", r);
    chrome.once("error", r);
  });
  const close = async () => {
    chrome.kill();
    await exited;
    try {
      rmSync(dir, { recursive: true, force: true });
    } catch {}
  };
  let ws;
  try {
    const wsUrl = await new Promise((ok, no) => {
      const timer = setTimeout(
        () => no(new Error("Chrome 30 秒内没有给出调试地址")),
        30000
      );
      let buf = "";
      chrome.stderr.on("data", (d) => {
        buf += d;
        const m = buf.match(/ws:\/\/\S+/);
        if (m) {
          clearTimeout(timer);
          ok(m[0]);
        }
      });
      chrome.on("error", no);
      chrome.on("exit", (code) =>
        no(new Error(`Chrome 启动失败（退出码 ${code}）`))
      );
    });
    ws = new WebSocket(wsUrl);
    await new Promise((ok, no) => {
      ws.addEventListener("open", ok);
      ws.addEventListener("error", () =>
        no(new Error("连不上 Chrome 的调试端口"))
      );
    });
  } catch (e) {
    await close();
    throw e;
  }
  let seq = 0;
  const pending = new Map();
  const listeners = new Set();
  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id);
      pending.delete(m.id);
      m.error ? p.no(new Error(JSON.stringify(m.error))) : p.ok(m.result);
    } else if (m.method) for (const f of [...listeners]) f(m);
  });
  const send = (method, params = {}, sessionId) =>
    new Promise((ok, no) => {
      const id = ++seq;
      pending.set(id, { ok, no });
      ws.send(JSON.stringify({ id, method, params, sessionId }));
    });
  const on = (f) => {
    listeners.add(f);
    return () => listeners.delete(f);
  };
  // 等下一个 method 事件；给了 sessionId 只认那个页面的
  const until = (method, { sessionId, timeout = 90000 } = {}) =>
    new Promise((ok, no) => {
      const off = on((m) => {
        if (m.method !== method || (sessionId && m.sessionId !== sessionId))
          return;
        clearTimeout(timer);
        off();
        ok(m);
      });
      const timer = setTimeout(() => {
        off();
        no(new Error(`等 ${method} 超时`));
      }, timeout);
    });
  return { send, until, on, close };
}
