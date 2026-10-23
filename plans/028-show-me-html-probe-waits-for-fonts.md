# Plan 028: 冻结场景探针截图前等网络字体到齐，字体取不到时报出来

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。索引 `plans/README.md` 由审阅者维护，你不要改它。
>
> **Drift check (run first)**: `git diff --stat eec315f..HEAD -- skills/show-me-html/scripts/probe_round.mjs skills/show-me-html/scenarios/README.md skills/show-me-html/assets/shell.html` 应无输出。有输出就对照下面「Current state」里的引文，引文原样还在就继续，对不上就 STOP。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容已经是 prettier 格式，原样粘贴即可，粘贴后 `prettier --check` 应直接通过。

## Status

- **Priority**: P2
- **Effort**: S（一个脚本里加一段等待和一段报告，文档一句）
- **Risk**: LOW（只改评测用的探针，不碰页面、骨架和 `build.py`）
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `eec315f`, 2026-10-23

## Why this matters

改了 show-me-html 的样式或骨架后，要跑一轮「冻结场景」：`scripts/probe_round.mjs` 把五个固定页面按 light / dark × 390 / 500 / 1280 截 30 张图，与上一轮逐字节比对，用来发现意外的画面变化。最近几次审阅中，第一次跑几乎总有大量截图不同：027 审阅三次首跑分别有 12、6、2 张，026 审阅两次首跑分别有 18、12 张，其中一次 `probe.json` 还有 4 处不同。差异遍布全页文字的字形，重跑一次就全部相同。于是每份计划都要写「首跑不同先重跑一次」，每次审阅也要多跑一轮。另外，字体真取不到时，比如断网，探针照样退出码 0，30 张图全不同，却没有任何提示说明这一轮的对比不可信。

原因是探针打开页面后只固定等 1.5 秒就截图，而网页字体的分片常常要更久才下完。本计划让探针先等字体到齐（最多 30 秒）再截图；取不到字体时在摘要里写明原因，并以退出码 1 结束。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `eec315f`。

- `scripts/probe_round.mjs:78-81`，每次打开页面都走 `open()`，等到 load 事件后固定睡 1.5 秒，然后读数、截图：

  ```js
  const loaded = until("Page.loadEventFired");
  await S("Page.navigate", { url: pathToFileURL(file).href });
  await loaded;
  await sleep(1500);
  ```

  `ev()`（在页面里求值，`awaitPromise: true`）定义在这之后的 `:82-89`。`S` 在 `:58` 定义，`await S("Page.enable");` 在 `:59`，全文件只有这一处。每一页要打开 13 次（4 次主题、2 次动效、6 次截图、1 次导出加判据），再加 2 次键盘；这些打开都共用同一个 Chrome，所以会共用 HTTP 缓存。

- `assets/shell.html:20-27`，骨架的网页字体样式表异步加载：`<link rel="stylesheet" media="print" onload="this.media = 'all'" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:…&family=IBM+Plex+Sans:…&family=Newsreader:…&family=Noto+Serif+SC:…&display=swap">`。规划时实测（`eec315f`，对 `2026-10-23-6b6872b-027` 轮的五页）得到三点：
  - load 事件触发时，这张样式表已经取回，`media` 已换回 `all`。所以 load 之后 `media` 还是 `print`，就说明样式表没取到，不用轮询等它。
  - woff2 字体分片要等排版后才开始下载。Noto Serif SC 按 unicode-range 切成两百多片，每页只下用到的十几片。新 Chrome 打开的第一页，在原来截图的时刻（load 后 1.5 秒）还有 7 片没到，又过了 10 秒才到齐。
  - `document.fonts` 里每页还有 1–2 个状态恒为 `error` 的字体：`assets/show-me.css:964` 起用 `local()` 声明的兜底字体 `Han Serif Balanced`，本机没装时就是 `error`。它不在样式表请求的四个字族里，判断就位时要排除。

- `scripts/probe_round.mjs:413` 起是摘要：`let failed = false;`，每页打印一行（`<页名>: 无问题` 或问题列表）；`:459` 的 `if (PREV) {` 起与上一轮对比 `probe.json`（只比 `pages` 下的内容）和 30 张截图。最后 `process.exit(failed ? 1 : 0)`。

- 规划时用临时补丁让每个请求慢 4 秒（`Network.emulateNetworkConditions`，latency 4000）做过对照：
  - 旧探针：30 张截图 0 张相同，`probe.json` 14 处不同，退出码却是 0。
  - 本计划的探针：30/30，`probe.json` 相同。
  - 正常网络连跑三轮：30、29、30 张相同。29 那次不同的一张只差 24 个像素，集中在一块 14×3 像素的区域里，是抗锯齿噪声。

## Commands you will need

| Purpose  | Command                                                     | Expected on success                          |
| -------- | ----------------------------------------------------------- | -------------------------------------------- |
| JS 语法  | `node --check skills/show-me-html/scripts/probe_round.mjs`  | 无输出                                       |
| 格式     | `npx prettier --check <文件>`                               | `All matched files use Prettier code style!` |
| 文档门禁 | `make check`                                                | exit 0，`技能文档引用检查通过`               |
| 像素差   | `magick compare -metric AE <新图> <旧图> null:`（本机已装） | 打印不同的像素数                             |

命令都在仓库根目录跑。Step 3–5 的 shell 片段用 bash（本机默认 shell 是 fish，`VAR=$(…)` 赋值和 `${PIPESTATUS[0]}` 在 fish 里不成立）。每跑一轮探针约 2.5 分钟。

## Scope

**In scope**：`skills/show-me-html/scripts/probe_round.mjs`、`skills/show-me-html/scenarios/README.md`（第 4 步加一句）。

**Out of scope**：

- `scripts/render.mjs`、`scripts/cdp.mjs`、`scripts/build.py`：`build.py` 的截图、`--snap`、`--pdf` 走 `render.mjs` 的虚拟时间，会等网络请求结束，没有这个问题。
- `assets/shell.html` 的字体加载方式：异步加载是有意的（网络不通时首屏不卡），不改。
- `probe.json`：不加字段。对比只看 `pages`，加字段会让与旧轮次的对比多出差异。
- 单元测试：这个行为要真实 Chrome 和网络才能测，Step 3–5 的轮次和反证就是检查；不新增 `tests/` 里的测试。
- `plans/README.md`：审阅者维护。

## Git workflow

从本地 `main` 开分支 `advisor/028-show-me-html-probe-waits-for-fonts`。提交信息例如 `fix(show-me-html): probe_round waits for web fonts before screenshots`。pre-commit 会跑 prettier 和 `make check`。不要 push。

## Steps

### Step 1: 探针先等字体到齐

`scripts/probe_round.mjs` 里改五处。

**1a.** 文件头的功能清单，在 `//   - 场景判据：按 SCENARIO.md 的通过标准读数，再用真实按键操作各场景的交互` 这一行（`:9`）之后加一行：

<!-- prettier-ignore -->
```js
//   - 字体：每次打开页面先等网络字体到齐（至多 30 秒）再读数、截图；取不到时摘要报「字体未就绪」，退出码 1
```

**1b.** `:18` 的 `import { join, resolve } from "node:path";` 改为：

<!-- prettier-ignore -->
```js
import { basename, join, resolve } from "node:path";
```

**1c.** `:36` 的 `const sleep = (ms) => new Promise((r) => setTimeout(r, ms));` 之后（`const { send, until, close } = await launch(…)` 之前）插入下面这段，前面空一行：

<!-- prettier-ignore -->
```js

// 截图前等网络字体就位。骨架的字体样式表异步加载（shell.html：media="print"，onload 换回 all），
// load 事件时样式表已经取回，但 woff2 分片要排版后才开始下载；只等固定的 1.5 秒时，慢的分片会让截图
// 落在兜底字体上，与上一轮逐字节对比时整页字形都不同。就位返回 null，否则返回原因。
// show-me.css 用 local() 声明的兜底字体（Han Serif Balanced）本机没装时状态是 error，它不在样式表的字族里，不算。
const FONT_WAIT_MS = 30000;
const FONTS_READY = `(async () => {
  const link = document.querySelector('link[rel="stylesheet"][href*="fonts.googleapis.com"]');
  if (!link) return null;
  if (link.media !== "all" || !link.sheet) return "字体样式表没有取到";
  const families = [...link.href.matchAll(/family=([^:&]+)/g)].map((m) => decodeURIComponent(m[1].replace(/\\+/g, " ")));
  const end = Date.now() + ${FONT_WAIT_MS};
  for (;;) {
    document.body.getBoundingClientRect();
    await Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, Math.max(0, end - Date.now())))]);
    const faces = [...document.fonts].filter((f) => families.includes(f.family.replace(/"/g, "")));
    const bad = faces.filter((f) => f.status === "error").map((f) => f.family);
    if (bad.length) return "字体分片下载失败：" + [...new Set(bad)].join("、");
    if (!faces.some((f) => f.status === "loading")) return null;
    if (Date.now() >= end) return "字体 ${FONT_WAIT_MS / 1000} 秒内没有下完";
    await new Promise((r) => setTimeout(r, 50));
  }
})()`;
// 第一次没等到字体就记下原因，之后的页面不再等（免得每次打开都等满 30 秒），摘要里报出
let fontTrouble = null;
```

注意 `replace(/\\+/g, " ")` 里是两个反斜杠：它在模板字符串里，传进页面时变成 `/\+/g`。

**1d.** 把 `open()` 里的 `ev` 定义挪到 `S` 之后。也就是把

<!-- prettier-ignore -->
```js
  const S = (m, p) => send(m, p, s);
  await S("Page.enable");
```

改为

<!-- prettier-ignore -->
```js
  const S = (m, p) => send(m, p, s);
  const ev = async (expr) =>
    (
      await S("Runtime.evaluate", {
        expression: expr,
        returnByValue: true,
        awaitPromise: true,
      })
    ).result.value;
  await S("Page.enable");
```

**1e.** 同一个函数里，把

<!-- prettier-ignore -->
```js
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
```

改为

<!-- prettier-ignore -->
```js
  await loaded;
  if (!fontTrouble) {
    const why = await ev(FONTS_READY);
    if (why) fontTrouble = `${basename(file, ".html")}：${why}`;
  }
  await sleep(1500);
```

`sleep(1500)` 保留：动效检查读的是「1.5 秒后仍在运行的动画」。字体只在每页第一次打开时真正要等，之后命中缓存，等待几乎为零，动效读数不受影响。

**1f.** 摘要里，在 `if (PREV) {`（`:459`）之前插入下面这段，后面空一行：

<!-- prettier-ignore -->
```js
if (fontTrouble) {
  failed = true;
  console.log(
    `字体未就绪（${fontTrouble}），之后的页面不再等字体：截图落在兜底字体上，与上一轮的对比不可信，网络恢复后重跑`
  );
}
```

**Verify**：

- `node --check skills/show-me-html/scripts/probe_round.mjs` 无输出。
- `npx prettier --check skills/show-me-html/scripts/probe_round.mjs` → `All matched files use Prettier code style!`（不要跑 `--write`；不通过说明粘贴时改了缩进或空行，对照上面的代码块改回）。
- 计数（每条一个 `grep -c '<模式>' skills/show-me-html/scripts/probe_round.mjs`）：`FONT_WAIT_MS = 30000` → `1`；`fontTrouble` → `5`；`const ev = async` → `1`；`await sleep(1500)` → `1`；`basename, join, resolve` → `1`。

### Step 2: 文档

`scenarios/README.md`「轮次流程」第 4 步，在 `   场景判据的选择器按当前基线页面写：重新生成过页面、摘要报「未命中」时，按 SCENARIO.md 把选择器改到新页面上。` 这一行之后加一行（行首三个空格，与上一行对齐）：

<!-- prettier-ignore -->
```markdown
   探针每次打开页面先等网络字体到齐（至多 30 秒）再截图；取不到字体时摘要多一行「字体未就绪」、退出码 1，这一轮的截图对比不可信，联网后重跑。
```

**Verify**：`npx prettier --check skills/show-me-html/scenarios/README.md` 通过；`grep -c '字体未就绪' skills/show-me-html/scenarios/README.md` → `1`；`make check` → exit 0。

### Step 3: 正常网络下连跑两轮

本计划不改页面、骨架和 `build.py`，所以五页 HTML 直接复制上一轮的，不用重建；轮次建在临时目录里，不进 `scenarios/rounds/`。上一轮 `2026-10-23-6b6872b-027` 只存在于主检出目录，下面用绝对路径只读它。用 bash 跑：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-6b6872b-027
T=$(mktemp -d)
for i in 1 2; do
  mkdir -p "$T/r$i"
  for n in status-report approach-compare code-review concept-explainer triage-board; do cp "$PREV/$n.html" "$T/r$i/"; done
  node skills/show-me-html/scripts/probe_round.mjs "$T/r$i" "$PREV" | grep -E '^[a-z-]+: |字体|probe\.json|截图：|Markdown 不同'
  echo "exit=${PIPESTATUS[0]}"
done
echo "$T"
```

**Verify**（每一轮）：

- 五行 `无问题`，没有 `字体未就绪`，`exit=0`。
- `与上一轮对比：probe.json 相同`，没有 `Markdown 不同`。
- `截图：30/30 张逐字节相同`。偶尔有一两张不同时，用 `magick compare -metric AE "$T/r<i>/_probe/<文件>" "$PREV/_probe/<文件>" null:` 量一下：不到 100 个像素就是抗锯齿噪声，在汇报里列出文件名和像素数即可（规划时遇到过一张 24 像素）。上千、上万个像素，或者整页文字都不同，说明修法没生效，按 STOP 处理；**不要靠重跑把它跑过去**。

### Step 4: 反证：网络变慢时，等字体与不等字体的区别

用一个临时补丁让每个网络请求慢 4 秒。在 `scripts/probe_round.mjs` 唯一的 `  await S("Page.enable");` 之后临时加两行（`grep -c 'await S("Page.enable");' skills/show-me-html/scripts/probe_round.mjs` 应为 `1`）：

<!-- prettier-ignore -->
```js
  await S("Network.enable");
  await S("Network.emulateNetworkConditions", { offline: false, latency: 4000, downloadThroughput: -1, uploadThroughput: -1 });
```

然后用 bash 跑两次，第二次之前把 `const FONT_WAIT_MS = 30000;` 临时改成 `const FONT_WAIT_MS = 0;`（相当于不等字体）：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-6b6872b-027
R=$(mktemp -d)
for n in status-report approach-compare code-review concept-explainer triage-board; do cp "$PREV/$n.html" "$R/"; done
node skills/show-me-html/scripts/probe_round.mjs "$R" "$PREV" | grep -E '^[a-z-]+: |字体|probe\.json|截图：' | cut -c1-120
echo "exit=${PIPESTATUS[0]}"
```

**Verify**：

- `FONT_WAIT_MS = 30000`：五行 `无问题`，没有 `字体未就绪`，`probe.json 相同`，`截图：30/30`，`exit=0`。
- `FONT_WAIT_MS = 0`：多一行 `字体未就绪（status-report：字体 0 秒内没有下完），之后的页面不再等字体：…`，`probe.json` 有十几处不同（规划时 14 处），`截图：0/30`，`exit=1`。

做完把两处临时改动都撤掉：

- `grep -c 'emulateNetworkConditions' skills/show-me-html/scripts/probe_round.mjs` → `0`。
- `grep -c 'FONT_WAIT_MS = 30000' skills/show-me-html/scripts/probe_round.mjs` → `1`。
- `npx prettier --check skills/show-me-html/scripts/probe_round.mjs` 通过。

### Step 5: 断网时报出来

让 Chrome 走一个不存在的代理，字体样式表就取不到。用 bash 跑：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-6b6872b-027
R=$(mktemp -d)
for n in status-report approach-compare code-review concept-explainer triage-board; do cp "$PREV/$n.html" "$R/"; done
HTTPS_PROXY=http://127.0.0.1:9 NO_PROXY= no_proxy= node skills/show-me-html/scripts/probe_round.mjs "$R" "$PREV" | grep -E '字体|截图：' | cut -c1-120
echo "exit=${PIPESTATUS[0]}"
```

**Verify**：

- 有一行 `字体未就绪（status-report：字体样式表没有取到），…`。
- `截图：0/30`，`exit=1`。
- 用时和正常一轮差不多（规划时 136 秒）：样式表失败是立刻判出来的，不会等满 30 秒。

不要在命令里打印或读取你环境里原有的代理变量；上面的前缀只对这一条命令生效。

## Test plan

- 不新增单元测试，原因见 Scope：这个行为离不开真实 Chrome 和网络。
- Step 3：正常网络连跑两轮，首跑就是 30/30，不靠重跑。
- Step 4：反证。请求变慢时，等字体能得到 30/30；不等字体是 0/30，而且会报出来、退出码 1。
- Step 5：断网时报「字体样式表没有取到」，退出码 1，不额外耗时。

## Done criteria

- [ ] Step 1 的语法、格式和五条计数全部满足
- [ ] Step 3 两轮：五页 `无问题`，`exit=0`，`probe.json 相同`，截图 30/30；如有不同，每张都不到 100 个像素
- [ ] Step 4：等字体时 30/30、`exit=0`；`FONT_WAIT_MS = 0` 时出现 `字体 0 秒内没有下完`、`exit=1`；临时改动已撤掉
- [ ] Step 5：出现 `字体样式表没有取到`，`exit=1`
- [ ] `make check` exit 0；`git status` 只显示 `probe_round.mjs` 和 `scenarios/README.md`

## STOP conditions

- Drift check 有输出，且「Current state」里的引文对不上。
- Step 3 有截图差上千像素，或文字整页不同；或 `probe.json` 不同；或出现 `字体未就绪`（说明这台机器当时取不到字体，先确认网络，再汇报）。
- Step 4 等字体时仍不是 30/30，或者 `FONT_WAIT_MS = 0` 时没有报 `字体未就绪`。
- Step 5 的退出码是 0，或者用时比正常一轮多出几分钟。
- 为了让检查通过，需要改 Scope 之外的文件。

## Maintenance notes

- 合入后，新计划和审阅不再写「冻结场景首跑不同先重跑一次」：首跑就不该有字形差异，有就是问题。026 已经写了这句，留着无害，不改。
- `FONT_WAIT_MS` 是每页第一次打开时的上限。慢网络下第一页可能要等十几秒；整轮比原来多十几秒属于正常。
- 字体判断只认 `fonts.googleapis.com` 那张样式表请求的字族。以后骨架换字体来源（例如自托管），要同步改 `FONTS_READY` 里的选择器，否则它会直接返回「就位」。
- 第一次没等到字体之后，后面的页面都不再等，所以只报第一页的原因。这样断网时一轮不会多出半小时；代价是汇报里只看得到第一个出问题的页面。
- `render.mjs`（`build.py` 的截图、`--snap`、`--pdf`）靠虚拟时间等网络请求，没有这个问题。022 记录过另一种情况：某个字体请求一直挂着，会拖住虚拟时间，直到 90 秒超时。那是另一件事。
