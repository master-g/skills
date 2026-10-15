# Plan 011: show-me-html 指标带成为通用组件，构建检查拦下被压小的大数与过小的正文字

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 55a66e8..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/scripts/build.py skills/show-me-html/tests/test_build.py skills/show-me-html/references/components.md skills/show-me-html/references/layouts.md skills/show-me-html/references/anti-patterns.md`
> 如果计划 010 已经合入，输出里只会出现 `show-me.css`、`components.md`（010 的改动在 `.item-group` 和 `.src` 附近，与本计划的位置不重叠），这属于预期。出现别的文件，或者下面「Current state」的摘录与现行文件对不上，就是 STOP 条件。

## Status

- **Priority**: P1
- **Effort**: M（CSS、构建探针、一个测试、三份文档；验证要跑一轮冻结场景）
- **Risk**: LOW–MED（`status-report` 场景的指标卡外观会变，见「Why this matters」末段；新检查是 ERROR，会拦下现有的坏页面，这是有意的）
- **Depends on**: 建议在 `plans/010-show-me-html-item-divider-and-source-line.md` 之后执行（两者都改 `show-me.css`，位置不重叠；先 010 再本计划，场景高度的预期值按这个顺序写）
- **Category**: bug
- **Planned at**: commit `55a66e8`, 2026-10-14

## Why this matters

show-me-html 把素材做成单文件 HTML 页面，共用的视觉系统 `assets/show-me.css` 在构建时内联进页面。维护者的一份页面（ReelShort 技术笔记，`feature-explainer` 配方）开头有一排「指标带」，里面的大数在 1280px 下实测只有 **12.8px**，单位 `<small>` 只有 **6.4px**，「1s」里的 s 几乎看不见。同一页暗卡里的 `.stat-num` 是正常的 44px。

原因有三层：

1. **组件缺位。** 骨架只给 `status-report` 配方提供 `.metric-band`（`show-me.css:2049` 的选择器带着 `[data-recipe="status-report"]`），而 `references/layouts.md` 要求所有报告类页面都用「指标带」作证据。其他配方的模型只能自己写 `.stat-band`。
2. **自写的样式误伤了大数。** 页面写了 `.stat-band p { font-size: 0.8rem }`，本意是给标签用，但 `.stat-num` 本身也是 `<p>`。`.stat-band p` 的优先级是 (0,1,1)，高于骨架 `.stat-num` 的 (0,1,0)，页面 `<style>` 又排在后面，于是大数被压成标签字号；`small` 按 0.5em 计算，又再减半。
3. **构建看不见这个问题。** `build.py` 的渲染检查只量图表 SVG 里的字号，不量 HTML 文字，这页零 WARN 通过。

本计划给出通用的 `.metric-band`：任何配方都能用，标签有现成样式，格内的大数比 `.metric-band p` 这类页面选择器优先级高。`small` 加一个最小字号。渲染探针新增两条检查：`.stat-num` 计算字号低于 1.75rem，或正文文字低于 10px，就报 ERROR。

**可见变化（有意的）**：冻结场景 `status-report` 的指标卡里，标签从 16px 正文色变成 13px 次要色，格内段落的默认外边距被清掉，卡片变矮。advisor 在 scratchpad 里看过前后截图，新样式更像常见的 KPI 卡。

**为什么报 ERROR 而不是 WARN（advisor 的建议，维护者可改）**：同一个探针里已有的「图内字号低于下限」就是 ERROR（`references/anti-patterns.md` 第 9 条），6px 的字和 13px 的大数没有正当用途，报 ERROR 能挡住带病交付。代价是旧页面重新构建会失败，`--open` 也不会打开，必须先修页面；不重新构建的历史页面不受影响。维护者若决定用 WARN，按 Step 3 末尾的「WARN 变体」做。**执行前先看 `plans/README.md` 的 show-me-html 一节有没有记录维护者的决定；没有记录就按 ERROR 做。**

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）：`assets/show-me.css` 是内联进每个页面的视觉系统，`scripts/build.py` 负责构建与自检，`tests/test_build.py` 是 unittest 测试，`references/*.md` 是给生成页面的模型读的契约。

- `assets/show-me.css:885-910`（当前，大数契约）：

```css
/* ── 大数契约 ────────────────────────────────────────────────────
   数字是衬线大字，单位进 <small>：数字走拉丁字形可以收字距，汉字单位不能。
   184<small>万条/日</small> 读作一个量，整串放大会让"万条/日"跟数字抢大小。
   上限 2.75rem 低于首屏 h1，h1 始终是页面最大字。 */
.stat-num {
  font-family: var(--font-serif);
  font-size: clamp(1.75rem, 4vw, 2.75rem);
  font-weight: 500;
  line-height: 1.05;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums lining-nums;
}
/* 它常写成 <p>：浏览器默认 1em 外边距在 44px 字号下是 44px 空隙。
   :where 让它零优先级，骨架的 main > section > * + * 节奏仍然压得过它 */
:where(.stat-num) {
  margin-block: 0;
}
.stat-num > strong {
  font-weight: inherit;
}
.stat-num small {
  font-size: 0.5em;
  font-weight: 500;
  letter-spacing: 0;
  margin-inline-start: 0.12em;
}
```

- `assets/show-me.css:2049-2063`（当前，只属于 status-report 的指标带；若计划 010 已合入，行号约 +20）：

```css
[data-recipe="status-report"] .metric-band,
.recipe-matrix > [data-recipe="status-report"] .metric-band {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 9rem), 1fr));
  gap: 0.75rem; /* 面色分格，不画边线；auto-fit 折行后不会留下空格子 */
}
[data-recipe="status-report"] .metric-band > * {
  min-width: 0;
  padding: 1rem;
  background: var(--color-card);
  border-radius: var(--radius);
}
[data-recipe="status-report"] .metric-band strong {
  display: block;
}
```

**注意**：`tests/test_build.py` 的 `test_css_covers_every_recipe` 要求 CSS 里出现每个配方的 `[data-recipe="<名>"]` 字样。`status-report` 只在这几行出现，所以第二个选择器 `.recipe-matrix > [data-recipe="status-report"] .metric-band` **必须保留**。

- `scripts/build.py:822-839`（当前，渲染探针 `PROBE` 字符串的结尾；这是一个普通的 Python 三引号字符串，里面的 JS 正则反斜杠要写成 `\\`，参照 813 行的 `split(/\\s+/)`）：

```js
  var sw = de.scrollWidth, cw = de.clientWidth;
  // 字号下限（charts.md「文字」，viewBox 单位）：图只在滚入视野时才画，先强制全画，等入场定时器跑完再量
  document.querySelectorAll('figure[data-chart] svg').forEach(function(s){ if (s._replay) s._replay(); });
  setTimeout(function(){
    var small = [];
    document.querySelectorAll('figure[data-chart]').forEach(function(f){
      var wide = f.classList.contains('wide'), floor = wide ? 5.5 : 6.5, min = Infinity;
      f.querySelectorAll('svg text, svg tspan').forEach(function(t){
        if (t.textContent.trim()) min = Math.min(min, parseFloat(getComputedStyle(t).fontSize));
      });
      if (min < floor) {
        var svg = f.querySelector('svg[id]');
        small.push(f.dataset.chart + (svg ? '（#' + svg.id + '）' : '') + ' 最小 ' + min + ' < ' + (wide ? '通栏' : '半宽') + '下限 ' + floor);
      }
    });
    document.title = 'PROBE|' + sw + '|' + cw + '|' + over.slice(0, 4).join('  ') + '|' + small.join('；');
  }, 1500);
});</script>
```

- `scripts/build.py:1009` 与 `1024-1027`（当前，`render_check()` 解析探针结果；`render_check` 返回的 issues 在 `main()` 1084 行被并进 errors）：

```python
            m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)</title>", out, re.S)
```

```python
            small = htmllib.unescape(m.group(4).strip())  # --dump-dom 把 <title> 里的 < 转义了
            if small and w == max(widths):  # viewBox 单位与视口宽度无关，报一次
                issues.append(f"图内字号低于下限：{small}。装不下改 <title> hover 出，不缩字号硬塞（charts.md「文字」）")
    return issues, measured, True
```

- `tests/test_build.py:334-351`：`test_render_check_flags_chart_text_below_font_floor` 是新测试要照抄的结构（`@unittest.skipUnless(… find_chrome …)`，`self.copy_fixture()`，往 `</main>` 前插标记，用 `subprocess.run([sys.executable, str(BUILD), str(page)])` 跑**不带** `--no-render` 的构建，断言 stdout 文字和退出码，并用 `subTest` 写正例与反例）。新测试插在它后面、`def test_gallery_loops_are_registered_for_pause` 之前（当前第 353 行）。
- `references/components.md:82-97`：「大数」一节，开头是 `## 大数` 和一段 html 示例，最后一行是「`<strong>` 可加可不加，字重由 `.stat-num` 定。」
- `references/layouts.md:239`（`status-report` 配方）：

```markdown
- 指标块：`.card[data-size=sm]` 或 `.metric-band`，大数写 `.stat-num`（单位进 `<small>`，见 components.md「大数」）+ 变化量（涨跌用 `.badge[data-variant]`）。
```

- `references/anti-patterns.md`：反模式名册是一张表，最后一行是 `| 9   | 硬塞小字     | 已检查   | …`。表后面有「状态推进记录：」列表。

**仓库约定**：CSS 注释用中文写「为什么」；不写字面颜色，只用 `var(--…)`。Python 只用标准库，报告文字用中文。文档按标题名引用章节（「大数」），不按编号，`make check` 会检查。Markdown 用 prettier 格式化。

## Commands you will need

在仓库根目录执行：

| Purpose    | Command                                                                                                             | Expected on success                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 单元测试   | `python3 -m unittest skills.show-me-html.tests.test_build`                                                          | 末行 `OK`；改完后 `Ran 46 tests`（约 90 秒，需本机 Chrome）       |
| 单个新测试 | `python3 -m unittest skills.show-me-html.tests.test_build.BuildCliTests.test_render_check_flags_shrunk_stat_num -v` | `ok`                                                              |
| 语法检查   | `python3 -W error -c "import ast; ast.parse(open('skills/show-me-html/scripts/build.py').read())"`                  | 无输出、exit 0（有 SyntaxWarning 说明 JS 里的 `\s` 没写成 `\\s`） |
| 文档门禁   | `make check`                                                                                                        | exit 0                                                            |
| 格式化     | `npx prettier --write <改过的 .md>`                                                                                 | exit 0                                                            |
| 构建单页   | `python3 skills/show-me-html/scripts/build.py <页面.html>`                                                          | 末尾 `自检通过。`                                                 |
| 场景探针   | `node skills/show-me-html/scripts/probe_round.mjs <本轮目录> <上一轮目录>`                                          | 每个场景一行 `无问题`                                             |

不要用 pytest（未安装）。

## Scope

**In scope**：

- `skills/show-me-html/assets/show-me.css`（大数契约块、status-report 指标带块）
- `skills/show-me-html/scripts/build.py`（`PROBE` 字符串、`render_check()`）
- `skills/show-me-html/tests/test_build.py`（新增一个测试）
- `skills/show-me-html/references/components.md`（「大数」一节）
- `skills/show-me-html/references/layouts.md`（第 239 行一句）
- `skills/show-me-html/references/anti-patterns.md`（新增第 10 条）

**Out of scope**：

- `.item-group`、`.src` / `.fig-src`：属于计划 010。
- `.table`：属于计划 012。
- 图表探针的已有逻辑（`small` 那段）和它的 ERROR 文案：只在后面追加，不改。
- `MAINTENANCE.md`、`SKILL.md`。
- 维护者的 `reelshort-tech-notes.html`（不在仓库里，不要找也不要改）。
- `tests/fixtures/*.html`：不需要改。

## Git workflow

- 分支：`advisor/011-show-me-html-metric-band`。
- conventional commits，scope 写技能名。建议两个提交：`feat(show-me-html): metric-band works in every recipe, stat-num holds its size inside it` 和 `feat(show-me-html): render check flags shrunk stat-num and sub-10px text`。
- pre-commit 会跑 prettier 和 `make check`。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`。

## Steps

### Step 1: 指标带改为通用组件

把 `assets/show-me.css` 里上面摘录的 status-report 指标带整块（从 `[data-recipe="status-report"] .metric-band,` 到 `.metric-band strong { display: block; }` 的右花括号）替换为：

```css
/* 指标带不再只属于 status-report：任何配方的首屏或证据段都用它，页面不要自造 .stat-band */
.metric-band,
.recipe-matrix > [data-recipe="status-report"] .metric-band {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 9rem), 1fr));
  gap: 0.75rem; /* 面色分格，不画边线；auto-fit 折行后不会留下空格子 */
}
.metric-band > * {
  min-width: 0;
  padding: 1rem;
  background: var(--color-card);
  border-radius: var(--radius);
}
.metric-band strong {
  display: block;
}
.metric-band > * > * {
  margin-block: 0;
}
.metric-band > * > * + * {
  margin-block-start: 0.35rem;
}
/* 格内除大数以外的段落是标签或注记：小一号、次要色。写成 .metric-band p 会连大数一起改掉 */
.metric-band > * > p:not(.stat-num) {
  font-size: 0.8125rem;
  color: var(--color-muted-foreground);
}
```

**Verify**: `grep -c '\[data-recipe="status-report"\] \.metric-band' skills/show-me-html/assets/show-me.css` → `1`（只剩 recipe-matrix 那一个）；`grep -c '^\.metric-band > \* > p:not(.stat-num) {' skills/show-me-html/assets/show-me.css` → `1`。

### Step 2: 大数在指标带里压不小，单位有最小字号

在上面摘录的大数契约块里做两处改动：

1. 把 `.stat-num {` 这一行（选择器那行）改为两行选择器：

   ```css
   .stat-num,
   .metric-band .stat-num {
   ```

   规则体不变。`.metric-band .stat-num` 的优先级是 (0,2,0)，页面写 `.metric-band p { font-size: … }`（(0,1,1)）就压不动大数了。

2. 把 `.stat-num small {` 规则里的 `font-size: 0.5em;` 改为：

   ```css
   font-size: max(0.5em, 0.8125rem); /* 大数被压小时单位不跟着缩到看不清 */
   ```

**Verify**: `python3 -m unittest skills.show-me-html.tests.test_build` → 末行 `OK`，`Ran 45 tests`（新测试还没加）。

### Step 3: 渲染探针量正文字号与大数

1. 在 `scripts/build.py` 的 `PROBE` 字符串里，把这一行

   <!-- prettier-ignore -->
   ```js
       document.title = 'PROBE|' + sw + '|' + cw + '|' + over.slice(0, 4).join('  ') + '|' + small.join('；');
   ```

   替换为下面的代码（缩进与原行一致，4 个空格）。**注意**：`split(/\\s+/)` 在 .py 文件里必须是两个反斜杠：

   <!-- prettier-ignore -->
   ```js
       // 正文文字字号下限（不含图内 SVG 与公式）：页面 <style> 用宽选择器压掉骨架字号时，构建要看得见。
       // 只量自己直接带文字的可见元素；收起的 <details> 内容尺寸为 0，自动跳过
       var text = [], doc = document.getElementById('doc') || document.body;
       var name = function(el){
         return el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim()
           ? '.' + el.className.trim().split(/\\s+/).slice(0,2).join('.') : '');
       };
       var shown = function(el){ var r = el.getBoundingClientRect(); return r.width >= 2 && r.height >= 2; };
       doc.querySelectorAll('*').forEach(function(el){
         if (el.closest('svg, math')) return;
         var own = false;
         for (var n = el.firstChild; n; n = n.nextSibling)
           if (n.nodeType === 3 && n.textContent.trim()) { own = true; break; }
         if (!own || !shown(el)) return;
         var fs = parseFloat(getComputedStyle(el).fontSize);
         if (fs < 10) text.push(name(el) + ' ' + fs + 'px「' + el.textContent.trim().slice(0, 12) + '」 < 10px');
       });
       // 大数契约（components.md「大数」）：.stat-num 最小 1.75rem。更小说明被页面样式覆盖了
       doc.querySelectorAll('.stat-num').forEach(function(el){
         if (!shown(el)) return;
         var fs = parseFloat(getComputedStyle(el).fontSize);
         if (fs < 27.5) text.push('.stat-num「' + el.textContent.trim().slice(0, 12) + '」' + fs + 'px < 1.75rem');
       });
       document.title = 'PROBE|' + sw + '|' + cw + '|' + over.slice(0, 4).join('  ') + '|' + small.join('；')
         + '|' + text.slice(0, 4).join('；') + (text.length > 4 ? ' 等 ' + text.length + ' 处' : '');
   ```

2. 在 `render_check()` 里把正则改成 5 个分组：

   ```python
               m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)</title>", out, re.S)
   ```

3. 紧接在 `issues.append(f"图内字号低于下限：…")` 那行之后（同一个 `for w in widths` 循环体内，与 `small = …` 同级缩进）加：

   ```python
               text = htmllib.unescape(m.group(5).strip())
               if text and w == max(widths):
                   issues.append(f"正文字号过小：{text}。多半是页面 <style> 的宽选择器（如 .xxx p）压掉了骨架字号，"
                                 "改窄选择器或换骨架组件（components.md「大数」「指标带」）")
   ```

**Verify**: 语法检查命令无输出；`python3 -m unittest skills.show-me-html.tests.test_build` → `OK`，`Ran 45 tests`（已有的图内字号测试依赖探针的 `|` 分段，它通过就说明分段没被改坏）。

**WARN 变体（仅当 `plans/README.md` 记录维护者选择了 WARN）**：第 3 小步改成往一个新列表 `notes` 里追加；`render_check` 返回 `issues, measured, True, notes`（另外两处提前 `return` 补上第 4 个值 `[]`）；`main()` 第 1084 行改为 `render_issues, measured, rendered, render_warns = render_check(args.page)`，再加一行 `warns += render_warns`。注意 `warns` 在 1088 行就打印了，`render_check` 调用在它之前（1082-1085），所以只要在打印前合并即可。Step 4 测试里的断言相应改成：flagged 时 stdout 含 `WARN   正文字号过小`，且两种情况退出码都是 0。

### Step 4: 回归测试

在 `tests/test_build.py` 中、`def test_gallery_loops_are_registered_for_pause(self):` 之前插入（缩进 4 空格，属于 `BuildCliTests` 类）：

```python
    @unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")
    def test_render_check_flags_shrunk_stat_num(self):
        """页面 <style> 写 .band p 会连 .stat-num 一起压小（2026-10 实例：12.8px 的大数、6.4px 的单位）。"""
        band = """<section><div class="metric-band"><div><p class="stat-num">720<small>p</small></p>
          <p>ABR 自动档上限</p></div></div></section>"""
        for style, flagged in ((".metric-band p { font-size: 0.8rem; }", False),
                               (".band p { font-size: 0.8rem; }", True)):
            with self.subTest(style=style):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                markup = band if not flagged else band.replace('class="metric-band"', 'class="band"')
                html = html.replace("</main>", markup + "</main>").replace(
                    "</head>", f"<style>{style}</style></head>")
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual("正文字号过小：.stat-num「720p」" in result.stdout, flagged, result.stdout)
                self.assertEqual(result.returncode, 1 if flagged else 0, result.stdout)

```

两个子用例分别证明：用骨架的 `.metric-band` 时，页面写宽选择器也压不小大数（Step 2 的效果）；自造 `.band` 把大数压小时，构建报 ERROR（Step 3 的效果）。

**Verify**: 单个新测试命令 → `ok`；全量 → `OK`，`Ran 46 tests`。

### Step 5: 文档

1. `references/components.md`「大数」一节，在最后一行「`<strong>` 可加可不加，字重由 `.stat-num` 定。」之后空一行，追加：

   ````markdown
   ### 指标带

   一排并列的大数用 `.metric-band`，所有配方都能用；每格一个块，大数加标签，可再跟一行注记：

   ```html
   <div class="metric-band">
     <div>
       <p class="stat-num">1<small>s</small></p>
       <p>每集预加载的数据量</p>
     </div>
     <div>
       <p class="stat-num">720<small>p</small></p>
       <p>ABR 自动档上限</p>
     </div>
   </div>
   ```

   格内大数以外的 `<p>` 自动是小号次要色标签，标签写在大数上面还是下面都行。不要自造 `.stat-band` 一类的外壳，也不要写 `.xxx p { font-size }`：
   这条选择器会连 `.stat-num`（它也是 `<p>`）一起压小。构建的渲染检查发现 `.stat-num` 小于 1.75rem 或正文小于 10px 时会报 ERROR。
   ````

2. `references/layouts.md` 第 239 行，把「`.card[data-size=sm]` 或 `.metric-band`」改为「`.metric-band`（components.md「大数」下的「指标带」，任何配方通用）或 `.card[data-size=sm]`」，其余不变。

3. `references/anti-patterns.md`：在表格第 9 行之后加一行（列数与上一行相同）：

   ```markdown
   | 10 | 宽选择器压字号 | 已检查 | 页面 `<style>` 写 `.外壳 p { font-size }` 一类宽选择器，误伤同为 `<p>` 的 `.stat-num` 等骨架类（2026-10 实例：指标带大数 12.8px、单位 6.4px）。 | 用骨架组件（`.metric-band`）；必须自写时用 `:not(.stat-num)` 或给标签单独的类。build.py 渲染检查：`.stat-num` < 1.75rem 或正文 < 10px 报 ERROR。 |
   ```

   并在「状态推进记录：」列表末尾加一行：`- <执行当天日期> 第 10 条登记即为已检查（渲染检查量 .stat-num 与正文字号）。`

4. `npx prettier --write skills/show-me-html/references/components.md skills/show-me-html/references/layouts.md skills/show-me-html/references/anti-patterns.md`

**Verify**: `make check` → exit 0；`grep -c '^### 指标带' skills/show-me-html/references/components.md` → `1`；`grep -c '宽选择器压字号' skills/show-me-html/references/anti-patterns.md` → `1`。

### Step 6: 冻结场景轮次

与计划 010 的 Step 5 相同：复用上一轮页面，重新构建后探针对比。

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-09-23-bb65054
NEW=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-011
mkdir -p "$NEW"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$NEW/" && python3 skills/show-me-html/scripts/build.py "$NEW/$n.html" | tail -2
done
node skills/show-me-html/scripts/probe_round.mjs "$NEW" "$PREV"
```

**Verify**（advisor 在 scratchpad 套用 010 和本计划后的实测值）：

- 五次构建各打印 `自检通过。`：新检查在五个场景上没有误报。advisor 另外验证过两个夹具页和 gallery 全图页（59 图），也都没有误报。
- 探针五行 `无问题`；`status-report` 的判据里仍是 `"statNum":4`、`"metricOneRow1280":true`。
- 高度：`status-report` 1280px 2205 → 2063、390px 2417 → 2190；`concept-explainer` 2632 → 2598。其他场景不变。若 010 尚未合入，`status-report` 会少减约 85px，`concept-explainer` 不变。
- 人眼看 `"$NEW"/_probe/status-report-light-1280.png`：四张指标卡里，标签是灰色小字，在大数上方；大数仍是衬线大字，一排四格。

## Test plan

- 新增 `test_render_check_flags_shrunk_stat_num`（Step 4），一个正例一个反例。结构照抄 `test_render_check_flags_chart_text_below_font_floor`。
- 现有 45 个测试全部保持通过；其中 `test_css_covers_every_recipe` 保证 status-report 的选择器字样还在，`test_render_check_flags_chart_text_below_font_floor` 保证探针的 `|` 分段没被改坏。
- 误报面：Step 6 的五个场景。

## Done criteria

- [ ] `python3 -m unittest skills.show-me-html.tests.test_build` → `OK`，`Ran 46 tests`
- [ ] `python3 -W error -c "import ast; ast.parse(open('skills/show-me-html/scripts/build.py').read())"` 无输出
- [ ] `make check` exit 0
- [ ] `grep -c '正文字号过小' skills/show-me-html/scripts/build.py` → `1`
- [ ] Step 6 五个场景构建都是 `自检通过。`，探针五行 `无问题`
- [ ] `git status --short` 只列出 Scope 里的六个文件
- [ ] `plans/README.md` 本计划状态行已更新

## STOP conditions

- Drift check 出现 Scope 以外的改动，或摘录对不上（010 已合入导致的行号偏移不算）。
- Step 6 有任何一个场景构建报「正文字号过小」：说明检查对合规页面误报，汇报具体元素，不要放宽阈值了事。
- 现有测试 `test_render_check_flags_chart_text_below_font_floor` 失败：探针分段被改坏，修一次仍不过就停下。
- `PREV` 目录不存在：汇报，不要自己生成场景页。
- 发现 `.metric-band` 在别的配方块里也有规则（`grep -n 'metric-band' skills/show-me-html/assets/show-me.css` 出现 Step 1 以外的行）。

## Maintenance notes

- 正文字号下限定为 10px，是因为骨架最小的正文小字 `.src` 原来是 10.24px（计划 010 之后中文页是 12px）。以后新增比 10px 更小的骨架文字，会被这条检查拦下：要么别加，要么同步调整阈值。
- `.stat-num` 的阈值 27.5px 对应 `clamp(1.75rem, …)` 的下限 28px，留了 0.5px 余量防止舍入误差。改大数的 clamp 下限时，这里要一起改。
- 探针只在最宽视口（1280px）报一次。字号依赖 `vw` 时，窄屏的值可能不同；这个情况由 `clamp` 的下限兜住。
- `.metric-band > * > * + *` 的 0.35rem 间距在 status-report 场景里看起来偏紧（标签离大数近）。审阅者觉得要松一点，可以改成 0.5rem，只影响观感，不影响检查。
- 维护者那份触发本计划的页面，重新构建后会因为本计划报 ERROR，这符合预期。修法是在页面里把 `stat-band` 换成 `metric-band`，并删掉页面自己的 `.stat-band` 样式块。
