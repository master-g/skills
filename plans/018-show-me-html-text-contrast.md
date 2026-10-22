# Plan 018: show-me-html 次要文字与图内文字的对比度达到 4.5:1，构建加文字对比度检查

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat fff32ba..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/assets/charts.js skills/show-me-html/assets/gallery skills/show-me-html/scripts/build.py skills/show-me-html/tests/test_build.py skills/show-me-html/references/visual-system.md skills/show-me-html/references/charts.md skills/show-me-html/references/compose-and-check.md skills/show-me-html/references/anti-patterns.md`
> 计划 017 先合入时，`charts.js`（`G.type` 一行）、gallery 四页、`build.py`（字号下限几行）、`test_build.py`、`charts.md`、`anti-patterns.md` 会出现在输出里，属于预期，本计划按 017 已合入来写行号。出现 `show-me.css`、`visual-system.md`、`compose-and-check.md` 的改动，或者下面「Current state」的摘录对不上，就是 STOP 条件。
>
> **2026-10-22 补充（写计划 020–027 时加）**：以下改动也属于预期，与本计划的锚点不重叠。
>
> - `7c94bce` 在 `show-me.css` 主打印块末尾加了 `@page { size: A4 }` 和几条分页规则（之后的行号往后挪约 18 行），并改了 `visual-system.md`「响应式与打印」的打印一行；同日那一行的措辞又收窄过一次。
> - 计划 020（维护者定在本计划之前执行）改了 `build.py` 里三处 Chrome 启动参数、新增 `chrome_proxy_args()`，`test_build.py` 多一个测试，`components.md`、`layouts.md` 各改一处。020 合入后，本计划里所有 `Ran 48 tests` / `Ran 49 tests` 都按多 1 个计。
>
> **2026-10-22 派发前复核（advisor，HEAD `15d5ddc`，017 与 020 都已合入）**：「Current state」的锚点逐条核对过，都还在。三处按此执行：
>
> - 测试数：Step 1–3 的 `Ran 48 tests` 实际是 `Ran 49 tests`，Step 4 及以后的 `Ran 49 tests` 实际是 `Ran 50 tests`。
> - F3 那两个 `txt(…)` 调用在仓库里被 prettier 排成了多行（`txt(` / `s,` / `label({ x: gap, y: Y0 - 34, "text-anchor": "middle" }),` / `"台风"` / `);`，第二个同理），与 Step 5 第 3 小步的引文换行不同；按内容找到这两段整体替换即可，不算对不上。
> - Step 7 第 2 小步的上一轮改用 `2026-10-22-6d39fa5-printbreak`（最近一轮；020 的回归与它逐字节相同）。原写的 `2026-10-16-7454494-base` 与当前 main 之间本来就有 10 处与本计划无关的 `probe.json` 差异。
>
> 本文件里的 js / css / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P1
- **Effort**: M（三个 token、四条 CSS 规则、运行时两处、构建探针一段、一个测试、四份文档，外加 gallery 里 29 张图的文字颜色）
- **Risk**: MED（全站次要文字变深一档，主角色文字变成偏砖红的深一档；新检查报 ERROR，重新构建的旧页面可能因此失败，见 Maintenance notes）
- **Depends on**: 建议在 `plans/017-show-me-html-chart-type-scale.md` 之后执行：两份都改 `charts.js` 的 `G` 与 gallery 图块，先改字号再改颜色，diff 不互相覆盖；本计划的工作清单是在 017 的改档之后量的。
- **Category**: bug
- **Planned at**: commit `fff32ba`, 2026-10-21

## Why this matters

show-me-html 把素材做成单文件 HTML 页面，视觉系统 `assets/show-me.css` 用「墨」`--ink` 与「纸」`--paper` 两极按比例混出一串明度阶（`--ink-90 … --ink-4`）。维护者 2026-10-21 反馈一页报告「一些脚注颜色过淡，导致对比度不足」。实测（WCAG 2.x 对比度公式）：

| 文字                                                     | 现在的颜色                                                  | 亮色主题                     | 暗色主题 |
| -------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------- | -------- |
| 图下来源行 `.fig-src`、图型标签 `.fig-id`（卡面上）      | `--ink-45`                                                  | 2.82:1                       | 3.27:1   |
| 表格与指标带下的来源行 `.src`（页面底色上）              | `--ink-45`                                                  | 3.09:1                       | 3.55:1   |
| 图内刻度与单位（运行时 `tick()` 的默认色 `G.ink.quiet`） | `--ink-45`                                                  | 2.82:1                       | 3.27:1   |
| 单位行、表头、指标带标签等（`--color-muted-foreground`） | `--ink-60`                                                  | 4.43:1                       | 5.11:1   |
| 主角色写字（G4 图例「300106 连接重置」、G10「15.1%」）   | `--hero` `#f5572f`                                          | 2.65:1                       | 4.71:1   |
| 告急徽标 `.badge[data-variant="destructive"]` 的字       | `--color-destructive`（= `--hero`）                         | 2.40:1（在它自己的淡橙底上） | 4.05:1   |
| 告急按钮 `.btn[data-variant="destructive"]` 的字         | `--destructive-foreground`（= `--paper`），压在 `--hero` 上 | 2.90:1                       | 5.15:1   |
| 链接样式按钮 `.btn[data-variant="link"]`、正文链接悬停色 | `--link-accent`（主角色掺三成墨）                           | 4.40:1（卡面上）             | 6.73:1   |

WCAG AA 要求正文 4.5:1，大字（≥ 24px，或 ≥ 18.66px 粗体）3:1。上表亮色一列全都不到。`references/compose-and-check.md` 也把它列为「已知缺口：没有自动的对比度检查」。

**维护者决定（2026-10-21）**：

- 所有次要文字 ≥ 4.5:1：新增明度阶 `--ink-65`，`--muted-foreground` 从 `--ink-60` 改到 `--ink-65`（卡面上亮 5.16:1、暗 5.86:1），来源行、图型标签、图内刻度都改用它。层级改靠字号与字体区分。
- 主角色写字加一个专用色 `--hero-text` = 主角色掺四成墨（亮 5.29:1、暗 7.50:1），图里叫 `--chart-hero-text`。图形（柱、点、线）仍用原来的 `--hero`。

上表最后两行是 advisor 复核组件夹具 `tests/fixtures/component-states.html` 时补查出来的：不改的话，新检查会拦下所有用了告急按钮、或在卡片里放了链接样式按钮的页面。改法沿用上面两条决定：告急按钮的字改用固定深墨 `--ink-fixed`（压在主角色上两种主题都是 5.15:1；暗色主题下它本来就是深色字），链接强调色改为 `--hero-text`。维护者 2026-10-22 派发时确认了告急按钮的这个改法（橙底深字），没有采用「底色改 `--hero-text`、字仍用纸色」的备选。

本计划还给构建加一道文字对比度检查（ERROR），在亮色主题下量每段 HTML 文字和每个 SVG 文字，免得同样的问题回到页面里。是 ERROR 还是 WARN 由 advisor 定，维护者可改，Step 3 末尾写了 WARN 变体。

**advisor 的预演**：在 scratchpad 的副本里，在 017 的代码改动之后叠加本计划 Step 1–4 与 Step 5 的第 1 小步（换 gallery 页头的两个常量）。单元测试 49 个 OK；五个冻结场景页和组件夹具 `component-states.html`（加一个卡片内的链接按钮）全部 `自检通过。`；gallery 总览页上检查报出 29 张图共 33 组、176 处文字低于 4.5:1。这些都是图块里写死的颜色，就是 Step 5 的工作清单。维护者那页重建后报出的 4 组（页面自己写的 `I45` 和橙色文字）也在意料之中。advisor 第一次在组件夹具上跑时报 0 处，那是因为夹具没有 `<head>` 主题脚本，跟着本机暗色外观跑了；Step 3 固定亮色以后才报出告急按钮与链接按钮两处。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `fff32ba`；017 合入后 `references/charts.md` 第 147 行以后的行号往后挪 1 行，其余文件的行号不变。行号对不上时以引文为准。

- `assets/show-me.css:40-43`（派生层的明度阶，挂在 `:root, .card[data-variant="ink"]` 上，暗卡内会重算一遍）：

  <!-- prettier-ignore -->
  ```css
    --ink-90: color-mix(in oklab, var(--ink) 90%, var(--paper));
    --ink-70: color-mix(in oklab, var(--ink) 70%, var(--paper));
    --ink-60: color-mix(in oklab, var(--ink) 60%, var(--paper));
    --ink-45: color-mix(in oklab, var(--ink) 45%, var(--paper));
  ```

- `assets/show-me.css:61-62`、`65-66` 与 `70-71`（角色层）：

  <!-- prettier-ignore -->
  ```css
    --muted: var(--ink-8);
    --muted-foreground: var(--ink-60);
  ```

  <!-- prettier-ignore -->
  ```css
    --destructive: var(--hero);
    --destructive-foreground: var(--paper);
  ```

  <!-- prettier-ignore -->
  ```css
    --link-accent: color-mix(in oklab, var(--hero) 70%, var(--ink));
    --ink-fixed: #1c1c1a;
  ```

  `--ink-fixed` 是固定的深墨色，不随主题翻转，目前没有任何地方用它；本计划用它给告急按钮和主角色色块上的字着色。`--color-destructive-foreground`（= `--destructive-foreground`）只用在 `.btn[data-variant="destructive"]` 的字色（第 298 行）；`--link-accent` 用在 `.btn[data-variant="link"]` 的字色（第 292 行）和正文链接 `main a` 的悬停色（第 1279–1280 行）。正文链接平时是正文色加主角色下划线（第 1270 行注释：「clay 直接当文字色只有 2.9:1」），不受影响。`@media print` 里另有一组写死的打印色（含 `--destructive-foreground: #fff;`），不动。

- `assets/show-me.css:94-100`（图表角色）：

  <!-- prettier-ignore -->
  ```css
    /* 图表：明度即数据。--chart-1 最重要（最黑，深色下最亮），依次变浅；
       --chart-hero 只给一张图里的一个主角元素。 */
    --chart-1: var(--ink);
    ...
    --chart-hero: var(--hero);
  ```

- `assets/show-me.css:427-439`（告急徽标）：

  <!-- prettier-ignore -->
  ```css
  .badge[data-variant="destructive"] {
    border-color: color-mix(
      in oklab,
      var(--color-destructive) 38%,
      var(--color-border)
    );
    background: color-mix(
      in oklab,
      var(--color-destructive) 12%,
      var(--color-card)
    );
    color: var(--color-destructive);
  }
  ```

- `assets/show-me.css` 里正好有三处 `  color: var(--ink-45);`：`.fig-id`（第 1466 行）、`.fig-src, .src`（第 1480 行）、`.fig-status [data-pin]`（第 1515 行）。`grep -n '  color: var(--ink-45);' skills/show-me-html/assets/show-me.css` 应输出这三行。
- `assets/charts.js:88-94` 与 `110-122`（017 合入后 `G.type` 那一行已是 `tick: 9, label: 10, value: 10`，行号不变）：

  <!-- prettier-ignore -->
  ```js
      ink: {
        strong: "var(--ink)",
        data: "var(--ink-70)",
        quiet: "var(--ink-45)",
        mass: "var(--ink-30)",
        guide: "var(--ink-30)",
      },
  ```

  <!-- prettier-ignore -->
  ```js
    const tick = (a) => ({
      "font-size": G.type.tick,
      fill: G.ink.quiet,
      "letter-spacing": G.type.track,
      ...a,
    });
    const value = (a, hero) => ({
      "font-size": G.type.value,
      "font-weight": 600,
      fill: hero ? "var(--chart-hero)" : G.ink.strong,
      "letter-spacing": G.type.track * 0.6,
      ...a,
    });
  ```

  `G.ink.quiet` 同时被很多图块拿来画线和面（`grep -c 'G.ink.quiet' assets/gallery/*.html` 合计约 100 处），所以不改它的值，另加一个文字专用的 `note`。

- 四个 gallery 页（`assets/gallery/basics.html:885-898`、`big.html:274-287`、`editorial.html:956-969`、`glance.html:930-943`）页尾脚本的开头完全相同：

  <!-- prettier-ignore -->
  ```js
          const INK = "var(--ink)",
            PAPER = "var(--paper)",
            HERO = "var(--chart-hero)";
          const I90 = "var(--ink-90)",
            ...
            I8 = "var(--ink-8)";
          const MUTED = I45,
            GRID = I14,
            FAINT = I22;
  ```

  `MUTED` 只出现在 `fill: MUTED`（全在 glance，16 处），都是文字。

- `scripts/build.py` 的 `PROBE`（普通三引号字符串，不是 % 格式化；JS 里的反斜杠要写成 `\\`）。正文字号检查那段定义了本计划要复用的三个变量（第 847–851 行）：

  <!-- prettier-ignore -->
  ```js
      var text = [], doc = document.getElementById('doc') || document.body;
      var name = function(el){
        return el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim()
          ? '.' + el.className.trim().split(/\\s+/).slice(0,2).join('.') : '');
      };
      var shown = function(el){ var r = el.getBoundingClientRect(); return r.width >= 2 && r.height >= 2; };
  ```

  结尾（第 884–888 行）：

  <!-- prettier-ignore -->
  ```js
      document.title = 'PROBE|' + sw + '|' + cw + '|' + over.slice(0, 4).join('  ') + '|' + small.join('；')
        + '|' + text.slice(0, 4).join('；') + (text.length > 4 ? ' 等 ' + text.length + ' 处' : '')
        + '|' + diag.join('；');
    }, 1500);
  });</script>
  ```

- `scripts/build.py` 的 `render_check()`：第 1046–1047 行把探针拼到页面后面写进临时文件，第 1058 行解析结果，第 1081–1085 行是最后一项（示意图字号）：

  ```python
          probe = Path(td) / "probe.html"
          probe.write_text(html + PROBE, encoding="utf-8")
  ```

  ```python
              m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)</title>", out, re.S)
  ```

  ```python
              diag = htmllib.unescape(m.group(6).strip())
              if diag:
                  issues.append(f"{cw}px 下示意图字号渲染后低于 8px：{diag}。宽版缩得太小就画窄版，"
                                "窄版控制 viewBox 宽度（diagrams.md「窄屏另画一版」）")
      return issues, measured, True
  ```

  **主题**：页面的主题由 `<head>` 里的防闪烁脚本（读 `localStorage["show-me-theme"]`）和骨架脚本 `shell.js`（读 `document.documentElement.dataset.theme`，没有就按系统）决定。`render_check` 现在不设主题，所以跟着本机外观走（advisor 的机器是暗色，测出来是暗色的数）。测试夹具 `tests/fixtures/minimal-shell.html` 没有那段防闪烁脚本，只写 localStorage 管不住它；要同时设 `dataset.theme`。

- `tests/test_build.py`：渲染类测试的结构照抄 `test_render_check_flags_shrunk_stat_num`（`@unittest.skipUnless(… find_chrome …)`、`self.copy_fixture()`、往 `</main>` 前插标记、往 `<!--SHOW-ME:JS-->` 后插脚本、跑不带 `--no-render` 的构建、`subTest` 写正反例）。新测试插在 `test_render_check_measures_only_the_shown_diagram_variant` 那个测试的装饰器行之前。
- `references/visual-system.md`：「Token 分层」一节的分层表里，明度阶一行写着「不改，加档要说明用途」；角色表（第 35–46 行）有「弱化面与次要文字 | `--color-muted`, `--color-muted-foreground`」一行。「明度即数据」一节在第 48–58 行，下一节是「## 公式」。
- `references/compose-and-check.md:121`：

  <!-- prettier-ignore -->
  ```markdown
  **已知缺口**：没有自动的对比度检查。自有 token 的前景/背景组合在 component-state fixture 中统一维护，`build.py` 会对写死的颜色报 WARN；页面自己搭出来的颜色组合（色调面上再叠一层、自绘 SVG 的填充色）仍然需要人工检查。截图可以用已装的 `ego-browser` skill。
  ```

- `references/charts.md`：「硬规则」下的 `**颜色**` 小节（第 130 行起），第一条是「**明度即数据**」，第二条是「**一律实心**」；「发丝语法」表格里 `tick()` / `value()` / `label()` 那一行的「用在哪里」写着「刻度与单位（等宽、加字距、quiet 墨）/ 数值（600、主角时 hero 色）/ 类目名（正文字）」；「运行时与查代码」一节的「页面脚本模板」（第 258–265 行）：

  <!-- prettier-ignore -->
  ```js
    const INK = "var(--ink)",
      PAPER = "var(--paper)",
      HERO = "var(--chart-hero)";
    const I70 = "var(--ink-70)",
      I45 = "var(--ink-45)",
      I30 = "var(--ink-30)",
      I22 = "var(--ink-22)",
      I14 = "var(--ink-14)";
  ```

- `references/anti-patterns.md`：名册表最后一行是第 11 条（若 019 先合入则是第 12 条）。

**仓库约定**：`show-me.css` 只有原语层（`--ink`、`--paper`、`--hero`、`--tone-*`）允许字面色值，派生层一律 `color-mix`；`tests/test_build.py` 的 `test_literal_colors_live_only_in_primitive_layer` 盯着字面色的个数（本计划不加字面色）。CSS 注释用中文写「为什么」。文档按标题名引用章节（「对比度」），不按编号，`make check` 会检查，所以构建报错文案里引用的「visual-system.md「对比度」」必须在 Step 6 真的建出这一节。

## Commands you will need

在仓库根目录执行：

| Purpose      | Command                                                                                                                                | Expected on success                                               |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 单元测试     | `python3 -m unittest skills.show-me-html.tests.test_build`                                                                             | 末行 `OK`；Step 4 之后 `Ran 49 tests`（约 170 秒，需本机 Chrome） |
| 单个新测试   | `python3 -m unittest skills.show-me-html.tests.test_build.BuildCliTests.test_render_check_flags_low_contrast_text -v`                  | `ok`                                                              |
| 语法检查     | `python3 -W error::SyntaxWarning -c "import ast,pathlib; ast.parse(pathlib.Path('skills/show-me-html/scripts/build.py').read_text())"` | 无输出、exit 0                                                    |
| 图库完整构建 | `G=$(mktemp -d) && python3 skills/show-me-html/scripts/gallery.py --out "$G" --shots`                                                  | 见 Step 5、Step 7                                                 |
| 文档门禁     | `make check`                                                                                                                           | exit 0                                                            |
| 格式化       | `npx prettier --write <改过的文件>`                                                                                                    | exit 0                                                            |

不要用 pytest（未安装）。

## Scope

**In scope**：

- `skills/show-me-html/assets/show-me.css`（派生层：新增 `--ink-65`、`--hero-text`、`--chart-hero-text`，改 `--muted-foreground`、`--destructive-foreground`、`--link-accent`；三处 `color: var(--ink-45)`；告急徽标的 `color`）
- `skills/show-me-html/assets/charts.js`（`G.ink` 加一项、`tick()` 与 `value()` 的默认色、`G` 上方注释一句）
- `skills/show-me-html/assets/gallery/{basics,big,editorial,glance}.html`：页头两个常量；Step 5 清单里 29 张图的**文字** `fill`
- `skills/show-me-html/scripts/build.py`（`PROBE` 末尾、`render_check()` 的探针写入、正则与新的一项报错）
- `skills/show-me-html/tests/test_build.py`（新增一个测试）
- `skills/show-me-html/references/{visual-system,charts,compose-and-check,anti-patterns}.md`

**Out of scope**：

- 语法高亮色 `--syn-*`：注释（`--ink-45`）和字符串（`--ink-60`）在代码块底色上只有 2.6–4.1:1，同样不达标，但维护者没提到代码块，改它会动所有代码块的观感。检查跳过 `pre` 里的文字，问题记在 `plans/README.md` 的「未规划」里。
- 图形（线、面、点、网格）的颜色：只改文字的 `fill`。`G.ink.quiet` 的值不变。
- 字号与排法：属于计划 017。
- `@media print` 里那组写死的打印色。
- `MAINTENANCE.md`、`SKILL.md`、维护者 bedrock 仓库里的页面。

## Git workflow

- 分支：`advisor/018-show-me-html-text-contrast`。
- conventional commits，scope 写技能名。建议的提交：
  1. `fix(show-me-html): secondary text and hero text reach 4.5:1`（Step 1–2）
  2. `feat(show-me-html): render check flags low-contrast text`（Step 3–4）
  3. `fix(show-me-html): gallery text colors clear the contrast check`（Step 5）
  4. `docs(show-me-html): contrast rules for text, hero text and text on fills`（Step 6）
- pre-commit 会跑 prettier 和 `make check`。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`。

## Steps

### Step 1: token 与骨架样式

在 `assets/show-me.css` 里：

1. 在 `--ink-70: …;` 这一行之后插入：

   <!-- prettier-ignore -->
   ```css
     --ink-65: color-mix(in oklab, var(--ink) 65%, var(--paper)); /* 次要文字：卡面上亮 5.2:1、暗 5.9:1 */
   ```

2. `--muted-foreground: var(--ink-60);` 改为 `--muted-foreground: var(--ink-65);`。
3. `--destructive-foreground: var(--paper);` 改为：

   <!-- prettier-ignore -->
   ```css
     --destructive-foreground: var(--ink-fixed); /* 纸色字压在主角色上只有 2.9:1；固定深墨两种主题都是 5.2:1 */
   ```

   告急按钮在亮色主题下从「橙底白字」变成「橙底深字」，与暗色主题下的样子一致。

4. 把 `--link-accent: color-mix(in oklab, var(--hero) 70%, var(--ink));` 这一行替换为三行：

   <!-- prettier-ignore -->
   ```css
     /* 主角色写字：纯 --hero 在亮色卡面上只有 2.7:1，掺四成墨后亮 5.3:1、暗 7.5:1；图形仍用 --hero */
     --hero-text: color-mix(in oklab, var(--hero) 60%, var(--ink));
     --link-accent: var(--hero-text); /* 原为主角色掺三成墨，卡面上只有 4.4:1 */
   ```

5. 在 `--chart-hero: var(--hero);` 这一行之后插入 `  --chart-hero-text: var(--hero-text);`。
6. 把三处 `  color: var(--ink-45);`（`.fig-id`、`.fig-src, .src`、`.fig-status [data-pin]`）都改为 `  color: var(--color-muted-foreground);`。
7. `.badge[data-variant="destructive"]` 规则里的 `color: var(--color-destructive);` 改为 `color: var(--hero-text);`（边框和底色不变；改后字在它自己的淡橙底上亮 4.77:1、暗 6.44:1）。

**Verify**: `grep -c '  color: var(--ink-45);' skills/show-me-html/assets/show-me.css` → `0`；`grep -c 'ink-65' skills/show-me-html/assets/show-me.css` → `2`；`grep -c 'hero-text' skills/show-me-html/assets/show-me.css` → `4`（定义、`--link-accent`、`--chart-hero-text`、徽标各一行）；`grep -c 'destructive-foreground: var(--ink-fixed)' skills/show-me-html/assets/show-me.css` → `1`；单元测试 → `OK`，`Ran 48 tests`。

### Step 2: 运行时的文字默认色

在 `assets/charts.js` 里：

1. `G.ink` 里 `quiet: "var(--ink-45)",` 之后加一行：

   <!-- prettier-ignore -->
   ```js
         note: "var(--color-muted-foreground)",
   ```

   并在 `G` 上方那段注释里「网格用 ink-30 而非更浅一档：深色主题下 ink-22 的发丝几乎看不见。」那一句之后补一句（同一段注释里另起一行，保持 `     ` 缩进）：`文字不用 quiet / mass / guide，它们是线和面的墨；次要文字用 note（卡面上 5.2:1）。`

2. `tick()` 里 `fill: G.ink.quiet,` 改为 `fill: G.ink.note,`。
3. `value()` 里 `fill: hero ? "var(--chart-hero)" : G.ink.strong,` 改为 `fill: hero ? "var(--chart-hero-text)" : G.ink.strong,`。

**Verify**: `grep -c 'G.ink.note' skills/show-me-html/assets/charts.js` → `1`；`grep -c 'chart-hero-text' skills/show-me-html/assets/charts.js` → `1`；单元测试 → `OK`，`Ran 48 tests`。

### Step 3: 构建探针量文字对比度

1. 在 `scripts/build.py` 的 `PROBE` 里，找到 `document.title = 'PROBE|' + sw + …` 这一行（4 个空格缩进），在它**正上方**插入下面这段（advisor 在 scratchpad 里跑通过；里面没有反斜杠，可以原样粘贴）：

   <!-- prettier-ignore -->
   ```js
       // 文字对比度（visual-system.md「对比度」）：render_check 把页面固定在亮色主题下量，亮色是明度阶与主角色最差的一侧。
       // 颜色先经 canvas 解析成 sRGB（color-mix、oklab 也读得出），再按 WCAG 2.x 算；正文要 4.5:1，24px 以上或 18.66px 以上的粗体要 3:1
       var cv = document.createElement('canvas'); cv.width = cv.height = 1;
       var cx = cv.getContext('2d', {willReadFrequently: true});
       var rgba = function(c){ cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); return cx.getImageData(0, 0, 1, 1).data; };
       var lum = function(a){
         var f = function(v){ v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
         return 0.2126 * f(a[0]) + 0.7152 * f(a[1]) + 0.0722 * f(a[2]);
       };
       var ratio = function(a, b){ var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
       var need = function(px, weight){ return px >= 24 || (px >= 18.66 && weight >= 700) ? 3 : 4.5; };
       // 盒子的底色：往上找第一个不透明的背景
       var boxBg = function(el){
         for (var p = el; p && p.nodeType === 1; p = p.parentElement) {
           var v = rgba(getComputedStyle(p).backgroundColor);
           if (v[3] > 200) return v;
         }
         return rgba(getComputedStyle(document.body).backgroundColor);
       };
       // SVG 文字的底色：文字中心往下第一个有填充的图形，没有就是图所在的卡面
       var SHAPE = {rect: 1, circle: 1, ellipse: 1, path: 1, polygon: 1};
       var svgBg = function(t){
         var r = t.getBoundingClientRect(), stack = document.elementsFromPoint(r.left + r.width / 2, r.top + r.height / 2);
         for (var i = 0; i < stack.length; i++) {
           var e = stack[i], tag = e.tagName.toLowerCase();
           if (e === t || e.closest('text')) continue;
           if (e.namespaceURI !== 'http://www.w3.org/2000/svg' || tag === 'svg') break;
           if (!SHAPE[tag]) continue;
           var cs = getComputedStyle(e), v = rgba(cs.fill);
           if (cs.fill !== 'none' && v[3] > 128 && parseFloat(cs.fillOpacity) * parseFloat(cs.opacity) > 0.5) return v;
         }
         return boxBg(t.closest('svg'));
       };
       var dim = [], dimSeen = {};
       var dimNote = function(where, cr, s){
         var k = where + cr.toFixed(2);
         if (dimSeen[k]) { dimSeen[k].n++; return; }
         dimSeen[k] = {s: where + '「' + s.split('|').join('/').slice(0, 10) + '」' + cr.toFixed(2) + ':1', n: 1};
         dim.push(dimSeen[k]);
       };
       doc.querySelectorAll('*').forEach(function(el){
         if (el.closest('svg, math, pre, [aria-hidden="true"]') || el.matches(':disabled')) return;
         var own = false;
         for (var n = el.firstChild; n; n = n.nextSibling)
           if (n.nodeType === 3 && n.textContent.trim()) { own = true; break; }
         if (!own || !shown(el)) return;
         var cs = getComputedStyle(el);
         if (cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
         var cr = ratio(rgba(cs.color), boxBg(el));
         if (cr < need(parseFloat(cs.fontSize), parseInt(cs.fontWeight, 10))) dimNote(name(el), cr, el.textContent.trim());
       });
       doc.querySelectorAll('svg').forEach(function(s){
         var texts = [].filter.call(s.querySelectorAll('text'), function(t){ return t.textContent.trim(); });
         if (!texts.length || !s.getClientRects().length || s.closest('[aria-hidden="true"]')) return;
         // 命中测试只认视口里的点，先把图滚进视口；页面有 scroll-behavior: smooth，不写 instant 就不会立刻到位
         s.scrollIntoView({block: 'center', behavior: 'instant'});
         var fig = s.closest('figure[data-chart]'), where = (fig ? fig.dataset.chart : 'svg') + (s.id ? '（#' + s.id + '）' : '');
         texts.forEach(function(t){
           var cs = getComputedStyle(t), m = t.getScreenCTM(), r = t.getBoundingClientRect();
           if (!m || r.width < 1 || cs.fill === 'none' || parseFloat(cs.opacity) === 0 || t.closest('[aria-hidden="true"]')) return;
           var cr = ratio(rgba(cs.fill), svgBg(t));
           if (cr < need(parseFloat(cs.fontSize) * Math.hypot(m.a, m.b), parseInt(cs.fontWeight, 10))) dimNote(where, cr, t.textContent.trim());
         });
       });
   ```

   几个要点（写给审阅者，不用改代码）：`scrollIntoView` 必须带 `behavior: 'instant'`，骨架给 `html` 设了 `scroll-behavior: smooth`。advisor 一开始没写，滚动没到位，`elementsFromPoint` 拿到空栈，结果把压在深色块上的浅色字当成压在卡面上，报了一串 1.0:1 的假问题。`pre` 里的文字不量（语法高亮不在本计划范围）。文字片段里的 `|` 换成 `/`，因为结果是用 `|` 分段塞进 `document.title` 的。

2. 把 `document.title = …` 表达式的最后一行 `      + '|' + diag.join('；');` 改为三行：

   <!-- prettier-ignore -->
   ```js
         + '|' + diag.join('；')
         + '|' + dim.slice(0, 6).map(function(d){ return d.s + (d.n > 1 ? ' ×' + d.n : ''); }).join('；')
         + (dim.length > 6 ? ' 等 ' + dim.length + ' 组' : '');
   ```

3. `render_check()` 里把 `probe.write_text(html + PROBE, encoding="utf-8")` 换成：

   ```python
           # 固定亮色主题：对比度在亮色下最差；其余几何检查与主题无关，固定下来结果也不随本机外观变
           probe.write_text(html.replace(
               "<head>", '<head><script>document.documentElement.dataset.theme="light";'
               'try{localStorage.setItem("show-me-theme","light")}catch(e){}</script>', 1) + PROBE,
               encoding="utf-8")
   ```

4. 正则改为（在 `</title>` 前加一个命名分组；017 不改这一行）：

   ```python
               m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(?P<contrast>.*?)</title>", out, re.S)
   ```

   若 019 已先合入，正则里已有 `\|(?P<scaled>.*?)`：把 `\|(?P<contrast>.*?)` 插在它**前面**，与 JS 里 `dim` 那段在 `scaled` 之前的顺序一致；JS 那边同样把 Step 3.2 的两行放在 `+ '|' + scaled.join('；')` 之前。

5. 在示意图那段 `issues.append(f"{cw}px 下示意图字号渲染后低于 8px：…")` 之后（与 `diag = …` 同级，12 个空格缩进）加：

   ```python
               contrast = htmllib.unescape(m.group("contrast").strip())
               if contrast and w == max(widths):
                   issues.append(f"文字对比度不足（亮色主题；正文要 4.5:1，大字要 3:1）：{contrast}。次要文字用 --color-muted-foreground，"
                                 "主角色写字用 --chart-hero-text，纯装饰的字加 aria-hidden=\"true\"（visual-system.md「对比度」）")
   ```

   只在最宽视口（1280px）报一次，与图内字号下限一样：颜色不随视口变。

**WARN 变体（仅当 `plans/README.md` 的本节记录了维护者改选 WARN）**：第 5 小步改成追加到 WARN 列表，构建不失败。

- 019 已合入时，`render_check` 已经返回 `(issues, notes, measured, ran)`，把 `issues.append(f"文字对比度不足…")` 改成 `notes.append(…)` 即可。
- 019 未合入时，先照 019 的 Step 2 第 1、2、3、5 小步改 `render_check` 的返回值与 `main()`（只改返回值、`notes` 列表和 `main()` 的三行，不加 `scaled` 那段），再用 `notes.append`。
- Step 4 测试里的断言相应改为：flagged 时 stdout 含 `WARN   文字对比度不足`，两种情况退出码都是 `0`。

**Verify**: 语法检查无输出；单元测试 → `OK`，`Ran 48 tests`（现有渲染测试都在亮色下跑，最小夹具里没有低对比度文字）。

### Step 4: 回归测试

在 `tests/test_build.py` 中、`test_render_check_measures_only_the_shown_diagram_variant` 那个测试的 `@unittest.skipUnless(…)` 装饰器行之前插入（缩进 4 空格，属于 `BuildCliTests` 类）：

```python
    @unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")
    def test_render_check_flags_low_contrast_text(self):
        """来源行与图内刻度字在亮色主题下要 4.5:1；ink-45 只有 2.8–3.1:1（2026-10 实例：进房基线报告的来源行与刻度）。"""
        markup = """<section><p class="src">来源 · 演示数据</p><figure class="fig" data-chart="F1"><div class="fig-box">
          <svg id="dim" viewBox="0 0 400 120" role="img" aria-labelledby="dim-t dim-d"><title id="dim-t">t</title>
          <desc id="dim-d">d</desc></svg></div></figure></section>"""
        script = """<script>showMeChart.reveal(document.getElementById("dim"), (s) =>
          showMeChart.txt(s, showMeChart.tick({ x: 20, y: 40EXTRA }), "刻度 10"));</script>"""
        for style, extra, flagged in (("", "", False),
                                      (".src { color: var(--ink-45); }", ', fill: "var(--ink-45)"', True)):
            with self.subTest(flagged=flagged):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                html = html.replace("</main>", markup + "</main>").replace(
                    "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script.replace("EXTRA", extra)).replace(
                    "</head>", f"<style>{style}</style></head>")
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                for part in ("文字对比度不足", "p.src「来源 · 演示数据」", "F1（#dim）「刻度 10」"):
                    self.assertEqual(part in result.stdout, flagged, result.stdout)
                self.assertEqual(result.returncode, 1 if flagged else 0, result.stdout)

```

正例用骨架默认色（来源行与 `tick()` 都是 `--color-muted-foreground`），不报；反例把两者都写回 `--ink-45`，报出 `p.src「来源 · 演示数据」3.09:1` 和 `F1（#dim）「刻度 10」2.82:1`（advisor 实测值）。

**Verify**: 单个新测试 → `ok`；全量 → `OK`，`Ran 49 tests`。

### Step 5: gallery 的文字颜色

1. 四个 gallery 页的页头常量（四处写法完全相同）改两处：

   <!-- prettier-ignore -->
   ```js
           const INK = "var(--ink)",
             PAPER = "var(--paper)",
             HERO = "var(--chart-hero)",
             HERO_TEXT = "var(--chart-hero-text)"; // 主角色写字用它，图形仍用 HERO
   ```

   <!-- prettier-ignore -->
   ```js
           const MUTED = "var(--color-muted-foreground)", // 次要文字；I45 及更浅的阶只给线和面
             GRID = I14,
             FAINT = I22;
   ```

2. 跑图库完整构建命令。构建会报 `ERROR  文字对比度不足…等 33 组`，列表只显示前 6 组。逐张图按下表改，每改完一批重跑，直到这条 ERROR 消失。下表是 advisor 在 017 之后、做完本步第 1 小步时量到的全部 33 组（编号、文字开头、对比度、出现次数）。图块按 `// ════ 编号 ` 在对应页里找，再找画这段字的 `txt(…)` / `tick({…})` / `value({…})` 调用，看它的 `fill`：

   | 改法                                                                      | 图与文字（对比度 × 次数）                                                                                                                                                   |
   | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `fill: I60` 的文字 → `MUTED`                                              | F13「PRODUCT · 」4.43 ×3；G6「Product」4.43 ×10；G7「Editor」4.43 ×4；G11「Slack」4.43 ×12；G15「P0 CRITICA」4.43 ×4；B1「platform/p」4.43 ×15                              |
   | `I45` 或 `G.ink.quiet` 的文字 → `MUTED`（用 `G` 的块写 `G.ink.note`）     | L6「设计 14 人」2.82 ×5；L11「5 路」2.82 ×3；L16「30」2.82；G10「−6%」2.82 ×4；G12「40」2.82 ×9；G18「JAN」2.82 ×6；B3「web4」2.82 ×59                                      |
   | `I30` / `I22` 的文字 → `MUTED`                                            | G5「ONE TREE =」1.87；G8「$0K」1.87 ×6；G9「PRICE $ →」1.87 ×3；G13「45m」1.87、「15m」1.42 ×2；G15「HOURS TO R」1.87                                                       |
   | `HERO` 当文字色 → `HERO_TEXT`（用 `G` 的块写 `"var(--chart-hero-text)"`） | L1「滨江740」2.65；G3「$486K」2.65；G4「现场窗口」2.65 ×2；G5「117k2026 —」2.65；G8「118」2.65；G10「+34%」2.65；G17「46k」2.65；G19「晚高峰」2.65 ×3；B3「legacy-aut」2.65 |
   | 字压在色块上，按下面「压在色块上的字」选色                                | G21「饭团」2.65 ×9（卡面色的字压在主角色条上）；G16「$47K」2.25（数值压在条上）；B2「notify」3.09 ×2、「analytics」2.04 ×2（纸色字压在 `I45` / `I30` 的节点上）             |
   | 大字（≥ 24px）只要 3:1                                                    | G16「2020」1.25（40px 的年份水印，`fill: I14`）→ 改 `I60`（亮 4.43:1）                                                                                                      |

   **压在色块上的字**（亮暗两种主题都要过 4.5:1，构建只量亮色，所以按规则选，不要只看构建结果）：

   - 块是 `I30` 或更浅：字用 `INK`（亮 8.0:1、暗 6.6:1）。
   - 块是 `I70`、`I90`、`INK`：字用 `PAPER` 或 `"var(--color-card)"`（亮 6.0–6.6:1、暗 7.3–8.0:1）。
   - 块是 `HERO`：字用 `"var(--ink-fixed)"`（固定深墨，两种主题都是 5.2:1）。不要用 `INK`：暗色主题下 `INK` 是浅色，压在橙色上只有 2.9:1。
   - 块是 `I45` / `I60`：墨色字、纸色字在其中一个主题下都不到 4.5:1。把字挪到块外，或把这一块的填充换成相邻一档（`I30` 或 `I70`），换哪档以不破坏「明度即数据」的排序为准。B2 的节点是这种情况。
   - 动态图（G16 是条形赛跑，数值在条内外切换）：两个位置的颜色都按上面选。

   改完一张图看一眼它的 light 和 dark 截图（`"$G/shots/<编号>-light.png"`、`-dark.png`），确认字仍然分得出主次。

3. **F3「台风 / 闭园」改竖排单列**（2026-10-22 维护者要求并进本计划；来自 017 执行记录的遗留）。`assets/gallery/basics.html` 的 `// ════ F3 · Hairline Area ════` 图块里，闭园空档只有约 18 个单位宽（左右发丝在 x = 150 和 168），两行「台风」「闭园」各 2 个 10 号字、宽 20，两侧各压到发丝约 1 个单位。把这两个 `txt(…)` 调用：

   ```js
   txt(s, label({ x: gap, y: Y0 - 34, "text-anchor": "middle" }), "台风");
   txt(
     s,
     label({
       x: gap,
       y: Y0 - 34 + G.type.label * 1.25,
       "text-anchor": "middle",
     }),
     "闭园"
   );
   ```

   换成：

   <!-- prettier-ignore -->
   ```js
               // 空档只有约 18 个单位宽，两字一行会压到两侧发丝：竖排单列，末字落在地面线上方 8 个单位
               [..."台风闭园"].forEach((ch, k) =>
                 txt(
                   s,
                   label({
                     x: gap,
                     y: Y0 - 8 - (3 - k) * G.type.label * 1.25,
                     "text-anchor": "middle",
                   }),
                   ch
                 )
               );
   ```

   如果第 2 小步已经改过这两段的 `fill`，把同样的 `fill` 写进新的 `label({…})` 里。advisor 在 scratchpad 里截图确认过：四个字在空档正中，左右都不碰发丝，最上面的「台」在 4 千人那条点线下方。改完看 `"$G/shots/F3-light.png"` 和 `-dark.png`。

**Verify**: 图库完整构建 → 构建输出里没有 `文字对比度不足`；`grep -n 'const MUTED = I45' skills/show-me-html/assets/gallery/*.html` 无输出；单元测试 → `OK`，`Ran 49 tests`。

### Step 6: 文档

1. `references/visual-system.md`：

   - 「Token 分层」分层表里明度阶一行的「内容」一格改为 `` `--ink-90 … --ink-4`，墨在纸上的 `color-mix` 占比；`--ink-65` 是能在卡面上写字的最浅一档 ``，「谁能改」一格不变。
   - 角色表「弱化面与次要文字」一行之后加一行：``| 主角色写字 | `--hero-text`（图里用 `--chart-hero-text`） |``。
   - 在「## 明度即数据」一节的末尾、「## 公式」之前加一节：

     <!-- prettier-ignore -->
     ```markdown
     ## 对比度

     文字与它的底色在亮暗两种主题下都要达到 WCAG AA：正文 4.5:1，24px 以上或 18.66px 以上的粗体 3:1。

     - 次要文字（来源行、单位、刻度、图型标签）用 `--color-muted-foreground`，即 `--ink-65`：卡面上亮 5.2:1、暗 5.9:1。`--ink-60` 在卡面上只有 4.4:1，`--ink-45` 只有 2.8:1，这两档和更浅的阶只给线、面和网格。图里用 `tick()`（默认色 `G.ink.note`）或 gallery 的 `MUTED`。
     - 主角色写字用 `--chart-hero-text`（主角色掺四成墨，亮 5.3:1、暗 7.5:1）。纯 `--hero` 在亮色卡面上只有 2.7:1，只给图形。链接强调色 `--link-accent` 与告急徽标的字也用这一色；告急按钮是主角色底，字用 `--ink-fixed`。
     - 字压在色块上时按色块选字色：`--ink-30` 或更浅的块上用墨色，`--ink-70` 或更深的块上用纸色，主角色块上用 `--ink-fixed`。`--ink-45`、`--ink-60` 的块上，墨色字和纸色字总有一个主题不到 4.5:1，把字挪到块外。
     - 纯装饰、不承载信息的字加 `aria-hidden="true"`，检查会跳过它。
     - 构建的渲染检查把页面固定在亮色主题下，量每段文字和图内文字的对比度，低于要求报 ERROR。暗色主题和代码块（`pre`）里的语法高亮色不在检查范围内。
     ```

2. `references/compose-and-check.md:121` 那一段替换为：

   <!-- prettier-ignore -->
   ```markdown
   **已知缺口**：对比度检查只在亮色主题下量，也不量代码块的语法高亮色（注释与字符串在代码底色上约 2.6–4.1:1）。暗色主题下压在色块上的字，按 `visual-system.md`「对比度」的选色规则写，再看一眼暗色截图。截图可以用已装的 `ego-browser` skill。
   ```

3. `references/charts.md`：

   - `**颜色**` 小节里，「**一律实心**」那一条之后加一条：

     <!-- prettier-ignore -->
     ```markdown
     - **文字不用线和面的墨。** 图内文字的 `fill` 只用 `INK` / `I70`（`G.ink.strong` / `G.ink.data`）、次要文字 `G.ink.note`（gallery 里是 `MUTED`）、主角色文字 `var(--chart-hero-text)`（gallery 里是 `HERO_TEXT`）。`G.ink.quiet` / `mass` / `guide` 和 `I45` 及更浅的阶只给线、面和网格。字压在色块上怎么选色见 `visual-system.md`「对比度」，构建会量每个字的对比度。
     ```

   - 「发丝语法」表格里 `tick()` / `value()` / `label()` 那一行的「用在哪里」一格改为：`刻度与单位（等宽、加字距、次要文字色 G.ink.note）/ 数值（600、主角时 --chart-hero-text）/ 类目名（正文字）`（数值一格的 `9 / 10 / 10` 是 017 改的，保持不变）。
   - 「页面脚本模板」里把 `HERO = "var(--chart-hero)";` 改为 `HERO = "var(--chart-hero)",` 并在下一行加 `    HERO_TEXT = "var(--chart-hero-text)";`；在 `I14 = "var(--ink-14)";` 之后加一行 `  const MUTED = "var(--color-muted-foreground)"; // 次要文字；I45 及更浅只给线和面`。

4. `references/anti-patterns.md`：表格最后一行之后加一行（编号接着表里最大的编号；017 之后、019 之前是 12）：

   <!-- prettier-ignore -->
   ```markdown
   | 12 | 淡字 | 已检查 | 次要文字、图内刻度、主角色文字用了线和面的墨（`--ink-45`、纯 `--hero`），卡面上只有 2.6–3.1:1（2026-10 实例：报告页来源行与 F12 刻度 2.82:1、G4 图例橙字 2.65:1）。 | 次要文字用 `--color-muted-foreground`，主角色写字用 `--chart-hero-text`，压在色块上的字按 visual-system.md「对比度」选色。build.py 渲染检查在亮色主题下量每个字，正文 < 4.5:1、大字 < 3:1 报 ERROR。 |
   ```

   并在「状态推进记录：」列表末尾加一行：`- <执行当天日期> 第 12 条登记即为已检查（文字对比度）。次要文字色从 ink-60 提到 ink-65，来源行、图型标签、刻度字从 ink-45 改用它；主角色写字、链接强调色与告急徽标改用 --hero-text，告急按钮的字改用 --ink-fixed。`

5. `npx prettier --write skills/show-me-html/references/visual-system.md skills/show-me-html/references/compose-and-check.md skills/show-me-html/references/charts.md skills/show-me-html/references/anti-patterns.md`

**Verify**: `make check` → exit 0；`grep -c '^## 对比度' skills/show-me-html/references/visual-system.md` → `1`；`grep -c '没有自动的对比度检查' skills/show-me-html/references/compose-and-check.md` → `0`；`grep -c '淡字' skills/show-me-html/references/anti-patterns.md` → `1`。

### Step 7: 回归

1. 图库完整构建 → 017 已合入时只有一条 `WARN … 超过 400 KB`，`自检通过（1 个警告需逐条判断）。`，末尾 `问题    0 条`。逐张看 Step 5 改过的 29 张图的 light 与 dark 截图。
2. 冻结场景轮次：

   ```sh
   PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-22-6d39fa5-printbreak
   NEW=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-018
   mkdir -p "$NEW"
   for n in status-report approach-compare code-review concept-explainer triage-board; do
     cp "$PREV/$n.html" "$NEW/" && python3 skills/show-me-html/scripts/build.py "$NEW/$n.html" | tail -2
   done
   node skills/show-me-html/scripts/probe_round.mjs "$NEW" "$PREV"
   ```

   **Verify**: 五次构建各打印 `自检通过。`（advisor 实测：没有 Step 1 第 7 小步的徽标修正时，status-report、concept-explainer、triage-board 会因告急徽标 2.40:1 报 ERROR）；探针五行 `无问题`；人眼看 `"$NEW"/_probe/status-report-light-1280.png`，次要文字比改前略深，层级仍然清楚。本计划改了颜色，截图与上一轮不同属于预期；探针打印的 `probe.json` 差异逐条写进汇报（预期只有颜色相关的读数变化，页高、Tab 停靠数、溢出、打印页数不该变，变了就在汇报里标出）。

3. 组件夹具：它收齐了按钮、徽标、提示框等组件的各个变体，但现有测试只用 `--no-render` 构建它，渲染检查从没在它上面跑过。

   ```sh
   T=$(mktemp -d) && cp skills/show-me-html/tests/fixtures/component-states.html "$T/cs.html"
   python3 - "$T/cs.html" <<'EOF'
   import pathlib, sys
   p = pathlib.Path(sys.argv[1])
   p.write_text(p.read_text(encoding="utf-8").replace("</main>",
       '<section><div class="card"><p>卡里的按钮 <button type="button" class="btn" data-variant="link">查看来源</button></p></div></section></main>', 1),
       encoding="utf-8")
   EOF
   python3 skills/show-me-html/scripts/build.py "$T/cs.html" | tail -2
   ```

   **Verify**: 打印 `自检通过。`（advisor 实测：没有 Step 1 第 3、4 小步时报 `button.btn「危险」2.90:1；button.btn「查看来源」4.40:1`）。夹具和临时目录都不进提交。

## Test plan

- 新增 `test_render_check_flags_low_contrast_text`（Step 4），正反例各一。
- 现有 48 个测试保持通过：字号下限、大数、示意图宽窄版几个渲染测试证明 `|` 分段没被改坏；`test_literal_colors_live_only_in_primitive_layer` 证明没有新增字面色。
- 误报面：gallery 总览页（59 张图）、五个冻结场景、`diagram-variants.html` 夹具（由现有测试渲染）、`component-states.html` 夹具（Step 7 第 3 小步）。advisor 预演时这些都没有误报。

## Done criteria

- [ ] 全量单元测试 → `OK`，`Ran 49 tests`（017 已合入；若 019 也已合入则 50；020 已合入再加 1）
- [ ] `grep -c '"台风闭园"' skills/show-me-html/assets/gallery/basics.html` → `1`（F3 竖排单列）
- [ ] 语法检查无输出
- [ ] `grep -c '  color: var(--ink-45);' skills/show-me-html/assets/show-me.css` → `0`
- [ ] `grep -c '文字对比度不足' skills/show-me-html/scripts/build.py` → `1`
- [ ] 图库完整构建没有 `文字对比度不足`
- [ ] Step 7 五个场景 `自检通过。`，探针五行 `无问题`
- [ ] Step 7 组件夹具 `自检通过。`
- [ ] `make check` exit 0
- [ ] `git status --short` 只列出 Scope 里的文件
- [ ] `plans/README.md` 本计划状态行已更新

## STOP conditions

- Drift check 出现 `show-me.css`、`visual-system.md`、`compose-and-check.md` 的改动，或摘录对不上。
- Step 3 之后现有测试失败：多半是 `|` 分段或正则写错，修一次仍不过就停下。
- Step 5 第 2 小步报出的组数与 33 相差超过 3 组，或出现表里没有的图：汇报实际列表。
- 某处文字按「压在色块上的字」的规则怎么选都不过（例如字必须压在 `I45` 块上、又没地方挪）：停在这张图，附截图汇报。
- 冻结场景里出现检查报出、但截图里看着没问题的文字（疑似误报）：汇报元素和截图，不要放宽阈值或加跳过规则。

## Maintenance notes

- **旧页面重新构建会因为页面自己写的颜色报 ERROR。** 维护者 2026-10-21 那页（bedrock 仓库，进房全球基线）advisor 试过：重建后来源行、F12 刻度这些走骨架和运行时的地方自动达标，但页面脚本里自己定义的 `MUTED = I45` 和橙色文字报出 4 组（G4 图例「93 格」2.82:1、「300106 连接重置」2.65:1，G10「← 用户日占比」2.82:1、「15.1%」2.65:1）。修法和 Step 5 一样：页面常量 `MUTED` 改成 `"var(--color-muted-foreground)"`，文字里的 `HERO` 改成 `"var(--chart-hero-text)"`。这不属于本计划。
- 检查只量亮色。暗色主题下唯一会更差的组合是「字压在色块上」，靠 visual-system.md「对比度」的选色规则和人眼看暗色截图兜住。
- 背景色只认纯色：`background-image`（渐变、图片）上的字会按它下面最近的纯色底来算，可能误报或漏报。骨架里没有这种用法；页面出现时按误报处理，加 `aria-hidden` 不是正确修法，要换成纯色底。
- `elementsFromPoint` 跳过 `pointer-events: none` 的元素。gallery 里有两处这样的图形（`big.html:811`、`editorial.html:2052`，017 合入后是 2068），压在上面的字会被当成压在卡面上。目前这两处上面没有字；以后在 `pointer-events: none` 的色块上写字，检查会算错。
- `--ink-65` 与 `--ink-70` 只差 5%，次要文字与类目名（`I70`）的颜色很接近，层级主要靠字号和字体（等宽 / 正文）区分。审阅时看 status-report 场景和 gallery 截图，确认层级没有糊掉。
- 告急按钮在亮色主题下变成橙底深字，与暗色主题一致；正文链接悬停色和链接样式按钮变深一档。这两处是为了让骨架组件本身过检查，审阅时看一眼组件夹具的亮色截图。
- 组件夹具 `component-states.html` 和 `recipe-matrix.html` 没有 `<head>` 主题脚本。advisor 在本机暗色外观下看到 `recipe-matrix.html` 的 `contenteditable` 字与底色几乎相同（1.10:1），没有查明原因。现有测试不渲染它，渲染检查又固定在亮色，所以不影响本计划。
