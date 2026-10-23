# Plan 021: show-me-html 一次构建只启动一个无头 Chrome：渲染检查、快照切片与定尺卡截图改走 CDP 运行器

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat a2c1798..HEAD -- skills/show-me-html/scripts skills/show-me-html/tests/test_build.py skills/show-me-html/SKILL.md skills/show-me-html/README.md skills/show-me-html/references/compose-and-check.md skills/show-me-html/references/visual-system.md skills/show-me-html/references/diagrams.md` → 无输出。再确认 020、018、019 都在：
>
> - `grep -c 'def chrome_proxy_args' skills/show-me-html/scripts/build.py` → `1`（020）
> - `grep -c '(?P<contrast>' skills/show-me-html/scripts/build.py` → `1`（018）
> - `grep -c '(?P<scaled>' skills/show-me-html/scripts/build.py` → `1`，且 `grep -n 'render_issues, render_notes, measured, rendered = render_check' skills/show-me-html/scripts/build.py` 有一行（019）
>
> 三条有任何一条不满足就是 STOP 条件。drift check 有输出时，对照下面「Current state」里的引文；引文找不到也是 STOP 条件。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。
>
> **派发前复核（advisor，2026-10-22，`a2c1798`）**：020、018、019 均已合入，「Current state」的引文与 HEAD 逐字一致，行号已按 `a2c1798` 更新。一位没看过本计划上下文的审阅者把初版计划原样套到副本上跑了一遍，复现出两处初版验证发现不了的错误：一是运行器 stdout 超过 64 KB 被截断，长页面 `--snap` 直接崩溃；二是 `--shot` 的卡片被缩到 0.95 倍，右侧和底部露白。另有几处问题：Node 太旧时构建失败并留下孤儿 Chrome、每次运行留下几十 MB 的 Chrome 配置目录、漏了 `--no-sandbox`。下面的代码块、测试和验证步骤已经改好，照原样执行即可。
>
> - 全量单元测试：执行前 `Ran 51 tests`，执行后 `Ran 56 tests`。

## Status

- **Priority**: P1
- **Effort**: L（两个新 Node 脚本、`build.py` 三个函数换传输方式、两个新参数、测试与五份文档）
- **Risk**: MED（渲染检查的等待机制换了实现；快照文件名从 `light-500.png` 变成切片；390px 新增一条 WARN）
- **Depends on**: `plans/020-show-me-html-chrome-proxy.md`、`plans/018-show-me-html-text-contrast.md`、`plans/019-show-me-html-chart-scale-warn.md` 都已合入（维护者定的顺序：020 → 018 → 019 → 021）
- **Category**: perf
- **Planned at**: commit `2f0e439`, 2026-10-22；`a2c1798` 复核并修订

## Why this matters

show-me-html 的 `scripts/build.py` 每次构建都要用无头 Chrome 渲染页面做检查，而现在每个任务都冷启动一次 Chrome：

- 渲染检查在 500 / 1024 / 1280px 各启动一次；
- `--snap` 在 light/dark × 500/1280 每种组合启动两次（一次量页高，一次截图）。

合计 11 次，每次都是全新配置，没有字体缓存。2026-10-22 在维护者本机用一页 status-report 实测，`--snap` 全流程要 119.8 秒；一次 32 分钟的会话里，有 20.5 分钟在等 Chrome。

advisor 在 scratchpad 里试过另一种做法：只开一个 Chrome 实例，走 CDP（Chrome DevTools Protocol，Node 内置的 WebSocket 就能连）。

- 同一页面跑 3 次检查再加切片截图，带代理时总共约 4 秒。
- 检查结果与现在的 `--dump-dom` 逐字相同，字体也已加载完。

之后又把本计划初版 Step 2–7 的代码原样套到 `2f0e439` 的副本上（当时 018/019 尚未合入，返回值临时改成了 019 的形状）：

- 当时的 51 个单元测试全部通过，用时从约 70 秒降到 32 秒。
- status-report 页 `--snap` 用 13.8 秒，改前 266.8 秒。那次只拍了 390、1280 两种宽度；本计划默认再加 500，会多几秒。

本计划把渲染检查、`--snap`、`--shot` 都换成同一个流程：Python 写任务清单，Node 运行器在一个 Chrome 里依次执行，返回 JSON。检查脚本 `PROBE` 和解析它的正则一行不改。

同一次改动顺带解决快照的几个问题。前三条来自交给维护者的方案；第四条中「390 进渲染检查、溢出只报 WARN」是维护者 2026-10-22 明确确认的：

- **快照按视口高度切片**：现在是整页一张长图。1280 宽时高 5840px；500 宽时超过 16000px，会被截断。读图工具会把长图降采样，细节看不清。改为每片 1500px 高（窄屏 1600px），输出时写明每片含哪几节（h2），小修后只重读那一两片即可。16000px 的截断随之消失。
- **视口高度不再被拉长**：现在截图前会把窗口拉到整页高度，页面里的 `100dvh`（幻灯片每张一屏）就跟着变成整页高。改为视口固定 900px、按区域裁切截图，截出来的就是读者看到的样子。advisor 用三张幻灯片的页面实测，改后每张仍是 900px。
- **`--snap-theme`、`--snap-width` 缩小拍摄范围**：小修只拍受影响的主题和宽度。
- **390px 手机宽度进自动检查**：
  - `--window-size` 最窄只到 500px；CDP 的设备模拟没有这个限制，`scripts/probe_round.mjs` 一直在用 390。
  - 渲染检查加一个 390 视口，只查横向溢出，报 WARN，不让现在能通过的页面失败。
  - `--snap` 默认宽度在原有的 500、1280 之外加上 390。500 照拍，它是 500–900px 中等宽度（例如看板变成两列）唯一的默认截图。维护者 2026-10-22 决定保留 500，不要去掉。

## Current state

技能目录是 `skills/show-me-html/`，下文路径都相对这个目录，行号按 `a2c1798`。

### `scripts/build.py`

**`render_check()`（`:1134` 起）**：开头、传输部分和结尾如下。中间的解析部分由 017–019 逐段追加，本计划不动。

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
        probe.write_text(html.replace(…) + PROBE, encoding="utf-8")   # 018 写的，原样保留
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

**`PROBE`（`:804` 起）**：追加在页面末尾的一段脚本。页面 `load` 后等 1500ms，把测量结果用 `|` 分段写进 `document.title`，开头是 `PROBE|文档宽|视口宽|…`。

- 现在靠 `--dump-dom` 打印整个 DOM，再用上面的正则从 `<title>` 里取结果。
- `--dump-dom` 打印时会转义标题里的 `<`、`>`、`&`，所以后面的解析都先 `htmllib.unescape(...)`。
- **这个约定和正则在本计划里原样保留。**

**`--virtual-time-budget=4000`**：

- 含义：Chrome 用虚拟时间跑页面。有网络请求未完成时虚拟时间暂停，直到页面的计时器跑满 4000 虚拟毫秒。这保证 `PROBE` 的 1500ms 计时器触发时字体已到齐。
- CDP 里同一机制是 `Emulation.setVirtualTimePolicy`（`policy: "pauseIfNetworkFetchesPending"`，`budget`），预算用完时发 `Emulation.virtualTimeBudgetExpired` 事件。
- advisor 实测，这样等到的标题与 `--dump-dom` 相同，`document.fonts.status` 为 `loaded`。

**快照代码（`:1028` 起）**：

- 从注释行 `# ── 整页快照（--snap）──…` 开始，依次是四行注释、`SNAP_PROBE` 字符串、`SNAP_MAX_H = 16000`、`snap_page()`（`:1043`），到 `return outs, notes, None` 结束；其后是 `CHROME_PATHS = (`。
- 每个主题 × 宽度先用 `--dump-dom` 跑一次 `SNAP_PROBE`，量出 `scrollHeight` 并取 `window.showMeMarkdown()` 的结果，再按这个高度开窗截整页。
- `light` 且最宽的那一次，Markdown 写进 `export.md`。

**`SHOT_CSS`（`:969`）与 `shoot_sheets()`（`:989`）**：

- 每张 `.sheet` 写一份只显示这张卡的临时 HTML：`<head>` 开头插一段写 localStorage 主题的 `<script>`，**文件末尾**（`</html>` 之后）追加 `SHOT_CSS`（隐藏 chrome，去掉版心的 padding）和隐藏其他卡的 `<style>`。
- 然后按卡的尺寸开窗，用 `--force-device-scale-factor=2` 截图，输出到页面旁边，文件名 `<页面名>[-序号][-dark].png`。
- `:1018` 的注释写明为什么要带 `--no-sandbox`：`# --no-sandbox：macOS 与普通用户下不需要，Linux 容器里以 root 跑 Chrome 时不加会直接退出`。`render_check` 也带这个参数。

**`assets/shell.js` 开头的 `fit()`**：

- 视口比卡窄时，它把 `.sheet` 等比缩小：`k = stage.clientWidth / s.offsetWidth`，`k < 1` 时设 `transform: scale(k)`。
- `fit()` 在脚本执行时跑一次，之后只在 `resize` 时再跑。
- 改走 CDP 后，视口在导航前就设好，不再有 `resize`。因此 `SHOT_CSS` 如果还追加在文件末尾，`fit()` 量到的版心仍带 padding（568 < 600），卡会被缩到 0.947 倍，截图右侧和底部露白（审阅时已复现）。Step 6 把 `SHOT_CSS` 移进 `<head>`。

**`main()`（`:1198` 起）**里与本计划有关的部分：

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

`--shot` 的结果在 `main()` 里打印成 `已截图  <路径>`；出错时打印 `--shot 未完成：<错误>`。

**其他相关位置**：

- `:1133` 的注释 `# 无头 Chrome 把窗口宽度钳在 500px，比这更窄的视口测不到 —— 390px 只能人眼验。` 不再成立。
- `compile_math()`（`:507` 起）已经要求 `node`（`shutil.which("node")`），用 `subprocess.run([node, str(MATH_SCRIPT), str(page)], …)` 调 `scripts/math.mjs`。新运行器按同样方式调用。

### `scripts/probe_round.mjs`（冻结场景探针，已经在用 CDP）

- import 区（`:16-26`）有 `spawn`、`fs` 的 `existsSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync`、`tmpdir`、`join, resolve`、`pathToFileURL`。
- `:45-70` 是 020 加的代理参数：从注释 `// 无头 Chrome 不读 HTTP(S)_PROXY 环境变量…` 到 `    : [];`。
- `:71-110` 是启动 Chrome、连 WebSocket、`send`、`until` 的连接代码：

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
const until = (method) =>
  new Promise((ok) => {
    const f = (m) => (m.method === method ? ok(m) : waiters.push(f));
    waiters.push(f);
  });
```

后文用到的只有 `send(...)`、`until("Page.loadEventFired")`，以及收尾时的 `chrome.kill();`（`:483`，在写 `probe.json` 之后，顶层代码）。

### `tests/test_build.py`

- 顶部有 `import shutil`、`FIND_CHROME = runpy.run_path(str(BUILD))["find_chrome"]`、`FIXTURES`、`SHELL`、`png_size()`。
- `run_build(page, *args)` 总是带 `--no-render`。
- 渲染相关的测试都带 `@unittest.skipUnless(FIND_CHROME(), "需要本机 Chrome/Chromium")` 或 `@unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")`，合计 6 个。
- 没有 `--shot` 的测试。
- 快照测试 `test_snap_renders_both_themes_and_exports_markdown` 断言了四个文件名和宽度：

```python
        for name, width in (("light-500", 500), ("dark-500", 500), ("light-1280", 1280), ("dark-1280", 1280)):
            png = out / f"{name}.png"
            self.assertTrue(png.exists(), name)
            self.assertEqual(png_size(png)[0], width, name)
        self.assertNotEqual((out / "light-1280.png").read_bytes(), (out / "dark-1280.png").read_bytes())
```

### `charts.js` 的滚入绘制

- 数据图用 `IntersectionObserver`，露出 20% 时才画。
- 每个图的 `svg._replay()` 能强制画出，`PROBE` 开头就这么做。
- reduced motion 下画的是末帧。
- 视口固定 900px 后，首屏以外的图要先 `_replay()` 再截图。

## Commands you will need

以下命令都在你的 worktree 根目录运行。

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
- `skills/show-me-html/README.md`（「目录」表加两行）
- `skills/show-me-html/references/compose-and-check.md`、`references/visual-system.md`、`references/diagrams.md`（各一两句）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**：

- `PROBE` 字符串，以及 `render_check()` 里从 `m = re.search(...)` 开始的解析代码。017–019 的检查都挂在这里，本计划换的只是「怎么拿到标题」。唯一例外是 Step 4 里 `if not m:` 下面那一行报错文字。
- `assets/shell.js` 的 `fit()`：`--shot` 的缩放问题在 `build.py` 里通过移动 `SHOT_CSS` 解决。
- 多卡 `--shot` 从第 2 张起截出来是空白：改前就是这样，`.sheet-stage:nth-of-type(k)` 按各自所在的 section 计数。另记，本计划不修。
- `scripts/gallery.py`：它的截图改走运行器是计划 022 的事，022 同时加 `--pdf`。本计划不碰它；`build.py` 里的 `chrome_proxy_args()` 也先留着给它用。
- 屏蔽字体、改用兜底字体做检查：维护者否决，阈值是在真实字体下定的。
- 没有 Node 时退回旧的多次冷启动：维护者决定只留一条路径。没有 Node、Node 早于 22，都和没有 Chrome 一样，报「渲染检查未运行」。
- 390px 下的字号、对比度、倍率检查：390 只看横向溢出。
- `PROJECT_MEMORY.md`：由审阅者回写。

## Git workflow

- 你在派发时建好的独立 git worktree 里工作，分支已经建好，直接在上面提交。没有 worktree 时才 `git checkout -b advisor/021-show-me-html-cdp-runner main`。
- 主检出目录 `/Users/mg/github/skills` 停在 `main`，也就是改前版本，Step 1 和 Step 9 拿它的绝对路径做对照。不要在那里改文件、切分支或提交。那里已有的 `PROJECT_MEMORY.md`、`docs/research/…` 改动与本计划无关。
- conventional commits，scope 写技能名。建议按步骤提交，例如：
  - `refactor(show-me-html): probe_round connects through a shared cdp.mjs`
  - `perf(show-me-html): render check runs in one headless Chrome`
  - `feat(show-me-html): snapshots come in viewport slices with a section map`
- pre-commit 的 lint-staged 会用 prettier 重排提交里的 `.mjs` 和 Markdown，这是预期。每次提交后重跑 JS 语法检查。
- 不要 push。

## Steps

### Step 1: 抽出共用的 `scripts/cdp.mjs`，`probe_round.mjs` 改用它

1. 新建 `scripts/cdp.mjs`：

   <!-- prettier-ignore -->
   ```js
   // 共用的无头 Chrome 连接：CDP，Node 22+ 内置 WebSocket，无第三方依赖。render.mjs 与 probe_round.mjs 共用。
   import { spawn } from "node:child_process";
   import { mkdtempSync, rmSync } from "node:fs";
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

   // 启动一个无头 Chrome 并连上。返回 send(方法, 参数, sessionId)、until(事件名, {sessionId, timeout})、on(监听)、close()。
   // close() 返回 Promise：结束 Chrome，等它退出后删掉这次的配置目录（每次几 MB 到几十 MB）。
   // 启动失败时先收拾干净再抛错，不留 Chrome 进程和目录。
   export async function launch(chromePath, prefix = "show-me-cdp-") {
     if (typeof WebSocket === "undefined") throw new Error("这个 node 没有内置 WebSocket，需要 Node 22 或更新版本");
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
         const timer = setTimeout(() => no(new Error("Chrome 30 秒内没有给出调试地址")), 30000);
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
         chrome.on("exit", (code) => no(new Error(`Chrome 启动失败（退出码 ${code}）`)));
       });
       ws = new WebSocket(wsUrl);
       await new Promise((ok, no) => {
         ws.addEventListener("open", ok);
         ws.addEventListener("error", () => no(new Error("连不上 Chrome 的调试端口")));
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
     return { send, until, on, close };
   }
   ```

2. 修改 `scripts/probe_round.mjs`：
   - 删掉 020 加的代理参数那段，即 `:45-70`，从注释 `// 无头 Chrome 不读 HTTP(S)_PROXY 环境变量…` 到 `    : [];`。
   - 删掉从 `const chrome = spawn(CHROME, [` 到 `until` 定义结束的整段，即 `waiters.push(f);` 之后的 `  });`，`async function open(` 之前。换成一行：

     <!-- prettier-ignore -->
     ```js
     const { send, until, close } = await launch(CHROME, "probe-round-");
     ```

   - 写完 `probe.json` 之后的 `chrome.kill();` 改为 `await close();`。
   - import 区：
     - 加 `import { launch } from "./cdp.mjs";`。
     - 删掉 `import { spawn } from "node:child_process";` 和 `import { tmpdir } from "node:os";`。
     - 从 `node:fs` 的 import 列表里删掉 `mkdtempSync`。
     - 删之前用 `grep -n 'spawn\|mkdtempSync\|tmpdir' skills/show-me-html/scripts/probe_round.mjs` 确认只剩 import 那几处。`join` 等其余 import 保留。

**Verify**:

- JS 语法检查无输出。
- `grep -c 'waiters\|pending\|new WebSocket\|PROXY_ARGS' skills/show-me-html/scripts/probe_round.mjs` → `0`。
- 用 018 那一轮冻结场景核对探针行为不变。旧版是主检出目录里还没改的 `probe_round.mjs`：

  ```sh
  R=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-22-5820240-018
  T=$(mktemp -d); mkdir "$T/a" "$T/b"
  cp "$R"/*.html "$T/a/"; cp "$R"/*.html "$T/b/"
  node /Users/mg/github/skills/skills/show-me-html/scripts/probe_round.mjs "$T/a" > /dev/null
  ls -d "$TMPDIR"/probe-round-* 2>/dev/null | wc -l
  node skills/show-me-html/scripts/probe_round.mjs "$T/b" "$T/a" | grep -E '^[a-z-]+: |probe\.json|截图：|Markdown 不同'
  ls -d "$TMPDIR"/probe-round-* 2>/dev/null | wc -l
  ```

  预期：
  - 五行 `<场景名>: 无问题`；
  - `与上一轮对比：probe.json 相同`；
  - `截图：30/30 张逐字节相同`；
  - 没有 `Markdown 不同`；
  - 两次 `wc -l` 的数字相同：新版不再留下 `probe-round-*` 配置目录，旧版那次留下的不用管。

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
// 没用到的字段不出现。退出码：0 正常；2 Chrome 起不来或运行器自身出错，原因写在 stderr 最后一行；
// 3 这个 node 没有内置 WebSocket（早于 22），build.py 按「没有 node」处理。
import { readFileSync, writeFileSync } from "node:fs";
import { launch } from "./cdp.mjs";

const spec = JSON.parse(readFileSync(process.argv[2], "utf8"));
let cdp;
try {
  cdp = await launch(spec.chrome);
} catch (e) {
  console.error(String(e.message || e));
  process.exit(typeof WebSocket === "undefined" ? 3 : 2);
}
const { send, until, on, close } = cdp;
const results = [];
let failed = "";
try {
  for (const job of spec.jobs) results.push(await run(job));
} catch (e) {
  failed = String(e.message || e);
}
await close();
if (failed) {
  console.error(failed);
  process.exit(2);
}
// 写管道在 macOS 上是异步的：等写完再退出，否则 64 KB 之后的部分会丢
process.stdout.write(JSON.stringify(results), () => process.exit(0));

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

**Verify**: JS 语法检查无输出。然后手动跑一次：

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
ls -d "$TMPDIR"/show-me-cdp-* 2>/dev/null | wc -l
node skills/show-me-html/scripts/render.mjs "$T/jobs.json"; echo; ls "$T"/s-*.png | head -3
ls -d "$TMPDIR"/show-me-cdp-* 2>/dev/null | wc -l
node --no-experimental-websocket skills/show-me-html/scripts/render.mjs "$T/jobs.json"; echo "exit=$?"
```

预期：

- 打印一个两项的 JSON 数组。第一项 `value` 以 `loaded ` 开头，`errors` 为空；第二项有 `slices`，`s-01.png` 存在。
- 两次 `wc -l` 的数字相同，说明配置目录已删。
- 最后一条命令打印 `这个 node 没有内置 WebSocket…`，然后是 `exit=3`。如果 node 报 `bad option: --no-experimental-websocket`（新版 Node 去掉了这个开关），就跳过这一项，在汇报里写明。

### Step 3: `build.py` 加 `run_jobs()`

在 `chrome_proxy_args()` 之后、`render_check` 上方那行注释之前加：

```python
RENDER_SCRIPT = Path(__file__).resolve().parent / "render.mjs"


def run_jobs(jobs):
    """在一个无头 Chrome 实例里依次跑完 jobs（scripts/render.mjs，走 CDP），返回 (结果列表, 错误信息)。
    任务与结果的字段见 render.mjs 文件头。找不到 Chrome 或 node、或 node 早于 22（没有内置 WebSocket）时
    返回 (None, None)：调用方按「这道关没跑」处理。"""
    import contextlib, json, os, shutil, signal, subprocess, tempfile
    chrome, node = find_chrome(), shutil.which("node")
    if not chrome or not node:
        return None, None
    with tempfile.TemporaryDirectory() as td:
        spec = Path(td) / "jobs.json"
        spec.write_text(json.dumps({"chrome": chrome, "jobs": jobs}, ensure_ascii=False), encoding="utf-8")
        # 运行器单独一个进程组：超时或被中断时连同它启动的 Chrome 一起结束，不留孤儿进程
        proc = subprocess.Popen([node, str(RENDER_SCRIPT), str(spec)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, encoding="utf-8", start_new_session=True)
        try:
            out, err = proc.communicate(timeout=90 * len(jobs) + 30)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):  # 进程组可能恰好已经自己退出
                os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            return None, "Chrome 运行器超时"
        except BaseException:  # Ctrl-C 等：单独的进程组收不到终端发来的信号，要自己结束它
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            raise
    if proc.returncode == 3:
        return None, None
    if proc.returncode:
        return None, (err.strip().splitlines() or [f"运行器退出码 {proc.returncode}"])[-1]
    try:
        return json.loads(out), None
    except ValueError:
        return None, f"运行器的输出不是完整的 JSON（{len(out)} 字节）"
```

`render_check` 上方那行注释 `# 无头 Chrome 把窗口宽度钳在 500px，比这更窄的视口测不到 —— 390px 只能人眼验。` 改为：

```python
# 390 用 CDP 的手机模拟（--window-size 最窄只到 500px，模拟不受这个限制），只查横向溢出、报 WARN；
# 字号、对比度、倍率这些检查只在 500 / 1024 / 1280 跑。
```

**Verify**:

- 语法检查无输出。
- `python3 -c "import runpy; r = runpy.run_path('skills/show-me-html/scripts/build.py')['run_jobs']([]); print(r)"` → `([], None)`。

### Step 4: 渲染检查改走运行器

在 `render_check()` 里改四处，再改 `main()` 里的提示：

1. docstring 和开头的

   ```python
       """返回 (issues, notes, measured, ran)。issues 是 ERROR，notes 是 WARN；ran=False 表示没有浏览器，这道关没跑。"""
       import html as htmllib, subprocess, tempfile
       chrome = find_chrome()
       if not chrome:
           return [], [], [], False
   ```

   改为

   ```python
       """返回 (issues, notes, measured, ran)。issues 是 ERROR，notes 是 WARN；
       ran=False 表示没有 Chrome、node 或 node 早于 22，这道关没跑。"""
       import html as htmllib, tempfile
   ```

2. 把 `for w in widths:` 这一行，连同紧跟着的整个 `try: … except Exception as e: return [f"渲染检查跑不起来：{e}"], [], [], False`（到这个 `return` 为止），替换为下面这段：
   - 缩进 8 个空格，与原来的 `for` 对齐。
   - 原来循环体里 `m = re.search(...)` 及之后的代码保持原样，仍在新的 `for` 循环体里。

   ```python
           # 一个 Chrome 依次跑完所有宽度（scripts/render.mjs）。PROBE 把结果写进 <title>；包回 --dump-dom 的样子，
           # 下面的正则与 unescape 原样沿用。读标题元素的文本而不是 document.title：后者会合并连续空格。
           # reduced motion 下量末帧，与 gallery.py 的探针、--snap 一致：逐帧布局的图（如 G11 力导向图）
           # 在无头 Chrome 里不一定跑完，量到的是节点还在原点的中间状态
           title = "(document.querySelector('head > title') || {}).textContent || ''"
           results, err = run_jobs([{"url": probe.as_uri(), "width": w, "reduced": True, "eval": title}
                                    for w in (390, *widths)])
           if results is None:  # err 为空：没有 Chrome、node 或 node 早于 22，这道关没跑；err 非空：运行器出错，记 ERROR
               return ([f"渲染检查跑不起来：{err}"] if err else []), [], [], False
           wrap = lambda r: "<title>" + htmllib.escape(r.get("value") or "", quote=False) + "</title>"
           why = lambda r: r.get("error") or "；".join(r.get("errors", [])[:2]) or "页面没写回结果"
           # 390（手机）只看横向溢出，报 WARN：字号类检查在 500px 已经量过窄版
           phone = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|", wrap(results[0]), re.S)
           if not phone:
               notes.append(f"390px（手机）：探针没返回结果（{why(results[0])}），这一档没查")
           elif int(phone.group(1)) > int(phone.group(2)) + 1:
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
                   issues.append(f"{w}px：探针没返回结果（{why(r)}）")
   ```

4. `main()` 里两句提示改为：

   ```python
       if rendered:
           print(f"渲染检查：{' / '.join(f'{w}px' for w in measured)} 无横向溢出；390px 手机视口另查，溢出只报 WARN。")
       elif not args.no_render:
           print("渲染检查未运行：找不到 Chrome/Chromium 或 node 22+。横向溢出没有被验证过，"
                 "自己在浏览器里拉一遍窄屏，不要报「已验证」。")
   ```

**Verify**:

- 语法检查无输出。
- `sed -n '/^def render_check/,/^def /p' skills/show-me-html/scripts/build.py | grep -c subprocess` → `0`。
- 全量单元测试 → `OK`，`Ran 51 tests`。017–019 的渲染测试原样通过，这是检查结果没变的第一道证据。

### Step 5: 快照改成切片，加 `--snap-theme` / `--snap-width`

1. 从注释行 `# ── 整页快照（--snap）──…` 起，到 `snap_page()` 的 `return outs, notes, None` 为止，整段替换为下面的代码。这一段包括四行注释、`SNAP_PROBE`、`SNAP_MAX_H` 和旧的 `snap_page()`；`CHROME_PATHS = (` 及之后不动。

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
           return [], [], err or "找不到 Chrome/Chromium 或 node 22+"
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

**Verify**:

- 语法检查无输出。
- `grep -c 'SNAP_MAX_H\|SNAP_PROBE\|整页 PNG' skills/show-me-html/scripts/build.py` → `0`。
- `grep -c '# ── 整页快照' skills/show-me-html/scripts/build.py` → `1`。
- `python3 skills/show-me-html/scripts/build.py x.html --snap-width 100; echo "exit=$?"` → stderr 含 `--snap-width 要写`，然后是 `exit=2`。

### Step 6: `--shot` 改走运行器

`shoot_sheets()` 改成先写好每张卡的临时文件、收集任务，再一次交给运行器。同时把 `SHOT_CSS` 和隐藏其他卡的样式从文件末尾移进 `<head>`：

- `assets/shell.js` 的 `fit()` 在页面脚本执行时就量版心宽度。那时如果样式还在文件末尾、没有生效，版心带着 padding，卡会被缩到 0.95 倍。
- 改前这个问题被 `--window-size` 之后的一次 `resize` 掩盖了，CDP 不会触发这次 `resize`。
- 每个任务另带一个 `eval`，读出卡片上的 `transform`：有缩放就报错，不交出缩小的截图。

`SHOT_CSS` 字符串本身不动，把整个 `shoot_sheets()` 替换为：

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
    # shell.js 的 fit() 视口比卡窄时把卡等比缩小；截图视口就是卡宽，读出缩放说明隐藏 chrome 的样式没在 fit() 之前生效
    scaled = "[].map.call(document.querySelectorAll('.sheet'), function(s){ return s.style.transform; }).join(' ').trim()"
    jobs = []
    with tempfile.TemporaryDirectory() as td:
        for i in range(n):
            hide = "".join(
                f".sheet-stage:nth-of-type({j + 1}){{display:none!important}}" for j in range(n) if j != i
            )
            # 样式放进 <head>：fit() 在页面脚本执行时就量版心，追加在文末的样式那时还没生效
            themed = html.replace(
                "<head>",
                f'<head><script>try{{localStorage.setItem("show-me-theme","{theme}")}}catch(e){{}}</script>'
                + SHOT_CSS + f"<style>{hide}</style>", 1,
            )
            probe = Path(td) / f"shot-{i}.html"
            probe.write_text(themed, encoding="utf-8")
            suffix = f"-{i + 1}" if n > 1 else ""
            out = page.with_name(f"{page.stem}{suffix}{'-dark' if theme == 'dark' else ''}.png")
            jobs.append({"url": probe.as_uri(), "width": w, "height": h, "dpr": scale, "mobile": False,
                         "eval": scaled, "shot": str(out)})
        results, err = run_jobs(jobs)
    if results is None:
        return [], err or "找不到 Chrome/Chromium 或 node 22+"
    outs = []
    for job, r in zip(jobs, results):
        if r.get("error"):
            return outs, f"截图失败：{r['error']}"
        if r.get("value"):
            return outs, f"截图失败：卡片被缩放（{r['value']}），截出来不是原尺寸"
        outs.append(Path(job["shot"]))
    return outs, None
```

**Verify**:

- 语法检查无输出。
- `grep -c -- '--headless' skills/show-me-html/scripts/build.py` → `0`，说明 `build.py` 里不再直接启动 Chrome。
- `grep -c 'chrome_proxy_args()' skills/show-me-html/scripts/build.py` → `0`：
  - 020 加在 `snap_page`、`shoot_sheets`、`render_check` 里的三处调用，都已随旧代码删掉，代理改由 `cdp.mjs` 处理。
  - 函数定义 `def chrome_proxy_args(env=None):` 留给 `gallery.py`，022 再删。
- `grep -c 'no-sandbox' skills/show-me-html/scripts/build.py` → `0`，`grep -c 'no-sandbox' skills/show-me-html/scripts/cdp.mjs` → `2`（注释一处，参数一处）。

### Step 7: 测试

1. 先 `grep -c '需要本机 Chrome/Chromium"' skills/show-me-html/tests/test_build.py`，确认是 `6`。然后：
   - 在文件顶部 `FIND_CHROME = …` 之后加一行：

     ```python
     RENDERER = bool(FIND_CHROME() and shutil.which("node"))
     ```

   - 把文件里**所有**渲染测试的装饰器换成 `@unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")`。要换的有两种写法：
     - `@unittest.skipUnless(FIND_CHROME(), "需要本机 Chrome/Chromium")`
     - `@unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")`

2. `test_snap_renders_both_themes_and_exports_markdown` 里，把断言四个文件名的那个 `for` 循环和紧跟的 `assertNotEqual` 换成下面这段。其余断言（`export.md` 那几行）不动。

   ```python
           for name, width in (("light-390", 390), ("dark-390", 390), ("light-500", 500), ("dark-500", 500),
                            ("light-1280", 1280), ("dark-1280", 1280)):
               png = out / f"{name}-01.png"
               self.assertTrue(png.exists(), name)
               self.assertEqual(png_size(png)[0], width, name)
           self.assertNotEqual((out / "light-1280-01.png").read_bytes(), (out / "dark-1280-01.png").read_bytes())
           self.assertIn("light-1280-01.png  含：第二节", result.stdout)
   ```

3. 在它后面加五个测试：

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
           self.assertIn("渲染检查未运行：找不到 Chrome/Chromium 或 node 22+", result.stdout)

       @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
       def test_runner_returns_long_output_whole(self):
           """运行器的结果经管道交回，macOS 上写管道是异步的：超过 64 KB 也要完整。"""
           run_jobs = runpy.run_path(str(BUILD))["run_jobs"]
           results, err = run_jobs([{"url": (FIXTURES / "minimal-shell.html").as_uri(), "eval": "'x'.repeat(200000)"}])
           self.assertIsNone(err)
           self.assertEqual(len(results[0]["value"]), 200000)

       @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
       def test_shot_keeps_card_at_full_size(self):
           """--shot 按卡的尺寸、两倍像素截图；卡没有被 fit() 缩小（缩小时 build 报「卡片被缩放」）。"""
           tmp = tempfile.TemporaryDirectory()
           self.addCleanup(tmp.cleanup)
           page = Path(tmp.name) / "card.html"
           html = SHELL.read_text(encoding="utf-8").replace("PAGE TITLE", "卡片测试").replace("choose-a-recipe", "share-card")
           html = re.sub(r'<main id="doc">.*?</main>',
                         '<main id="doc"><section><div class="sheet-stage"><article class="sheet">'
                         '<div class="sheet-mast"><strong>周报</strong><span>W35</span></div>'
                         '<div class="sheet-body"><h1>结论</h1><p>一句话说明。</p></div>'
                         '<div class="sheet-foot"><span>来源</span><span>2026-09-06</span></div>'
                         '</article></div></section></main>',
                         html, count=1, flags=re.S)
           page.write_text(html, encoding="utf-8")

           result = run_build(page, "--shot")

           self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
           self.assertNotIn("--shot 未完成", result.stdout)
           self.assertIn("已截图", result.stdout)
           self.assertEqual(png_size(page.with_name("card.png")), (1200, 2000))
   ```

**Verify**:

- `grep -c 'skipUnless(RENDERER' skills/show-me-html/tests/test_build.py` → `10`。
- `grep -c '需要本机 Chrome/Chromium"' skills/show-me-html/tests/test_build.py` → `0`。
- 全量单元测试 → `OK`，`Ran 56 tests`，没有 `skipped`。如果有 skipped，本机应该只会跳过 `test_render_check_reports_not_run_without_node`（`/usr/bin` 里有 node 时），这时要在汇报里写明。
- `test_shot_keeps_card_at_full_size` 是 `--shot` 缩放问题的回归测试。做一次反证：临时把 `shoot_sheets` 里的样式改回追加在文件末尾，单跑这个测试应当失败（输出含 `卡片被缩放`）；确认后改回去。命令：`python3 -m unittest skills.show-me-html.tests.test_build.BuildCliTests.test_shot_keeps_card_at_full_size`。

### Step 8: 文档

1. `SKILL.md`「交付与反馈」之前那段里，

   `新页验证主题、窄屏、实际交互、打印与导出：用 `--snap` 产出的双主题截图与 export.md 做眼检；小修检查受影响行为，可复用同一页面未改变部分的已有证据。`

   改为：

   <!-- prettier-ignore -->
   ```markdown
   新页验证主题、窄屏、实际交互、打印与导出：用 `--snap` 产出的双主题切片截图（390 / 500 / 1280）与 export.md 做眼检；小修用 `--snap-theme`、`--snap-width` 只拍受影响的主题和宽度，按输出里每片的「含：…」只重读受影响的切片，可复用同一页面未改变部分的已有证据。
   ```

2. `references/compose-and-check.md` 改三处：
   - 「渲染级」那一条，从 `装了 Chrome/Chromium 就在 500、1024 与 1280px 下实际渲染…` 到 `…390px 这一档只能人眼看。`，共三行，改为：

     <!-- prettier-ignore -->
     ```markdown
     - **渲染级**：装了 Chrome/Chromium 和 Node 22+ 就用一个无头 Chrome 在 500、1024 与 1280px 下实际渲染，检出横向溢出并点名越界元素；390px 按手机模拟，只查横向溢出、报 WARN。
       找不到浏览器或 node 时会明说这道关没跑 —— 那就自己拉一遍窄屏，**不要报「已验证」**。
     ```

   - 「眼睛关」第一段里：
     - `逐张读取打印出的 4 张 PNG（light/dark × 500/1280）` 改为 `逐张读取打印出的切片 PNG（light/dark × 390/500/1280，每片一屏多高，行尾写着这片含哪几节）`。
     - 同一句里 `交互（拖拽、键盘、折叠）与 390px 仍需真实浏览器` 改为 `交互（拖拽、键盘、折叠）仍需真实浏览器`。
   - `拉到 390px 看一遍：没有被挤成竖条的文字，没有贴边（这一档脚本测不到）。` 改为 `看 390 的切片：没有被挤成竖条的文字，没有贴边（脚本只报整页溢出，挤压和贴边靠眼睛）。`

3. `references/visual-system.md`「响应式与打印」：`- 自动几何检查跑 500、1024 和 1280px；390px 保留人工门禁。` 改为 `- 自动几何检查跑 500、1024 和 1280px；390px 按手机模拟只查横向溢出（WARN），挤压与贴边靠人眼看切片。`

4. `references/diagrams.md`：`（9px 的下限缩到九成左右还能过）；被隐藏的那版不量。390px 测不到，窄版的 viewBox 宽度按上面的范围控制。` 里的 `390px 测不到` 改为 `390px 只查横向溢出、不量字号`。

5. `README.md`「目录」表：在 `scripts/probe_round.mjs` 那一行后面加两行：

   <!-- prettier-ignore -->
   ```markdown
   | `scripts/render.mjs` | `build.py` 的 Chrome 运行器：一个无头实例跑完渲染检查、`--snap` 切片与 `--shot` 截图 |
   | `scripts/cdp.mjs` | 无头 Chrome 的 CDP 连接（启动、收发、清理），`render.mjs` 与 `probe_round.mjs` 共用 |
   ```

6. 格式化：`npx prettier --write skills/show-me-html/SKILL.md skills/show-me-html/README.md skills/show-me-html/references/compose-and-check.md skills/show-me-html/references/visual-system.md skills/show-me-html/references/diagrams.md`

**Verify**:

- `make check` → exit 0。
- `grep -rn '最窄只到 500px\|4 张 PNG\|390px 测不到\|390px 保留人工门禁' skills/show-me-html/SKILL.md skills/show-me-html/references` → 无输出。
- `grep -c 'scripts/render.mjs\|scripts/cdp.mjs' skills/show-me-html/README.md` → `2`。

### Step 9: 对照验收

以下每段都在 worktree 根目录、各自的新 shell 里运行，变量在段内定义。

1. **检查结果不变**：同一批页面分别用改前的 `build.py`（主检出目录，即 `main`）和本分支的 `build.py` 构建，比较 ERROR / WARN 行。

   ```sh
   OLD=/Users/mg/github/skills/skills/show-me-html/scripts
   NEW=skills/show-me-html/scripts
   R=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-22-5820240-018
   T=$(mktemp -d); echo "T=$T"
   for f in "$R"/*.html skills/show-me-html/tests/fixtures/component-states.html skills/show-me-html/tests/fixtures/diagram-variants.html; do
     n=$(basename "$f" .html); cp "$f" "$T/$n-old.html"; cp "$f" "$T/$n-new.html"
     python3 "$OLD/build.py" "$T/$n-old.html" | grep -E '^(ERROR|WARN)' | sort > "$T/$n.old"
     python3 "$NEW/build.py" "$T/$n-new.html" > "$T/$n.newout"
     grep -E '^(ERROR|WARN)' "$T/$n.newout" | grep -v '390px（手机）' | sort > "$T/$n.new"
     cmp -s "$T/$n.old" "$T/$n.new" && echo "$n 相同" || { echo "$n 不同"; diff "$T/$n.old" "$T/$n.new"; }
   done
   python3 "$OLD/gallery.py" --out "$T/g-old" | sed "s#$T/g-old#OUT#" | head -3 > "$T/g.old"
   python3 "$NEW/gallery.py" --out "$T/g-new" | sed "s#$T/g-new#OUT#" | head -3 > "$T/g.new"
   cmp -s "$T/g.old" "$T/g.new" && echo "gallery 相同" || diff "$T/g.old" "$T/g.new"
   cat "$T/g.new"
   grep -h '390px（手机）' "$T"/*.newout | sort -u
   ```

   **Verify**:
   - 七页每页一行 `相同`，并且有一行 `gallery 相同`。gallery 输出的三行是：`已合成  OUT/…`、一条 `超过 400 KB` 的 WARN、`自检通过（1 个警告需逐条判断）。`。
   - 只有一种差异属于预期：旧版某条消息里的视口宽度比新版少 15px 左右，比如旧 `485px` 对新 `500px`、`1009` 对 `1024`、`1265` 对 `1280`，其余文字相同。这是因为旧的渲染检查没加 `--hide-scrollbars`，偶尔把滚动条宽度量进去（plans/README「018 执行记录」记过这个偶发问题）。遇到这种差异，原样写进汇报，不算「不同」。其余差异都按 STOP 处理。
   - 最后一条命令列出新出现的 390 WARN。有的话原样写进汇报，不要修页面。

2. **快照能读、数据图画全**：

   ```sh
   R=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-22-5820240-018
   S=$(mktemp -d); echo "S=$S"
   cp "$R/status-report.html" "$S/p.html"
   /usr/bin/time -p python3 skills/show-me-html/scripts/build.py "$S/p.html" --snap "$S/snap" 2>&1 | grep -E '已快照|注意|未完成|^real'
   python3 skills/show-me-html/scripts/gallery.py --out "$S/g" > /dev/null
   python3 skills/show-me-html/scripts/build.py "$S/g/all-charts.html" --snap "$S/gsnap" | grep -E '未完成|light-1280-0[1-4]|export'
   ls "$S/gsnap" | wc -l
   ```

   **Verify**:
   - status-report 打印 `light-390-01.png`、`light-500-01.png`、`light-1280-01.png`、对应的 `dark-*` 切片，以及 `export.md`。每个切片行末有 `含：…`、`（页首）` 或 `（接上一片）`。advisor 实测 status-report 是 `light-1280-01.png  含：分组进展、风险` 和 `light-1280-02.png  含：下一步`。
   - 打开 `$S/snap/light-1280-01.png` 和 `$S/snap/light-390-01.png` 看一眼：没有截到动画中途，手机宽度下版式是单栏。
   - 把 `real` 秒数写进汇报。参考值：advisor 在 scratchpad 里拍 390、1280 两种宽度、带代理用了 13.8 秒；`2f0e439` 的 `build.py` 同一命令不带代理用了 266.8 秒。
   - gallery 总览页（59 张数据图，export.md 约 17 KB）没有 `--snap 未完成`，`ls | wc -l` 在 110 左右（advisor 在套用本计划的副本里实测 111 个，含渲染检查共 44.7 秒）。
   - 打开 `$S/gsnap/light-1280-03.png` 和 `$S/gsnap/light-1280-04.png`：这两片在首屏以外，里面的数据图都已画出（有坐标轴、柱、线或扇区），不是空框。

3. **幻灯片高度**：

   ```sh
   S=$(mktemp -d); echo "S=$S"
   python3 - "$S/deck.html" <<'EOF'
   import pathlib, re, sys
   shell = pathlib.Path("skills/show-me-html/assets/shell.html").read_text(encoding="utf-8")
   slides = "".join(f'<section class="slide"><h2>第 {i} 张</h2><p>内容</p></section>' for i in range(1, 4))
   page = re.sub(r'<main id="doc">.*?</main>', '<main id="doc">' + slides + '</main>',
                 shell.replace("PAGE TITLE", "幻灯").replace("choose-a-recipe", "slide-deck"), count=1, flags=re.S)
   pathlib.Path(sys.argv[1]).write_text(page, encoding="utf-8")
   EOF
   python3 skills/show-me-html/scripts/build.py "$S/deck.html" --snap "$S/deck" --snap-theme light --snap-width 1280 | grep 已快照
   ```

   **Verify**: 打开 `$S/deck/light-1280-01.png` 和 `-02.png`，每张幻灯片一屏高（约 900px），没有被拉成整页高。

4. **定尺卡截图**：同一张单卡页面，新旧 `--shot` 各拍一张，比较尺寸，再用眼睛看。

   ```sh
   OLD=/Users/mg/github/skills/skills/show-me-html/scripts
   NEW=skills/show-me-html/scripts
   S=$(mktemp -d); echo "S=$S"; mkdir "$S/old" "$S/new"
   python3 - "$S/old/card.html" <<'EOF'
   import pathlib, re, sys
   shell = pathlib.Path("skills/show-me-html/assets/shell.html").read_text(encoding="utf-8")
   card = ('<section><div class="sheet-stage"><article class="sheet"><div class="sheet-mast"><strong>周报</strong>'
           '<span>W35</span></div><div class="sheet-body"><h1>结论</h1><p>一句话说明。</p></div>'
           '<div class="sheet-foot"><span>来源</span><span>2026-09-06</span></div></article></div></section>')
   page = re.sub(r'<main id="doc">.*?</main>', '<main id="doc">' + card + '</main>',
                 shell.replace("PAGE TITLE", "卡片").replace("choose-a-recipe", "share-card"), count=1, flags=re.S)
   pathlib.Path(sys.argv[1]).write_text(page, encoding="utf-8")
   EOF
   cp "$S/old/card.html" "$S/new/card.html"
   python3 "$OLD/build.py" "$S/old/card.html" --shot | grep -E '已截图|未完成'
   python3 "$NEW/build.py" "$S/new/card.html" --shot | grep -E '已截图|未完成'
   python3 -c "import sys; [print(p, int.from_bytes(open(p,'rb').read()[16:20],'big'), int.from_bytes(open(p,'rb').read()[20:24],'big')) for p in sys.argv[1:]]" "$S/old/card.png" "$S/new/card.png"
   ```

   **Verify**:
   - 两次都打印 `已截图`，没有 `未完成`；两张 PNG 都是 `1200 2000`。
   - 打开两张图对比：新图的卡片铺满整张图，右侧和底部没有白边，版式与旧图一致。两张图的字节不同是正常的，两种截图方式的抗锯齿不一样。

5. **冻结场景轮次**：照 `skills/show-me-html/scenarios/README.md` 的流程新建一轮。本计划不改页面生成指引，所以不重新生成页面，而是复制 018 那一轮的五页重建：

   ```sh
   PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-22-5820240-018
   RND=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-021
   mkdir -p "$RND"
   for n in status-report approach-compare code-review concept-explainer triage-board; do
     cp "$PREV/$n.html" "$RND/" && python3 skills/show-me-html/scripts/build.py "$RND/$n.html" | grep -E '^(ERROR|WARN)|自检通过'
   done
   node skills/show-me-html/scripts/probe_round.mjs "$RND" "$PREV" | grep -E '^[a-z-]+: |probe\.json|截图：|Markdown 不同'
   ```

   **Verify**:
   - 五次构建都打印 `自检通过。`；五行 `<场景名>: 无问题`；`与上一轮对比：probe.json 相同`。
   - 截图应为 `30/30 张逐字节相同`。有不同就逐张打开看：只是抗锯齿噪声的，在汇报里列出文件名；版式或颜色有变化的，按 STOP 处理。
   - `scenarios/rounds/` 在 `.gitignore` 里，轮次目录不进提交。

## Test plan

- 改：`test_snap_renders_both_themes_and_exports_markdown`，断言改成切片文件名、390 / 500 / 1280 宽度和「含：第二节」。
- 新增：
  - `test_snap_narrows_to_one_theme_and_width`：`--snap-theme`、`--snap-width` 只出一组切片。
  - `test_render_check_warns_on_phone_overflow_only`：390 溢出报 WARN，不失败。
  - `test_render_check_reports_not_run_without_node`：没有 node 时明说没跑。
  - `test_runner_returns_long_output_whole`：运行器结果超过 64 KB 不被截断。
  - `test_shot_keeps_card_at_full_size`：`--shot` 的卡不被缩小。
- 不改但必须原样通过：017–019 留下的所有 `test_render_check_*`。它们是「换了传输方式、检查结果不变」的主要证据。
- `probe_round.mjs` 换用 `cdp.mjs` 后的连接代码，靠 Step 1 的新旧对照验证。
- Node 早于 22 时的退出码 3，靠 Step 2 的 `--no-experimental-websocket` 手动验证。

## Done criteria

- [ ] 全量单元测试末行 `OK`，`Ran 56 tests`，没有跳过渲染测试（本机有 Chrome 和 node）
- [ ] `grep -c -- '--headless' skills/show-me-html/scripts/build.py` → `0`
- [ ] `grep -c 'SNAP_MAX_H\|SNAP_PROBE' skills/show-me-html/scripts/build.py` → `0`
- [ ] JS 语法检查三个文件无输出；`grep -c 'waiters' skills/show-me-html/scripts/probe_round.mjs` → `0`
- [ ] Step 1 新旧 `probe_round` 对照：`probe.json 相同`，截图 `30/30`，不再留下 `probe-round-*` 目录
- [ ] Step 2：运行器跑完不留下 `show-me-cdp-*` 目录；`--no-experimental-websocket` 下 `exit=3`（或写明 node 不认这个开关）
- [ ] Step 7 的反证做过：样式改回文末时 `test_shot_keeps_card_at_full_size` 失败，改回后通过
- [ ] Step 9 第 1 小步：七页都 `相同`，`gallery 相同`（滚动条宽度造成的差异已在汇报里列出）
- [ ] Step 9 第 2–4 小步的切片和卡片截图都看过。汇报里写了 `--snap` 耗时、新出现的 390 WARN（没有就写「无」）、gallery 首屏外的数据图已画出
- [ ] Step 9 第 5 小步：五页 `自检通过`，探针五行 `无问题`，`probe.json 相同`
- [ ] `make check` exit 0；在你的 worktree 里 `git status` 只显示 Scope 里的文件（轮次目录被 gitignore，不会出现）
- [ ] `plans/README.md` 本计划的状态行已更新（审阅者说明由他维护时跳过）

## STOP conditions

- Drift check 里 020、018、019 任何一份未合入，或「Current state」的引文找不到。
- Step 2 的手动运行里，第一项的 `value` 不以 `loaded ` 开头（字体没到齐就测量了），或者一直等到超时：说明 `Emulation.setVirtualTimePolicy` 在本机 Chrome 上不按预期工作。不要改成固定等几秒，汇报 Chrome 版本（`"<Chrome 路径>" --version`）和运行器输出。
- Step 4 之后已有的 `test_render_check_*` 有任何一个失败，或 Step 9 第 1 小步出现滚动条宽度以外的 `不同`：说明拿到的标题和 `--dump-dom` 不一致。汇报 diff，不要改 `PROBE` 或正则去迁就。
- 切片截图里首屏以外的数据图是空的，或者幻灯片仍被拉成整页高。
- `--shot` 的卡仍被缩放（测试报 `卡片被缩放`，或 Step 9 第 4 小步的新图有白边）。
- 你发现需要改 `gallery.py` 或 `assets/shell.js` 才能让本计划的测试通过。

## Maintenance notes

- 运行器的任务字段是 `build.py` 和 `render.mjs` 之间的接口，文件头注释是唯一说明，退出码 3（node 太旧）也属于这个接口。计划 022 会给它加 `pdf` 字段，并让 `gallery.py` 改用它；计划 025（单页交互探针）直接用 `cdp.mjs`。
- `PROBE` 仍然只通过 `<title>` 交回结果。后续计划（例如 023 的越框检查）继续在末尾追加 `|` 分段和命名分组即可。以后想改成直接返回 JSON，那是另一份计划：要同时改 `PROBE` 末尾和全部解析代码。
- 一次构建启动 Chrome 的次数：渲染检查一次；`--snap` 一次；`--shot` 每个主题一次，`both` 是两次。每次都是新配置，字体各拉一次；带代理时这部分在一两秒内。
- `cdp.mjs` 的 `close()` 会删掉 Chrome 配置目录。运行器超时或构建被 Ctrl-C 中断时，`run_jobs` 结束整个进程组，不留 Chrome 进程，但目录会留下，这种情况很少见。改前 `probe_round.mjs` 每轮都留一个 `probe-round-*` 目录，改后不再留。
- 虚拟时间预算仍是 4000ms，和改前一致。页面里的计时器超过这个时长才出现的内容，检查和快照都看不到，和改前一样。
- 运行器总是模拟 `prefers-color-scheme`：给了主题就按主题，没给按浅色。改前无头 Chrome 跟随本机外观，缺防闪烁主题脚本的夹具在暗色外观的机器上会渲染成暗色（advisor 用表格样张复现过）。
- 渲染检查改在 reduced motion 下跑，改前没有模拟。advisor 在 scratchpad 里对比过：五个冻结场景、组件夹具、宽窄两版图夹具和 gallery 总览页的 ERROR / WARN，与不模拟时完全相同。计划 023 的越框检查需要它，否则 G11 力导向图在节点还没布局时，会被误报 20 处越框。
- 运行器总是隐藏滚动条（`--hide-scrollbars`）。改前渲染检查是唯一没加这个参数的 Chrome 调用。019 执行时，`test_render_check_measures_only_the_shown_diagram_variant` 偶发量到 485px，很可能就是滚动条，改后应当不再出现。
- 切片按固定高度切，最后一片可能很薄（几十像素）。这不影响阅读，暂不合并。
- 审阅时重点看：
  - `render_check` 里从 `m = re.search(...)` 往下的代码，diff 只有 `if not m:` 下面那一行；
  - `snap_page` 的 Markdown 来自 light、最宽那一组；
  - `shoot_sheets` 的样式在 `<head>` 里。
