// 冻结场景轮次探针（CDP，无第三方依赖，Node 22+ 内置 WebSocket）。
//   node scripts/probe_round.mjs scenarios/rounds/<本轮> [scenarios/rounds/<上一轮>]
// 对五个场景页：
//   - 主题：light / dark / system（偏好浅、偏好深）是否落到对的配色
//   - 动效：默认与 reduced motion 下 1.5s 后仍在运行的动画、无限循环动画
//   - 版式：light / dark × 390（移动视口，DPR 2）/ 500 / 1280 全页截图与横向溢出
//   - 键盘：1280 与 390 下发真实 Tab 键遍历焦点，核对可达、焦点环、遮挡、出视口、正 tabindex、DOM 回跳
//   - 导出与打印：页面自己的 Markdown 导出、打印 PDF 页数
//   - 场景判据：按 SCENARIO.md 的通过标准读数，再用真实按键操作各场景的交互
// 结果写 <本轮>/_probe/（截图、<场景>.md、<场景>.pdf、probe.json），每页一行摘要打到 stdout；
// 给了上一轮就对比 probe.json 与同名截图。有问题时退出码 1。截图仍要人眼逐张看。
//
// 场景判据里的选择器对应当前基线页面的写法，SCENARIO.md 只冻结行为、不冻结 DOM。
// 重新生成页面后选择器可能不再命中：摘要会报「未命中」，按 SCENARIO.md 把选择器改到新页面上。
// Chrome 路径默认 macOS，其他系统用环境变量 CHROME 指定。
import { spawn } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const CHROME =
  process.env.CHROME ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const SCHEMA = "probe_round/1";
const R = resolve(process.argv[2]);
const PREV = process.argv[3] && resolve(process.argv[3]);
const OUT = join(R, "_probe");
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
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "probe-round-"))}`,
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

async function open(
  file,
  {
    width = 1280,
    height = 900,
    theme = "light",
    scheme = "light",
    reduced = true,
  } = {}
) {
  const mobile = width < 500;
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
    features: [
      {
        name: "prefers-reduced-motion",
        value: reduced ? "reduce" : "no-preference",
      },
      { name: "prefers-color-scheme", value: scheme },
    ],
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
  // 按键交互前先确认选择器命中；不命中就记下来，由摘要报出，不静默跳过
  const missing = [];
  const need = async (...sels) => {
    for (const sel of sels)
      if (!(await ev(`!!document.querySelector(${JSON.stringify(sel)})`)))
        missing.push(sel);
    return !missing.length;
  };
  return {
    S,
    ev,
    key,
    need,
    missing,
    close: () => send("Target.closeTarget", { targetId }),
  };
}

const OVERFLOW = `(() => {
  const cw = document.documentElement.clientWidth, out = [];
  const scrolls = (el) => { for (let p = el.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === "auto" || o === "scroll" || o === "hidden" || o === "clip") return true; } return false; };
  for (const el of document.querySelectorAll("body *")) {
    const r = el.getBoundingClientRect();
    if (r.width && r.right > cw + 1 && !scrolls(el)) out.push(el.tagName.toLowerCase() + (el.className && typeof el.className === "string" ? "." + el.className.split(" ")[0] : "") + " right=" + Math.round(r.right));
  }
  return { scrollWidth: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight, offenders: out.slice(0, 8) };
})()`;

const ANIMATIONS = `(() => {
  const all = document.getAnimations();
  return { running: all.filter((a) => a.playState === "running").length,
    infinite: all.filter((a) => { const t = a.effect && a.effect.getTiming(); return t && t.iterations === Infinity; }).length };
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

// 场景判据的页内读数。q() 取必需元素，不命中记进 missing。
const scenarioExpr = (body) => `(() => {
  const r = {}, missing = [];
  const q = (s) => { const el = document.querySelector(s); if (!el) missing.push(s); return el; };
  const main = document.getElementById("doc");
  try { ${body} } catch (e) { r.error = String(e); }
  if (missing.length) r.missing = missing;
  return r;
})()`;

const SCENARIOS = {
  "status-report": {
    check: `
      r.statNum = main.querySelectorAll(".stat-num").length;
      r.statNumInHeading = [].filter.call(main.querySelectorAll("h1,h2,h3,h4"), (h) => h.querySelector(".stat-num") || /^[\\d.,%+−-]+$/.test(h.textContent.trim())).length;
      const band = q(".metric-band");
      r.metricCards = band.children.length;
      const tops = [].map.call(band.children, (c) => Math.round(c.getBoundingClientRect().top));
      r.metricOneRow1280 = tops.every((t) => t === tops[0]);
      r.badgeVariants = [].map.call(main.querySelectorAll(".badge[data-variant]"), (b) => b.dataset.variant).join(",");
      r.buttonsInMain = main.querySelectorAll("button").length;`,
  },
  "approach-compare": {
    check: `
      r.cards = main.querySelectorAll(".card").length;
      const probe = document.createElement("i"); probe.style.color = "var(--color-primary)"; document.body.appendChild(probe);
      const pc = getComputedStyle(probe).color; probe.remove();
      r.primaryBorderCards = [].filter.call(main.querySelectorAll(".card"), (c) => getComputedStyle(c).borderTopColor === pc).length;
      q("table");
      r.tableCols = main.querySelectorAll("table thead th").length;
      r.badgesInTable = main.querySelectorAll("table .badge").length;
      r.codeLangs = [].map.call(main.querySelectorAll("code[class*=language-]"), (c) => c.className).join(",");
      r.summaryTop = Math.round(q(".alert").getBoundingClientRect().top);`,
  },
  "code-review": {
    check: `
      const bg = (sel) => getComputedStyle(q(sel)).backgroundColor;
      r.dAdd = main.querySelectorAll(".d-add").length + " " + bg(".d-add");
      r.dDel = main.querySelectorAll(".d-del").length + " " + bg(".d-del");
      r.summaries = [].map.call(main.querySelectorAll("details > summary"), (s) => s.textContent.replace(/\\s+/g, " ").trim());
      r.checkboxes = q("#questions").querySelectorAll("input[type=checkbox]").length;
      r.structureBeforeFiles = !!(q("#structure").compareDocumentPosition(q("#files")) & Node.DOCUMENT_POSITION_FOLLOWING);`,
    keys: async (p) => {
      const box = "#questions input[type=checkbox]",
        sum = "details > summary";
      if (!(await p.need(box, sum))) return {};
      await p.ev(`document.querySelector("${box}").focus()`);
      const q = `document.querySelector("${box}").checked`;
      const checkboxBefore = await p.ev(q);
      await p.key(" ", "Space", 32);
      const checkboxAfterSpace = await p.ev(q);
      await p.ev(`document.querySelector("${sum}").focus()`);
      const open = `document.querySelector("${sum}").parentElement.open`;
      const detailsBefore = await p.ev(open);
      await p.key("Enter", "Enter", 13);
      return {
        checkboxBefore,
        checkboxAfterSpace,
        detailsBefore,
        detailsAfterEnter: await p.ev(open),
      };
    },
  },
  "concept-explainer": {
    check: `
      const ttl = q("#ttl-control"), hit = q("#hit-output");
      r.sliderAppearance = getComputedStyle(ttl).appearance;
      r.hitBefore = hit.textContent;
      r.minHit = q("#min-hit-output").textContent;
      ttl.value = 1800; ttl.dispatchEvent(new Event("input", { bubbles: true }));
      r.hitAfter = hit.textContent;
      r.hint = q(".fig-hint").textContent;
      r.caption = q("figcaption").textContent.replace(/\\s+/g, " ").trim();
      r.placeholders = [].filter.call(main.querySelectorAll("output"), (o) => o.textContent.trim() === "—").map((o) => o.id);`,
    keys: async (p) => {
      if (!(await p.need("#ttl-control", "#hit-output"))) return {};
      await p.ev(`document.getElementById("ttl-control").focus()`);
      const read = `document.getElementById("hit-output").textContent`;
      const before = await p.ev(read);
      for (let i = 0; i < 5; i++) await p.key("ArrowRight", "ArrowRight", 39);
      return {
        before,
        afterArrowRight5: await p.ev(read),
        value: await p.ev(`document.getElementById("ttl-control").value`),
      };
    },
  },
  "triage-board": {
    check: `
      const counts = () => [].map.call(document.querySelectorAll("[data-count]"), (c) => +c.textContent).join("/");
      q("[data-count]");
      r.countsStart = counts();
      const t = q(".ticket"); t.focus();
      t.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
      r.countsAfterArrow = counts(); r.status = q("#board-status").textContent;
      t.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }));
      r.countsBack = counts();
      r.draggable = document.querySelectorAll(".ticket[draggable=true]").length;
      const dom = q("#domain-filter"); dom.value = "支付"; dom.dispatchEvent(new Event("change", { bubbles: true }));
      const hidden = [].filter.call(document.querySelectorAll(".ticket"), (x) => x.hidden || x.closest("[hidden]"));
      r.hiddenAfterFilter = hidden.length;
      const md = window.showMeMarkdown ? window.showMeMarkdown() : "";
      r.hiddenInExport = hidden.filter((x) => { const id = x.querySelector(".ticket-id"); return id && md.indexOf(id.textContent.trim()) >= 0; }).length;
      r.exportButtonsInMain = [].filter.call(main.querySelectorAll("button"), (b) => /导出|Markdown|复制/.test(b.textContent)).length;`,
    keys: async (p) => {
      if (!(await p.need(".ticket", "[data-count]"))) return {};
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
  },
};

async function keyboard(p) {
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
  const idx = new Map(all.map((a, i) => [a.id, i]));
  const item = (d) => `${d.tag} ${d.label}`;
  return {
    steps: order.length,
    tabbable: all.length,
    unreached: all.filter((a) => !reached.has(a.id)).map(item),
    noRing: order.filter((d) => !d.ring || !d.focusVisible).map(item),
    offscreen: order.filter((d) => !d.inView).map(item),
    covered: order
      .filter((d) => d.covered)
      .map((d) => `${item(d)} ← ${d.covered}`),
    positiveTabindex: all.filter((a) => a.pos).map((a) => a.label),
    backJumps: order
      .filter(
        (d, i) =>
          i &&
          idx.has(d.id) &&
          idx.has(order[i - 1].id) &&
          idx.get(d.id) < idx.get(order[i - 1].id)
      )
      .map(item),
    order: order.map(item),
  };
}

const THEMES = [
  ["light", "light", "light", false],
  ["dark", "dark", "light", true],
  ["system-light", "system", "light", false],
  ["system-dark", "system", "dark", true],
];

const report = {};
for (const name of PAGES) {
  const file = join(R, `${name}.html`);
  const res = (report[name] = {
    theme: {},
    motion: {},
    layout: {},
    keyboard: {},
  });

  for (const [key, theme, scheme] of THEMES) {
    const p = await open(file, { theme, scheme });
    res.theme[key] = await p.ev(
      `({ dark: document.documentElement.classList.contains("dark"), bodyBg: getComputedStyle(document.body).backgroundColor })`
    );
    await p.close();
  }

  for (const reduced of [false, true]) {
    const p = await open(file, { reduced });
    res.motion[reduced ? "reduced" : "default"] = await p.ev(ANIMATIONS);
    await p.close();
  }

  for (const theme of ["light", "dark"])
    for (const width of [390, 500, 1280]) {
      const p = await open(file, {
        theme,
        width,
        height: width === 390 ? 844 : 900,
      });
      const o = await p.ev(OVERFLOW);
      res.layout[`${theme}-${width}`] = o;
      const shot = await p.S("Page.captureScreenshot", {
        format: "png",
        captureBeyondViewport: true,
        clip: {
          x: 0,
          y: 0,
          width,
          height: Math.min(o.height, 16000),
          scale: 1,
        },
      });
      writeFileSync(
        join(OUT, `${name}-${theme}-${width}.png`),
        Buffer.from(shot.data, "base64")
      );
      await p.close();
    }

  {
    // 导出先于判据：判据会改页面状态（移卡、筛选、拖滑块）
    const p = await open(file);
    writeFileSync(
      join(OUT, `${name}.md`),
      (await p.ev(`window.showMeMarkdown ? window.showMeMarkdown() : ""`)) || ""
    );
    const pdf = Buffer.from((await p.S("Page.printToPDF", {})).data, "base64");
    writeFileSync(join(OUT, `${name}.pdf`), pdf);
    res.pdfPages = (
      pdf.toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []
    ).length;
    res.scenario = await p.ev(scenarioExpr(SCENARIOS[name].check));
    await p.close();
  }

  for (const width of [1280, 390]) {
    const p = await open(file, { width, height: width === 390 ? 844 : 900 });
    res.keyboard[width] = await keyboard(p);
    if (width === 1280 && SCENARIOS[name].keys) {
      res.keys = await SCENARIOS[name].keys(p);
      if (p.missing.length) res.keys.missing = p.missing;
    }
    await p.close();
  }
}
writeFileSync(
  join(OUT, "probe.json"),
  JSON.stringify({ schema: SCHEMA, pages: report }, null, 1)
);
chrome.kill();

let failed = false;
for (const [name, v] of Object.entries(report)) {
  const issues = [];
  for (const [key, , , dark] of THEMES)
    if (v.theme[key].dark !== dark)
      issues.push(`主题 ${key} 落成${v.theme[key].dark ? "深" : "浅"}色`);
  const m = v.motion.reduced;
  if (m.running || m.infinite)
    issues.push(
      `reduced motion 下仍有 ${m.running} 个动画在跑、${m.infinite} 个无限循环`
    );
  for (const [k, o] of Object.entries(v.layout)) {
    const w = +k.split("-")[1];
    if (o.scrollWidth > w || o.offenders.length)
      issues.push(
        `${k} 溢出 ${o.offenders.join(", ") || "scrollWidth=" + o.scrollWidth}`
      );
  }
  for (const [w, k] of Object.entries(v.keyboard))
    for (const f of [
      "unreached",
      "noRing",
      "offscreen",
      "covered",
      "positiveTabindex",
      "backJumps",
    ])
      if (k[f].length) issues.push(`键盘 ${w} ${f}: ${k[f].join("; ")}`);
  const miss = [
    ...(v.scenario.missing || []),
    ...((v.keys && v.keys.missing) || []),
  ];
  if (miss.length)
    issues.push(
      `场景检查未命中 ${[...new Set(miss)].join(", ")}：页面重新生成过就按 SCENARIO.md 改选择器`
    );
  if (v.scenario.error && !miss.length)
    issues.push(`场景检查报错 ${v.scenario.error}`);
  if (issues.length) failed = true;
  const { missing, error, ...values } = v.scenario;
  console.log(`${name}: ${issues.length ? issues.join(" | ") : "无问题"}`);
  console.log(
    `  打印 ${v.pdfPages} 页 · 判据 ${JSON.stringify(values)}${v.keys ? " · 按键 " + JSON.stringify(v.keys) : ""}`
  );
}

if (PREV) {
  const prevJson = join(PREV, "_probe", "probe.json");
  const prev =
    existsSync(prevJson) && JSON.parse(readFileSync(prevJson, "utf8"));
  if (!prev || prev.schema !== SCHEMA)
    console.log(`\n上一轮没有 ${SCHEMA} 格式的 probe.json，跳过对比`);
  else {
    const diffs = [];
    const walk = (a, b, path) => {
      if (a && b && typeof a === "object" && typeof b === "object")
        for (const k of new Set([...Object.keys(a), ...Object.keys(b)]))
          walk(a[k], b[k], `${path}.${k}`);
      else if (JSON.stringify(a) !== JSON.stringify(b))
        diffs.push(`${path}: ${JSON.stringify(a)} → ${JSON.stringify(b)}`);
    };
    walk(prev.pages, report, "");
    console.log(
      `\n与上一轮对比：probe.json ${diffs.length ? diffs.length + " 处不同" : "相同"}`
    );
    for (const d of diffs) console.log("  " + d);
    const changed = [];
    for (const name of PAGES)
      for (const theme of ["light", "dark"])
        for (const width of [390, 500, 1280]) {
          const f = `${name}-${theme}-${width}.png`;
          const a = join(PREV, "_probe", f);
          if (
            !existsSync(a) ||
            !readFileSync(a).equals(readFileSync(join(OUT, f)))
          )
            changed.push(f);
        }
    console.log(
      `截图：${30 - changed.length}/30 张逐字节相同${changed.length ? "；不同：" + changed.join(", ") : ""}（不同的逐张看，抗锯齿噪声也会让字节不同）`
    );
    for (const name of PAGES) {
      const a = join(PREV, "_probe", `${name}.md`);
      if (
        existsSync(a) &&
        readFileSync(a, "utf8") !==
          readFileSync(join(OUT, `${name}.md`), "utf8")
      )
        console.log(`Markdown 不同：${name}`);
    }
  }
}
process.exit(failed ? 1 : 0);
