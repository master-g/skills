# Plan 019: show-me-html 图被拉大或压小时构建报 WARN，charts.md 写清单张图怎么排

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat fff32ba..HEAD -- skills/show-me-html/scripts/build.py skills/show-me-html/tests/test_build.py skills/show-me-html/references/charts.md skills/show-me-html/references/anti-patterns.md`
> 计划 017、018 先合入时，这四个文件都会出现在输出里，属于预期：017 只改 `PROBE` 里字号下限那一行和测试 `test_render_check_flags_chart_text_below_font_floor`；018 在 `PROBE` 末尾加了一段对比度测量，并在正则里加了一个 `(?P<contrast>…)` 分组。本计划的改动都是「追加在末尾」，与这两份计划不冲突。出现别的改动，或者下面「Current state」里的锚点行找不到，就是 STOP 条件。
>
> **2026-10-22 补充**：计划 020（维护者定在 018 之前执行）也会出现在输出里，属于预期：它给 `build.py` 的三处 Chrome 启动参数加了 `*chrome_proxy_args()`、新增这个函数，`test_build.py` 多一个测试，不碰 `PROBE`、正则和 `render_check` 的返回值。020 合入后本计划里的测试数都按多 1 个计。
>
> 本文件里的代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P2
- **Effort**: S（构建探针一段、`render_check` 返回值多一项、一个测试、两份文档）
- **Risk**: LOW（只加 WARN，不加 ERROR；gallery 59 张图和本机现有页面里只有一张会报）
- **Depends on**: 无硬依赖。建议排在 017、018 之后（三份都改 `PROBE` 的结尾和 `render_check` 的正则；按这个顺序执行，三份的验证预期值都已核对过）
- **Category**: dx
- **Planned at**: commit `fff32ba`, 2026-10-21

## Why this matters

show-me-html 把素材做成单文件 HTML 页面，数据图是 `<figure class="fig" data-chart="编号">` 里的一张 SVG，宽度 100%，高度按 viewBox 比例走。约定是半宽卡用 400 宽的 viewBox，两张并排放进 `<div class="charts">`；通栏图加 `.wide`，用 800 宽的 viewBox。在默认 60rem 版心、1280px 视口下，这两种都大约按 1:1 显示：半宽 1.07 倍，通栏 1.15 倍。

维护者 2026-10-21 的一页报告（`status-report` 配方）里，F5 刻度行是一张**单独的** `.fig`：没加 `.wide`，也不在 `.charts` 里，用的却是 400 宽的 viewBox。这张图被拉到 920px，放大 2.30 倍。刻度间距从 gallery 里的 8.2px 变成 12.4px，刻度线高 23px，字号 17.5px，同页的 F12 只有 7px。维护者的原话是「刻度之间的距离太大，太疏了」。`references/charts.md` 只写了「通栏图加 `.wide`」「多图放进 `.charts`」，没写**单张 `.fig` 会占满整栏**。`.charts` 用的是 `auto-fit`，里面只放一张时也会撑满。构建对这页零 WARN 通过。

本计划在构建的渲染探针里量每张数据图在 1280px 下的显示倍率（svg 显示宽度 ÷ viewBox 宽度），超出 0.8–1.5 时报 WARN，并在 charts.md 写清：单张图写成通栏，按单位计数的图改成通栏后要把单位细一档。计划 017 的字号下限按 viewBox 单位核对，前提是图大致按 1:1 显示；这条 WARN 也守住这个前提。

**为什么是 WARN 而不是 ERROR**：放大本身不一定错。比如维护者同一页的 G10 是 640 宽 viewBox 的通栏图，显示 1.44 倍，读起来没问题。连续图形放大以后只是变大，按单位计数的图才会变疏，构建分不出这两种情况。

**阈值的实测依据**（advisor 2026-10-21 在 1280px 下量）：gallery 半宽卡 1.075 倍，通栏 1.02–1.15 倍；72rem 版心（原型类配方）半宽约 1.31 倍、通栏约 1.39 倍；48rem 版心（各类 explainer）里 `.charts` 双栏的半宽卡约 0.835 倍。本机现有的两张 bedrock 报告页，除了上面的 F5（2.30）都在 1.07–1.44 之间。所以上限取 1.5、下限取 0.8，只抓「单张半宽图拉满整栏」和「800 宽的图塞进半宽卡」（约 0.54 倍）这两种明显错位。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）：`scripts/build.py` 负责构建与自检，`tests/test_build.py` 是 unittest 测试，`references/*.md` 是给生成页面的模型读的文档。行号按 `fff32ba`：017、018 都合入后，`references/charts.md` 的第 233 / 236 行会变成 235 / 238，`build.py` 里 `PROBE` 结尾与 `render_check` 的行号也会后移几十行。行号对不上时以引文为准，按引文的内容找位置。

- `scripts/build.py` 的 `PROBE` 是一个 Python 三引号字符串，里面是注入页面的 JS。它在 `setTimeout(function(){ … }, 1500)` 里依次量字号、正文字号、示意图字号，最后把结果用 `|` 拼进 `document.title`。在 `fff32ba`，结尾是（第 884–888 行）：

  <!-- prettier-ignore -->
  ```js
      document.title = 'PROBE|' + sw + '|' + cw + '|' + over.slice(0, 4).join('  ') + '|' + small.join('；')
        + '|' + text.slice(0, 4).join('；') + (text.length > 4 ? ' 等 ' + text.length + ' 处' : '')
        + '|' + diag.join('；');
    }, 1500);
  });</script>
  ```

  **若 018 已合入**，`document.title = …` 这一行前面多了一大段对比度测量，表达式末尾多了两行：

  <!-- prettier-ignore -->
  ```js
        + '|' + dim.slice(0, 6).map(function(d){ return d.s + (d.n > 1 ? ' ×' + d.n : ''); }).join('；')
        + (dim.length > 6 ? ' 等 ' + dim.length + ' 组' : '');
  ```

- `scripts/build.py` 的 `render_check()`（`fff32ba` 第 1036–1085 行）。下面摘出本计划要改的几行：

  ```python
  def render_check(page, widths=(500, 1024, 1280)):
      """返回 (issues, measured, ran)。ran=False 表示没有浏览器，这道关没跑。"""
      import html as htmllib, subprocess, tempfile
      chrome = find_chrome()
      if not chrome:
          return [], [], False

      html = page.read_text(encoding="utf-8")
      issues, measured = [], []
  ```

  ```python
              except Exception as e:
                  return [f"渲染检查跑不起来：{e}"], [], False
              m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)</title>", out, re.S)
  ```

  （018 合入后，这个正则在 `</title>` 前多一个 `\|(?P<contrast>.*?)`。）

  ```python
              diag = htmllib.unescape(m.group(6).strip())
              if diag:
                  issues.append(f"{cw}px 下示意图字号渲染后低于 8px：{diag}。宽版缩得太小就画窄版，"
                                "窄版控制 viewBox 宽度（diagrams.md「窄屏另画一版」）")
      return issues, measured, True
  ```

  （018 合入后，`return` 前面还有一段 `contrast = htmllib.unescape(m.group("contrast").strip())` 和它的 `if`。）

- `scripts/build.py` 的 `main()`（`fff32ba` 第 1139–1147 行）。`render_check` 只有这一个调用方，`warns` 在调用之后才打印：

  ```python
      rendered, measured = False, []
      if not args.no_render and not errors:
          render_issues, measured, rendered = render_check(args.page)
          errors += render_issues

      for w in warns:
          print(f"WARN   {w}")
  ```

- `tests/test_build.py`：渲染类测试都长这样：`@unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")`，`page = self.copy_fixture()`（复制 `tests/fixtures/minimal-shell.html`，它是 `status-report` 配方，60rem 版心），往 `</main>` 前插标记，用 `subprocess.run([sys.executable, str(BUILD), str(page)], …)` 跑**不带** `--no-render` 的构建，断言 stdout 和退出码。结构照抄 `test_render_check_flags_shrunk_stat_num`。新测试插在 `def test_duplicate_svg_ids_fail(self):` 之前。
- `references/charts.md` 第 233 行和第 236 行（「五件套外壳」一节，html 示例后面的要点列表）：

  <!-- prettier-ignore -->
  ```markdown
  - 通栏图加 `class="fig wide"`；多图放进 `<div class="charts">` 栅格。
  ```

  <!-- prettier-ignore -->
  ```markdown
  - 半宽卡 viewBox `0 0 400 320`，通栏 `0 0 800 320` 起；宽高比由 viewBox 决定，svg 宽 100%。
  ```

- `references/anti-patterns.md`：反模式名册是一张表，最后一行是 `| 11  | 窄屏硬缩图 | 已检查 | …`（若 018 已合入，最后一行是 018 加的第 12 条）。表后面有「状态推进记录：」列表，最后一条以 `- 2026-10-16 第 11 条登记即为已检查` 开头（018 合入后最后一条是 018 加的）。

**仓库约定**：Python 只用标准库，报告文字用中文；`PROBE` 是普通三引号字符串（不是 % 格式化），JS 里的正则反斜杠要写成 `\\`，本计划的 JS 不含反斜杠。文档按标题名引用章节（「五件套外壳」），不按编号，`make check` 会检查。Markdown 用 prettier 格式化；计划里给出的代码粘进 `.py` 文件后不受 prettier 影响。

## Commands you will need

在仓库根目录执行：

| Purpose    | Command                                                                                                                                | Expected on success                                     |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 单元测试   | `python3 -m unittest skills.show-me-html.tests.test_build`                                                                             | 末行 `OK`（测试数见各步，约 100–170 秒，需本机 Chrome） |
| 单个新测试 | `python3 -m unittest skills.show-me-html.tests.test_build.BuildCliTests.test_render_check_warns_when_a_chart_is_scaled_up -v`          | `ok`                                                    |
| 语法检查   | `python3 -W error::SyntaxWarning -c "import ast,pathlib; ast.parse(pathlib.Path('skills/show-me-html/scripts/build.py').read_text())"` | 无输出、exit 0                                          |
| 文档门禁   | `make check`                                                                                                                           | exit 0                                                  |
| 格式化     | `npx prettier --write <改过的 .md>`                                                                                                    | exit 0                                                  |
| 图库总览   | `G=$(mktemp -d) && python3 skills/show-me-html/scripts/gallery.py --out "$G"`                                                          | 见 Step 4                                               |

不要用 pytest（未安装）。

## Scope

**In scope**：

- `skills/show-me-html/scripts/build.py`（`PROBE` 字符串结尾、`render_check()`、`main()` 里调用 `render_check` 的两行）
- `skills/show-me-html/tests/test_build.py`（新增一个测试）
- `skills/show-me-html/references/charts.md`（「五件套外壳」的两条要点）
- `skills/show-me-html/references/anti-patterns.md`（新增一行与一条记录）

**Out of scope**：

- `assets/show-me.css` 的 `.charts` / `.fig` 布局：不改栅格，不给单张 `.fig` 加最大宽度。是否让单张半宽图保持半宽，是另一个视觉决定，维护者没有要求。
- `PROBE` 里已有的各项测量与它们的报错文案：只在末尾追加，不改。
- gallery 图块、`assets/charts.js`：属于计划 017 / 018。
- 维护者 bedrock 仓库里的报告页（不在本仓库里，不要找也不要改）。
- `MAINTENANCE.md`、`SKILL.md`。

## Git workflow

- 分支：`advisor/019-show-me-html-chart-scale-warn`。
- conventional commits，scope 写技能名。一个提交即可：`feat(show-me-html): render check warns when a chart is stretched or squeezed`。
- pre-commit 会跑 prettier 和 `make check`。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`。

## Steps

### Step 1: 探针量每张数据图的显示倍率

在 `scripts/build.py` 的 `PROBE` 字符串里，找到 `document.title = 'PROBE|' + sw + …` 这一行（4 个空格缩进），在它**正上方**插入：

<!-- prettier-ignore -->
```js
    // 图的显示倍率（charts.md「五件套外壳」）：字号下限按 viewBox 单位核对，前提是图大致按 1:1 显示。
    // 半宽卡的 400 宽 viewBox 单独放进整栏会放大一倍多，刻度和珠子变疏、字比同页别的图大一圈；缩到 0.8 倍以下字就小于下限
    var scaled = [];
    document.querySelectorAll('figure[data-chart] svg[viewBox]').forEach(function(s){
      var vb = s.viewBox.baseVal, w = s.getBoundingClientRect().width;
      if (!vb || !vb.width || !w) return;
      var k = w / vb.width;
      if (k > 1.5 || k < 0.8)
        scaled.push(s.closest('figure').dataset.chart + (s.id ? '（#' + s.id + '）' : '') + ' viewBox 宽 ' + vb.width + '，显示 ' + Math.round(w) + 'px，' + k.toFixed(2) + ' 倍');
    });
```

然后把 `document.title = …` 这个表达式的**最后一行**末尾的 `;` 去掉，另起一行接上（缩进 6 个空格）`+ '|' + scaled.join('；');`：

- 018 **未**合入时，最后一行原本是 `      + '|' + diag.join('；');`，改完是：

  <!-- prettier-ignore -->
  ```js
        + '|' + diag.join('；')
        + '|' + scaled.join('；');
  ```

- 018 **已**合入时，最后一行原本是 `      + (dim.length > 6 ? ' 等 ' + dim.length + ' 组' : '');`，改完是：

  <!-- prettier-ignore -->
  ```js
        + (dim.length > 6 ? ' 等 ' + dim.length + ' 组' : '')
        + '|' + scaled.join('；');
  ```

**Verify**: 语法检查命令无输出；`grep -c "scaled.join('；')" skills/show-me-html/scripts/build.py` → `1`。

### Step 2: `render_check` 把倍率报成 WARN

在 `render_check()` 里做五处改动：

1. 文档字符串改为：

   ```python
       """返回 (issues, notes, measured, ran)。issues 是 ERROR，notes 是 WARN；ran=False 表示没有浏览器，这道关没跑。"""
   ```

2. `return [], [], False`（没找到 Chrome 的那个）改为 `return [], [], [], False`；紧接着的 `issues, measured = [], []` 改为 `issues, notes, measured = [], [], []`。
3. `return [f"渲染检查跑不起来：{e}"], [], False` 改为 `return [f"渲染检查跑不起来：{e}"], [], [], False`。
4. 正则：在 `</title>` 前加一个命名分组 `\|(?P<scaled>.*?)`。018 未合入时改完是：

   ```python
               m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(?P<scaled>.*?)</title>", out, re.S)
   ```

   018 已合入时改完是：

   ```python
               m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(?P<contrast>.*?)\|(?P<scaled>.*?)</title>", out, re.S)
   ```

5. 函数末尾的 `return issues, measured, True` 改为 `return issues, notes, measured, True`，并在它**正上方**（`for w in widths` 循环体内、与 `diag = …` 同级的 12 个空格缩进；018 已合入时放在 `contrast` 那段之后）加：

   ```python
               scaled = htmllib.unescape(m.group("scaled").strip())
               if scaled and w == max(widths):
                   notes.append(f"{cw}px 下图的显示倍率超出 0.8–1.5：{scaled}。单张图独占整栏时写成 .fig.wide 配 800 宽 viewBox，"
                                "按单位计数的图（刻度、珠子、点阵）把单位细一档，保持标记间距（charts.md「五件套外壳」）")
   ```

   只在最宽视口（1280px）报一次：窄视口下单栏排布，半宽卡本来就会放大，那不是错位。

然后在 `main()` 里把

```python
        render_issues, measured, rendered = render_check(args.page)
        errors += render_issues
```

改为

```python
        render_issues, render_notes, measured, rendered = render_check(args.page)
        errors += render_issues
        warns += render_notes
```

`warns` 在这之后才打印，`自检通过（N 个警告需逐条判断）` 的计数会把它算进去。

**Verify**: 语法检查无输出；`grep -n "render_check(args.page)" skills/show-me-html/scripts/build.py` → 一行，内容含 `render_notes`；全量单元测试 → `OK`，测试数与执行前相同（017、018 都已合入时是 `Ran 49 tests`），没有失败。

### Step 3: 回归测试

在 `tests/test_build.py` 中、`def test_duplicate_svg_ids_fail(self):` 之前插入（缩进 4 空格，属于 `BuildCliTests` 类）：

```python
    @unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")
    def test_render_check_warns_when_a_chart_is_scaled_up(self):
        """半宽卡的 400 宽 viewBox 单独占整栏会放大一倍多（2026-10 实例：F5 刻度行 2.3 倍，刻度间距 12px）。"""
        fig = """<figure class="fig" data-chart="F5"><div class="fig-box"><svg id="ID" viewBox="0 0 400 200" role="img"
          aria-labelledby="ID-t"><title id="ID-t">t</title></svg></div></figure>"""
        for layout, flagged in (("lone", True), ("pair", False)):
            with self.subTest(layout=layout):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                body = fig.replace("ID", "solo") if layout == "lone" else (
                    '<div class="charts">' + fig.replace("ID", "left") + fig.replace("ID", "right") + "</div>")
                page.write_text(html.replace("</main>", f"<section>{body}</section></main>"), encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual("WARN   1280px 下图的显示倍率超出 0.8–1.5：F5（#solo）" in result.stdout, flagged, result.stdout)
                self.assertEqual(result.returncode, 0, result.stdout)

```

两个子用例分别证明：单张 400 宽的图在 60rem 版心里被拉满时报 WARN（实测 2.30 倍），两张并排放进 `.charts` 时不报；两种情况构建都通过（WARN 不拦交付）。

**Verify**: 单个新测试命令 → `ok`（advisor 在 scratchpad 实测约 18 秒）；全量 → `OK`，测试数比 Step 2 多 1。

### Step 4: 现有页面不误报

```sh
G=$(mktemp -d) && python3 skills/show-me-html/scripts/gallery.py --out "$G" 2>&1 | grep -c "显示倍率"
```

**Verify**: 输出 `0`。gallery 59 张图在 1280px 下的倍率都在 1.02–1.15 之间。

注意：017 还没把 gallery 修完时，这条命令里的构建会因为字号或对比度 ERROR 返回非零。这不影响本步的判断，渲染检查的 WARN 与 ERROR 同时打印，只看「显示倍率」出现的次数。

### Step 5: 文档

1. `references/charts.md`「五件套外壳」一节，把第 233 行

   <!-- prettier-ignore -->
   ```markdown
   - 通栏图加 `class="fig wide"`；多图放进 `<div class="charts">` 栅格。
   ```

   改为

   <!-- prettier-ignore -->
   ```markdown
   - 两张半宽图并排放进 `<div class="charts">` 栅格；通栏图加 `class="fig wide"`。
   ```

   把第 236 行

   <!-- prettier-ignore -->
   ```markdown
   - 半宽卡 viewBox `0 0 400 320`，通栏 `0 0 800 320` 起；宽高比由 viewBox 决定，svg 宽 100%。
   ```

   改为下面三条：

   <!-- prettier-ignore -->
   ```markdown
   - 半宽卡 viewBox `0 0 400 320`，通栏 `0 0 800 320` 起；宽高比由 viewBox 决定，svg 宽 100%。
   - **单张图会占满整栏**：不在 `.charts` 里，或 `.charts` 里只有它一张，都一样。这时仍用 400 宽的 viewBox，60rem 版心下会放大 2.3 倍，字比同页别的图大一圈，刻度和珠子之间空出大缝。单张图写成通栏：加 `.wide`，viewBox 改成 800 宽，按新宽度重排。构建在 1280px 下量每张图的显示倍率，超出 0.8–1.5 报 WARN。
   - 按单位计数的图（F5 刻度行、F12 串珠、点阵、华夫格）按显示尺寸检查密度：1280px 下相邻标记的间距不超过约 8px（gallery 半宽卡里的 F5 是 8.2px）。改成通栏后行变长，把单位细一档（一根 = 0.1 个百分点改成 0.05 个百分点），根数翻倍，间距回到原来的大小，单位行同步改写。
   ```

2. `references/anti-patterns.md`：在表格最后一行之后加一行（列数与上一行相同；编号接着表里最大的编号，018 未合入时是 12，已合入时是 13，下面按 13 写）：

   <!-- prettier-ignore -->
   ```markdown
   | 13 | 单张图拉满 | 已检查 | 半宽卡的 400 宽 viewBox 单独放进整栏，被放大一倍多：刻度、珠子变疏，字比同页别的图大一圈（2026-10 实例：F5 刻度行 2.30 倍，刻度间距 12.4px）。 | 单张图写成 `.fig.wide` 配 800 宽 viewBox；按单位计数的图把单位细一档。build.py 在 1280px 下量显示倍率，超出 0.8–1.5 报 WARN。 |
   ```

   并在「状态推进记录：」列表末尾加一行：`- <执行当天日期> 第 13 条登记即为已检查（显示倍率 WARN）。`（编号与上面那行一致。）

3. `npx prettier --write skills/show-me-html/references/charts.md skills/show-me-html/references/anti-patterns.md`

**Verify**: `make check` → exit 0；`grep -c '单张图会占满整栏' skills/show-me-html/references/charts.md` → `1`；`grep -c '单张图拉满' skills/show-me-html/references/anti-patterns.md` → `1`。

### Step 6: 冻结场景轮次

`MAINTENANCE.md`「联动规则」要求改 `build.py` 后跑五个冻结场景。五个场景页都没有数据图，新检查不会命中，这一步确认没有连带改坏别的东西。

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-16-7454494-base
NEW=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-019
mkdir -p "$NEW"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$NEW/" && python3 skills/show-me-html/scripts/build.py "$NEW/$n.html" | tail -2
done
node skills/show-me-html/scripts/probe_round.mjs "$NEW" "$PREV"
```

**Verify**: 五次构建都打印 `自检通过。`，不出现「显示倍率」（advisor 在 017 + 018 + 019 叠加的副本里实测如此）；探针五行 `无问题`。`scenarios/rounds/` 在 `.gitignore` 里，轮次目录不进提交。

## Test plan

- 新增 `test_render_check_warns_when_a_chart_is_scaled_up`（Step 3），一个正例一个反例。结构照抄 `test_render_check_flags_shrunk_stat_num`。
- 现有渲染类测试（字号下限、大数、示意图宽窄版，018 合入后还有对比度）全部保持通过，证明 `|` 分段和 `render_check` 的新返回值没把它们改坏。
- 误报面：Step 4 的 gallery 总览页（59 张图）、Step 6 的五个冻结场景。

## Done criteria

- [ ] 全量单元测试 → `OK`，测试数比执行前多 1（017、018 都已合入时是 `Ran 50 tests`）
- [ ] 语法检查无输出
- [ ] `make check` exit 0
- [ ] `grep -c '显示倍率超出 0.8–1.5' skills/show-me-html/scripts/build.py` → `1`
- [ ] Step 4 输出 `0`
- [ ] Step 6 五个场景构建都不含「显示倍率」，探针五行 `无问题`
- [ ] `git status --short` 只列出 Scope 里的四个文件
- [ ] `plans/README.md` 本计划状态行已更新

## STOP conditions

- Drift check 出现 Scope 以外的改动，或 Step 1/2 的锚点行找不到（例如 `document.title = 'PROBE|'` 不止一处，或 `render_check` 已经有了别的返回值）。
- Step 4 输出不是 `0`：说明 gallery 里有图的倍率超出阈值，汇报是哪张、多少倍，不要调阈值了事。
- 新测试的 `lone` 子用例没报 WARN，或报出的倍率不在 2.2–2.4 之间：`minimal-shell.html` 的版心可能变了，汇报实际倍率。
- 任何已有测试失败，修一次仍不过。

## Maintenance notes

- 阈值 0.8 / 1.5 是按 2026-10 的三档版心定的（见「Why this matters」末段）。以后改 `--page` 宽度、`.charts` 的列宽下限（`minmax(min(100%, 22rem), 1fr)`）或 `.fig-box` 的内边距，要重新量 gallery 的倍率，看会不会穿过阈值。
- 48rem 版心里双栏的半宽卡是 0.835 倍，离下限很近。如果有人把 48rem 改窄，或者把 `.fig-box` 的内边距加大，这些图会开始报 WARN。
- 只量 `figure[data-chart]` 里带 `viewBox` 的 svg。示意图（diagrams.md）另有一套「渲染后低于 8px」的检查，不在这里。
- 这条检查在 1280px 下报一次。手机宽度下单栏排布时半宽卡会放大，属于正常情况。窄屏上通栏图会缩到 0.5 倍左右，字号太小（gallery 的 9 张通栏图在 500px 视口下只有 3.3–4.8px），这是另一个已知问题，记在 `plans/README.md` 的「未规划」里。
- 维护者那一页 F5 的修法（不属于本计划）：加 `.wide`，viewBox 改成 `0 0 800 …`，一根刻度改成 0.05 个百分点（也门 4.80% 变成 96 根），`GAP` 按新宽度重算，单位行改成「一根刻度 = 0.05 个百分点」。
