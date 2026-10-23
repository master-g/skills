# Plan 023: show-me-html 构建时报出越出 SVG 图框、会被裁掉的文字（WARN）

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: 本计划要求计划 018、019、021 已合入（它在 018、019 之后往 `PROBE` 末尾再追加一段；021 让渲染检查在 reduced motion 下量末帧，没有它逐帧布局的图会被误报）。先确认：`grep -c '(?P<contrast>' skills/show-me-html/scripts/build.py` → `1`，`grep -c '(?P<scaled>' skills/show-me-html/scripts/build.py` → `1`，`grep -c '"reduced": True, "eval": title' skills/show-me-html/scripts/build.py` → `1`。不满足就 STOP。
> 再跑 `git diff --stat 2f0e439..HEAD -- skills/show-me-html/references/charts.md skills/show-me-html/references/anti-patterns.md`，对照下面「Current state」里的引文。
>
> 2026-10-23 advisor 在 `90fb8af` 上做过冷读审阅：子代理把本计划原样套到副本上跑通，全部 Verify 满足；只按审阅结果改了 Step 4 的轮次目录和两处文档行号。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P2
- **Effort**: S（`PROBE` 一段、`render_check` 几行、一个测试、两份文档各一两句）
- **Risk**: LOW（只加 WARN，不让任何页面失败）
- **Depends on**: `plans/018-show-me-html-text-contrast.md`、`plans/019-show-me-html-chart-scale-warn.md`、`plans/021-show-me-html-cdp-runner.md`
- **Category**: bug
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 页面里的图是内联 SVG。SVG 的内容超出它的 viewBox 时，浏览器把超出的部分裁掉（HTML 里 `svg` 默认 `overflow: hidden`，`show-me.css` 没有改它）。2026-10-22 维护者的一页报告里，F5 图最长一行的行尾文字「其中 135 条仍引用」越出图框，在 1280px 下被裁掉一截；构建零 WARN 通过，看整页截图时也没看出来，事后才发现。

`scripts/gallery.py --shots` 的探针已经会查「文字越出图框」，但只在图库上跑；`build.py` 的渲染检查（每次构建都跑）没有这一项。按 `MAINTENANCE.md`「毕业规则」：同一失败第二次出现，要毕业为 `build.py` 检查。本计划只搬越框这一部分，报 WARN。`plans/README.md` 记录过「文字重叠检查不进 `build.py`」（用户页面排法多，误报代价高），那条不变：越框没有这个顾虑，字的外接框超出 SVG 的盒子，就一定有一部分看不见。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。

- `scripts/gallery.py` 的 `PROBE` 里现成的越框判断（`2f0e439` 的 `:178-189`），本计划照搬它的判据：

  ```js
          var sr = s.getBoundingClientRect(), boxes = [];
          s.querySelectorAll('text').forEach(function(t){
            if (!t.textContent.trim()) return;
            fonts.push(parseFloat(getComputedStyle(t).fontSize));
            // 文字重叠与越界（charts.md「交付前自检」第 3 条）：只比水平文字，旋转文字的外接框天然互相交叠
            var m = t.getScreenCTM(), r = t.getBoundingClientRect(), cs = getComputedStyle(t);
            if (!m || Math.abs(m.b) > 1e-3 || Math.abs(m.c) > 1e-3 || r.width < 1 || cs.display === 'none' || parseFloat(cs.opacity) === 0) return;
            …
            if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1) clipped.push(name);
  ```

- `scripts/build.py` 的 `PROBE`：页面 `load` 后先对每张数据图调 `_replay()` 强制画出，`setTimeout` 1500ms 后逐项测量，最后把结果用 `|` 分段写进 `document.title`。018、019 合入后，测量部分的末尾是 019 的 `scaled` 一段，接着是：

  <!-- prettier-ignore -->
  ```js
      document.title = 'PROBE|' + sw + '|' + cw + '|' + over.slice(0, 4).join('  ') + '|' + small.join('；')
        + '|' + text.slice(0, 4).join('；') + (text.length > 4 ? ' 等 ' + text.length + ' 处' : '')
        + '|' + diag.join('；')
        + '|' + dim.slice(0, 6).map(function(d){ return d.s + (d.n > 1 ? ' ×' + d.n : ''); }).join('；')
        + (dim.length > 6 ? ' 等 ' + dim.length + ' 组' : '')
        + '|' + scaled.join('；');
  ```

  `PROBE` 里已有的辅助：`doc`（`#doc` 或 `body`）、`shown(el)`（盒子宽高都 ≥ 2）。

- `render_check()` 的正则（018、019 合入后）：

  ```python
              m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(?P<contrast>.*?)\|(?P<scaled>.*?)</title>", out, re.S)
  ```

  019 加的 `scaled` 处理（循环体内，12 个空格缩进）：

  ```python
              scaled = htmllib.unescape(m.group("scaled").strip())
              if scaled and w == max(widths):
                  notes.append(…)
  ```

  函数开头有 `issues, notes, measured = [], [], []`，结尾是 `return issues, notes, measured, True`。`notes` 会在 `main()` 里作为 `WARN` 打印。

- `tests/test_build.py` 的 `test_render_check_flags_chart_text_below_font_floor` 是本计划测试的样板：往最小夹具里塞一张 `figure[data-chart]`，再塞一段用 `showMeChart.reveal` / `showMeChart.txt` 画字的脚本，然后跑完整构建。021 之后它的装饰器是 `@unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")`，新测试照抄。

- 021 之后，`render_check()` 用 `run_jobs()` 在一个 Chrome 里跑各宽度，任务带 `"reduced": True`：数据图画的是末帧。advisor 在 scratchpad 里试过不带它：gallery 总览页的 G11 力导向图在节点布局完成前被量到，20 个节点标签全被报成越框。

- `references/charts.md`「文字」小节（`90fb8af` 的 `:149`）：`… \`scripts/gallery.py --shots\` 的探针会报出图库里互相重叠或越出图框的文字。` 「交付前自检」第 3 条（`:293`）：`3. 标签会不会重叠？邻近峰值只标一个？`

- `references/anti-patterns.md` 是「反模式名册」：表格列为 `# | 名字 | 状态 | 识别特征 | 当页修法`，表后有「状态推进记录：」列表。018、019 各加了一行，编号接表里最大的编号。

## Commands you will need

| Purpose  | Command                                                      | Expected on success |
| -------- | ------------------------------------------------------------ | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`   | 末行 `OK`           |
| 语法检查 | `python3 -m py_compile skills/show-me-html/scripts/build.py` | 无输出              |
| 文档门禁 | `make check`                                                 | exit 0              |

## Scope

**In scope**：`skills/show-me-html/scripts/build.py`、`tests/test_build.py`、`references/charts.md`、`references/anti-patterns.md`、`plans/README.md`（状态行）。

**Out of scope**：

- 文字重叠检查：维护者此前决定只留在 `gallery.py`。
- 改成 ERROR：先 WARN，再出现一次漏网再议。
- `gallery.py` 的探针：不动，两边判据一致即可。
- 旋转的文字：与 gallery 一致，只查水平文字。

## Git workflow

从本地 `main` 开分支 `advisor/023-show-me-html-clipped-chart-text`；提交例如 `feat(show-me-html): render check warns on chart text cut off by the frame`。不要 push。

## Steps

### Step 1: `PROBE` 量越框文字

1. 在 `document.title = 'PROBE|' + sw + …` 这一行（4 个空格缩进）**正上方**插入：

   <!-- prettier-ignore -->
   ```js
       // 文字越出图框（charts.md「交付前自检」第 3 条）：SVG 外面的部分被裁掉，读者看到半截字。
       // 判据同 gallery.py 的探针：只比水平文字，外接框超出 SVG 的盒子 1px 以上就算
       var clipped = [];
       doc.querySelectorAll('svg').forEach(function(s){
         if (!s.getClientRects().length || !shown(s) || getComputedStyle(s).overflow === 'visible') return;
         var sr = s.getBoundingClientRect(), fig = s.closest('figure[data-chart]');
         var where = (fig ? fig.dataset.chart : 'svg') + (s.id ? '（#' + s.id + '）' : '');
         s.querySelectorAll('text').forEach(function(t){
           var cs = getComputedStyle(t), m = t.getScreenCTM(), r = t.getBoundingClientRect();
           if (!t.textContent.trim() || !m || Math.abs(m.b) > 1e-3 || Math.abs(m.c) > 1e-3 || r.width < 1
               || cs.display === 'none' || parseFloat(cs.opacity) === 0) return;
           if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1)
             clipped.push(where + '「' + t.textContent.trim().split('|').join('/').split('；').join(';').slice(0, 12) + '」');
         });
       });
   ```

2. 把 `document.title = …` 表达式的最后一行 `      + '|' + scaled.join('；');` 改为两行：

   <!-- prettier-ignore -->
   ```js
         + '|' + scaled.join('；')
         + '|' + clipped.slice(0, 20).join('；');
   ```

**Verify**: 语法检查无输出（`PROBE` 是 Python 字符串，语法检查只保证字符串没断）；`grep -c "clipped.slice(0, 20)" skills/show-me-html/scripts/build.py` → `1`。

### Step 2: `render_check` 汇总成一条 WARN

1. 正则在 `\|(?P<scaled>.*?)` 之后、`</title>` 之前加 `\|(?P<clipped>.*?)`，改完是：

   ```python
               m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(?P<contrast>.*?)\|(?P<scaled>.*?)\|(?P<clipped>.*?)</title>", out, re.S)
   ```

2. `issues, notes, measured = [], [], []` 之后另起一行 `    clipped = []  # 越框文字跨宽度去重：数据图的 viewBox 不随视口变，同一处在每个宽度都会报`。

3. 在 019 的 `scaled` 处理之后（循环体内，12 个空格缩进）加：

   ```python
               for c in htmllib.unescape(m.group("clipped").strip()).split("；"):
                   if c and c not in clipped:
                       clipped.append(c)
   ```

4. 在函数最后的 `return issues, notes, measured, True` **正上方**（4 个空格缩进，`with` 块之外）加：

   ```python
       if clipped:
           notes.append(f"文字越出图框，SVG 外的部分会被裁掉：{'；'.join(clipped[:6])}"
                        + (f" 等 {len(clipped)} 处" if len(clipped) > 6 else "")
                        + "。把字挪进 viewBox 或缩短；确实放不下再加宽 viewBox，不缩字号（charts.md「交付前自检」第 3 条）")
   ```

**Verify**: 语法检查无输出；全量单元测试 → `OK`，测试数与改前相同。

### Step 3: 测试

在 `test_render_check_flags_chart_text_below_font_floor` 之后加（装饰器照抄它的）：

```python
    def test_render_check_warns_on_text_outside_the_frame(self):
        """SVG 外的部分会被裁掉：文字越出图框报 WARN，构建不失败。"""
        chart = """<section><figure class="fig" data-chart="F1"><div class="fig-box">
          <svg id="edge" viewBox="0 0 400 120" role="img" aria-labelledby="edge-t edge-d"><title id="edge-t">t</title>
          <desc id="edge-d">d</desc></svg></div></figure></section>"""
        script = """<script>showMeChart.reveal(document.getElementById("edge"), (s) =>
          showMeChart.txt(s, { x: X, y: 60, "font-size": 10 }, "越出图框的长标签"));</script>"""
        for x, flagged in (("360", True), ("20", False)):
            with self.subTest(x=x):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                html = html.replace("</main>", chart + "</main>").replace(
                    "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script.replace("X", x))
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual("文字越出图框，SVG 外的部分会被裁掉：F1（#edge）「越出图框的长标签」" in result.stdout,
                                 flagged, result.stdout)
                self.assertEqual(result.returncode, 0, result.stdout)
```

（`x: 360` 起写 8 个 10 号中文字，约 80 个单位宽，右缘约 440，超出 400 宽的 viewBox。这张单独的半宽图在 1280px 下会被拉大，019 会另报一条倍率 WARN，与本测试无关。）

**Verify**: `python3 -m unittest skills.show-me-html.tests.test_build -k outside_the_frame` → `OK`；全量 → `OK`，测试数比改前多 1。

### Step 4: 现有页面不误报

冻结场景轮次 `rounds/` 被 gitignore，只在主检出里有，所以下面用主检出的绝对路径，并写死基线轮次的目录名（`rounds/` 下还有别的轮次，不要用 `ls | tail -1` 去挑）。页面先复制到临时目录再构建，主检出里的文件不动。用 bash 跑（zsh 下目录不存在时 glob 会直接报错）：

```sh
R=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-b52953a-022/
T=$(mktemp -d)
for f in "$R"*.html skills/show-me-html/tests/fixtures/component-states.html skills/show-me-html/tests/fixtures/diagram-variants.html; do
  cp "$f" "$T/"; printf '%s ' "$(basename "$f")"; python3 skills/show-me-html/scripts/build.py "$T/$(basename "$f")" | grep -c '文字越出图框'
done
python3 skills/show-me-html/scripts/gallery.py --out "$T/g" | grep -c '文字越出图框'
```

**Verify**: 七个页面各一行，都是 `0`；最后 gallery 那一行也是 `0`（`gallery.py --out` 合成总览页后会跑一遍 `build.py`，59 张数据图都在这页上，是误报的主要检验；五个场景页里的 SVG 多是图标和图示。图库探针此前是 `问题 0 条`，两边判据相同；advisor 冷读审阅时在 `90fb8af` 上按本计划的代码跑过，七个页面和 gallery 都是 0）。有页面报出时，打开它看那段字是不是真的被裁：是真的，就在汇报里列出（不修页面）；不是真的（误报），STOP。

### Step 5: 文档

1. `references/charts.md`：
   - 「交付前自检」第 3 条 `3. 标签会不会重叠？邻近峰值只标一个？` 改为 `3. 标签会不会重叠、会不会越出图框？邻近峰值只标一个？`
   - 「文字」小节那句 `` `scripts/gallery.py --shots` 的探针会报出图库里互相重叠或越出图框的文字。`` 改为 `` `scripts/gallery.py --shots` 的探针会报出图库里互相重叠或越出图框的文字；越出图框的文字 `build.py` 的渲染检查也会报 WARN。``
2. `references/anti-patterns.md`：表格最后一行之后加一行（编号接表里最大的编号 + 1，下面以 `N` 代替）：

   <!-- prettier-ignore -->
   ```markdown
   | N | 越框文字 | 已检查 | 图内文字写到 viewBox 外，SVG 外的部分被裁掉，读者看到半截字（2026-10 实例：报告页 F5 行尾「其中 135 条仍引用」在 1280px 下被裁）。 | 把字挪进 viewBox 或缩短；确实放不下再加宽 viewBox，不缩字号。build.py 渲染检查查每段水平 SVG 文字的外接框，超出图框报 WARN。 |
   ```

   并在「状态推进记录：」列表末尾加一行：`- <执行当天日期> 第 N 条登记即为已检查（越框文字）：gallery.py 的探针此前在图库里查过，这次在真实页面再次出现，按毕业规则搬进 build.py，报 WARN；文字重叠仍只在 gallery 查。`

3. `npx prettier --write skills/show-me-html/references/charts.md skills/show-me-html/references/anti-patterns.md`

**Verify**: `make check` → exit 0；`grep -c '越框文字' skills/show-me-html/references/anti-patterns.md` → `2`（表格一行、记录一行）。

## Test plan

- 新增 `test_render_check_warns_on_text_outside_the_frame`：越框报 WARN、不越框不报，两种情况退出码都是 0。
- Step 4 用冻结场景、组件夹具、宽窄两版图夹具和 gallery 总览页确认不误报。

## Done criteria

- [ ] 全量单元测试 `OK`，测试数比执行前多 1
- [ ] `grep -c '(?P<clipped>' skills/show-me-html/scripts/build.py` → `1`
- [ ] Step 4 七个页面和 gallery 都是 `0`
- [ ] `make check` exit 0；`git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- 018 或 019 未合入。
- Step 4 出现误报（字其实完整可见）。
- 新测试的正例没有报出，或报出的文字片段与断言不同：先打开页面确认那段字确实越界，再汇报，不要放宽判据。

## Maintenance notes

- 判据和 `gallery.py` 的探针保持一致；改其中一边时同步另一边。
- 以后若再出现越框文字漏到交付（例如旋转的轴标题被裁），再考虑把旋转文字纳入，或升为 ERROR。
- `PROBE` 的 `|` 分段现在到第 10 段（`clipped`）。后续计划继续在末尾追加。
