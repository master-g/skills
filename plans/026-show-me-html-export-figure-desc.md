# Plan 026: show-me-html 的 Markdown 导出带上图的 `<desc>`，复制出去数据不丢

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 2f0e439..HEAD -- skills/show-me-html/assets/shell.js skills/show-me-html/references/components.md`
> 有输出时对照下面「Current state」里的引文；引文对不上就是 STOP 条件。`tests/test_build.py` 可能已被 020–023 改过，不影响本计划。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写；提交时 pre-commit 会用 prettier 重排，属于预期。

## Status

- **Priority**: P3
- **Effort**: S（导出器一个分支、一个测试、一句文档）
- **Risk**: LOW（只多导出一段文字）
- **Depends on**: none（021 前后都能执行，测试的装饰器照抄当时的写法）
- **Category**: direction
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 页面工具条上的「复制为 Markdown」由骨架脚本 `assets/shell.js` 把正文转成 Markdown。它跳过所有 `<svg>`，数据图在导出里只剩标题、单位行和图注。按技能的无障碍约定，每张图的 SVG 里都有 `<title>` 和 `<desc>`，`<desc>` 写的正是图里的数据摘要（2026-10-22 维护者那页的 F5 图在 `<desc>` 里写了每种语言的数字）。导出时把 `<desc>` 作为一段文字带上，复制到别处的 Markdown 就还留着数据。

advisor 在 scratchpad 里套用了 Step 1 的改动：最小夹具里加一张带 `<desc>` 的图，`export.md` 在图注前多出那段数据；concept-explainer 冻结场景页的导出只多了一行（它的模型图的 `<desc>`），其余逐字相同。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `2f0e439`。

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

- `assets/shell.js:171-178`：

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

- `assets/shell.js:288-293`，块级遍历的开头（本计划改这里）：

  ```js
    function block(el, depth) {
      var out = "";
      Array.from(el.children).forEach(function (n) {
        if (skipped(n)) return;
        var t = n.tagName.toUpperCase();
        if (t === "SUMMARY")
  ```

- 图的结构：`figure.fig > … > .fig-box > svg`，SVG 的直接子元素里有 `<title>` 和 `<desc>`；`figcaption` 是图注。数据图由 `charts.js` 的 `reveal` 画，重画时只清图形、保留 `<title>` / `<desc>`。宽窄两版的示意图（`.diagram-wide` / `.diagram-narrow`）同时在 DOM 里，靠媒体查询只显示一版。

- `tests/test_build.py` 的 `test_snap_renders_both_themes_and_exports_markdown` 是样板：用 `--snap` 让 `build.py` 在无头 Chrome 里调用页面的 `window.showMeMarkdown()`，结果写进快照目录的 `export.md`。

- `references/charts.md:235`（「页面脚本模板」之后的要点列表里）：`` - `<title>`/`<desc>` 留在 svg 里，重播时运行时只清图形。``

## Commands you will need

| Purpose  | Command                                                                                            | Expected on success |
| -------- | -------------------------------------------------------------------------------------------------- | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`                                         | 末行 `OK`           |
| JS 语法  | `node -e "new Function(require('fs').readFileSync('skills/show-me-html/assets/shell.js','utf8'))"` | 无输出              |
| 文档门禁 | `make check`                                                                                       | exit 0              |

## Scope

**In scope**：`skills/show-me-html/assets/shell.js`、`tests/test_build.py`、`references/charts.md`（一行）、`plans/README.md`（状态行）。

**Out of scope**：

- `<title>`：它和图的结论标题重复，不导出。
- 不在 `figure` 里的 SVG（图标、装饰图形）：不导出。
- 把数据导出成 Markdown 表格：`<desc>` 是作者写的自然语言摘要，原样导出成一段。

## Git workflow

从本地 `main` 开分支 `advisor/026-show-me-html-export-figure-desc`；提交例如 `feat(show-me-html): Markdown export keeps each figure's desc`。不要 push。

## Steps

### Step 1: 导出器处理 SVG

`assets/shell.js` 的 `block()` 里，把

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
           宽窄两版的示意图只导出正在显示的那一版 */
        var desc = n.closest("figure") && n.querySelector(":scope > desc");
        var d = desc ? txt(desc.textContent).trim() : "";
        if (d && n.getClientRects().length && n.getAttribute("aria-hidden") !== "true" && !n.hasAttribute("data-md-skip"))
          out += d + "\n\n";
        return;
      }
      if (skipped(n)) return;
```

（`SVG` 仍留在 `SKIP` 里：行内遍历 `inline()` 遇到 SVG 照旧跳过。）然后 `npx prettier --write skills/show-me-html/assets/shell.js`。

**Verify**: JS 语法检查无输出；`npx prettier --check skills/show-me-html/assets/shell.js` → `All matched files use Prettier code style!`。

### Step 2: 测试

在 `test_snap_renders_both_themes_and_exports_markdown` 之后加一个测试，装饰器照抄它的：

```python
    def test_markdown_export_keeps_figure_desc(self):
        """图的 <desc> 是数据摘要：导出成图注前的一段，复制出去数据不丢。"""
        page = self.copy_fixture()
        fig = """<section><figure class="fig" data-chart="F1"><div class="fig-box">
          <svg id="d1" viewBox="0 0 400 120" role="img" aria-labelledby="d1-t d1-d"><title id="d1-t">月度客流</title>
          <desc id="d1-d">四月 120 千人，五月 135 千人，六月 98 千人。</desc></svg></div>
          <figcaption>五月是全年峰值。</figcaption></figure></section>"""
        page.write_text(page.read_text(encoding="utf-8").replace("</main>", fig + "</main>"), encoding="utf-8")
        out = page.parent / "snap"
        result = run_build(page, "--snap", str(out))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        md = (out / "export.md").read_text(encoding="utf-8")
        self.assertIn("四月 120 千人，五月 135 千人，六月 98 千人。\n\n五月是全年峰值。", md)
        self.assertNotIn("月度客流", md)
```

**Verify**: `python3 -m unittest skills.show-me-html.tests.test_build -k figure_desc` → `OK`；全量 → `OK`，测试数比执行前多 1。

### Step 3: 冻结场景的导出只多出图的摘要

```sh
R=$(ls -d /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/*/ | tail -1)
T=$(mktemp -d)
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$R/$n.html" "$T/"; python3 skills/show-me-html/scripts/build.py "$T/$n.html" --no-render --snap "$T/$n" > /dev/null
  echo "== $n"; diff "$R/_probe/$n.md" "$T/$n/export.md"
done
```

`$R/_probe/<场景>.md` 是 `probe_round.mjs` 导出的，和 `--snap` 的 `export.md` 一样都来自页面的 `window.showMeMarkdown()`，所以两者可以直接比。

**Verify**: 每个 diff 只有新增行（`>` 开头），新增的都是页面里某张图 `<desc>` 的文字；没有 `<` 开头的删除行。advisor 实测 concept-explainer 只多一行 `当前 QPS 为 400，TTL 为 600 秒，命中率为 76%。`（和一个空行），其余四页无差异。

再确认宽窄两版的示意图只导出一版：

```sh
cp skills/show-me-html/tests/fixtures/diagram-variants.html "$T/dv.html"
python3 skills/show-me-html/scripts/build.py "$T/dv.html" --no-render --snap "$T/dv" > /dev/null
grep -c '本地验证、AI 评审、自动检查、人工批准' "$T/dv/export.md"
```

→ `1`（advisor 实测）。

### Step 4: 文档

`references/charts.md` 里 `` - `<title>`/`<desc>` 留在 svg 里，重播时运行时只清图形。`` 这一行之后加一行：

<!-- prettier-ignore -->
```markdown
- 「复制为 Markdown」会把 `<desc>` 导出成图注前的一段，所以把读者需要的数字写在 `<desc>` 里，不只写「一张柱状图」。
```

然后 `npx prettier --write skills/show-me-html/references/charts.md`。

**Verify**: `make check` → exit 0；`grep -c '会把 `<desc>` 导出' skills/show-me-html/references/charts.md` → `1`。

## Test plan

- 新增 `test_markdown_export_keeps_figure_desc`：`<desc>` 出现在图注之前，`<title>` 不出现。
- Step 3 对照五个冻结场景的导出，确认只多出图的摘要。

## Done criteria

- [ ] 全量单元测试 `OK`，测试数比执行前多 1
- [ ] `npx prettier --check skills/show-me-html/assets/shell.js` 通过
- [ ] Step 3 的 diff 只有新增的图摘要行
- [ ] `make check` exit 0；`git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- Step 3 出现删除行，或新增了不是 `<desc>` 的内容。
- 宽窄两版的示意图把两版的 `<desc>` 都导出了（`tests/fixtures/diagram-variants.html` 可用来检查）。

## Maintenance notes

- 冻结场景的 `export.md` 基线会因此多出几行；下一轮 `probe_round.mjs` 对比 Markdown 时这属于预期。
- 以后若要导出 `<title>`，注意它通常和图的结论标题重复。
