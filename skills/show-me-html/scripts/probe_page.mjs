// 单页交互探针：对任意 show-me-html 成品页逐个操作 #doc 里的控件，记下 DOM 变化、状态、控制台报错和操作前后的截图。
//   node scripts/probe_page.mjs 页面.html [--width 390] [--theme dark] [--out 目录]
// 覆盖：折叠（summary）、选择框、复选框与单选、滑块、文本输入、按钮、标签页。每个控件在重新加载的页面上单独操作一次，
// 前一个控件（例如筛选器）改掉的状态不影响后一个。拖拽、hover、键盘遍历不在范围内（键盘遍历见 probe_round.mjs）。
// 每个控件一行摘要打到 stdout，截图与 report.md 写进输出目录。
// 页面加载或操作时有 JS 异常 / console.error 时退出码 1；页面不存在、用法错或探针自身出错退出码 2。
// Chrome 路径默认 macOS，其他系统用环境变量 CHROME 指定。
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { launch } from "./cdp.mjs";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    width: { type: "string", default: "1280" },
    theme: { type: "string", default: "light" },
    out: { type: "string" },
  },
});
if (!positionals[0]) {
  console.error(
    "用法：node scripts/probe_page.mjs 页面.html [--width 390] [--theme dark] [--out 目录]"
  );
  process.exit(2);
}
const PAGE = resolve(positionals[0]);
if (!existsSync(PAGE)) {
  console.error(`找不到页面：${PAGE}`);
  process.exit(2);
}
const WIDTH = Number(values.width);
const MOBILE = WIDTH < 500;
const OUT = resolve(
  values.out ||
    mkdtempSync(join(tmpdir(), `probe-page-out-${basename(PAGE, ".html")}-`))
);
mkdirSync(OUT, { recursive: true });
const CHROME =
  process.env.CHROME ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

let cdp;
try {
  cdp = await launch(CHROME, "probe-page-cdp-");
} catch (e) {
  console.error(`Chrome 起不来：${e.message || e}`);
  process.exit(2);
}
const { send, until, on, close } = cdp;
// 被 Ctrl-C 或命令超时的 SIGTERM 打断时也结束 Chrome、删掉配置目录（SIGKILL 拦不住）
for (const sig of ["SIGINT", "SIGTERM"])
  process.once(sig, () =>
    close().finally(() => process.exit(sig === "SIGINT" ? 130 : 143))
  );
let code = 2;
try {
  const { targetId } = await send("Target.createTarget", {
    url: "about:blank",
  });
  const { sessionId } = await send("Target.attachToTarget", {
    targetId,
    flatten: true,
  });
  const S = (method, params) => send(method, params, sessionId);
  const errors = [];
  on((m) => {
    if (m.sessionId !== sessionId) return;
    if (m.method === "Runtime.exceptionThrown") {
      const d = m.params.exceptionDetails;
      errors.push(
        ((d.exception && d.exception.description) || d.text || "").split(
          "\n"
        )[0]
      );
    } else if (
      m.method === "Runtime.consoleAPICalled" &&
      m.params.type === "error"
    )
      errors.push(
        m.params.args.map((a) => a.value ?? a.description ?? "").join(" ")
      );
  });
  await S("Page.enable");
  await S("Runtime.enable");
  await S("Emulation.setDeviceMetricsOverride", {
    width: WIDTH,
    height: 900,
    deviceScaleFactor: 1,
    mobile: MOBILE,
  });
  if (MOBILE) await S("Emulation.setTouchEmulationEnabled", { enabled: true });
  await S("Emulation.setEmulatedMedia", {
    features: [
      { name: "prefers-reduced-motion", value: "reduce" },
      { name: "prefers-color-scheme", value: values.theme },
    ],
  });
  await S("Page.addScriptToEvaluateOnNewDocument", {
    source: `try{localStorage.setItem("show-me-theme",${JSON.stringify(values.theme)})}catch(e){}`,
  });
  // 每次重新加载页面：等 load，再等 1 秒让骨架脚本和首屏的图跑完
  const fresh = async () => {
    const loaded = until("Page.loadEventFired", { sessionId });
    await S("Page.navigate", { url: pathToFileURL(PAGE).href });
    await loaded;
    await new Promise((r) => setTimeout(r, 1000));
  };
  const ev = async (expression) =>
    (
      await S("Runtime.evaluate", {
        expression,
        returnByValue: true,
        awaitPromise: true,
      })
    ).result.value;
  const shot = async (file) =>
    writeFileSync(
      join(OUT, file),
      Buffer.from(
        (await S("Page.captureScreenshot", { format: "png" })).data,
        "base64"
      )
    );

  // 只看正文 #doc 里的控件；代码块工具条（复制 / 换行）是骨架的，跳过
  const LIST = `(() => {
  const doc = document.getElementById("doc") || document.body;
  const sel = 'details > summary, select, input:not([type=hidden]), textarea, button, [role="tab"]';
  return [...doc.querySelectorAll(sel)].filter((el) => !el.closest(".code-tools") && !el.disabled).map((el, i) => {
    el.dataset.probeId = i + 1;
    const role = el.getAttribute("role");
    const label = (el.getAttribute("aria-label") || (el.labels && el.labels[0] && el.labels[0].textContent)
      || el.textContent || el.value || el.name || "").replace(/\\s+/g, " ").trim().slice(0, 30);
    return { id: i + 1, label, tag: el.tagName.toLowerCase() + (el.type && el.tagName !== "BUTTON" ? "[" + el.type + "]" : role ? "[" + role + "]" : "") };
  });
})()`;
  // 图表滚入视口才画（charts.js 的 reveal）：先把控件滚到视口中间，等两帧
  const SCROLL = (id) => `(async () => {
  const el = document.querySelector('[data-probe-id="${id}"]');
  if (!el || el.closest("[hidden], [inert]")) return false;
  const r0 = el.getBoundingClientRect();
  if (!r0.width || !r0.height) return false;
  el.scrollIntoView({ block: "center", behavior: "instant" });
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  return true;
})()`;
  const ACT = (id) => `(async () => {
  const el = document.querySelector('[data-probe-id="${id}"]');
  let n = 0;
  const mo = new MutationObserver((ms) => { n += ms.length; });
  mo.observe(document.documentElement, { subtree: true, childList: true, attributes: true, characterData: true });
  const tag = el.tagName, type = (el.type || "").toLowerCase();
  const fire = (name) => el.dispatchEvent(new Event(name, { bubbles: true }));
  if (tag === "SELECT") { el.selectedIndex = (el.selectedIndex + 1) % el.options.length; fire("input"); fire("change"); }
  else if (tag === "INPUT" && type === "range") { el.value = el.value === el.max ? el.min : el.max; fire("input"); fire("change"); }
  else if (tag === "TEXTAREA" || (tag === "INPUT" && !["checkbox", "radio", "button", "submit", "reset", "color", "file"].includes(type))) {
    el.focus(); el.value = "a"; fire("input"); fire("change");
  } else el.click();
  await new Promise((r) => setTimeout(r, 300));
  mo.disconnect();
  const state = tag === "SELECT" || tag === "TEXTAREA" || (tag === "INPUT" && !["checkbox", "radio"].includes(type)) ? el.value
    : type === "checkbox" || type === "radio" ? el.checked
    : tag === "SUMMARY" ? el.parentElement.open
    : el.getAttribute("aria-selected") ?? el.getAttribute("aria-pressed") ?? el.getAttribute("aria-expanded");
  return { mutations: n, state: state === null || state === undefined ? "" : String(state) };
})()`;

  await fresh();
  const loadErrors = errors.splice(0);
  const controls = await ev(LIST);
  const rows = [];
  let erred = 0;
  for (const c of controls) {
    const n = String(c.id).padStart(2, "0");
    const name = `${c.tag}「${c.label}」`;
    if (c.id > 1) {
      await fresh();
      errors.splice(0);
      await ev(LIST); // 新页面上重新编号，顺序不变
    }
    if (!(await ev(SCROLL(c.id)))) {
      rows.push(`| ${n} | ${name} | 不可见，跳过 | | | |`);
      console.log(`${n} ${name} 不可见，跳过`);
      continue;
    }
    await shot(`${n}-before.png`);
    const r = await ev(ACT(c.id));
    await shot(`${n}-after.png`);
    const errs = errors.splice(0);
    if (errs.length) erred++;
    const quiet = !r.mutations && !r.state;
    rows.push(
      `| ${n} | ${name} | ${r.mutations} | ${r.state} | ${errs.join("；")} | ${n}-before.png / ${n}-after.png |`
    );
    console.log(
      `${n} ${name} DOM 变化 ${r.mutations}${r.state ? " · 状态 " + r.state : ""}${quiet ? " · 没反应？看截图" : ""}${errs.length ? " · 报错 " + errs.join("；") : ""}`
    );
  }
  writeFileSync(
    join(OUT, "report.md"),
    [
      `# 交互探针 · ${basename(PAGE)}`,
      "",
      `页面 \`${PAGE}\`，视口 ${WIDTH}px，${values.theme} 主题，reduced motion。`,
      "",
      `加载时报错：${loadErrors.length ? loadErrors.join("；") : "无"}`,
      "",
      "| # | 控件 | DOM 变化 | 操作后状态 | 报错 | 截图 |",
      "| - | ---- | -------- | ---------- | ---- | ---- |",
      ...rows,
      "",
    ].join("\n")
  );
  console.log(
    `\n${controls.length} 个控件 · 加载时报错 ${loadErrors.length} 条 · 报告 ${join(OUT, "report.md")}`
  );
  code = loadErrors.length || erred ? 1 : 0;
} catch (e) {
  console.error(`探针中途出错：${e.message || e}`);
} finally {
  await close(); // close() 等 Chrome 退出后才删配置目录，先 await 再退出
}
process.exit(code);
