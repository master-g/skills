# Plan 021: show-me-html 一次构建只启动一个无头 Chrome：渲染检查、快照切片与定尺卡截图改走 CDP 运行器

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 2f0e439..HEAD -- skills/show-me-html/scripts skills/show-me-html/tests/test_build.py skills/show-me-html/SKILL.md skills/show-me-html/references/compose-and-check.md skills/show-me-html/references/visual-system.md skills/show-me-html/references/diagrams.md`
> 本计划排在 020、018、019 之后执行，这三份合入后上面的文件都会出现在输出里，属于预期。开工前先确认三份都已合入：
>
> - `grep -c 'def chrome_proxy_args' skills/show-me-html/scripts/build.py` → `1`（020）
> - `grep -c '(?P<contrast>' skills/show-me-html/scripts/build.py` → `1`（018）
> - `grep -c '(?P<scaled>' skills/show-me-html/scripts/build.py` → `1`，且 `grep -n 'render_issues, render_notes, measured, rendered = render_check' skills/show-me-html/scripts/build.py` 有一行（019）
>
> 任何一条不满足就是 STOP 条件。其余文件出现别的改动时，对照下面「Current state」里的锚点；锚点找不到也是 STOP 条件。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P1
- **Effort**: L（两个新 Node 脚本、`build.py` 三个函数换传输方式、两个新参数、测试与四份文档）
- **Risk**: MED（渲染检查的等待机制换了实现；快照文件名从 `light-500.png` 变成切片；390px 新增一条 WARN）
- **Depends on**: `plans/020-show-me-html-chrome-proxy.md`、`plans/018-show-me-html-text-contrast.md`、`plans/019-show-me-html-chart-scale-warn.md` 都已合入（维护者定的顺序：020 → 018 → 019 → 021）
- **Category**: perf
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 的 `scripts/build.py` 每次构建都用无头 Chrome 渲染页面做检查，现在是每个任务冷启动一次 Chrome：渲染检查在 500 / 1024 / 1280px 各启动一次，`--snap` 在 light/dark × 500/1280 各启动两次（一次量页高、一次截图），合计 11 次。每次都是全新配置，没有字体缓存。2026-10-22 维护者本机一页 status-report 页面实测：`--snap` 全流程 119.8 秒，一次 32 分钟的会话里 20.5 分钟在等 Chrome。

advisor 在 scratchpad 里用一个 Chrome 实例、走 CDP（Chrome DevTools Protocol，Node 内置 WebSocket 就能连）验证过：同一页面 3 次检查加切片截图，带代理时总共约 4 秒；检查结果与现在的 `--dump-dom` 逐字相同，字体已加载。又把本计划 Step 2–7 的代码原样套到 `2f0e439` 的副本上（018/019 尚未合入，返回值按 019 的形状临时改了），全量单元测试 51 个 OK，用时从约 70 秒降到 32 秒；status-report 页 `--snap` 13.8 秒（当时拍 390、1280 两种宽度，本计划默认再加 500，会多几秒），改前 266.8 秒。本计划把渲染检查、`--snap`、`--shot` 都换成「Python 写任务清单 → Node 运行器在一个 Chrome 里依次执行 → 返回 JSON」。检查脚本 `PROBE` 本身和解析它的正则一行不改。

同一次改动顺带解决快照的几个问题。前三条来自交给维护者的方案；最后一条里「390 进渲染检查、溢出只报 WARN」是维护者 2026-10-22 明确确认的：

- **快照改成按视口高度切片**：现在是整页一张长图，1280 宽高 5840px，500 宽超过 16000px 被截断；读图工具会把长图降采样，细节看不清。改为每片 1500px（窄屏 1600px）高，输出时写明每片含哪几节（h2），小修后只重读那一两片。16000px 的截断随之消失。
- **视口高度不再被拉长**：现在截图前把窗口拉到整页高度，页面里的 `100dvh`（幻灯片每张一屏）会跟着变成整页高。改为视口固定 900px、按区域裁切截图，截出来的就是读者看到的样子。advisor 实测：三张幻灯片的页面，改后每张仍是 900px。
- **`--snap-theme`、`--snap-width` 缩小拍摄范围**：小修只拍受影响的主题和宽度。
- **390px 手机宽度进自动检查**：窗口参数 `--window-size` 最窄只到 500px，CDP 的设备模拟没有这个限制（`scripts/probe_round.mjs` 一直在用 390）。渲染检查加一个 390 视口，只查横向溢出、报 WARN，不让现在能通过的页面失败。`--snap` 默认宽度在原有的 500、1280 之外加上 390；500 照常拍，它是 500–900px 中等宽度（例如看板变成两列）唯一的默认截图。维护者 2026-10-22 决定保留 500，不要去掉。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `2f0e439`；020、018、019 合入后会往后挪，以引文为准。

**`scripts/build.py`**

- `render_check()`（`:1036` 起）。019 合入后它的开头、传输部分和结尾是这样（018 改过 `probe.write_text`、019 改过返回值；中间的解析部分由 017–019 逐段追加，本计划不动）：

  ```python
  def render_check(page, widths=(500, 1024, 1280)):
      """返回 (issues, notes, measured, ran)。issues 是 ERROR，notes 是 WARN；ran=False 表示没有浏览器，这道关没跑。"""
      import html as htmllib, subprocess, tempfile
      chrome = find_chrome()
      if not chrome:
          return [], [], [], False

      html = page.read_text(encoding="utf-8")
      issues, notes, measured = [], [], []
      with tempfile.TemporaryDirectory() as td:
          probe = Path(td) / "probe.html"
          # 固定亮色主题：对比度在亮色下最差；其余几何检查与主题无关，固定下来结果也不随本机外观变
          probe.write_text(html.replace(…), encoding="utf-8")   # 018 写的，原样保留
          for w in widths:
              try:
                  out = subprocess.run(
                      # --no-sandbox 见 shoot_sheets 的说明
                      [chrome, "--headless", "--disable-gpu", "--no-sandbox", *chrome_proxy_args(),
                       "--virtual-time-budget=4000", f"--window-size={w},900",
                       "--dump-dom", probe.as_uri()],
                      capture_output=True, text=True, timeout=90).stdout
              except Exception as e:
                  return [f"渲染检查跑不起来：{e}"], [], [], False
              m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(?P<contrast>.*?)\|(?P<scaled>.*?)</title>", out, re.S)
              if not m:
                  issues.append(f"{w}px：探针没返回结果（页面 JS 可能报错，去控制台看）")
                  continue
              …（解析与报错，不动）
      return issues, notes, measured, True
  ```

  `PROBE`（`:804-889`）是追加在页面末尾的一段脚本：页面 `load` 后等 1500ms，把测量结果用 `|` 分段写进 `document.title`，开头是 `PROBE|文档宽|视口宽|…`。现在靠 `--dump-dom` 把整个 DOM 打印出来，再用上面的正则从 `<title>` 里取。`--dump-dom` 打印时会把标题里的 `<`、`>`、`&` 转义，所以后面的解析都先 `htmllib.unescape(...)`。**这个约定和正则在本计划里原样保留。**

- `--virtual-time-budget=4000` 的含义：Chrome 用虚拟时间跑页面，有网络请求未完成时虚拟时间暂停，直到页面的计时器跑满 4000 虚拟毫秒。这保证 `PROBE` 的 1500ms 计时器触发时字体已到齐。CDP 里同一机制是 `Emulation.setVirtualTimePolicy`（`policy: "pauseIfNetworkFetchesPending"`，`budget`），预算用完时发 `Emulation.virtualTimeBudgetExpired` 事件。advisor 实测这样等到的标题与 `--dump-dom` 相同，`document.fonts.status` 为 `loaded`。

- `snap_page()`（`:955-1013`）、`SNAP_PROBE`、`SNAP_MAX_H = 16000`：每个主题 × 宽度先用 `--dump-dom` 跑一次 `SNAP_PROBE` 量 `scrollHeight` 和取 `window.showMeMarkdown()`，再按这个高度开窗截整页；`light` 且最宽那一次的 Markdown 写进 `export.md`。

- `shoot_sheets()`（`:912-949`）：每张 `.sheet` 写一份只显示这张卡的临时 HTML（`SHOT_CSS` 隐藏 chrome，`<style>` 隐藏其他卡，`<head>` 里写 localStorage 主题），按卡的尺寸开窗、`--force-device-scale-factor=2` 截图，输出到页面旁边 `<页面名>[-序号][-dark].png`。

- `main()`（`:1088` 起）里与本计划有关的部分：

  ```python
      ap.add_argument(
          "--snap",
          nargs="?",
          const="",
          metavar="DIR",
          help="自检通过后在 light/dark × 500/1280px 下各截一张整页 PNG，并导出 Markdown 到 export.md；"
               "不给 DIR 时写到新建的临时目录。供眼睛关读图用",
      )
  ```

  ```python
      print(f"自检通过{f'（{len(warns)} 个警告需逐条判断）' if warns else ''}。")
      if rendered:
          print(f"渲染检查：{' / '.join(f'{w}px' for w in measured)} 无横向溢出。"
                "（无头 Chrome 最窄只到 500px，更窄的屏幕仍需人眼过一遍。）")
      elif not args.no_render:
          print("渲染检查未运行：找不到 Chrome/Chromium。横向溢出没有被验证过，"
                "自己在浏览器里拉一遍窄屏，不要报「已验证」。")

      if args.snap is not None:
          import tempfile
          out_dir = Path(args.snap) if args.snap else Path(tempfile.mkdtemp(prefix=f"show-me-snap-{args.page.stem}-"))
          outs, notes, err = snap_page(args.page, out_dir)
          for o in outs:
              print(f"已快照  {o}")
          for n in notes:
              print(f"注意    {n}")
          if err:
              print(f"--snap 未完成：{err}")
  ```

- `:1035` 的注释 `# 无头 Chrome 把窗口宽度钳在 500px，比这更窄的视口测不到 —— 390px 只能人眼验。` 不再成立。

- `compile_math()`（`:507` 起）已经要求 `node`（`shutil.which("node")`），用 `subprocess.run([node, str(MATH_SCRIPT), str(page)], …)` 调 `scripts/math.mjs`。新运行器按同样方式调用。

**`scripts/probe_round.mjs`**（冻结场景探针，已经在用 CDP）：开头 import 了 `spawn`、`mkdtempSync`、`tmpdir` 等；020 在 `const chrome = spawn(CHROME, [` 上方加了一段 `PROXY_ARGS`；接着是启动 Chrome、连 WebSocket、`send`、`until` 的连接代码（`2f0e439` 的 `:43-85`）：

```js
const chrome = spawn(CHROME, [
  "--headless=new",
  "--remote-debugging-port=0",
  "--hide-scrollbars",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "probe-round-"))}`,
  ...PROXY_ARGS,
  "about:blank",
]);
const wsUrl = await new Promise((ok) => { … chrome.stderr 里匹配 ws:// … });
const ws = new WebSocket(wsUrl);
await new Promise((r) => ws.addEventListener("open", r));
let seq = 0;
const pending = new Map();
const waiters = [];
ws.addEventListener("message", (e) => { … });
const send = (method, params = {}, sessionId) => new Promise((ok, no) => { … });
const until = (method) => new Promise((ok) => { … });
```

后文用到的只有 `send(...)`、`until("Page.loadEventFired")` 和收尾的 `chrome.kill();`（`:456`）。

**`tests/test_build.py`**：渲染相关的测试都带 `@unittest.skipUnless(FIND_CHROME(), "需要本机 Chrome/Chromium")` 或 `@unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")`。快照测试 `test_snap_renders_both_themes_and_exports_markdown` 断言了四个文件名和宽度：

```python
        for name, width in (("light-500", 500), ("dark-500", 500), ("light-1280", 1280), ("dark-1280", 1280)):
            png = out / f"{name}.png"
            self.assertTrue(png.exists(), name)
            self.assertEqual(png_size(png)[0], width, name)
        self.assertNotEqual((out / "light-1280.png").read_bytes(), (out / "dark-1280.png").read_bytes())
```

**`charts.js` 的滚入绘制**：数据图用 `IntersectionObserver` 在露出 20% 时才画，每个图的 `svg._replay()` 能强制画出（`PROBE` 开头就这么做）。reduced motion 下画的是末帧。视口固定 900px 后，首屏以外的图要先 `_replay()` 再截图。

## Commands you will need

以下命令都在仓库根目录运行。

| Purpose  | Command                                                                                                                                                               | Expected on success |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`                                                                                                            | 末行 `OK`           |
| 语法检查 | `python3 -m py_compile skills/show-me-html/scripts/build.py`                                                                                                          | 无输出              |
| JS 语法  | `node --check skills/show-me-html/scripts/cdp.mjs && node --check skills/show-me-html/scripts/render.mjs && node --check skills/show-me-html/scripts/probe_round.mjs` | 无输出              |
| 文档门禁 | `make check`                                                                                                                                                          | exit 0              |
| 格式化   | `npx prettier --write <file>`                                                                                                                                         | exit 0              |

测试不要用 pytest。本机需要 Chrome 和 Node 22+（内置 `WebSocket`）。

## Scope

**In scope**：

- `skills/show-me-html/scripts/cdp.mjs`（新建）
- `skills/show-me-html/scripts/render.mjs`（新建）
- `skills/show-me-html/scripts/probe_round.mjs`
- `skills/show-me-html/scripts/build.py`
- `skills/show-me-html/tests/test_build.py`
- `skills/show-me-html/SKILL.md`（一行）
- `skills/show-me-html/references/compose-and-check.md`、`references/visual-system.md`、`references/diagrams.md`（各一两句）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**：

- `PROBE` 字符串和 `render_check()` 里从 `m = re.search(...)` 开始的解析代码：017–019 的检查都挂在这里，换的只是「怎么拿到标题」。唯一例外是 Step 4 里 `if not m:` 那一行的报错文字。
- `scripts/gallery.py`：它的截图改走运行器是计划 022，同时加 `--pdf`。本计划不碰它，`build.py` 里的 `chrome_proxy_args()` 也先留着给它用。
- 屏蔽字体、改用兜底字体做检查：维护者否决，阈值是在真实字体下定的。
- 在没有 Node 时退回旧的多次冷启动：维护者决定只留一条路径，没有 Node 和没有 Chrome 一样报「渲染检查未运行」。
- 390px 下的字号、对比度、倍率检查：390 只看横向溢出。

## Git workflow

- 从**本地** `main` 开分支：`git checkout -b advisor/021-show-me-html-cdp-runner main`。
- conventional commits，scope 写技能名。建议按步骤提交，例如 `refactor(show-me-html): probe_round connects through a shared cdp.mjs`、`perf(show-me-html): render check runs in one headless Chrome`、`feat(show-me-html): snapshots come in viewport slices with a section map`。
- 不要 push。

## Steps

### Step 1: 抽出共用的 `scripts/cdp.mjs`，`probe_round.mjs` 改用它

1. 新建 `scripts/cdp.mjs`：

   <!-- prettier-ignore -->
   ```js
   // 共用的无头 Chrome 连接：CDP，Node 22+ 内置 WebSocket，无第三方依赖。render.mjs 与 probe_round.mjs 共用。
   import { spawn } from "node:child_process";
   import { mkdtempSync } from "node:fs";
   import { tmpdir } from "node:os";
   import { join } from "node:path";

   // 无头 Chrome 不读 HTTP(S)_PROXY 环境变量：配了代理就显式传，否则每次直连 Google Fonts。规则同 build.py 的 chrome_proxy_args
   export function proxyArgs(env = process.env) {
     const pick = (...names) => names.map((n) => (env[n] || "").trim()).find(Boolean) || "";
     const proxy = pick("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy");
     const bypass = pick("NO_PROXY", "no_proxy").split(",").map((h) => h.trim()).filter(Boolean);
     if (!proxy || bypass.includes("*")) return [];
     const args = [`--proxy-server=${proxy.replace(/\/$/, "")}`];
     if (bypass.length)
       args.push(`--proxy-bypass-list=${bypass.map((h) => (h.startsWith(".") ? "*" + h : h)).join(";")}`);
     return args;
   }

   // 启动一个无头 Chrome 并连上。返回 send(方法, 参数, sessionId)、until(事件名, {sessionId, timeout})、on(监听)、close()
   export async function launch(chromePath, prefix = "show-me-cdp-") {
     const chrome = spawn(chromePath, [
       "--headless=new",
       "--remote-debugging-port=0",
       "--hide-scrollbars",
       `--user-data-dir=${mkdtempSync(join(tmpdir(), prefix))}`,
       ...proxyArgs(),
       "about:blank",
     ]);
     const wsUrl = await new Promise((ok, no) => {
       let buf = "";
       chrome.stderr.on("data", (d) => {
         buf += d;
         const m = buf.match(/ws:\/\/\S+/);
         if (m) ok(m[0]);
       });
       chrome.on("error", no);
       chrome.on("exit", (code) => no(new Error(`Chrome 启动失败（退出码 ${code}）`)));
     });
     const ws = new WebSocket(wsUrl);
     await new Promise((r) => ws.addEventListener("open", r));
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
           if (m.method !== method || (sessionId && m.sessionId !== sessionId)) return;
           clearTimeout(timer);
           off();
           ok(m);
         });
         const timer = setTimeout(() => {
           off();
           no(new Error(`等 ${method} 超时`));
         }, timeout);
       });
     return { send, until, on, close: () => chrome.kill() };
   }
   ```

2. `scripts/probe_round.mjs`：
   - 删掉 020 加的 `PROXY_ARGS` 那段（从注释 `// 无头 Chrome 不读 HTTP(S)_PROXY 环境变量…` 到 `: [];`）。
   - 删掉从 `const chrome = spawn(CHROME, [` 到 `until` 定义结束（`waiters.push(f);` 之后的 `  });`）的整段，换成一行：

     ```js
     const { send, until, close } = await launch(CHROME, "probe-round-");
     ```

   - 文件末尾附近的 `chrome.kill();` 改为 `close();`。
   - import 区加 `import { launch } from "./cdp.mjs";`，删掉不再用到的 `spawn`、`mkdtempSync`、`tmpdir`（删之前用 `grep -n 'spawn\|mkdtempSync\|tmpdir' skills/show-me-html/scripts/probe_round.mjs` 确认只剩 import 那几处）。`join` 等其余 import 保留。

**Verify**:

- JS 语法检查无输出；`grep -c 'waiters\|pending\|new WebSocket' skills/show-me-html/scripts/probe_round.mjs` → `0`。
- 用最近一轮冻结场景核对探针行为不变：

  ```sh
  R=$(ls -d /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/*/ | tail -1)
  T=$(mktemp -d); mkdir "$T/a" "$T/b"
  cp "$R"/*.html "$T/a/"; cp "$R"/*.html "$T/b/"
  # 旧版：主检出目录（本地 main）里还没改的 probe_round.mjs
  node /Users/mg/github/skills/skills/show-me-html/scripts/probe_round.mjs "$T/a" > /dev/null
  node skills/show-me-html/scripts/probe_round.mjs "$T/b" "$T/a" | tail -8
  ```

  预期：五页摘要行都是 `无问题`，末尾 `与上一轮对比：probe.json 相同`，截图对比没有不同。

### Step 2: 新建运行器 `scripts/render.mjs`

<!-- prettier-ignore -->
```js
// build.py 的 Chrome 运行器：一个无头 Chrome 实例依次跑完一批页面任务（CDP）。
//   node scripts/render.mjs <jobs.json>
// jobs.json：{"chrome": "<Chrome 路径>", "jobs": [任务, …]}。任务字段：
//   url      页面地址（file://…，可带 ?query）
//   width    视口宽，默认 1280；height 视口高，默认 900；dpr 像素比，默认 1
//   mobile   是否按手机模拟（触屏、viewport meta 生效），默认 width < 500
//   theme    "light" / "dark"：页面加载前写 localStorage 的 show-me-theme，并模拟同色的 prefers-color-scheme；
//            不给时只模拟浅色系统配色（本机是暗色外观也一样）
//   reduced  true 时模拟 prefers-reduced-motion: reduce
//   budget   虚拟时间预算（毫秒），默认 4000。有网络请求未完成时虚拟时间暂停（同 --virtual-time-budget）：
//            字体到齐、页面计时器跑满预算才往下走，结果不随网速变
//   eval     预算用完后求值的 JS 表达式，结果放进 value
//   slices   {"prefix": 路径前缀, "height": 每片高}：先把数据图全部画出来，再按整页高度切片截图，存为 前缀-01.png …
//   shot     路径：截当前视口
//   timeout  每个任务的真实时间上限（毫秒），默认 90000
// stdout：与任务一一对应的 JSON 数组，每项 {value, slices: [{path, top, height}], shot, errors: [页面 JS 异常], error: "哪一步失败"}，
// 没用到的字段不出现。Chrome 起不来时退出码 2，原因写 stderr。
import { readFileSync, writeFileSync } from "node:fs";
import { launch } from "./cdp.mjs";

const spec = JSON.parse(readFileSync(process.argv[2], "utf8"));
let cdp;
try {
  cdp = await launch(spec.chrome);
} catch (e) {
  console.error(String(e.message || e));
  process.exit(2);
}
const { send, until, on, close } = cdp;
const results = [];
for (const job of spec.jobs) results.push(await run(job));
process.stdout.write(JSON.stringify(results));
close();
process.exit(0);

async function run(job) {
  const width = job.width || 1280;
  const mobile = job.mobile ?? width < 500;
  const out = { errors: [] };
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
  const S = (method, params) => send(method, params, sessionId);
  const off = on((m) => {
    if (m.sessionId !== sessionId || m.method !== "Runtime.exceptionThrown") return;
    const d = m.params.exceptionDetails;
    out.errors.push(((d.exception && d.exception.description) || d.text || "").split("\n")[0]);
  });
  const ev = async (expression) => {
    const r = await S("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  let step = "打开页面";
  try {
    await S("Page.enable");
    await S("Runtime.enable");
    await S("Emulation.setDeviceMetricsOverride", { width, height: job.height || 900, deviceScaleFactor: job.dpr || 1, mobile });
    if (mobile) await S("Emulation.setTouchEmulationEnabled", { enabled: true });
    // 系统配色也按主题模拟（没给主题按浅色）：没有防闪烁脚本的页面跟随系统配色，结果不随本机外观变
    await S("Emulation.setEmulatedMedia", {
      features: [
        { name: "prefers-reduced-motion", value: job.reduced ? "reduce" : "no-preference" },
        { name: "prefers-color-scheme", value: job.theme === "dark" ? "dark" : "light" },
      ],
    });
    if (job.theme)
      await S("Page.addScriptToEvaluateOnNewDocument", {
        source: `try{localStorage.setItem("show-me-theme",${JSON.stringify(job.theme)})}catch(e){}`,
      });
    step = "等页面稳定";
    await S("Emulation.setVirtualTimePolicy", { policy: "pause" });
    await S("Page.navigate", { url: job.url });
    const settled = until("Emulation.virtualTimeBudgetExpired", { sessionId, timeout: job.timeout || 90000 });
    await S("Emulation.setVirtualTimePolicy", { policy: "pauseIfNetworkFetchesPending", budget: job.budget || 4000 });
    await settled;
    // 预算用完后回到真实时间：截图要等真实的绘制帧
    await S("Emulation.setVirtualTimePolicy", { policy: "advance" });
    if (job.eval) {
      step = "求值";
      out.value = await ev(job.eval);
    }
    if (job.slices) {
      step = "切片截图";
      // 数据图滚入视口才画（charts.js 的 reveal），视口固定 900px 时首屏以外的图还没画
      await ev("document.querySelectorAll('figure[data-chart] svg').forEach(function(s){ if (s._replay) s._replay(); }), 1");
      await new Promise((r) => setTimeout(r, 300));
      const total = await ev("document.documentElement.scrollHeight");
      out.slices = [];
      for (let top = 0, k = 1; top < total; top += job.slices.height, k++) {
        const height = Math.min(job.slices.height, total - top);
        const shot = await S("Page.captureScreenshot", {
          format: "png",
          captureBeyondViewport: true,
          clip: { x: 0, y: top, width, height, scale: 1 },
        });
        const path = `${job.slices.prefix}-${String(k).padStart(2, "0")}.png`;
        writeFileSync(path, Buffer.from(shot.data, "base64"));
        out.slices.push({ path, top, height });
      }
    }
    if (job.shot) {
      step = "截图";
      const shot = await S("Page.captureScreenshot", { format: "png" });
      writeFileSync(job.shot, Buffer.from(shot.data, "base64"));
      out.shot = job.shot;
    }
  } catch (e) {
    out.error = `${step}：${e.message || e}`;
  } finally {
    off();
    await send("Target.closeTarget", { targetId }).catch(() => {});
  }
  return out;
}
```

**Verify**: JS 语法检查无输出。手动跑一次（换成本机 Chrome 路径；Linux 上用 `which google-chrome`）：

```sh
T=$(mktemp -d)
cp skills/show-me-html/tests/fixtures/component-states.html "$T/p.html"
python3 skills/show-me-html/scripts/build.py "$T/p.html" --no-render > /dev/null
python3 - "$T" <<'EOF'
import json, pathlib, runpy, sys
T = pathlib.Path(sys.argv[1])
chrome = runpy.run_path("skills/show-me-html/scripts/build.py")["find_chrome"]()
url = (T / "p.html").as_uri()
(T / "jobs.json").write_text(json.dumps({"chrome": chrome, "jobs": [
    {"url": url, "eval": "document.fonts.status + ' ' + document.title"},
    {"url": url, "width": 390, "theme": "dark", "reduced": True, "slices": {"prefix": str(T / "s"), "height": 1500}},
]}), encoding="utf-8")
EOF
node skills/show-me-html/scripts/render.mjs "$T/jobs.json"; echo; ls "$T"/s-*.png | head -3
```

预期：打印一个两项的 JSON 数组；第一项 `value` 以 `loaded ` 开头，`errors` 为空；第二项有 `slices`，`s-01.png` 存在。

### Step 3: `build.py` 加 `run_jobs()`

在 `find_chrome()` 和 `chrome_proxy_args()` 之后（`render_check` 之前）加：

```python
RENDER_SCRIPT = Path(__file__).resolve().parent / "render.mjs"


def run_jobs(jobs):
    """在一个无头 Chrome 实例里依次跑完 jobs（scripts/render.mjs，走 CDP），返回 (结果列表, 错误信息)。
    任务与结果的字段见 render.mjs 文件头。找不到 Chrome 或 node 时返回 (None, None)：调用方按「这道关没跑」处理。"""
    import json, shutil, subprocess, tempfile
    chrome, node = find_chrome(), shutil.which("node")
    if not chrome or not node:
        return None, None
    with tempfile.TemporaryDirectory() as td:
        spec = Path(td) / "jobs.json"
        spec.write_text(json.dumps({"chrome": chrome, "jobs": jobs}, ensure_ascii=False), encoding="utf-8")
        try:
            out = subprocess.run([node, str(RENDER_SCRIPT), str(spec)], capture_output=True, text=True,
                                 timeout=90 * len(jobs) + 30)
        except subprocess.TimeoutExpired:
            return None, "Chrome 运行器超时"
    if out.returncode:
        return None, (out.stderr.strip().splitlines() or [f"运行器退出码 {out.returncode}"])[-1]
    return json.loads(out.stdout), None
```

把 `:1035` 那行注释 `# 无头 Chrome 把窗口宽度钳在 500px，比这更窄的视口测不到 —— 390px 只能人眼验。` 改为：

```python
# 390 用 CDP 的手机模拟（--window-size 最窄只到 500px，模拟不受这个限制），只查横向溢出、报 WARN；
# 字号、对比度、倍率这些检查只在 500 / 1024 / 1280 跑。
```

**Verify**: 语法检查无输出；`python3 -c "import runpy; r = runpy.run_path('skills/show-me-html/scripts/build.py')['run_jobs']([]); print(r)"` → `([], None)`。

### Step 4: 渲染检查改走运行器

在 `render_check()` 里：

1. 开头的

   ```python
       import html as htmllib, subprocess, tempfile
       chrome = find_chrome()
       if not chrome:
           return [], [], [], False
   ```

   改为

   ```python
       import html as htmllib, tempfile
   ```

2. 把 `for w in widths:` 这一行和紧跟着的 `try: … except Exception as e: return [f"渲染检查跑不起来：{e}"], [], [], False` 整块（到 `return` 那一行为止）替换为下面这段，缩进 8 个空格，与原来的 `for` 对齐。原来 `for` 循环体里 `m = re.search(...)` 及之后的代码保持原样，仍在新的 `for` 循环体里：

   ```python
           # 一个 Chrome 依次跑完所有宽度（scripts/render.mjs）。PROBE 把结果写进 <title>；包回 --dump-dom 的样子，
           # 下面的正则与 unescape 原样沿用。读标题元素的文本而不是 document.title：后者会合并连续空格。
           # reduced motion 下量末帧，与 gallery.py 的探针、--snap 一致：逐帧布局的图（如 G11 力导向图）
           # 在无头 Chrome 里不一定跑完，量到的是节点还在原点的中间状态
           title = "(document.querySelector('head > title') || {}).textContent || ''"
           results, err = run_jobs([{"url": probe.as_uri(), "width": w, "reduced": True, "eval": title}
                                    for w in (390, *widths)])
           if results is None:  # err 为空：没有 Chrome 或 node，这道关没跑；err 非空：运行器出错，记 ERROR
               return ([f"渲染检查跑不起来：{err}"] if err else []), [], [], False
           wrap = lambda r: "<title>" + htmllib.escape(r.get("value") or "", quote=False) + "</title>"
           # 390（手机）只看横向溢出，报 WARN：字号类检查在 500px 已经量过窄版
           phone = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|", wrap(results[0]), re.S)
           if phone and int(phone.group(1)) > int(phone.group(2)) + 1:
               who = htmllib.unescape(phone.group(3).strip())
               notes.append(f"390px（手机）视口横向溢出：文档宽 {phone.group(1)}px" + (f"；越界元素：{who}" if who else "")
                            + "。手机上要横向拖动整页，把越界元素收窄或放进局部滚动容器（visual-system.md「响应式与打印」）")
           for w, r in zip(widths, results[1:]):
               out = wrap(r)
   ```

   运行器出错时的返回与原来 `except` 分支一致：一条 ERROR，`ran=False`。

3. 循环体里

   ```python
                   issues.append(f"{w}px：探针没返回结果（页面 JS 可能报错，去控制台看）")
   ```

   改为（缩进不变）：

   ```python
                   why = r.get("error") or "；".join(r.get("errors", [])[:2]) or "页面没写回结果"
                   issues.append(f"{w}px：探针没返回结果（{why}）")
   ```

4. `main()` 里两句提示改为：

   ```python
       if rendered:
           print(f"渲染检查：{' / '.join(f'{w}px' for w in measured)} 无横向溢出；390px 手机视口另查，溢出只报 WARN。")
       elif not args.no_render:
           print("渲染检查未运行：找不到 Chrome/Chromium 或 node。横向溢出没有被验证过，"
                 "自己在浏览器里拉一遍窄屏，不要报「已验证」。")
   ```

**Verify**: 语法检查无输出；`grep -c 'subprocess' skills/show-me-html/scripts/build.py` 比改前少 1（`render_check` 不再用它）；全量单元测试 → `OK`，测试数与改前相同（017–019 的渲染测试原样通过，这是检查结果没变的第一道证据）。

### Step 5: 快照改成切片，加 `--snap-theme` / `--snap-width`

1. 删掉 `SNAP_PROBE` 字符串和 `SNAP_MAX_H` 常量（连同它们上方「整页快照（--snap）」那段注释的后两行），把 `snap_page()` 整个替换为：

   ```python
   # ── 整页快照（--snap）──────────────────────────────────────────────
   # 眼睛关的替身：agent 没有交互浏览器，但能读图。每个主题 × 宽度按视口高度切片截图（长图读进来会被降采样），
   # 每片写明含哪几节，小修后只重读受影响的那几片；外加页面自带导出器的 Markdown。
   SNAP_EVAL = """(function(){
     var heads = [].map.call(document.querySelectorAll('#doc h2'), function(h){
       return [Math.round(h.getBoundingClientRect().top + scrollY), h.textContent.replace(/\\s+/g, ' ').trim()];
     });
     return {md: window.showMeMarkdown ? window.showMeMarkdown() : null, heads: heads};
   })()"""
   SNAP_SLICE = {390: 1600, 500: 1600}  # 每片高度：读图时不被明显降采样（2026-10 实测 1280×1500、500×1600 读得清）；其余宽度 1500


   def snap_page(page, out_dir, widths=(390, 500, 1280), themes=("light", "dark")):
       """返回 (输出列表 [(路径, 说明)], 提示信息列表, 错误信息或 None)。"""
       out_dir.mkdir(parents=True, exist_ok=True)
       md_from = ("light" if "light" in themes else themes[0], max(widths))
       jobs = [{"url": page.resolve().as_uri(), "width": w, "theme": t, "reduced": True, "eval": SNAP_EVAL,
                "slices": {"prefix": str(out_dir / f"{t}-{w}"), "height": SNAP_SLICE.get(w, 1500)}}
               for t in themes for w in widths]
       results, err = run_jobs(jobs)
       if results is None:
           return [], [], err or "找不到 Chrome/Chromium 或 node"
       outs, notes = [], []
       for job, r in zip(jobs, results):
           if r.get("error"):
               return outs, notes, f"{job['theme']} {job['width']}px：{r['error']}"
           heads = r["value"]["heads"]
           for s in r["slices"]:
               names = [h for top, h in heads if s["top"] <= top < s["top"] + s["height"]]
               about = "含：" + "、".join(names) if names else ("（页首）" if s["top"] == 0 else "（接上一片）")
               outs.append((Path(s["path"]), about))
           if (job["theme"], job["width"]) == md_from:
               md = out_dir / "export.md"
               md.write_text(r["value"]["md"] or "", encoding="utf-8")
               outs.append((md, ""))
               if r["value"]["md"] is None:
                   notes.append("页面没有 window.showMeMarkdown：导出器缺失，export.md 为空")
       return outs, notes, None
   ```

2. `main()` 里 `--snap` 的 help 改为 `"自检通过后按 light/dark × 390/500/1280px 切片截图（每片约一屏多高，输出时写明每片含哪几节），并导出 Markdown 到 export.md；不给 DIR 时写到新建的临时目录。供眼睛关读图用"`，并在它后面加两个参数：

   ```python
       ap.add_argument("--snap-theme", choices=("light", "dark", "both"), default="both",
                       help="--snap 拍哪个主题，默认 both；小修只拍受影响的主题")
       ap.add_argument("--snap-width", default="390,500,1280", metavar="W[,W…]",
                       help="--snap 拍哪些视口宽度（px），逗号分隔，默认 390,500,1280；小于 500 按手机模拟")
   ```

   在 `args = ap.parse_args()` 之后加校验：

   ```python
       try:
           snap_widths = tuple(int(x) for x in args.snap_width.split(",") if x.strip())
       except ValueError:
           snap_widths = ()
       if not snap_widths or any(not 320 <= w <= 2560 for w in snap_widths):
           ap.error("--snap-width 要写 320–2560 之间的整数，逗号分隔，例如 390,1280")
   ```

3. `main()` 里 `--snap` 那段改为：

   ```python
       if args.snap is not None:
           import tempfile
           out_dir = Path(args.snap) if args.snap else Path(tempfile.mkdtemp(prefix=f"show-me-snap-{args.page.stem}-"))
           themes = ("light", "dark") if args.snap_theme == "both" else (args.snap_theme,)
           outs, notes, err = snap_page(args.page, out_dir, snap_widths, themes)
           for path, about in outs:
               print(f"已快照  {path}" + (f"  {about}" if about else ""))
           for n in notes:
               print(f"注意    {n}")
           if err:
               print(f"--snap 未完成：{err}")
   ```

**Verify**: 语法检查无输出；`grep -c 'SNAP_MAX_H\|SNAP_PROBE' skills/show-me-html/scripts/build.py` → `0`；`python3 skills/show-me-html/scripts/build.py x.html --snap-width 100` → 退出码 2，stderr 含 `--snap-width 要写`。

### Step 6: `--shot` 改走运行器

`shoot_sheets()` 改成先写好每张卡的临时文件、收集任务，再一次交给运行器。替换为：

```python
def shoot_sheets(page, theme="light", scale=2):
    """把每张 .sheet 渲染成 PNG：按卡的尺寸开视口，隐藏 chrome 与桌面，两倍像素。
    返回 (输出文件列表, 错误信息)。"""
    import tempfile
    html = page.read_text(encoding="utf-8")
    # 只数 class 里独立的 sheet 一词：sheet-stage / sheet-body 不算
    n = len(re.findall(r'class=["\'](?:[^"\']*\s)?sheet(?:\s[^"\']*)?["\']', html))
    if not n:
        return [], "页面里没有 .sheet"
    w, h = sheet_size(html)
    jobs = []
    with tempfile.TemporaryDirectory() as td:
        for i in range(n):
            hide = "".join(
                f".sheet-stage:nth-of-type({j + 1}){{display:none!important}}" for j in range(n) if j != i
            )
            themed = html.replace(
                "<head>",
                f'<head><script>try{{localStorage.setItem("show-me-theme","{theme}")}}catch(e){{}}</script>', 1,
            ) + SHOT_CSS + f"<style>{hide}</style>"
            probe = Path(td) / f"shot-{i}.html"
            probe.write_text(themed, encoding="utf-8")
            suffix = f"-{i + 1}" if n > 1 else ""
            out = page.with_name(f"{page.stem}{suffix}{'-dark' if theme == 'dark' else ''}.png")
            jobs.append({"url": probe.as_uri(), "width": w, "height": h, "dpr": scale, "mobile": False, "shot": str(out)})
        results, err = run_jobs(jobs)
    if results is None:
        return [], err or "找不到 Chrome/Chromium 或 node"
    outs = []
    for job, r in zip(jobs, results):
        if r.get("error"):
            return outs, f"截图失败：{r['error']}"
        outs.append(Path(job["shot"]))
    return outs, None
```

**Verify**: 语法检查无输出；`grep -c -- '--headless' skills/show-me-html/scripts/build.py` → `0`（`build.py` 里不再直接启动 Chrome）；`grep -c 'chrome_proxy_args()' skills/show-me-html/scripts/build.py` → `0`（020 加在 `snap_page`、`shoot_sheets`、`render_check` 里的三处调用都已随旧代码删掉，代理改由 `cdp.mjs` 处理；函数定义留给 `gallery.py`，022 再删）。

### Step 7: 测试

1. 文件顶部 `FIND_CHROME = …` 之后加一行：

   ```python
   RENDERER = bool(FIND_CHROME() and shutil.which("node"))
   ```

   然后把文件里**所有**渲染测试的装饰器 `@unittest.skipUnless(FIND_CHROME(), "需要本机 Chrome/Chromium")` 和 `@unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")` 换成 `@unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")`。先 `grep -c '需要本机 Chrome/Chromium"' skills/show-me-html/tests/test_build.py` 记下改前的个数 N。

2. `test_snap_renders_both_themes_and_exports_markdown` 里，把断言四个文件名的那个 `for` 循环和紧跟的 `assertNotEqual` 换成：

   ```python
           for name, width in (("light-390", 390), ("dark-390", 390), ("light-500", 500), ("dark-500", 500),
                            ("light-1280", 1280), ("dark-1280", 1280)):
               png = out / f"{name}-01.png"
               self.assertTrue(png.exists(), name)
               self.assertEqual(png_size(png)[0], width, name)
           self.assertNotEqual((out / "light-1280-01.png").read_bytes(), (out / "dark-1280-01.png").read_bytes())
           self.assertIn("light-1280-01.png  含：第二节", result.stdout)
   ```

   其余断言（`export.md` 那几行）不动。

3. 在它后面加三个测试：

   ```python
       @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
       def test_snap_narrows_to_one_theme_and_width(self):
           page = self.copy_fixture()
           out = page.parent / "snap"
           result = run_build(page, "--snap", str(out), "--snap-theme", "dark", "--snap-width", "1280")
           self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
           self.assertEqual(sorted(p.name for p in out.glob("*.png")), ["dark-1280-01.png"])
           self.assertTrue((out / "export.md").exists())

       @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
       def test_render_check_warns_on_phone_overflow_only(self):
           """390 按手机模拟：420px 宽的块在 500 及以上放得下，只在 390 溢出，报 WARN 不报 ERROR。"""
           page = self.copy_fixture()
           html = page.read_text(encoding="utf-8").replace(
               "</main>", '<section><div style="width: 420px">定宽的块</div></section></main>')
           page.write_text(html, encoding="utf-8")
           result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
           self.assertEqual(result.returncode, 0, result.stdout)
           self.assertIn("WARN   390px（手机）视口横向溢出", result.stdout)
           self.assertNotIn("ERROR", result.stdout)

       @unittest.skipIf(shutil.which("node", path="/usr/bin:/bin"), "/usr/bin 里有 node，造不出没有 node 的环境")
       def test_render_check_reports_not_run_without_node(self):
           page = self.copy_fixture()
           result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True,
                                   check=False, env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home())})
           self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
           self.assertIn("渲染检查未运行：找不到 Chrome/Chromium 或 node", result.stdout)
   ```

**Verify**: `grep -c 'skipUnless(RENDERER' skills/show-me-html/tests/test_build.py` → N + 2；全量单元测试 → `OK`，测试数比执行前多 3。（advisor 用最小夹具实测过：这个 420px 的块在 390 下右缘 420px、文档宽 421px，在 500 下不溢出。）

### Step 8: 文档

1. `SKILL.md`「交付与反馈」之前那段里，

   `新页验证主题、窄屏、实际交互、打印与导出：用 `--snap` 产出的双主题截图与 export.md 做眼检；小修检查受影响行为，可复用同一页面未改变部分的已有证据。`

   改为：

   <!-- prettier-ignore -->
   ```markdown
   新页验证主题、窄屏、实际交互、打印与导出：用 `--snap` 产出的双主题切片截图（390 / 500 / 1280）与 export.md 做眼检；小修用 `--snap-theme`、`--snap-width` 只拍受影响的主题和宽度，按输出里每片的「含：…」只重读受影响的切片，可复用同一页面未改变部分的已有证据。
   ```

2. `references/compose-and-check.md`：
   - 「渲染级」那一条（`装了 Chrome/Chromium 就在 500、1024 与 1280px 下实际渲染…`到`…390px 这一档只能人眼看。`三行）改为：

     <!-- prettier-ignore -->
     ```markdown
     - **渲染级**：装了 Chrome/Chromium 和 node 就用一个无头 Chrome 在 500、1024 与 1280px 下实际渲染，检出横向溢出并点名越界元素；390px 按手机模拟，只查横向溢出、报 WARN。
       找不到浏览器或 node 时会明说这道关没跑 —— 那就自己拉一遍窄屏，**不要报「已验证」**。
     ```

   - 「眼睛关」第一段里 `逐张读取打印出的 4 张 PNG（light/dark × 500/1280）` 改为 `逐张读取打印出的切片 PNG（light/dark × 390/500/1280，每片一屏多高，行尾写着这片含哪几节）`；同一句里 `交互（拖拽、键盘、折叠）与 390px 仍需真实浏览器` 改为 `交互（拖拽、键盘、折叠）仍需真实浏览器`。
   - `拉到 390px 看一遍：没有被挤成竖条的文字，没有贴边（这一档脚本测不到）。` 改为 `看 390 的切片：没有被挤成竖条的文字，没有贴边（脚本只报整页溢出，挤压和贴边靠眼睛）。`

3. `references/visual-system.md`「响应式与打印」：`- 自动几何检查跑 500、1024 和 1280px；390px 保留人工门禁。` 改为 `- 自动几何检查跑 500、1024 和 1280px；390px 按手机模拟只查横向溢出（WARN），挤压与贴边靠人眼看切片。`

4. `references/diagrams.md`：`（9px 的下限缩到九成左右还能过）；被隐藏的那版不量。390px 测不到，窄版的 viewBox 宽度按上面的范围控制。` 里的 `390px 测不到` 改为 `390px 只查横向溢出、不量字号`。

5. `npx prettier --write skills/show-me-html/SKILL.md skills/show-me-html/references/compose-and-check.md skills/show-me-html/references/visual-system.md skills/show-me-html/references/diagrams.md`

**Verify**: `make check` → exit 0；`grep -rn '最窄只到 500px\|4 张 PNG\|390px 测不到\|390px 保留人工门禁' skills/show-me-html/SKILL.md skills/show-me-html/references` → 无输出。

### Step 9: 对照验收

1. **检查结果不变**：同一批页面分别用合入前的 `build.py`（主检出目录，也就是本地 `main`）和本分支的 `build.py` 构建，比较 ERROR / WARN 行。

   ```sh
   OLD=/Users/mg/github/skills/skills/show-me-html/scripts/build.py
   NEW=skills/show-me-html/scripts/build.py
   R=$(ls -d /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/*/ | tail -1)
   T=$(mktemp -d)
   for f in "$R"*.html skills/show-me-html/tests/fixtures/component-states.html skills/show-me-html/tests/fixtures/diagram-variants.html; do
     n=$(basename "$f" .html); cp "$f" "$T/$n-old.html"; cp "$f" "$T/$n-new.html"
     python3 "$OLD" "$T/$n-old.html" | grep -E '^(ERROR|WARN)' | sort > "$T/$n.old"
     python3 "$NEW" "$T/$n-new.html" | grep -E '^(ERROR|WARN)' | grep -v '390px（手机）' | sort > "$T/$n.new"
     cmp -s "$T/$n.old" "$T/$n.new" && echo "$n 相同" || { echo "$n 不同"; diff "$T/$n.old" "$T/$n.new"; }
   done
   python3 /Users/mg/github/skills/skills/show-me-html/scripts/gallery.py --out "$T/g-old" | head -3
   python3 skills/show-me-html/scripts/gallery.py --out "$T/g-new" | head -3
   grep -h '390px（手机）' <(for f in "$T"/*-new.html; do python3 "$NEW" "$f" --check-only; done) | sort -u
   ```

   **Verify**: 每页一行 `相同`；两次 gallery 构建的前三行相同（都是一条 `超过 400 KB` 的 WARN 和 `自检通过（1 个警告需逐条判断）。`）。最后一条命令列出新出现的 390 WARN：有的话原样写进汇报，不要修页面。

2. **快照能读**：

   ```sh
   S=$(mktemp -d)
   cp "$R/status-report.html" "$S/p.html"
   /usr/bin/time -p python3 "$NEW" "$S/p.html" --snap "$S/snap" 2>&1 | tail -12
   ```

   **Verify**: 列出 `light-390-01.png …`、`dark-1280-01.png …` 和 `export.md`，每个切片行末有 `含：…`、`（页首）` 或 `（接上一片）`（advisor 实测 status-report 的 `light-1280-01.png  含：分组进展、风险`、`light-1280-02.png  含：下一步`）；打开 `light-1280-01.png` 和 `light-390-01.png` 看一眼：数据图已画出、没有截到动画中途、手机宽度下版式是单栏。把 `real` 秒数写进汇报（advisor 在 scratchpad 里实测：拍 390、1280 两种宽度、带代理 13.8 秒；`2f0e439` 的 `build.py` 同一命令不带代理 266.8 秒）。

3. **幻灯片高度**：

   ```sh
   python3 - "$S/deck.html" <<'EOF'
   import pathlib, re, sys
   shell = pathlib.Path("skills/show-me-html/assets/shell.html").read_text(encoding="utf-8")
   slides = "".join(f'<section class="slide"><h2>第 {i} 张</h2><p>内容</p></section>' for i in range(1, 4))
   page = re.sub(r'<main id="doc">.*?</main>', '<main id="doc">' + slides + '</main>',
                 shell.replace("PAGE TITLE", "幻灯").replace("choose-a-recipe", "slide-deck"), count=1, flags=re.S)
   pathlib.Path(sys.argv[1]).write_text(page, encoding="utf-8")
   EOF
   python3 "$NEW" "$S/deck.html" --snap "$S/deck" --snap-theme light --snap-width 1280 | grep 已快照
   ```

   **Verify**: 打开 `light-1280-01.png`、`-02.png`：每张幻灯片一屏高（约 900px），不是被拉成整页高。

4. **冻结场景轮次**：按 `skills/show-me-html/scenarios/README.md` 的流程新建一轮（目录名后缀 `-021`），五页构建、跑 `probe_round.mjs` 对上一轮。**Verify**: 五页 `自检通过`，探针五行 `无问题`。

## Test plan

- 改：`test_snap_renders_both_themes_and_exports_markdown` 改断言切片文件名、390 / 500 / 1280 宽度和「含：第二节」。
- 新增：`test_snap_narrows_to_one_theme_and_width`（`--snap-theme`、`--snap-width` 只出一组切片）、`test_render_check_warns_on_phone_overflow_only`（390 溢出报 WARN、不失败）、`test_render_check_reports_not_run_without_node`（没有 node 时明说没跑）。
- 不改但必须原样通过：017–019 留下的所有 `test_render_check_*`。它们是「换了传输方式、检查结果不变」的主要证据。
- `probe_round.mjs` 的连接代码换成 `cdp.mjs`：靠 Step 1 的新旧对照。

## Done criteria

- [ ] 全量单元测试末行 `OK`，测试数比执行前多 3，没有跳过渲染测试（本机有 Chrome 和 node）
- [ ] `grep -c -- '--headless' skills/show-me-html/scripts/build.py` → `0`
- [ ] `grep -c 'SNAP_MAX_H\|SNAP_PROBE' skills/show-me-html/scripts/build.py` → `0`
- [ ] JS 语法检查三个文件无输出；`grep -c 'waiters' skills/show-me-html/scripts/probe_round.mjs` → `0`
- [ ] Step 1 新旧 `probe_round` 对照：`probe.json 相同`、截图无不同
- [ ] Step 9 第 1 小步每页 `相同`，gallery 两次构建前三行相同
- [ ] Step 9 第 2、3 小步的切片看过，汇报里写了 `--snap` 耗时和新出现的 390 WARN（没有就写「无」）
- [ ] `make check` exit 0；`git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- Drift check 里 020、018、019 任何一份未合入。
- Step 2 的手动运行里第一项的 `value` 不是以 `loaded ` 开头（字体没到齐就测量了），或者一直等到超时：说明 `Emulation.setVirtualTimePolicy` 在本机 Chrome 上不按预期工作。不要改成固定等几秒，汇报 Chrome 版本（`"<Chrome 路径>" --version`）和运行器输出。
- Step 4 之后已有的 `test_render_check_*` 有任何一个失败，或 Step 9 第 1 小步出现 `不同`：说明拿到的标题和 `--dump-dom` 不一致。汇报 diff，不要改 `PROBE` 或正则去迁就。
- 切片截图里首屏以外的数据图是空的，或幻灯片仍被拉成整页高。
- 你发现需要改 `gallery.py` 才能让本计划的测试通过。

## Maintenance notes

- 运行器的任务字段是 `build.py` 和 `render.mjs` 之间的接口，文件头注释是唯一说明。计划 022 会给它加 `pdf` 字段并让 `gallery.py` 改用它；计划 025（单页交互探针）直接用 `cdp.mjs`。
- `PROBE` 仍然只通过 `<title>` 交回结果，后续计划（例如 023 的越框检查）继续在末尾追加 `|` 分段和命名分组即可。以后想改成直接返回 JSON，那是另一份计划：要同时改 `PROBE` 末尾和全部解析代码。
- 一次构建最多启动两次 Chrome：渲染检查一次，自检通过后 `--snap` 或 `--shot` 各一次。每次都是新配置，字体各拉一次；带代理时这部分在一两秒内。
- 虚拟时间预算仍是 4000ms，和改前一致。页面里的计时器超过这个时长才出现的内容，检查和快照都看不到，和改前一样。
- 运行器总是模拟 `prefers-color-scheme`（给了主题就按主题，没给按浅色）。改前无头 Chrome 跟随本机外观：缺防闪烁主题脚本的夹具在暗色外观的机器上会渲染成暗色（advisor 用表格样张复现过）。
- 渲染检查改在 reduced motion 下跑（改前没有模拟）。advisor 在 scratchpad 里对比过：五个冻结场景、组件夹具、宽窄两版图夹具和 gallery 总览页的 ERROR / WARN 与不模拟时完全相同；计划 023 的越框检查需要它，否则 G11 力导向图在节点还没布局时会被误报 20 处越框。
- 审阅时重点看：`render_check` 里从 `m = re.search(...)` 往下的代码 diff 只有 `if not m:` 那一处；`snap_page` 的 Markdown 来自 light、最宽那一组。
