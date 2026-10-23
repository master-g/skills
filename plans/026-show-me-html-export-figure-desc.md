# Plan 026: show-me-html 的 Markdown 导出带上图的 `<desc>`，复制出去数据不丢

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。索引 `plans/README.md` 由审阅者维护，你不要改它。
>
> **Drift check (run first)**: `git diff --stat eec315f..HEAD -- skills/show-me-html/assets/shell.js skills/show-me-html/references/charts.md skills/show-me-html/tests/test_build.py` 应无输出。有输出就对照下面「Current state」里的引文，引文原样还在就继续，对不上就 STOP。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容已经是 prettier 格式，原样粘贴即可，粘贴后 `prettier --check` 应直接通过。
>
> **2026-10-23 审阅修订（advisor）**：初版写于 `2f0e439`。审阅时把初版的 Step 1 套到 `eec315f` 的副本上，复现出一处缺陷：用 `getClientRects()` 判断可见，会丢掉未选中标签页里那张图的 `<desc>`，而导出器会照常导出该面板的正文和图注。初版的测试在这个缺陷上也能通过。修订版改为看 SVG 自己的 `display`，测试补上标签页、宽窄两版和五件套外壳；验证改为 MAINTENANCE.md 要求的冻结场景轮次，另外用 gallery 总览页检查数据图。详见 `plans/README.md`「026 审阅记录」。

## Status

- **Priority**: P3
- **Effort**: S（导出器一个分支、一个测试、一行文档）
- **Risk**: LOW（只多导出一段文字；屏幕、打印、截图都不变）
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `2f0e439`, 2026-10-22；2026-10-23 审阅后按 `eec315f` 刷新

## Why this matters

show-me-html 页面工具条上的「复制为 Markdown」由骨架脚本 `assets/shell.js` 把正文转成 Markdown。它跳过所有 `<svg>`，所以数据图导出后只剩标题、单位行、来源行和图注，图里的数字全没了。按技能的无障碍契约，每张图的 SVG 里都有 `<title>` 和 `<desc>`，缺了 `build.py` 会报 WARN；`<desc>` 写的正是图的数据摘要。例如 gallery 里图书借阅那张写的是「东湖 3,400 册，老城 2,600，西山 1,200……」，concept-explainer 冻结场景那张写的是「当前 QPS 为 400，TTL 为 600 秒，命中率为 76%」。导出时把 `<desc>` 放在图所在的位置、作为一段文字带出来，复制到别处的 Markdown 里就还有这些数据。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `eec315f`。

- `assets/shell.js:128-139`，导出器的跳过表，`SVG` 在里面：

  ```js
  /* ── 复制为 Markdown ──
  遍历 #doc（或 [data-md-root]）生成 GFM。跳过 [data-md-skip] / [hidden] / 脚本 / 弹层。 */
  (function () {
    var SKIP = new Set([
      "SCRIPT",
      "STYLE",
      "TEMPLATE",
      "DIALOG",
      "NOSCRIPT",
      "SVG",
      "CANVAS",
    ]);
  ```

- `assets/shell.js:171-181`，`skipped()` 与 `txt()`：

  ```js
  function skipped(el) {
    return (
      SKIP.has(el.tagName.toUpperCase()) ||
      el.hasAttribute("data-md-skip") ||
      el.hasAttribute("hidden") ||
      el.getAttribute("aria-hidden") === "true"
    );
  }
  function txt(s) {
    return (s || "").replace(/\s+/g, " ");
  }
  ```

- `assets/shell.js:288-294`，块级遍历的开头，本计划改这里：

  ```js
    function block(el, depth) {
      var out = "";
      Array.from(el.children).forEach(function (n) {
        if (skipped(n)) return;
        var t = n.tagName.toUpperCase();
        if (t === "SUMMARY")
          return; /* DETAILS 分支已单独输出，这里再走一遍会裸文本重复 */
  ```

- `assets/shell.js:348-356`：标签页分支**有意把隐藏的面板也导出**。它直接 `block(panel, depth)`，绕过了面板上 `hidden` 属性的跳过：

  ```js
      } else if (n.classList.contains("tabs")) {
        /* Markdown 没有标签页：每个标签导出成小标题 + 它的面板，隐藏的面板也要出。 */
        ...
            if (panel) out += block(panel, depth);
  ```

  所以判断 SVG 是否显示时不能用 `getClientRects()`：隐藏面板里的 SVG 没有布局盒，`getClientRects()` 返回空，结果面板正文和图注导出了，图的摘要却丢了（审阅时已复现）。`display` 不继承，隐藏面板里 SVG 自己的计算值仍是 `block`。

- `assets/show-me.css:1539-1551`，宽窄两版图（diagrams.md「窄屏另画一版」）：两版 SVG 前后挨着放在同一个 `.fig-box` 里，`display: none !important` 直接写在 SVG 自身上，`.diagram-narrow` 平时隐藏，`@media (max-width: 640px)` 下改为隐藏 `.diagram-wide`。所以 `getComputedStyle(svg).display !== "none"` 恰好只排除没在显示的那一版。

- 数据图的「五件套外壳」（`references/charts.md`「五件套外壳」）：`figure.fig[data-chart] > div.fig-box > (div.fig-head, p.fig-sub, svg, p.fig-src)`，`figcaption` 在 `.fig-box` 之后。`fig-sub` 是单位行，`fig-src` 是来源行，`.fig-tools` 带 `data-md-skip`。所以 `<desc>` 导出的位置在单位行之后、来源行之前，不是紧挨着图注。

- gallery 里有 10 张图的 `<desc>` 与单位行逐字相同（例如 `Q2 2026 · MRR, $K`）。agent 写页面时会照抄 gallery，这种写法会被带进用户页面，所以 `<desc>` 与上一段导出文字相同时不再重复导出。

- `charts.js` 重画时只清图形，保留 `<title>` / `<desc>`（`references/charts.md:236`：`` - `<title>`/`<desc>` 留在 svg 里，重播时运行时只清图形。``）。审阅时在 gallery 总览页上核实过：59 张数据图的 `<desc>` 都还在。

- 测试样板：`tests/test_build.py:251` 的 `test_snap_renders_both_themes_and_exports_markdown`，以及 `:285` 的 `test_snap_narrows_to_one_theme_and_width`（用 `--snap-theme` / `--snap-width` 只拍一种主题、一个宽度，`export.md` 取自这一档）。装饰器是 `@unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")`。`copy_fixture()` 复制 `tests/fixtures/minimal-shell.html`，`run_build(page, *args)` 自带 `--no-render`。

## Commands you will need

| Purpose  | Command                                                                                            | Expected on success                          |
| -------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`                                         | `Ran 60 tests`、末行 `OK`（执行前是 59）     |
| JS 语法  | `node -e "new Function(require('fs').readFileSync('skills/show-me-html/assets/shell.js','utf8'))"` | 无输出                                       |
| 格式     | `npx prettier --check <文件>`                                                                      | `All matched files use Prettier code style!` |
| 文档门禁 | `make check`                                                                                       | exit 0，`技能文档引用检查通过`               |

命令都在仓库根目录跑。Step 3、Step 4 的 shell 片段用 bash（本机默认 shell 是 fish，`VAR=$(…)` 赋值在 fish 里不成立）。

## Scope

**In scope**：`skills/show-me-html/assets/shell.js`、`skills/show-me-html/tests/test_build.py`、`skills/show-me-html/references/charts.md`（一行）。

**Out of scope**：

- `<title>`：它和图的结论标题重复，不导出。
- 不在 `figure` 里的 SVG（图标、装饰图形）：不导出。
- 把数据导出成 Markdown 表格：`<desc>` 是作者写的自然语言摘要，原样导出成一段。
- `inline()` 里的 SVG：仍按 `SKIP` 跳过，`SVG` 留在 `SKIP` 里。
- gallery 里那 10 张 `<desc>` 只重复单位行的图：改写它们的 `<desc>` 是另一件事，本计划不碰 `assets/gallery/`。
- `plans/README.md`：审阅者维护。

## Git workflow

从本地 `main` 开分支 `advisor/026-show-me-html-export-figure-desc`。提交信息例如 `feat(show-me-html): Markdown export keeps each figure's desc`。pre-commit 会跑 prettier 和 `make check`。不要 push。

## Steps

### Step 1: 导出器处理 SVG

`assets/shell.js` 的 `block()` 里，把

<!-- prettier-ignore -->
```js
    Array.from(el.children).forEach(function (n) {
      if (skipped(n)) return;
      var t = n.tagName.toUpperCase();
```

改为

<!-- prettier-ignore -->
```js
    Array.from(el.children).forEach(function (n) {
      var t = n.tagName.toUpperCase();
      if (t === "SVG") {
        /* 图本身不导出；图里的 <desc> 是写给读屏器的数据摘要，导出成一段文字，复制出去数据不丢。
           看 svg 自己的 display：宽窄两版图只出正在显示的那版，隐藏标签页里的图照样出
           （getClientRects 会把后者也丢掉）。和上一段（多半是单位行）相同就不再重复。 */
        var desc = n.closest("figure") && n.querySelector(":scope > desc");
        var d = desc ? txt(desc.textContent).trim() : "";
        if (
          d &&
          !out.endsWith(d + "\n\n") &&
          getComputedStyle(n).display !== "none" &&
          n.getAttribute("aria-hidden") !== "true" &&
          !n.hasAttribute("data-md-skip")
        )
          out += d + "\n\n";
        return;
      }
      if (skipped(n)) return;
```

（`if (skipped(n)) return;` 从第一行挪到 SVG 分支之后，其余不变。SVG 上有 `hidden` 属性时，`show-me.css:1015` 的 `[hidden] { display: none !important; }` 会压过 `.fig svg { display: block }`，计算值是 `none`，所以不用再单独判断。）

**Verify**：

- JS 语法检查无输出。
- `npx prettier --check skills/show-me-html/assets/shell.js` → `All matched files use Prettier code style!`（不要跑 `--write`；不通过说明粘贴时改了缩进，对照上面的代码块改回）。
- `grep -c 'getComputedStyle(n).display' skills/show-me-html/assets/shell.js` → `1`；`grep -c 'getClientRects' skills/show-me-html/assets/shell.js` → `0`。

### Step 2: 测试

在 `tests/test_build.py` 的 `test_snap_renders_both_themes_and_exports_markdown` 之后（它的最后一行是 `self.assertNotIn("__snap", md)`，后面空一行），`test_snap_narrows_to_one_theme_and_width` 之前，插入：

```python
    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_markdown_export_keeps_figure_desc(self):
        """图的 <desc> 是数据摘要：在图的位置导出成一段（单位行之后、来源行之前）。宽窄两版只出正在显示的那版，隐藏标签页里的图照样出，和上一段相同的不重复出。"""
        page = self.copy_fixture()
        figs = """<section><figure class="fig" data-chart="F1"><div class="fig-box">
          <div class="fig-head"><span class="fig-title">五月客流最高</span></div>
          <p class="fig-sub">单位：千人 · 2026 Q2</p>
          <svg id="d1" viewBox="0 0 400 120" role="img" aria-labelledby="d1-t d1-d"><title id="d1-t">月度客流</title>
          <desc id="d1-d">四月 120 千人，五月 135 千人，六月 98 千人。</desc></svg>
          <p class="fig-src">票务系统 · 2026 Q2</p></div>
          <figcaption>五月是全年峰值。</figcaption></figure>
          <figure class="fig"><div class="fig-box">
          <svg class="diagram-wide" viewBox="0 0 400 120" role="img"><title>流程</title><desc>宽版：甲到乙到丙。</desc></svg>
          <svg class="diagram-narrow" viewBox="0 0 200 300" role="img"><title>流程</title><desc>窄版：甲到乙到丙。</desc></svg>
          </div></figure>
          <figure class="fig"><div class="fig-box"><p class="fig-sub">单位：次 · 9 月</p>
          <svg viewBox="0 0 400 120" role="img"><title>重复</title><desc>单位：次 · 9 月</desc></svg></div></figure>
          <div class="tabs" id="tb"><nav role="tablist">
          <button type="button" role="tab" id="t1" aria-controls="p1" aria-selected="true" tabindex="0">甲</button>
          <button type="button" role="tab" id="t2" aria-controls="p2" aria-selected="false" tabindex="-1">乙</button></nav>
          <div role="tabpanel" id="p1" aria-labelledby="t1" tabindex="-1"><p>甲面板。</p></div>
          <div role="tabpanel" id="p2" aria-labelledby="t2" tabindex="-1" hidden><figure class="fig"><div class="fig-box">
          <svg viewBox="0 0 400 120" role="img"><title>乙</title><desc>乙面板的图：七月 88 千人。</desc></svg></div></figure></div>
          </div></section>"""
        page.write_text(page.read_text(encoding="utf-8").replace("</main>", figs + "</main>"), encoding="utf-8")
        md = {}
        for width in ("1280", "390"):
            out = page.parent / f"snap-{width}"
            result = run_build(page, "--snap", str(out), "--snap-theme", "light", "--snap-width", width)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            md[width] = (out / "export.md").read_text(encoding="utf-8")
        self.assertIn("单位：千人 · 2026 Q2\n\n四月 120 千人，五月 135 千人，六月 98 千人。\n\n票务系统 · 2026 Q2", md["1280"])
        self.assertNotIn("月度客流", md["1280"])
        self.assertIn("宽版：甲到乙到丙。", md["1280"])
        self.assertNotIn("窄版", md["1280"])
        self.assertIn("窄版：甲到乙到丙。", md["390"])
        self.assertNotIn("宽版", md["390"])
        self.assertIn("乙面板的图：七月 88 千人。", md["1280"])
        self.assertEqual(md["1280"].count("单位：次 · 9 月"), 1)
```

每个用例都防着一种具体的错误写法，不要删减或合并：

- 第一张图按五件套外壳写：断言 `<desc>` 出现在单位行和来源行之间。
- 宽窄两版：1280 和 390 各拍一次，各自只出一版。
- 隐藏标签页里的图：用 `getClientRects()` 判断可见时，这条会失败。
- 单位行与 `<desc>` 相同的图：没有 `!out.endsWith(...)` 时，这条会失败。

**Verify**：

- `python3 -m unittest skills.show-me-html.tests.test_build -k figure_desc` → `OK`。
- 反证一次：临时把 Step 1 里的 `getComputedStyle(n).display !== "none"` 换成 `n.getClientRects().length`，同一命令应失败于 `'乙面板的图：七月 88 千人。' not found`；改回后再跑一次 → `OK`。反证改动不要提交，改回后 `git diff` 里的 `shell.js` 应与 Step 1 一致。
- 全量 → `Ran 60 tests`、`OK`。

### Step 3: 冻结场景轮次

MAINTENANCE.md 规定改 `assets/shell.js` 后要跑冻结场景轮次。按 `skills/show-me-html/scenarios/README.md` 的流程新建一轮，目录后缀 `-026`：五页 HTML 复制自上一轮，用新的骨架重建，再跑探针。上一轮在主检出目录 `/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-6b6872b-027/`。`rounds/` 被 gitignore，只存在于主检出里，所以下面用绝对路径读它、不往里写；新的一轮建在你当前工作的检出里。用 bash 跑：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-6b6872b-027
RND=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-026
mkdir -p "$RND"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$RND/" && python3 skills/show-me-html/scripts/build.py "$RND/$n.html" | grep -E '^(ERROR|WARN)|自检通过'
done
node skills/show-me-html/scripts/probe_round.mjs "$RND" "$PREV" | grep -E '^[a-z-]+: |probe\.json|截图：|Markdown 不同'
diff "$PREV/_probe/concept-explainer.md" "$RND/_probe/concept-explainer.md"
```

**Verify**（advisor 在 `eec315f` 的副本上跑出的就是下面这些）：

- 五行 `自检通过。`，没有 ERROR / WARN。
- 探针五行 `无问题`。
- `与上一轮对比：probe.json 相同`，`截图：30/30 张逐字节相同`。本计划不改屏幕和打印，截图应完全相同。advisor 两次新建轮次，首跑都不是 30/30：一次 `probe.json` 4 处不同、截图 18/30，另一次 `probe.json` 相同、截图 12/30。不同的都在 status-report、approach-compare、code-review 三页，差异遍布全页文字的字形，约 1.1 万像素。两次都只重跑 `probe_round.mjs` 一次，就变成 `probe.json` 相同、30/30，与 027 记录的字体加载时机问题一致。遇到这种情况，只重跑 `node … probe_round.mjs` 那一行和 `diff` 那一行，重跑后仍不同再按 STOP 处理。
- 只有一行 `Markdown 不同：concept-explainer`。
- `diff` 的输出正好是下面三行。这段摘要由页面脚本按滑块状态改写，HTML 源码里写的是另一句；探针在跑判据前先导出，所以导出的是初始状态：

  ```
  22a23,24
  > 当前 QPS 为 400，TTL 为 600 秒，命中率为 76%。
  >
  ```

### Step 4: gallery 总览页的数据图都带上摘要

五个场景页里没有 `charts.js` 画的数据图，数据图要用 gallery 总览页检查。用 bash 跑：

```sh
G=$(mktemp -d)
python3 skills/show-me-html/scripts/gallery.py --out "$G" --no-render | tail -1
python3 skills/show-me-html/scripts/build.py "$G/all-charts.html" --no-render --snap "$G/snap" --snap-theme light --snap-width 1280 | tail -1
python3 - "$G" <<'EOF'
import re, sys
from pathlib import Path
g = Path(sys.argv[1])
html = (g / "all-charts.html").read_text(encoding="utf-8")
md = (g / "snap" / "export.md").read_text(encoding="utf-8")
descs = [" ".join(d.split()) for d in re.findall(r'<desc id="[^"]+">(.*?)</desc>', html, re.S)]
paras = [p.strip() for p in md.split("\n\n")]
print("desc", len(descs), "exported", sum(d in md for d in descs),
      "adjacent-dups", sum(1 for a, b in zip(paras, paras[1:]) if a and a == b))
EOF
rm -rf "$G"
```

**Verify**：

- 第一行是 `总览页  …/all-charts.html（59 张）`。
- 第二行是 `已快照  …/snap/export.md`。
- 最后一行是 `desc 59 exported 59 adjacent-dups 0`。

advisor 实测：改前是 `desc 59 exported 18 adjacent-dups 0`，那 18 条都是和单位行或别处文字碰巧相同的 `<desc>`。只改 Step 1 的 `display` 判断、不加去重时是 `exported 59 adjacent-dups 10`。

### Step 5: 文档

`references/charts.md` 里 `` - `<title>`/`<desc>` 留在 svg 里，重播时运行时只清图形。`` 这一行（`:236`）之后加一行：

<!-- prettier-ignore -->
```markdown
- 「复制为 Markdown」会把 `<desc>` 在图的位置导出成一段（单位行之后、来源行之前），所以把读者需要的数字写在 `<desc>` 里，不只写「一张柱状图」。
```

**Verify**：

- `npx prettier --check skills/show-me-html/references/charts.md` → `All matched files use Prettier code style!`。
- `grep -c '复制为 Markdown」会把' skills/show-me-html/references/charts.md` → `1`。
- `make check` → exit 0。

## Test plan

- 新增 `test_markdown_export_keeps_figure_desc`，覆盖四件事：
  - 按五件套外壳写的图，`<desc>` 夹在单位行和来源行之间，`<title>` 不出现。
  - 宽窄两版图在 1280 和 390 下各只出正在显示的那版。
  - 隐藏标签页里的图照样出。
  - 与单位行相同的 `<desc>` 不重复出。
- 反证：把可见判断换回 `getClientRects()` 时，新测试失败。
- Step 3 的冻结场景轮次：只有 concept-explainer 的导出多一行图摘要，截图和 `probe.json` 不变。
- Step 4 的 gallery 总览页：59 张数据图的摘要都在，没有相邻重复段。

## Done criteria

- [ ] `python3 -m unittest skills.show-me-html.tests.test_build` → `Ran 60 tests`、`OK`
- [ ] `npx prettier --check skills/show-me-html/assets/shell.js skills/show-me-html/references/charts.md` 通过
- [ ] `grep -c 'getComputedStyle(n).display' skills/show-me-html/assets/shell.js` → `1`
- [ ] Step 3：五页 `无问题`，`probe.json 相同`，30/30，只有 `Markdown 不同：concept-explainer`，`diff` 是那三行
- [ ] Step 4：`desc 59 exported 59 adjacent-dups 0`
- [ ] `make check` exit 0；`git status` 只显示 Scope 里的三个文件（新轮次目录在 gitignore 里，不会显示）

## STOP conditions

- Drift check 有输出，且「Current state」里的引文对不上。
- 反证时新测试没有失败（说明测试没测到隐藏标签页）。
- Step 3 中，除 concept-explainer 外还有别的 `Markdown 不同`；或 `diff` 多出、少了行，或出现 `<` 开头的删除行。
- Step 3 重跑一次后，`probe.json` 仍不同，或截图仍不是 30/30。
- Step 4 的 `exported` 小于 59，或 `adjacent-dups` 不是 0。
- 任何一步需要改 Scope 之外的文件，例如为了让测试通过去改 `build.py` 或 `show-me.css`。

## Maintenance notes

- 导出取的是复制那一刻的 DOM。页面脚本会改写 `<desc>` 的交互图（concept-explainer 就是），复制出去的是当时的读数。`probe_round.mjs` 先导出再跑判据，所以冻结轮次的 `.md` 是初始状态。
- 冻结场景的 Markdown 基线从本计划的轮次起，concept-explainer 多一行；下一轮对比时这一行属于预期。
- 去重只比较同一个 `.fig-box` 里紧挨在前面的那段（`out` 是本层 `block()` 的累积）。单位行如果不在 SVG 前面、不是同一层，就不会去重。
- gallery 有 10 张图（多为英文示例图，例如 `Q2 2026 · MRR, $K`、`sign-ups per market · bars cascade in · click to replay`）的 `<desc>` 只重复了单位行，没写数据，不符合 Step 5 加的那行文档。导出端已经去重；要不要改写这些 `<desc>`，留给维护者另定。
- 以后如果要导出 `<title>`，注意它通常和图的结论标题重复。
- 以后改导出器的可见性判断时，要同时守住两条：标签页分支导出隐藏面板，宽窄两版只出一版。新测试的两个用例就是为此写的。
