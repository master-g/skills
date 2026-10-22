# Plan 025: show-me-html 加单页交互探针 `probe_page.mjs`，眼检能自动点一遍页面里的控件

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: 本计划要求计划 021 已合入：`ls skills/show-me-html/scripts/cdp.mjs` 存在，且 `grep -c 'export async function launch' skills/show-me-html/scripts/cdp.mjs` → `1`。不满足就 STOP。再确认 `references/compose-and-check.md` 里有 021 写的这句：`grep -c '交互（拖拽、键盘、折叠）仍需真实浏览器' skills/show-me-html/references/compose-and-check.md` → `1`。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P3
- **Effort**: M（一个约 150 行的新脚本、两句文档；脚本已在 scratchpad 里跑通，见下）
- **Risk**: LOW（新增的独立脚本，不改构建）
- **Depends on**: `plans/021-show-me-html-cdp-runner.md`（用它的 `scripts/cdp.mjs`）
- **Category**: dx
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 页面常有筛选器、折叠、滑块、可移动的卡片。生成页面的 agent 没有交互浏览器，技能文档只写了「交互需真实浏览器」，于是交互要么没验，要么临时加载另一个浏览器技能、读几百行指南再写脚本。2026-10-22 维护者的一次会话在这上面花了约 3 分钟，还踩了两个坑：选择器同时命中两个元素；图表要滚进视口才画，第一次断言拿到 0 根刻度。仓库里的 `scripts/probe_round.mjs` 已经有按键、截图这些原语，但只服务 5 个冻结场景页。

本计划加一个对任意成品页都能跑的探针：在 `#doc` 里找出折叠、选择框、复选框、单选、滑块、文本输入、按钮、标签页，每个控件在新加载的页面上单独操作一次，记下 DOM 变化次数、操作后的状态、控制台报错，并截操作前后的视口。有 JS 报错时退出码 1。

advisor 在 scratchpad 里（021 的代码已套上）跑过下面 Step 1 的脚本：

- triage-board 场景页：19 个控件全部操作到（两个筛选器、17 个「移到左列 / 右列」按钮），每个都有 DOM 变化，30 秒。最初的版本在同一页面上连续操作，筛选器把后面的卡片藏掉了，后 16 个控件被跳过；所以改成每个控件重新加载页面。
- code-review 场景页：2 个折叠、3 个复选框；concept-explainer 在 390px 下：2 个滑块。
- 一个故意写坏的按钮（点击时 `throw new Error('boom')`）：该行报 `报错 Error: boom`、`没反应？看截图`，退出码 1。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。

- `scripts/cdp.mjs`（021 新建）导出 `launch(chromePath, prefix)`，返回 `{ send(method, params, sessionId), until(method, { sessionId, timeout }), on(listener), close() }`，Chrome 启动参数里已含代理（`proxyArgs()`）。
- `scripts/probe_round.mjs`：冻结场景探针，Chrome 路径写法是 `process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`，新脚本照抄。
- 骨架在代码块里注入「复制 / 换行」工具条（`.code-tools`），那是骨架自己的按钮，探针跳过。
- 数据图在 `charts.js` 的 `reveal` 里用 `IntersectionObserver` 滚入视口才画。
- `references/compose-and-check.md`「眼睛关」第一段（021 之后）末句是：`…用它们完成下列与主题、窄屏、版式、Markdown 相关的检查；交互（拖拽、键盘、折叠）仍需真实浏览器，没跑就写「未验证」。` 同一节后面有一行 `JavaScript 不平凡时，顺手看一眼浏览器控制台有没有报错。`

## Commands you will need

| Purpose  | Command                                                    | Expected on success |
| -------- | ---------------------------------------------------------- | ------------------- |
| JS 语法  | `node --check skills/show-me-html/scripts/probe_page.mjs`  | 无输出              |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build` | 末行 `OK`           |
| 文档门禁 | `make check`                                               | exit 0              |

## Scope

**In scope**：`skills/show-me-html/scripts/probe_page.mjs`（新建）、`skills/show-me-html/references/compose-and-check.md`（两处）、`plans/README.md`（状态行）。

**Out of scope**：

- 拖拽、hover、键盘 Tab 遍历：键盘遍历在 `probe_round.mjs`，拖拽和 hover 仍靠真实浏览器。
- 把探针接进 `build.py`：它会改页面状态、耗时几十秒，作为单独的工具按需跑。
- `probe_round.mjs`：不改。
- 单元测试：脚本不是构建的一部分，靠 Step 2 的实跑验证。

## Git workflow

从本地 `main` 开分支 `advisor/025-show-me-html-probe-page`；提交例如 `feat(show-me-html): probe_page.mjs clicks through any page's controls`。不要 push。

## Steps

### Step 1: 新建 `scripts/probe_page.mjs`

内容原样如下：

<!-- prettier-ignore -->
```js
// 单页交互探针：对任意 show-me-html 成品页逐个操作 #doc 里的控件，记下 DOM 变化、状态、控制台报错和操作前后的截图。
//   node scripts/probe_page.mjs 页面.html [--width 390] [--theme dark] [--out 目录]
// 覆盖：折叠（summary）、选择框、复选框与单选、滑块、文本输入、按钮、标签页。每个控件在重新加载的页面上单独操作一次，
// 前一个控件（例如筛选器）改掉的状态不影响后一个。拖拽、hover、键盘遍历不在范围内（键盘遍历见 probe_round.mjs）。
// 每个控件一行摘要打到 stdout，截图与 report.md 写进输出目录。
// 页面加载或操作时有 JS 异常 / console.error 时退出码 1。Chrome 路径默认 macOS，其他系统用环境变量 CHROME 指定。
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
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
  console.error("用法：node scripts/probe_page.mjs 页面.html [--width 390] [--theme dark] [--out 目录]");
  process.exit(2);
}
const PAGE = resolve(positionals[0]);
const WIDTH = Number(values.width);
const MOBILE = WIDTH < 500;
const OUT = resolve(values.out || mkdtempSync(join(tmpdir(), `probe-page-${basename(PAGE, ".html")}-`)));
mkdirSync(OUT, { recursive: true });
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const { send, until, on, close } = await launch(CHROME, "probe-page-");
const { targetId } = await send("Target.createTarget", { url: "about:blank" });
const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
const S = (method, params) => send(method, params, sessionId);
const errors = [];
on((m) => {
  if (m.sessionId !== sessionId) return;
  if (m.method === "Runtime.exceptionThrown") {
    const d = m.params.exceptionDetails;
    errors.push(((d.exception && d.exception.description) || d.text || "").split("\n")[0]);
  } else if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error")
    errors.push(m.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
});
await S("Page.enable");
await S("Runtime.enable");
await S("Emulation.setDeviceMetricsOverride", { width: WIDTH, height: 900, deviceScaleFactor: 1, mobile: MOBILE });
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
  (await S("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
const shot = async (file) =>
  writeFileSync(join(OUT, file), Buffer.from((await S("Page.captureScreenshot", { format: "png" })).data, "base64"));

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
  rows.push(`| ${n} | ${name} | ${r.mutations} | ${r.state} | ${errs.join("；")} | ${n}-before.png / ${n}-after.png |`);
  console.log(`${n} ${name} DOM 变化 ${r.mutations}${r.state ? " · 状态 " + r.state : ""}${quiet ? " · 没反应？看截图" : ""}${errs.length ? " · 报错 " + errs.join("；") : ""}`);
}
writeFileSync(join(OUT, "report.md"), [
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
].join("\n"));
console.log(`\n${controls.length} 个控件 · 加载时报错 ${loadErrors.length} 条 · 报告 ${join(OUT, "report.md")}`);
close();
process.exit(loadErrors.length || erred ? 1 : 0);
```

**Verify**: `node --check skills/show-me-html/scripts/probe_page.mjs` 无输出；`node skills/show-me-html/scripts/probe_page.mjs; echo $?` 打印用法和 `2`。

### Step 2: 实跑

```sh
R=$(ls -d /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/*/ | tail -1)
T=$(mktemp -d)
node skills/show-me-html/scripts/probe_page.mjs "$R/triage-board.html" --out "$T/tb" > "$T/tb.log"; echo "exit=$?"; tail -4 "$T/tb.log"
node skills/show-me-html/scripts/probe_page.mjs "$R/code-review.html" --out "$T/cr" | tail -7
node skills/show-me-html/scripts/probe_page.mjs "$R/concept-explainer.html" --width 390 --out "$T/ce" | tail -4
```

**Verify**: triage-board 末行 `19 个控件 · 加载时报错 0 条 · …`，`exit=0`，没有 `不可见，跳过`；code-review 列出 2 个 `summary` 和 3 个 `input[checkbox]`；concept-explainer 列出 2 个 `input[range]`。场景页重新生成过、控件数不同也可以，只要没有报错、没有大批 `不可见，跳过`。打开 `"$T/tb/01-before.png"`、`"$T/tb/01-after.png"`：筛选前后卡片数量不同。

再用一个故意写坏的页面确认报错能被抓到：

```sh
python3 - "$T/bad.html" <<'PY'
import pathlib, sys
html = pathlib.Path("skills/show-me-html/tests/fixtures/minimal-shell.html").read_text(encoding="utf-8")
html = html.replace("</main>", '<section><button type="button" class="btn" id="bad">坏按钮</button>'
                    '<details><summary>好折叠</summary><p>内容</p></details></section></main>')
html = html.replace("<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS--><script>document.getElementById('bad')"
                    ".addEventListener('click', function(){ throw new Error('boom'); });</script>")
pathlib.Path(sys.argv[1]).write_text(html, encoding="utf-8")
PY
python3 skills/show-me-html/scripts/build.py "$T/bad.html" > /dev/null
node skills/show-me-html/scripts/probe_page.mjs "$T/bad.html" --out "$T/bad"; echo "exit=$?"
```

**Verify**: 第一行含 `button「坏按钮」` 和 `报错 Error: boom`，第二行 `summary「好折叠」 DOM 变化 1 · 状态 true`，`exit=1`。

### Step 3: 文档

`references/compose-and-check.md`：

1. 「眼睛关」第一段末句 `交互（拖拽、键盘、折叠）仍需真实浏览器，没跑就写「未验证」。` 改为：

   <!-- prettier-ignore -->
   ```markdown
   交互先跑 `node <skill-path>/scripts/probe_page.mjs 页面.html`（窄屏加 `--width 390`）：它在新加载的页面上逐个操作折叠、选择框、复选框、滑块、输入框、按钮和标签页，报出控制台错误和「没反应」的控件，并截下每次操作前后的视口。拖拽、hover 和键盘遍历仍需真实浏览器，没跑就写「未验证」。
   ```

2. `JavaScript 不平凡时，顺手看一眼浏览器控制台有没有报错。` 之后另起一句（同一段）：

   <!-- prettier-ignore -->
   ```markdown
   自己写浏览器脚本断言图内元素时，先把图 `scrollIntoView`：数据图滚入视口才画，没滚到的图里一个图元都没有。
   ```

3. `npx prettier --write skills/show-me-html/references/compose-and-check.md`

**Verify**: `make check` → exit 0；`grep -c 'probe_page.mjs' skills/show-me-html/references/compose-and-check.md` → `1`。

## Test plan

不加单元测试。Step 2 覆盖三类场景页（筛选与按钮、折叠与复选框、390px 滑块）和一个必报错的页面。

## Done criteria

- [ ] `node --check skills/show-me-html/scripts/probe_page.mjs` 无输出
- [ ] Step 2 的四次运行结果与 Verify 一致（坏页面 `exit=1`，其余退出码 0）
- [ ] 全量单元测试 `OK`（本计划不改 Python，只确认没碰坏别的）
- [ ] `make check` exit 0；`git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- 021 未合入（没有 `cdp.mjs`）。
- triage-board 上出现大批 `不可见，跳过`，或任何场景页报出控制台错误：先在浏览器里打开该页确认是不是页面本身的问题，汇报，不要改场景页。
- 坏按钮页面的退出码不是 1。

## Maintenance notes

- 探针只按标签和 `role="tab"` 找控件。页面自造的可点元素（带 `role="button"` 的 `div` 之类）会被 `build.py` 的可访问性检查拦下，所以不必在这里另找。
- 「没反应？看截图」是提示不是失败：复选框、滑块只改属性值，`MutationObserver` 看不到，靠「操作后状态」一列判断。
- 每个控件都重新加载页面，控件多的页面会慢（约每个 1.5 秒）。以后需要连续操作（先筛选再移动卡片）时，再加一个按顺序操作的模式。
