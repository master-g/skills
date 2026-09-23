// 冻结场景轮次的 390px 与键盘探针（CDP，无第三方依赖，Node 22+ 内置 WebSocket）。
//   node scripts/probe390.mjs scenarios/rounds/<轮次>
// 对五个场景页：390×844 移动视口截 light / dark 全页并找横向溢出；1280 与 390 下发真实 Tab 键遍历焦点，
// 核对可达、焦点环、遮挡、出视口、正 tabindex 与 DOM 回跳；再用真实按键操作各场景的交互。
// 结果写 <轮次>/_probe/390/（截图 + probe390.json），每页一行摘要打到 stdout。截图仍要人眼逐张看。
// Chrome 路径默认 macOS，其他系统用环境变量 CHROME 指定。
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const CHROME =
  process.env.CHROME ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const R = resolve(process.argv[2]);
const OUT = join(R, "_probe", "390");
mkdirSync(OUT, { recursive: true });
const PAGES = [
  "status-report",
  "approach-compare",
  "code-review",
  "concept-explainer",
  "triage-board",
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  "--headless=new",
  "--remote-debugging-port=0",
  "--hide-scrollbars",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "kb390-"))}`,
  "about:blank",
]);
const wsUrl = await new Promise((ok) => {
  let buf = "";
  chrome.stderr.on("data", (d) => {
    buf += d;
    const m = buf.match(/ws:\/\/\S+/);
    if (m) ok(m[0]);
  });
});
const ws = new WebSocket(wsUrl);
await new Promise((r) => ws.addEventListener("open", r));
let seq = 0;
const pending = new Map();
const waiters = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id);
    pending.delete(m.id);
    m.error ? p.no(new Error(JSON.stringify(m.error))) : p.ok(m.result);
  } else if (m.method) for (const w of waiters.splice(0)) w(m);
});
const send = (method, params = {}, sessionId) =>
  new Promise((ok, no) => {
    const id = ++seq;
    pending.set(id, { ok, no });
    ws.send(JSON.stringify({ id, method, params, sessionId }));
  });
const until = (method) =>
  new Promise((ok) => {
    const f = (m) => (m.method === method ? ok(m) : waiters.push(f));
    waiters.push(f);
  });

async function open(file, { width, height, theme, mobile }) {
  const { targetId } = await send("Target.createTarget", {
    url: "about:blank",
  });
  const { sessionId: s } = await send("Target.attachToTarget", {
    targetId,
    flatten: true,
  });
  const S = (m, p) => send(m, p, s);
  await S("Page.enable");
  await S("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: mobile ? 2 : 1,
    mobile,
  });
  await S("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: "reduce" }],
  });
  await S("Page.addScriptToEvaluateOnNewDocument", {
    source: `try{localStorage.setItem("show-me-theme","${theme}")}catch(e){}`,
  });
  const loaded = until("Page.loadEventFired");
  await S("Page.navigate", { url: pathToFileURL(file).href });
  await loaded;
  await sleep(1500);
  const ev = async (expr) =>
    (
      await S("Runtime.evaluate", {
        expression: expr,
        returnByValue: true,
        awaitPromise: true,
      })
    ).result.value;
  const key = async (k, code, vk, mods = 0) => {
    for (const type of ["rawKeyDown", "keyUp"])
      await S("Input.dispatchKeyEvent", {
        type,
        key: k,
        code,
        windowsVirtualKeyCode: vk,
        modifiers: mods,
      });
    if (k === " " || k === "Enter")
      await S("Input.dispatchKeyEvent", {
        type: "char",
        text: k === " " ? " " : "\r",
      });
    await sleep(60);
  };
  return { S, ev, key, close: () => send("Target.closeTarget", { targetId }) };
}

const OVERFLOW = `(() => {
  const cw = document.documentElement.clientWidth, out = [];
  const scrolls = (el) => { for (let p = el.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === "auto" || o === "scroll" || o === "hidden" || o === "clip") return true; } return false; };
  for (const el of document.querySelectorAll("body *")) {
    const r = el.getBoundingClientRect();
    if (r.width && r.right > cw + 1 && !scrolls(el)) out.push(el.tagName.toLowerCase() + (el.className && typeof el.className === "string" ? "." + el.className.split(" ")[0] : "") + " right=" + Math.round(r.right));
  }
  return { scrollWidth: document.documentElement.scrollWidth, clientWidth: cw, offenders: out.slice(0, 8), height: document.documentElement.scrollHeight };
})()`;

const DESCRIBE = `(() => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  if (!el.__kbId) el.__kbId = ++window.__kbSeq;
  const cs = getComputedStyle(el), r = el.getBoundingClientRect();
  const ring = (cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== "none";
  const cx = Math.min(Math.max(r.left + r.width / 2, 0), innerWidth - 1), cy = Math.min(Math.max(r.top + Math.min(r.height / 2, 10), 0), innerHeight - 1);
  const hit = document.elementFromPoint(cx, cy);
  const label = (el.getAttribute("aria-label") || el.textContent || el.value || "").replace(/\\s+/g, " ").trim().slice(0, 28);
  return { id: el.__kbId, tag: el.tagName.toLowerCase() + (el.type ? "[" + el.type + "]" : ""), label,
    focusVisible: el.matches(":focus-visible"), ring, inView: r.bottom > 0 && r.top < innerHeight && r.width > 0,
    covered: !!hit && hit !== el && !el.contains(hit) && !hit.contains(el) ? hit.tagName.toLowerCase() + "." + (hit.className || "") : null };
})()`;

const TABBABLE = `(() => {
  window.__kbSeq = window.__kbSeq || 0;
  const sel = 'a[href],button,input,select,textarea,summary,[tabindex],[contenteditable="true"]';
  return [...document.querySelectorAll(sel)].filter((el) => {
    if (el.disabled || el.tabIndex < 0) return false;
    if (el.closest("[hidden],[inert]")) return false;
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none" || (!r.width && !r.height)) return false;
    if (el.closest("details:not([open])") && el.tagName !== "SUMMARY") return false;
    return true;
  }).map((el) => { if (!el.__kbId) el.__kbId = ++window.__kbSeq; return { id: el.__kbId, tag: el.tagName.toLowerCase(), label: (el.getAttribute("aria-label") || el.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 28), pos: el.tabIndex > 0 }; });
})()`;

const INTERACT = {
  "concept-explainer": async (p) => {
    await p.ev(`document.getElementById("ttl-control").focus()`);
    const before = await p.ev(
      `document.getElementById("hit-output").textContent`
    );
    for (let i = 0; i < 5; i++) await p.key("ArrowRight", "ArrowRight", 39);
    return {
      before,
      afterArrowRight5: await p.ev(
        `document.getElementById("hit-output").textContent`
      ),
      value: await p.ev(`document.getElementById("ttl-control").value`),
    };
  },
  "triage-board": async (p) => {
    const counts = `[...document.querySelectorAll("[data-count]")].map((c) => c.textContent.trim()).join("/")`;
    await p.ev(`document.querySelector(".ticket").focus()`);
    const start = await p.ev(counts);
    await p.key("ArrowRight", "ArrowRight", 39);
    const right = await p.ev(counts);
    const focusKept = await p.ev(
      `document.activeElement.classList.contains("ticket")`
    );
    await p.key("ArrowLeft", "ArrowLeft", 37);
    return { start, right, focusKept, back: await p.ev(counts) };
  },
  "code-review": async (p) => {
    await p.ev(
      `document.querySelector("#questions input[type=checkbox]").focus()`
    );
    const q = `document.querySelector("#questions input[type=checkbox]").checked`;
    const before = await p.ev(q);
    await p.key(" ", "Space", 32);
    const summary = `document.querySelector("details")`;
    await p.ev(`${summary}.querySelector("summary").focus()`);
    const openBefore = await p.ev(`${summary}.open`);
    await p.key("Enter", "Enter", 13);
    return {
      checkboxBefore: before,
      checkboxAfterSpace: await p.ev(q),
      detailsBefore: openBefore,
      detailsAfterEnter: await p.ev(`${summary}.open`),
    };
  },
};

const report = {};
for (const name of PAGES) {
  const file = join(R, `${name}.html`);
  const res = (report[name] = {});
  for (const theme of ["light", "dark"]) {
    const p = await open(file, {
      width: 390,
      height: 844,
      theme,
      mobile: true,
    });
    const o = await p.ev(OVERFLOW);
    res[`overflow390-${theme}`] = o;
    const shot = await p.S("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: true,
      clip: {
        x: 0,
        y: 0,
        width: 390,
        height: Math.min(o.height, 12000),
        scale: 1,
      },
    });
    writeFileSync(
      join(OUT, `${name}-${theme}-390.png`),
      Buffer.from(shot.data, "base64")
    );
    await p.close();
  }
  for (const width of [1280, 390]) {
    const p = await open(file, {
      width,
      height: width === 390 ? 844 : 900,
      theme: "light",
      mobile: width === 390,
    });
    const all = await p.ev(TABBABLE);
    const order = [];
    for (let i = 0; i < 250; i++) {
      await p.key("Tab", "Tab", 9);
      const d = await p.ev(DESCRIBE);
      if (d && order.length && d.id === order[0].id) break;
      if (d) order.push(d);
      else if (order.length) break;
    }
    const reached = new Set(order.map((d) => d.id));
    // DOM 顺序回跳：按 TABBABLE 的文档序号比对
    const idx = new Map(all.map((a, i) => [a.id, i]));
    const backJumps = order
      .filter(
        (d, i) =>
          i &&
          idx.has(d.id) &&
          idx.has(order[i - 1].id) &&
          idx.get(d.id) < idx.get(order[i - 1].id)
      )
      .map((d) => d.label);
    res[`keyboard${width}`] = {
      steps: order.length,
      tabbable: all.length,
      unreached: all
        .filter((a) => !reached.has(a.id))
        .map((a) => `${a.tag} ${a.label}`),
      noRing: order
        .filter((d) => !d.ring || !d.focusVisible)
        .map((d) => `${d.tag} ${d.label}`),
      offscreen: order
        .filter((d) => !d.inView)
        .map((d) => `${d.tag} ${d.label}`),
      covered: order
        .filter((d) => d.covered)
        .map((d) => `${d.tag} ${d.label} ← ${d.covered}`),
      positiveTabindex: all.filter((a) => a.pos).map((a) => a.label),
      backJumps,
      order: order.map((d) => `${d.tag} ${d.label}`),
    };
    if (width === 1280 && INTERACT[name])
      res.interact = await INTERACT[name](p);
    await p.close();
  }
}
writeFileSync(join(OUT, "probe390.json"), JSON.stringify(report, null, 1));
for (const [name, v] of Object.entries(report)) {
  const issues = [];
  for (const t of ["light", "dark"])
    if (v[`overflow390-${t}`].offenders.length)
      issues.push(
        `390 ${t} 溢出 ${v[`overflow390-${t}`].offenders.join(", ")}`
      );
  for (const w of [1280, 390]) {
    const k = v[`keyboard${w}`];
    for (const f of [
      "unreached",
      "noRing",
      "offscreen",
      "covered",
      "positiveTabindex",
      "backJumps",
    ])
      if (k[f].length) issues.push(`${w} ${f}: ${k[f].join("; ")}`);
  }
  console.log(
    `${name}: ${issues.length ? issues.join(" | ") : "无问题"}${v.interact ? "  交互 " + JSON.stringify(v.interact) : ""}`
  );
}
chrome.kill();
process.exit(0);
