# Plan 030: show-me-html 的连线图改写 Mermaid 源码，构建时由 pele 编译成内联 SVG

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。索引 `plans/README.md` 由审阅者维护，你不要改它。
>
> **Drift check (run first)**: `git diff --stat fdf3059..HEAD -- skills/show-me-html skills/tufte-reader/assets/vendor` 应无输出。有输出就对照下面「Current state」里的引文，引文原样还在就继续，对不上就 STOP。
>
> 本计划的全部代码和文档改动在附件 `plans/030-show-me-html-mermaid/030.patch` 里（advisor 在仓库副本上跑通后导出，已经过 prettier）。你的工作是复制 vendor 文件、套用补丁、逐项验证，不需要重新写代码。补丁套不上就 STOP，不要手工改写。

## Status

- **Priority**: P1
- **Effort**: M（补丁现成；工作量在验证和看图）
- **Risk**: MED（新增一条构建期编译通道和一个 716 KB 的 vendor 文件；现有页面不含 Mermaid 源码时行为不变）
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `fdf3059`, 2026-11-12

## Why this matters

show-me-html 技能把素材做成单文件 HTML 页面。页面里的示意图（流程图、时序图等）至今全靠 agent 手写 SVG：逐个节点算坐标，再另画一版窄屏图。2026-11-12 审计了本机的真实页面：一张八步直链图的手写 SVG 约 5400 字符，同一张图的 Mermaid 源码约 680 字符；一例汇入型图用了规则禁止的斜线，构建报 ERROR；一例 780 宽的横向图在 1024px 下字号只有 7.7px。同仓库的 tufte-reader 技能已经 vendor 了 pele（JS 写的 Mermaid 渲染器，MIT，单文件无依赖），构建时把 Mermaid 源码编译成内联 SVG。维护者 2026-11-12 看过两张真实手绘图的 pele 重做对比后决定：节点连线的图默认写 Mermaid 源码，手写 SVG 只留给 Mermaid 没有对应图型的图。

这份计划落地后：作者在页面里写 `<pre class="mermaid">`，`build.py` 把它编译成跟随主题的内联 SVG；横向图自动多出一版纵向窄图；「复制为 Markdown」把源码导出成 mermaid 代码块；页面仍然离线可开、不带 Mermaid 运行时。

## Current state

技能目录是 `skills/show-me-html/`（下文不带前缀的路径都相对这个目录）。行号按 `fdf3059`。

- `scripts/build.py` — 合成与自检脚本。`main()` 先调 `compile_math`（用 node 跑 `scripts/math.mjs` 把 LaTeX 编译成 MathML），再 `build()` 内联 CSS 和脚本，再 `check()`。本计划照 `compile_math` 的样子加 `compile_mermaid`。
  - `scripts/build.py:53`：

    ```python
    MATH_SCRIPT = Path(__file__).resolve().parent / "math.mjs"
    ```

  - `scripts/build.py:1337-1339`（`main()` 里）：

    ```python
        if compile_math(args.page, build_errors, build_warns):
            html = args.page.read_text(encoding="utf-8")
        html, changed, used, langs, warns_from_build = build(html, build_errors)
    ```

  - `scripts/build.py:265-283`，`check_svgs` 的无障碍检查，本计划给 Mermaid 图单独的提示语，并让它跳过后面的斜线检查：

    ```python
    def check_svgs(html, warns, errors):
        for m in SVG_BLOCK_RE.finditer(html):
            attrs, body = m.group(1), m.group(2)
            if "lucide" in attrs or 'aria-hidden="true"' in attrs:
                continue
            missing = []
            if 'role="img"' not in attrs:
                missing.append('role="img"')
    ```

  - `scripts/build.py:654-656`（`check()` 里），本计划在它后面加「还有没编译的 Mermaid 图」的 ERROR：

    ```python
        for slot in (CSS_SLOT, JS_SLOT):
            if slot in html:
                errors.append(f"占位符 {slot} 未被替换")
    ```

- `assets/show-me.css:1552-1558` — 图框里 SVG 文字的字体规则，本计划在它后面加 Mermaid 图的样式：

  ```css
  .fig svg text {
    font-family: var(--font-mono);
    user-select: none;
  }
  .fig svg text.name {
    font-family: var(--font-sans);
  }
  ```

  同文件 `:1530-1551` 已有宽窄两版图的机制：`.diagram-narrow` 平时 `display: none !important`，`@media (max-width: 640px)` 下改为隐藏 `.diagram-wide`。本计划的编译产物直接复用这两个 class。

- `assets/shell.js:334-337` — 「复制为 Markdown」导出器的代码块分支，本计划让 `pre.mermaid` 导出时带上语言名：

  ```js
        } else if (t === "PRE") {
          var code = n.querySelector("code");
          var lang =
            (code && (code.className.match(/language-([\w+-]+)/) || [])[1]) || "";
  ```

  同文件 `:292-308` 已经会把图里的 `<desc>` 导出成一段文字（只出正在显示的那版），不用改。

- `references/diagrams.md` — 图示规则，全文按手写 SVG 写。`:193` 把「照抄 Mermaid 的自动布局」列为反模式，本计划改掉这一行（维护者已决定）。
- `skills/tufte-reader/assets/vendor/pele/pele.mjs`（716 KB）和 `skills/tufte-reader/assets/vendor/LICENSE-pele.txt` — 仓库里已有的 pele 1.13.0，本计划原样复制一份到 show-me-html。技能各自安装成独立副本，不能跨技能 import，所以要各存一份。`skills/*/assets/vendor/**` 是「只整体更新、不手改」的第三方资产。
- `skills/tufte-reader/scripts/mermaid.mjs` — tufte-reader 的适配脚本，本计划的 `scripts/mermaid.mjs` 以它为样板（字宽估算表、拆旧产物的正则、错误信息格式相同），差别见 Step 2 的说明。**不要改 tufte-reader 的任何文件。**
- 测试：`tests/test_build.py` 是 unittest，`fdf3059` 上 65 个用例。`copy_fixture(name)` 把 `tests/fixtures/<name>` 复制到临时目录，`run_build(page, *args)` 跑 `build.py` 并自带 `--no-render`。需要浏览器的用例带 `@unittest.skipUnless(RENDERER, …)`。
- 仓库约定：Markdown 以简体中文为主；技能文档按标题名引用章节（「Mermaid 图」），不按编号，`make check` 会查；格式由 prettier 决定（pre-commit 会跑）；提交信息用 conventional commits，scope 写技能名。

pele 的几个事实（advisor 2026-11-12 实测，补丁依赖它们）：

- `render(src, { idPrefix, maxWidth, measurer, fontSize })` 返回 `{ svg, width, height }`；语法错误抛 `PeleError`（带 `line`、`column`）。
- 输出的 `<svg>` 带 `class="pele pele-<图型>"`、`role="graphics-document document"`、写死的 `width` / `height` 和 `style="max-width:100%;height:auto;…"`；源码写了 `accTitle` / `accDescr` 才有 `<title>` / `<desc>` 和 `aria-labelledby`。
- 颜色、字体全部读 `--pele-*` CSS 变量；节点是 `<g class="pele-node pele-shape-… [作者写的 class]" data-id="节点 id">`，第一个子元素是外形；源码里的 `A:::focus` 会把 `focus` 加到节点的 class 上。
- 横向（`LR`）流程图在 `maxWidth` 较小时自动改成纵向；时序图、类图不重排。
- 源码第一行写 `%%{init: {"flowchart": {"wrappingWidth": 360, "rankSpacing": 20, "nodeSpacing": 20}}}%%` 生效，对其他图型无害；但放在 frontmatter（`---`）前面会报「No diagram type detected」。

## Commands you will need

命令都在仓库根目录跑。

| Purpose  | Command                                                               | Expected on success                          |
| -------- | --------------------------------------------------------------------- | -------------------------------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`            | `Ran 71 tests`、末行 `OK`（执行前是 65）     |
| 只跑新增 | `python3 -m unittest skills.show-me-html.tests.test_build -k mermaid` | `Ran 6 tests`、`OK`                          |
| JS 语法  | `node --check skills/show-me-html/scripts/mermaid.mjs`                | 无输出                                       |
| 格式     | `npx prettier --check <文件>`                                         | `All matched files use Prettier code style!` |
| 文档门禁 | `make check`                                                          | exit 0，`技能文档引用检查通过`               |

基线说明：advisor 在 `fdf3059` 上跑全量测试三次，其中一次 `test_interrupted_build_leaves_no_chrome_profile` 失败（`AssertionError: 0 != -2`），另两次通过，是与本计划无关的偶发失败。遇到它单独重跑一次该用例；别的用例失败才算数。

需要 node 22+ 和本机 Chrome（渲染检查与 `--snap` 用）。本机无头 Chrome 不读代理环境变量以外的系统代理，直连 Google Fonts 较慢，`--snap` 一次可能要一两分钟，属正常。

## Scope

**In scope**（只改这些；除前两项外都由补丁完成）：

- `skills/show-me-html/assets/vendor/pele/pele.mjs`（新建，复制）
- `skills/show-me-html/assets/vendor/LICENSE-pele.txt`（新建，复制）
- `skills/show-me-html/assets/vendor/pele/README.md`（新建）
- `skills/show-me-html/scripts/mermaid.mjs`（新建）
- `skills/show-me-html/scripts/build.py`
- `skills/show-me-html/assets/show-me.css`
- `skills/show-me-html/assets/shell.js`
- `skills/show-me-html/tests/test_build.py`
- `skills/show-me-html/tests/fixtures/mermaid-flow.html`（新建）
- `skills/show-me-html/references/diagrams.md`、`references/layouts.md`、`references/compose-and-check.md`
- `skills/show-me-html/SKILL.md`、`README.md`、`MAINTENANCE.md`

**Out of scope**（看着相关也不要动）：

- `skills/tufte-reader/**` — 只读，作为复制来源和样板。
- `skills/show-me-html/references/interactions.md` — 可点节点的写法是 Plan 031 的事。
- `skills/show-me-html/assets/gallery/**`、`assets/charts.js`、`references/charts.md` — 数据图不走 Mermaid。
- `skills/show-me-html/scenarios/**` — 冻结场景的材料不改。
- 仓库根的 `README.md`、`AGENTS.md`、`PROJECT_MEMORY.md`、`plans/README.md` — 由审阅者处理。
- 不运行 `make install`，不推送。

## Git workflow

- 仓库惯例是直接提交到 `main`；作为被派发的执行者，在分支 `advisor/030-show-me-html-mermaid` 上做，由审阅者合入。
- 提交信息用 conventional commits，scope 写技能名，例如 `git log` 里的 `feat(farm): add OpenCode native worker backend`。本计划建议一个提交：`feat(show-me-html): compile Mermaid sources to inline SVG with vendored pele`。
- pre-commit 会跑 prettier 和 `make check`。如果你在 git worktree 里、根目录没有 `node_modules`，执行 `ln -s /Users/mg/github/skills/node_modules node_modules`（不要 `npm install`，它会改 `package-lock.json`）；提交完用 `rm node_modules`（不带结尾斜杠）删掉这个链接，并确认它没有被提交。
- 不要推送，不要开 PR。

## Steps

### Step 1: 复制 pele 和它的许可证

```bash
mkdir -p skills/show-me-html/assets/vendor/pele
cp skills/tufte-reader/assets/vendor/pele/pele.mjs skills/show-me-html/assets/vendor/pele/pele.mjs
cp skills/tufte-reader/assets/vendor/LICENSE-pele.txt skills/show-me-html/assets/vendor/LICENSE-pele.txt
```

**Verify**: `shasum -a 256 skills/show-me-html/assets/vendor/pele/pele.mjs skills/show-me-html/assets/vendor/LICENSE-pele.txt` → 两行分别以 `37bea5005aa6d2dd` 和 `311bccc30de6f7b9` 开头。

### Step 2: 套用补丁

```bash
git apply --check plans/030-show-me-html-mermaid/030.patch && git apply plans/030-show-me-html-mermaid/030.patch
```

**Verify**: `git status --short | wc -l` → `14`（10 个已修改的文件，加 4 个未跟踪项：`assets/vendor/LICENSE-pele.txt`、`assets/vendor/pele/`、`scripts/mermaid.mjs`、`tests/fixtures/mermaid-flow.html`），都在 Scope 之内；`node --check skills/show-me-html/scripts/mermaid.mjs` 无输出；`python3 -m py_compile skills/show-me-html/scripts/build.py` 无输出。

补丁做了什么（供你核对和向审阅者说明，逐项都能在 diff 里找到）：

1. **`scripts/mermaid.mjs`（新）**：读页面，先把上一次的产物 `div.mermaid-figure` 拆回源码，再把每个 `<pre class="mermaid">` 编译成 SVG，产物是 `<div class="mermaid-figure">SVG…<pre class="mermaid">源码</pre></div>`。与 tufte-reader 那份的差别：
   - 源码没有自带 frontmatter 或 `%%{` 指令时，在最前面注入一行布局参数（换行宽度 360、层间距 20、节点间距 20）；报语法错误的行号相应减 1。
   - 先按 720px 排一版；宽度超过 400px 的再按 340px 排一版，第二版不超过 400px 就两版都留（class 加 `diagram-wide` / `diagram-narrow`，id 前缀分别是 `mmdN-` / `mmdNn-`），否则只留宽版并发 WARN。
   - SVG 的 `role` 改成 `img`，去掉写死的 `width` / `height`，`max-width` 改成排出来的像素宽度，小图不会被 `width: 100%` 拉大。
   - 宽版排出来超过 960px 时发 WARN（放进 720 的图框要缩到 0.75 倍以下，字会偏小），提示改 `TD`、缩短标签或拆图。
   - 没有源码开关（tufte-reader 的 checkbox 和图标）。
2. **`scripts/build.py`**：加常量 `MERMAID_SCRIPT`、`MERMAID_ANY_RE`、`MERMAID_DONE`；加 `compile_mermaid()`，`main()` 在 `compile_math` 之后调用；`check()` 里统计没编译的 Mermaid 图并报 ERROR（先剥掉系统内联的 `<style>` / `<script>` 再数）；`check_svgs()` 对 class 含 `pele` 的 SVG 给专门的无障碍提示语，并跳过斜线检查；`render_check()` 里「示意图字号渲染后低于 8px」那条 ERROR 的建议补上 Mermaid 图的改法。
3. **`assets/show-me.css`**：在 `.fig svg text.name` 规则后面加一段：`.pele` 的 `--pele-*` 变量接到页面 token，并自带 `display: block; width: 100%; height: auto`（不依赖 `.fig svg`，在 `flowchart` 配方的 `.diagram-canvas` 里也成立）；图框（`.fig-box`）和配方画布（`.diagram-canvas`）里的遮罩底色用卡面色；文字用无衬线；隐藏 `pre.mermaid`；粗体行之后的行用次要色小一号；`focus` / `store` / `external` / `optional` 四种节点语义；分组框描边。**这段 CSS 的注释里不能出现带尖括号的 pre 开标签**：`mermaid.mjs` 按文本找源码，会把它当成一幅图（advisor 预演时踩过）。
4. **`assets/shell.js`**：导出代码块时，`pre` 带 `mermaid` class 且没有 `code` 子元素的，语言名用 `mermaid`。
5. **`tests/fixtures/mermaid-flow.html`（新）** 和 **`tests/test_build.py`** 的 6 个新用例，见「Test plan」。
6. **文档**：`references/diagrams.md` 开头说明两种画法、类型路由表加「画法」列和「类图 / ER 图」一行、新增「Mermaid 图」一节、「连线六条硬规则」注明只管手写、反模式表换掉「照抄 Mermaid 的自动布局」一行、自检的机械关补全；`references/layouts.md` 的 `flowchart` 配方改为主图写 Mermaid；`references/compose-and-check.md`、`SKILL.md`、`README.md`、`MAINTENANCE.md` 各补一两句；新建 `assets/vendor/pele/README.md`。

### Step 3: 跑测试与门禁

**Verify**（四条都要过）:

- `python3 -m unittest skills.show-me-html.tests.test_build -k mermaid` → `Ran 6 tests`、`OK`
- `python3 -m unittest skills.show-me-html.tests.test_build` → `Ran 71 tests`、`OK`（偶发失败的处理见「Commands you will need」）
- `make check` → exit 0
- `npx prettier --check skills/show-me-html/scripts/mermaid.mjs skills/show-me-html/assets/show-me.css skills/show-me-html/assets/shell.js skills/show-me-html/tests/fixtures/mermaid-flow.html skills/show-me-html/references/diagrams.md skills/show-me-html/SKILL.md skills/show-me-html/README.md skills/show-me-html/MAINTENANCE.md` → `All matched files use Prettier code style!`

### Step 4: 反证一次，确认新测试真的在测

临时把 `skills/show-me-html/scripts/mermaid.mjs` 里的 `const PHONE_PX = 400;` 改成 `const PHONE_PX = 4000;`，跑 `python3 -m unittest skills.show-me-html.tests.test_build -k mermaid_compiles`。

**Verify**: 该用例失败，报 `AssertionError: 0 != 1`（不再出窄版，`diagram-wide` 的计数成了 0）。然后把这一行改回 `400`，重跑同一条命令 → `OK`；`grep -c 'const PHONE_PX = 400;' skills/show-me-html/scripts/mermaid.mjs` → `1`。

### Step 5: 构建夹具页，看图

```bash
rm -rf /tmp/smh-030 && mkdir -p /tmp/smh-030 && cp skills/show-me-html/tests/fixtures/mermaid-flow.html /tmp/smh-030/page.html
python3 skills/show-me-html/scripts/build.py /tmp/smh-030/page.html --snap /tmp/smh-030/snap --snap-width 390,1280
python3 skills/show-me-html/scripts/build.py /tmp/smh-030/page.html --no-render && md5 -q /tmp/smh-030/page.html
python3 skills/show-me-html/scripts/build.py /tmp/smh-030/page.html --no-render && md5 -q /tmp/smh-030/page.html
```

**Verify**:

- 第一条构建输出 `自检通过。`，没有 `WARN` 和 `ERROR` 行；`已快照` 列出 `light-390-01.png`、`light-1280-01.png`、`dark-390-01.png`、`dark-1280-01.png` 和 `export.md`。
- 两次 `md5` 输出相同（重复构建结果不变）。
- `grep -c '```mermaid' /tmp/smh-030/snap/export.md` → `2`。
- 用 Read 工具打开 `/tmp/smh-030/snap/` 下的四张 PNG 逐张看，应当是：
  - 1280 两张：第一幅是横向流程图，两个菱形判断、一个圆柱（制品库，填充比别的节点深）、「灰度 5%」节点描边加粗且有第二行小字「观察 30 分钟」、「修复」是虚线框、一条从「修复」回到「提交 PR」的回边；第二幅是三条生命线的时序图，按原大居中，没有被放大到撑满图框。
  - 390 两张：第一幅是纵向流程图（同样的节点，自上而下），字清楚可读；时序图同上。
  - 深色两张里，节点、连线、文字都跟随深色主题，没有白底块或看不见的字。
  - 所有标签都在各自的框内，没有顶出框或被裁掉。

### Step 6: 冻结场景对照（MAINTENANCE.md「联动规则」要求改 CSS、shell.js、build.py 后做）

冻结场景的轮次页面不进 git，放在主检出目录。把最近一轮的五页各复制两份，一份用 `main` 的构建器重建，一份用你分支的构建器重建，再用探针对比。下面整段放在同一次 shell 调用里执行（变量 `R` 只在这一段里有效），用 bash：

```bash
R=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-27-e0d1995-split
rm -rf /tmp/smh-030-rounds && mkdir -p /tmp/smh-030-rounds/old /tmp/smh-030-rounds/new
for f in status-report approach-compare code-review concept-explainer triage-board; do cp "$R/$f.html" /tmp/smh-030-rounds/old/ && cp "$R/$f.html" /tmp/smh-030-rounds/new/; done
for f in /tmp/smh-030-rounds/old/*.html; do python3 /Users/mg/github/skills/skills/show-me-html/scripts/build.py "$f" --no-render | tail -1; done
for f in /tmp/smh-030-rounds/new/*.html; do python3 skills/show-me-html/scripts/build.py "$f" --no-render | tail -1; done
node /Users/mg/github/skills/skills/show-me-html/scripts/probe_round.mjs /tmp/smh-030-rounds/old
node skills/show-me-html/scripts/probe_round.mjs /tmp/smh-030-rounds/new /tmp/smh-030-rounds/old
```

（`/Users/mg/github/skills` 是主检出目录，停在 `main`；后两个 `skills/…` 是你工作目录里的分支版本。主检出目录里没有 `2026-10-27-e0d1995-split` 时，改用 `ls` 出来的最新一轮；一轮都没有就跳过本步并在汇报里写明。）

**Verify**: 十次构建的末行都是 `自检通过。`；第二次探针的摘要里五页都报 `无问题`，并有一行 `与上一轮对比：probe.json 相同`。这五页都不含 Mermaid 图，新加的 CSS 只作用于 `.pele` 和 `.mermaid-figure`，所以几何应当零差异；`probe.json` 不同就 STOP。

截图那一行允许个别字节不同：advisor 2026-11-12 用终版补丁跑是 `30/30 张逐字节相同`，前一轮预演是 `29/30 张逐字节相同`，不同的一张（`approach-compare-dark-500.png`）尺寸相同，只有一行文字范围内的 189 个像素不同，是字体加载时机造成的字形抗锯齿差异。你遇到字节不同的截图时用 Read 工具把两轮的同名图各看一遍，肉眼无差就在汇报里记下文件名；看得出版式差异就 STOP。探针摘要出现「字体未就绪」时这一轮截图对比不可信，联网后重跑。

## Test plan

补丁在 `tests/test_build.py` 的 `test_uncompiled_latex_is_an_error_in_check_only` 之前加 6 个用例，都以 `tests/fixtures/mermaid-flow.html` 为输入（一幅带分支、回边、四种节点语义和两级文字的横向流程图，一幅时序图）：

- `test_mermaid_compiles_to_wide_and_narrow_svg_and_stays_idempotent` — 流程图出宽窄两版、时序图出一版；三个 SVG 都是 `role="img"`、有 `aria-labelledby`、`max-width` 是像素值、没有 `width` 属性；`:::focus` 落到节点 class 上；没有「SVG 图缺少」「斜线」的输出；重复构建文件不变。
- `test_mermaid_syntax_error_names_the_source_line` — 把源码第 7 行写坏，构建退出码 1，报「Mermaid 图第 1 幅编译失败，源码第 7 行」和「有 1 幅 Mermaid 图没有编译成 SVG」，另一幅照常编译。
- `test_uncompiled_mermaid_is_an_error_in_check_only` — 对没构建过的夹具跑 `--check-only`，报「有 2 幅 Mermaid 图没有编译成 SVG」。
- `test_mermaid_without_acc_title_warns` — 删掉两幅图的 `accTitle` / `accDescr`，构建通过，「Mermaid 图没写 accTitle / accDescr」出现 2 次。
- `test_mermaid_overwide_chart_warns` — 给流程图再接两个长标签节点，宽版超过 960px，构建通过并报「Mermaid 图第 1 幅排出来宽 …px，放进图框要缩到 0.xx 倍」和「把主流向改成 TD」。
- `test_mermaid_page_passes_render_check_and_exports_source`（需要 Chrome）— 带渲染检查的完整构建零 WARN；`export.md` 里两个 mermaid 代码块各一次，`accDescr` 的文字作为段落导出一次。

结构样板是同文件的 `test_latex_compiles_to_mathml_and_stays_idempotent`。

## Done criteria

- [ ] `python3 -m unittest skills.show-me-html.tests.test_build` → `Ran 71 tests`、`OK`
- [ ] `make check` exit 0
- [ ] `shasum -a 256 skills/show-me-html/assets/vendor/pele/pele.mjs` 以 `37bea5005aa6d2dd` 开头
- [ ] `grep -c 'compile_mermaid' skills/show-me-html/scripts/build.py` → `2`
- [ ] `grep -c '^## Mermaid 图' skills/show-me-html/references/diagrams.md` → `1`；`grep -c '照抄 Mermaid' skills/show-me-html/references/diagrams.md` → `0`
- [ ] Step 5 的四张截图看过，与描述相符；两次 `md5` 相同
- [ ] Step 6 五页零差异（或写明跳过的原因）
- [ ] `git status --short` 只有 Scope 里的文件；`git diff --stat -- skills/tufte-reader` 无输出
- [ ] 汇报里写明每条验证的实际输出

## STOP conditions

停下汇报，不要自行发挥：

- `git apply --check` 失败，或「Current state」的引文与现有代码对不上（代码在计划写成后变过）。
- Step 1 的校验和对不上（tufte-reader 的 pele 升级过；布局参数和 CSS 选择器是按 1.13.0 的输出写的，需要 advisor 重新核对）。
- Step 3 有 `test_interrupted_build_leaves_no_chrome_profile` 以外的用例失败，或它连续失败两次。
- Step 5 的截图与描述明显不符：标签顶出框、窄版没有变成纵向、深色主题下有白底或看不见的字、时序图被放大撑满。把截图路径写进汇报。
- Step 6 出现几何差异。
- 需要改 Scope 之外的文件才能通过。

## Maintenance notes

- **合入后要重新安装技能才生效**：`~/.claude/skills` 里是副本。合入 `main` 后由维护者执行 `make install SKILL=show-me-html SOURCE=.`（改本机环境，执行者不做）。
- **pele 升级**：上游半个月出了 8 个次版本（1.5.0 → 1.13.0，2026-10-15 至 10-31）。`scripts/mermaid.mjs` 的 `LAYOUT` 参数、`adapt()` 里对 `role` / `width` / `style` 的字符串替换、`show-me.css` 里按 `.pele-node`、`.pele-label tspan[font-weight]`、`.pele-cluster > rect` 写的选择器，都依赖上游的输出结构。升级步骤写在 `MAINTENANCE.md`「Vendor 升级」；tufte-reader 那份要一起升。
- **旧页面**：重新构建不含 Mermaid 源码的旧页面，行为不变。已构建页面里的 Mermaid 图每次重建都重新编译，pele 升级后布局可能变。
- **审阅时重点看**：`mermaid.mjs` 的 `adapt()` 三处字符串替换是否都命中（测试断言了 `role="img"`、像素 `max-width`、无 `width` 属性）；`check()` 里统计未编译图时先剥系统样式这一步；`diagrams.md`「Mermaid 图」一节的措辞。
- **有意没做**：
  - 源码开关（tufte-reader 有）：show-me-html 的「复制为 Markdown」已经带出源码。
  - `timeline`、`quadrantChart`、`mindmap`：前者色块上的字对比度不够（构建的对比度检查会报 ERROR），中者轴名是竖排字，后者不接受 `accTitle`；文档里写明不用。
  - 用 pele 的按图型注册入口（`pele/core`）减小 vendor 体积：没试，等体积成为问题再说。
  - 可点节点：Plan 031。
  - 字宽表沿用 tufte-reader 那份（按 `-apple-system` 实测分档，宁宽勿窄）。show-me-html 的图内字体是 IBM Plex Sans / Noto Sans SC，advisor 在夹具页和两张真实页面的重做图上看过，标签都在框内；以后出现标签顶出框，先调 `mermaid.mjs` 的 `EM` 表。
