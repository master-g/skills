# Plan 017: show-me-html 图内字号升一档（刻度 9、类目名与数值 10），下限改为任何文字不小于 9

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。本计划工作量大，Step 4–7 每批一个提交；中途停下时，在状态行写明做完了哪几批。
>
> **Drift check (run first)**: `git diff --stat fff32ba..HEAD -- skills/show-me-html/assets/charts.js skills/show-me-html/assets/gallery skills/show-me-html/scripts/build.py skills/show-me-html/scripts/gallery.py skills/show-me-html/tests/test_build.py skills/show-me-html/references/charts.md skills/show-me-html/references/anti-patterns.md`
> 应当没有输出。有输出，或者下面「Current state」的摘录与现行文件对不上，就是 STOP 条件。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P1
- **Effort**: L（运行时一行、两个脚本、一个测试、两份文档，外加 gallery 里 26 张图逐张重排）
- **Risk**: MED（gallery 里每张用了 `tick()` / `label()` / `value()` 的图字都会变大；26 张要改排法。新下限仍是 ERROR，重新构建的旧页面可能因此报错，见 Maintenance notes）
- **Depends on**: 无。建议在 018、019 之前执行（三份计划都改 `build.py` 的渲染探针；018 也改 gallery 图块的颜色，先改字号再改颜色，冲突最少）
- **Category**: bug
- **Planned at**: commit `fff32ba`, 2026-10-21

## Why this matters

show-me-html 把素材做成单文件 HTML 页面，数据图用内联 SVG 画，宽度 100%，按 viewBox 缩放。维护者 2026-10-21 反馈一页报告（`status-report` 配方，含 G4、F12、G10、F5 四张图）「charts 字体过小，阅读困难」。实测 1280px 下，F12 的刻度字只有 **7.0px**，类目名和数值只有 **8.2px**；同一页正文的下限是 10px，来源行是 12px。构建对这页零 WARN 通过。

原因有三层：

1. **发丝语法的字号偏小。** 图内文字统一从运行时 `assets/charts.js` 的 `G.type` 取：刻度 6.5、类目名 7.6、数值 7.6，单位是 viewBox 单位。标准 viewBox 在桌面宽度下大约按 1:1 显示（60rem 版心、1280px 下半宽卡 400 宽显示约 430px，1024px 下约 399px），所以 viewBox 单位基本就是像素。gallery 59 张图在 1280px 下有 **42 张**最小字号渲染后不到 8px。
2. **下限也按这个数定。** 构建的渲染检查和 `scripts/gallery.py` 的探针按 viewBox 单位核对「半宽卡 ≥ 6.5、通栏 ≥ 5.5」，等于允许 6.5px 的字。这条下限是 2026-09-23（commit `3aed007`）登记的，当时把 `tick()` 从 6.2 提到 6.5 去过线，数字是贴着已有的图定的，没有从可读性出发。
3. **两套字号并存。** 快读型（G 族）图块把字号直接写在块里，多为 9–13；基础型、编辑型（F、L 族）调用 6.5–7.6 的 `tick()` / `label()` / `value()`。维护者 9 月那页只用了 G 族，读起来没问题；10 月这页加了 F12、F5，字就小了。`references/charts.md` 要求「新写或重写的图块一律从 `G` 取」，不先把 `G` 提上来，这条迁移只会把 G 族也拉小。

**维护者决定（2026-10-21）**：`G.type` 改为刻度 9、类目名 10、数值 10（advisor 给的两档里的 B 档）。下限改为图内任何文字 ≥ 9（viewBox 单位），半宽与通栏相同。1024px 下刻度正好 9px、类目名 10px，与 G 族写死的 9/10 一致，两套字号合成一套。

advisor 在 scratchpad 的副本里套用了 B 档，用本计划 Step 1 的重叠探针量过：gallery 里 16 张图出现新的文字重叠或越出图框，另有 12 张图块里写死了小于 9 的字号，两者去重后共 **26 张**要改。advisor 看过半宽卡 455px 下 F12 的前后截图：改档后刻度和类目名明显好读，这张图不用改排法。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。`assets/charts.js` 是图表运行时（挂在 `window.showMeChart`，构建时内联进页面）。`assets/gallery/{basics,editorial,glance,big}.html` 是四个图型参考页，每张图是一个 `<figure data-chart="编号">` 加页尾 `<script>` 里一个 `// ════ 编号 · 英文名 ════` 开头的渲染块。`scripts/gallery.py` 把四页拼成 `all-charts.html`，`--shots` 给每张图截 light / dark 两张 PNG，并写一份 `index.md`，开头是「探针发现的问题」列表。`scripts/build.py` 负责构建与自检。

- `assets/charts.js:86-91`（当前，`G` 的一部分）：

  <!-- prettier-ignore -->
  ```js
      dot: { tick: 0.9, mark: 2.1, head: 3.1 },
      type: { tick: 6.5, label: 7.6, value: 7.6, track: 0.5 },
      ink: {
        strong: "var(--ink)",
        data: "var(--ink-70)",
        quiet: "var(--ink-45)",
  ```

  `tick()` / `value()` / `label()`（第 110–128 行）分别用 `G.type.tick` / `G.type.value` / `G.type.label` 作默认 `font-size`，调用方传的属性会覆盖默认值。

- `scripts/gallery.py:34-35`：

  ```python
  # 字号下限（viewBox 单位），见 charts.md「文字」：半宽卡 6.5、通栏 5.5
  MIN_FONT = {"half": 6.5, "wide": 5.5}
  ```

- `scripts/gallery.py:175-184`（`PROBE` 字符串里，逐张图收集数据）：

  <!-- prettier-ignore -->
  ```js
        var marks = 0, fonts = [];
        svgs.forEach(function(s){
          marks += s.querySelectorAll('*:not(title):not(desc)').length;
          s.querySelectorAll('text').forEach(function(t){
            if (t.textContent.trim()) fonts.push(parseFloat(getComputedStyle(t).fontSize));
          });
        });
        return {id: f.dataset.chart, wide: f.classList.contains('wide'), h: Math.ceil(f.getBoundingClientRect().height),
          name: q(f, '.fig-id'), title: q(f, '.fig-title'), sub: q(f, '.fig-sub'), cap: q(f, 'figcaption'),
          svgs: svgs.length, marks: marks, minFont: fonts.length ? Math.min.apply(null, fonts) : null};
  ```

  **注意**：`gallery.py` 的 `PROBE` 是 `%` 格式化字符串（`PROBE % (json.dumps(SHOT_W), PAD)`），JS 里出现的 `%` 必须写成 `%%`，否则 `--shots` 报 `TypeError: not enough arguments for format string`（advisor 第一次就踩了）。反斜杠要写成 `\\`（参照第 172 行的 `/\\s+/g`）。

- `scripts/gallery.py:250-256`（`shots()` 里给每张图写问题）：

  ```python
              notes = []
              if f["svgs"] and f["marks"] == 0:
                  notes.append("空图")
              if f["minFont"] is not None and f["minFont"] < MIN_FONT[size]:
                  notes.append(f"最小字号 {f['minFont']:g} 低于{'通栏' if f['wide'] else '半宽'}下限 {MIN_FONT[size]:g}")
              missing = [t for t in ("light", "dark") if not made[(fid, t)]]
  ```

- `scripts/build.py:831-843`（`PROBE` 字符串里的图内字号下限；这是普通三引号字符串，不是 % 格式化）：

  <!-- prettier-ignore -->
  ```js
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
  ```

- `tests/test_build.py:334-351`：`test_render_check_flags_chart_text_below_font_floor`，子用例 `(("5", True), ("6.5", False))`，断言 `"字号低于下限：F1（#tiny） 最小 5 < 半宽下限 6.5" in result.stdout`。文档字符串是 `"""半宽卡图内字号下限 6.5：图滚入视野才画，探针要先强制画出来再量。"""`。
- `tests/test_build.py:308-320`：`test_gallery_overview_page_has_every_chart` 用 `--no-render` 拼总览页，断言只有一条「超过 400 KB」的 WARN。它不跑渲染检查，所以 Step 2 之后到 Step 8 之前，单元测试照样全过。
- `references/charts.md:147`（「文字」一节）：

  <!-- prettier-ignore -->
  ```markdown
  - SVG 最小字号（viewBox 单位）：半宽卡 6.5、通栏 5.5，`tick()` 默认 6.5 两种卡都达标。装不下改 `<title>` hover 出，不缩字号硬塞；有 Chrome 时 `build.py` 的渲染检查会逐张核对。
  ```

- `references/charts.md:168`（「发丝语法」表格的一行）：

  <!-- prettier-ignore -->
  ```markdown
  | `tick()` / `value()` / `label()` | 6.5 / 7.6 / 7.6                | 刻度与单位（等宽、加字距、quiet 墨）/ 数值（600、主角时 hero 色）/ 类目名（正文字） |
  ```

- `references/charts.md:292`（「交付前自检」第 4 条）：`4. 最小字号踩线没有（半宽 6.5 / 通栏 5.5）？`
- `references/anti-patterns.md:19`（名册第 9 条「硬塞小字」）的「识别特征」一格写着「（半宽卡 < 6.5、通栏 < 5.5，viewBox 单位）」；「状态推进记录：」第 45–46 行记着当年的登记。
- gallery 图块里写死的小于 9 的字号（advisor 2026-10-21 用 awk 扫出来的，执行时以 Step 3 的探针为准）：

  | 图  | 文件:行                                        | 现值                        |
  | --- | ---------------------------------------------- | --------------------------- |
  | L12 | `editorial.html:2483`                          | 6.5（36 个斜写菜名）        |
  | B1  | `big.html:386`                                 | 8.5                         |
  | G5  | `glance.html:1216`                             | 7                           |
  | G8  | `glance.html:1495` `1552` `1588` `1600` `1612` | 8、8、8、7、7               |
  | G9  | `glance.html:1659` `1697` `1708` `1784`        | 8.5、8、8、8                |
  | G10 | `glance.html:1859` `1888`                      | 8.5、7                      |
  | G12 | `glance.html:2106` `2136` `2148`               | 7.5、7.5、7                 |
  | G13 | `glance.html:2192` `2219`                      | 7、8.5                      |
  | G14 | `glance.html:2307`                             | 8.5                         |
  | G15 | `glance.html:2360` `2399`                      | 8.5、7                      |
  | G18 | `glance.html:2646`                             | 8                           |
  | G21 | `glance.html:3138`                             | `name.length > 3 ? 8 : 9.5` |

**仓库约定**：图块代码风格照抄所在块（prettier 格式、中文注释写「为什么」、数从 `G` 取、抖动用 `jit`）。Python 只用标准库，报告文字用中文。文档按标题名引用章节（「文字」「发丝语法」），不按编号，`make check` 会检查。Markdown 用 prettier 格式化。charts.md「硬规则」写明：**装不下改排法（错列、减量、挪位）或改 `<title>` hover 出，不缩字号硬塞**；**抖动只加在不编码数据的维度上**，柱高、射线长度、点的个数、曲线端点不能动。

## Commands you will need

在仓库根目录执行：

| Purpose        | Command                                                                                                                                                                                         | Expected on success                                                           |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 单元测试       | `python3 -m unittest skills.show-me-html.tests.test_build`                                                                                                                                      | 末行 `OK`，`Ran 48 tests`（约 100 秒，需本机 Chrome）                         |
| 单个测试       | `python3 -m unittest skills.show-me-html.tests.test_build.BuildCliTests.test_render_check_flags_chart_text_below_font_floor -v`                                                                 | `ok`                                                                          |
| 语法检查       | `python3 -W error::SyntaxWarning -c "import ast,pathlib; [ast.parse(pathlib.Path(p).read_text()) for p in ('skills/show-me-html/scripts/build.py', 'skills/show-me-html/scripts/gallery.py')]"` | 无输出、exit 0                                                                |
| 图库探针与截图 | `G=$(mktemp -d) && python3 skills/show-me-html/scripts/gallery.py --out "$G" --no-render --shots && sed -n '/## 探针发现的问题/,/^## 基础型/p' "$G/shots/index.md"`                             | 末尾打印「问题 N 条」；sed 打印问题列表。截图在 `"$G/shots/<编号>-light.png"` |
| 图库完整构建   | `G=$(mktemp -d) && python3 skills/show-me-html/scripts/gallery.py --out "$G" --shots`                                                                                                           | 见 Step 9                                                                     |
| 文档门禁       | `make check`                                                                                                                                                                                    | exit 0                                                                        |
| 格式化         | `npx prettier --write <改过的文件>`                                                                                                                                                             | exit 0                                                                        |

不要用 pytest（未安装）。`--shots` 一次约 2–4 分钟。

## Suggested executor toolkit

- 看截图用能读图片的文件查看工具（Read 之类）打开 `"$G/shots/<编号>-light.png"`。截图是两倍像素，半宽卡窗口 500px。
- 想对照着看改前改后，第一次跑探针时把 `$G` 目录记下来，留作「改前」。

## Scope

**In scope**：

- `skills/show-me-html/assets/charts.js`（只改 `G.type` 一行）
- `skills/show-me-html/scripts/gallery.py`（`MIN_FONT`、`PROBE` 的逐图收集、`shots()` 的问题列表）
- `skills/show-me-html/scripts/build.py`（`PROBE` 里字号下限那几行）
- `skills/show-me-html/tests/test_build.py`（改现有的字号下限测试）
- `skills/show-me-html/assets/gallery/{basics,editorial,glance,big}.html`：**只改下面 Step 4–7 点名的 26 张图的渲染块**（以及它们 `<figure>` 里 svg 的 `viewBox` 高度，如果需要加高）
- `skills/show-me-html/references/charts.md`（「文字」「发丝语法」「交付前自检」三处）
- `skills/show-me-html/references/anti-patterns.md`（第 9 条与状态推进记录）

**Out of scope**：

- 颜色：`fill` 用什么墨、对比度够不够，属于计划 018。本计划改图块时不要顺手换颜色。
- `G` 里除 `type` 以外的数（线宽、点径、墨色、抖动）。
- `assets/show-me.css`、`assets/shell.*`。
- 没被点名的图块。改一张图时发现另一张也不好看，记下来汇报，不要改。
- 图的数据编码：位置、长度、角度、点数、数值都不能为了腾地方而改（例外：L12 的演示菜单见 Step 5）。
- 给 `build.py` 加重叠检查：重叠探针只放在 `gallery.py` 里，用户页面上误报的代价更高。
- `MAINTENANCE.md`、`SKILL.md`、维护者 bedrock 仓库里的页面。

## Git workflow

- 分支：`advisor/017-show-me-html-chart-type-scale`。
- conventional commits，scope 写技能名。建议的提交：
  1. `feat(show-me-html): gallery probe flags overlapping and clipped chart text`（Step 1）
  2. `feat(show-me-html): chart type scale moves to 9 / 10 / 10`（Step 2–3）
  3. `fix(show-me-html): basics charts make room for the larger type`（Step 4）
  4. `fix(show-me-html): editorial charts make room for the larger type`（Step 5）
  5. `fix(show-me-html): glance charts drop text below 9 and make room`（Step 6）
  6. `fix(show-me-html): big charts make room for the larger type`（Step 7）
  7. `feat(show-me-html): chart font floor becomes 9 for every card`（Step 8–10）
- pre-commit 会跑 prettier 和 `make check`；prettier 会重排改过的 html 与 md。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`。

## Steps

### Step 1: gallery 探针报出文字重叠与越出图框

charts.md「交付前自检」第 3 条「标签会不会重叠？」目前只靠人眼。字号变大以后要改的图很多，先让探针把重叠报出来，后面每一步都拿它当门禁。

1. 在 `scripts/gallery.py` 的 `PROBE` 里，把摘录里的

   <!-- prettier-ignore -->
   ```js
         var marks = 0, fonts = [];
         svgs.forEach(function(s){
           marks += s.querySelectorAll('*:not(title):not(desc)').length;
           s.querySelectorAll('text').forEach(function(t){
             if (t.textContent.trim()) fonts.push(parseFloat(getComputedStyle(t).fontSize));
           });
         });
   ```

   替换为（注意注释里的 `15%%`）：

   <!-- prettier-ignore -->
   ```js
         var marks = 0, fonts = [], overlaps = [], clipped = [];
         svgs.forEach(function(s){
           marks += s.querySelectorAll('*:not(title):not(desc)').length;
           var sr = s.getBoundingClientRect(), boxes = [];
           s.querySelectorAll('text').forEach(function(t){
             if (!t.textContent.trim()) return;
             fonts.push(parseFloat(getComputedStyle(t).fontSize));
             // 文字重叠与越界（charts.md「交付前自检」第 3 条）：只比水平文字，旋转文字的外接框天然互相交叠
             var m = t.getScreenCTM(), r = t.getBoundingClientRect(), cs = getComputedStyle(t);
             if (!m || Math.abs(m.b) > 1e-3 || Math.abs(m.c) > 1e-3 || r.width < 1 || cs.display === 'none' || parseFloat(cs.opacity) === 0) return;
             var name = '';
             for (var n = t.firstChild; n; n = n.nextSibling) if (n.nodeType === 3 || n.nodeName === 'tspan') name += n.textContent;
             name = name.trim().slice(0, 12);
             if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1) clipped.push(name);
             boxes.push({r: r, s: name});
           });
           for (var i = 0; i < boxes.length; i++) for (var j = i + 1; j < boxes.length; j++) {
             var a = boxes[i].r, b = boxes[j].r;
             var w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
             // 同字同位是描边衬底的复本，不算重叠；交叠面积超过较小那个框的 15%% 才算
             if (w > 0 && h > 0 && w * h > 0.15 * Math.min(a.width * a.height, b.width * b.height)
                 && !(boxes[i].s === boxes[j].s && Math.abs(a.left - b.left) < 1 && Math.abs(a.top - b.top) < 1))
               overlaps.push(boxes[i].s + ' × ' + boxes[j].s);
           }
         });
   ```

   拼名字时只取文字节点和 `tspan`，因为运行时的 `tip()` 会往 `<text>` 里塞一个 `<title>`，`textContent` 会把提示文字也算进去。

2. 同一个 `return {…}` 里，把 `minFont: fonts.length ? Math.min.apply(null, fonts) : null};` 改为

   <!-- prettier-ignore -->
   ```js
           minFont: fonts.length ? Math.min.apply(null, fonts) : null,
           overlaps: overlaps, clipped: clipped};
   ```

3. 在 `shots()` 里、`missing = [t for t in ("light", "dark") if not made[(fid, t)]]` 这一行**正上方**（与 `if f["minFont"]` 同级）加：

   ```python
               if f["overlaps"]:
                   notes.append(f"文字重叠 {len(f['overlaps'])} 处：" + "；".join(f["overlaps"][:4]))
               if f["clipped"]:
                   notes.append(f"文字越出图框 {len(f['clipped'])} 处：" + "；".join(f["clipped"][:4]))
   ```

**Verify**: 语法检查无输出；图库探针命令 → 末尾 `问题    3 条`，列表正好是下面三行（`Other` 后面的两个空格和行尾的 `·` 是原文如此）：

```
- L1：文字越出图框 1 处：人民广场780
- G13：文字重叠 1 处：45m × Other  6% ·
- G13：文字越出图框 1 处：Chat  12% ·
```

这三处是现在就有的缺陷（advisor 看过截图：G13 的「Chat 12% · 11m」左边被图框切掉，「45m」压在「Other 6% · 7m」上），在 Step 5、6 里一起修。

### Step 2: 字号升档

1. `assets/charts.js` 第 87 行改为：

   <!-- prettier-ignore -->
   ```js
       type: { tick: 9, label: 10, value: 10, track: 0.5 },
   ```

2. `scripts/gallery.py` 第 34–35 行改为：

   ```python
   # 字号下限（viewBox 单位），见 charts.md「文字」：图内任何文字不小于 9，半宽与通栏相同
   MIN_FONT = {"half": 9, "wide": 9}
   ```

**Verify**: 单元测试 → `OK`，`Ran 48 tests`（`build.py` 的下限还没改，gallery 测试不跑渲染）。

### Step 3: 拿到这一轮的工作清单

跑图库探针命令。**Verify**：末尾 `问题    30 条`（advisor 在 scratchpad 实测；±2 条以内可以接受，差得更多就是 STOP 条件），涉及下面 26 张图，每张至少一条：

- 重叠或越框（16 张）：F2、F3、F4、F16、L1、L3、L5、L8、L12、L13、L17、L19、L20、G13、G22、B3
- 最小字号低于 9（12 张，L12、G13 两类都有）：L12、G5、G8、G9、G10、G12、G13、G14、G15、G18、G21、B1

把这次的 `$G` 目录记下来，作为「改前」截图。advisor 实测时探针报出的问题如下，供定位（每张图只列前四对）：

| 图  | 探针报的问题                                                               |
| --- | -------------------------------------------------------------------------- |
| F2  | 日均 × 213                                                                 |
| F3  | 台风 × 闭园；闭园前 × 周末均 11.3；越框：周末均 11.3                       |
| F4  | 厨余垃圾 × 52%；其他垃圾 × 29%；可回收物 × 17%；有害垃圾 × 2%              |
| F16 | 第 1 周 骑行只占 × 6%；第 31 周 骑行占到 × 29%；春节当周 × 991 万 · 平时的 |
| L1  | 越框：人民广场780；静安寺690                                               |
| L3  | 37.1° × 7/9；37.1° × 7/18                                                  |
| L5  | 开票慢 × 14；找不到入口 × 9；价格看不懂 × 8；客服难联系 × 7                |
| L8  | 华东仓 × 38.6k 单；华南仓 × 35.5k 单；华北仓 × 26.2k 单；西南仓 × 15.9k 单 |
| L12 | 川味 × 12；本帮 × 8；面档 × 6；粤式 × 4；最小字号 6.5                      |
| L13 | 投递 × 2,400；简历通过 × 860；笔试 × 410；面试 × 190                       |
| L17 | 连跑 25 天 × 10/2—10/26                                                    |
| L19 | 70 × 送达时长 · 分钟                                                       |
| L20 | 续航 × km；电耗 × kWh/百公里；快充 × 分钟；价格 × 万元                     |
| G13 | 45m × Other 6%；越框：Chat 12%；最小字号 7                                 |
| G22 | 在线客服 × 520；电话 × 310；邮件 × 240；应用内反馈 × 180                   |
| B3  | Postgres × 28；MySQL 旧库 × 27；Redis × 29；Kafka × 21                     |

其余 10 张（G5、G8、G9、G10、G12、G14、G15、G18、G21、B1）这时只报「最小字号低于 9」。

### Step 4–7 的通用改法

每张图按这个顺序处理：读探针的问题 → 打开「改前」截图看清是哪几个字撞在一起 → 在渲染块里找到画这些字的 `txt(…)` 调用 → 按下面的手法改 → 重跑探针，这张图的问题消失 → 看「改后」light 截图，字没有压住线和点，版面没有明显失衡。

常见的几种情况（advisor 看过 F4、L5 改档后的截图，都是第一种；从探针报的重叠对看，L8、L12、L13、L20、G22、B3 多半也是）：

1. **上下两行贴在一起**（类目名在上、数值在下，如 F4「厨余垃圾 / 52%」、L5「导出乱码 / 4」）。原来两行基线差是按 7.6 号字写死的数（常见 8–9），现在字是 10 号。把第二行的 `y` 偏移改成按字号算，基线差不小于较大字号的 1.25 倍。块里已经解构了 `G` 的，直接写 `G.type.label * 1.25`。整组字的位置同时往外挪半行，免得新的第二行压到图形。
2. **左右挨着撞上**（类目名与行尾数值、轴标题与刻度，如 F2「日均 × 213」、L19「70 × 送达时长」）。加大两者之间的水平间距，或者把左侧的类目名列加宽：块顶通常有 `X0` / `LX` 一类常量，加大它，图形区相应变窄，数据比例不变。
3. **越出图框**（如 L1、G13、F3）。把字往里挪，或改 `text-anchor`（贴右边的字用 `end`），或把 `<figure>` 里 svg 的 viewBox **高度**加大（宽度保持 400 / 800 不变）。
4. **字号低于 9 的写死值**（G 族、L12、B1）。先直接改成 9（或改用 `tick()`，它现在默认就是 9）。改完再跑探针，可能冒出新的重叠，再按 1–3 处理。

不允许的做法：把字号改回小于 9；删掉数值标签而不给 `<title>` hover；为了腾地方改数据（柱高、点数、角度）；改 `G.type`。实在放不下时，按 charts.md 的规则减量（邻近只标一个）并给被减掉的元素加 `tip(…)` 悬停提示，在提交说明里写明。

### Step 4: 基础型（`basics.html`）：F2、F3、F4、F16

按通用改法处理四张图。

**Verify**: 图库探针的问题列表里不再出现 `F2：`、`F3：`、`F4：`、`F16：` 开头的行；单元测试 `OK`；提交。

### Step 5: 编辑型（`editorial.html`）：L1、L3、L5、L8、L12、L13、L17、L19、L20

按通用改法处理。L12 另有两点：

- 底部 36 个菜名是旋转 −72° 的斜字（`editorial.html:2483` 的 `"font-size": 6.5`），探针不比旋转文字的重叠，要靠截图判断。先改成 `"font-size": 9`。advisor 估算过：相邻菜名在垂直于字的方向上间距约 9.9 个单位，9 号字刚好放得下；看截图如果相邻菜名的字形碰到一起，把演示数据 `MENU` 减到 30 道（这是演示数据，可以改；单位行 `fig-sub` 或图注里若写了道数，同步改），不要把字号改回去。
- 上方档口名与道数（「川味 × 12」）是第 1 种情况。

**Verify**: 问题列表里不再出现 `L` 开头的行；L12 的 light 截图里菜名清楚、互不压字；单元测试 `OK`；提交。

### Step 6: 快读型（`glance.html`）：G5、G8、G9、G10、G12、G13、G14、G15、G18、G21、G22

先把「Current state」表里 G 族写死的小于 9 的字号改成 9（G21 第 3138 行改成 `"font-size": name.length > 3 ? 9 : 9.5,`）。再跑探针，按通用改法处理 G13、G22 和新冒出来的问题。G13 的「Chat 12% · 11m」越框、「45m」压住「Other」是改档以前就有的，一起修。

**Verify**: `grep -nE '"font-size": *[0-8](\.[0-9]+)?[,} ]' skills/show-me-html/assets/gallery/glance.html` 无输出；问题列表里不再出现 `G` 开头的行；单元测试 `OK`；提交。

### Step 7: 交互大图（`big.html`）：B1、B3

B1 第 386 行的 8.5 改成 9；B3 按通用改法处理。

**Verify**: `grep -nE '"font-size": *[0-8](\.[0-9]+)?[,} ]' skills/show-me-html/assets/gallery/*.html` 无输出；图库探针 → `问题    0 条`；单元测试 `OK`；提交。

### Step 8: 构建的下限改为 9

1. `scripts/build.py` 第 831 行注释改为：

   <!-- prettier-ignore -->
   ```js
     // 字号下限（charts.md「文字」，viewBox 单位，半宽与通栏都是 9）：图只在滚入视野时才画，先强制全画，等入场定时器跑完再量
   ```

2. 第 836 行改为：

   <!-- prettier-ignore -->
   ```js
         var floor = 9, min = Infinity;
   ```

3. 第 842 行改为：

   <!-- prettier-ignore -->
   ```js
           small.push(f.dataset.chart + (svg ? '（#' + svg.id + '）' : '') + ' 最小 ' + min + ' < 下限 ' + floor);
   ```

4. `tests/test_build.py` 的 `test_render_check_flags_chart_text_below_font_floor`：文档字符串改为 `"""图内字号下限 9（viewBox 单位）：图滚入视野才画，探针要先强制画出来再量。"""`；子用例改为 `(("8", True), ("9", False))`；断言字符串改为 `"字号低于下限：F1（#tiny） 最小 8 < 下限 9"`。

**Verify**: 语法检查无输出；单个测试命令 → `ok`；全量单元测试 → `OK`，`Ran 48 tests`。advisor 在 scratchpad 里做过这一步，两项都通过。

### Step 9: 图库完整构建（带渲染检查）

跑图库完整构建命令。

**Verify**:

- 构建输出只有一条 `WARN   页面 … 超过 400 KB` 和 `自检通过（1 个警告需逐条判断）。`，没有「图内字号低于下限」。
- 末尾 `问题    0 条`。
- 逐张打开 Step 4–7 改过的 26 张图的 `-light.png` 和 `-dark.png`，确认：字不压线、不压点；没有字被切掉；主角色仍只在原来那一处。把每张图「改前 / 改后」的 light 截图路径列进汇报，方便审阅者对照。

### Step 10: 文档

1. `references/charts.md`「文字」一节，把第 147 行替换为下面两条：

   <!-- prettier-ignore -->
   ```markdown
   - SVG 最小字号（viewBox 单位）：图内任何文字不小于 9，半宽卡与通栏相同。`tick()` 默认 9，`label()` / `value()` 默认 10；60rem 版心下标准 viewBox 大约按 1:1 显示，所以这也约等于渲染后的像素。装不下改排法或改 `<title>` hover 出，不缩字号硬塞；有 Chrome 时 `build.py` 的渲染检查会逐张核对。
   - 上下叠放的两行字（类目名上、数值下），基线差不小于较大字号的 1.25 倍，按 `G.type` 算，不写死。`scripts/gallery.py --shots` 的探针会报出图库里互相重叠或越出图框的文字。
   ```

2. 第 168 行表格里的 `6.5 / 7.6 / 7.6` 改为 `9 / 10 / 10`，其余不变。
3. 第 292 行改为 `4. 最小字号踩线没有（任何文字 ≥ 9）？上下叠放的字留够 1.25 倍行距没有？`
4. `references/anti-patterns.md` 第 9 条「识别特征」里的「（半宽卡 < 6.5、通栏 < 5.5，viewBox 单位）」改为「（任何文字 < 9，viewBox 单位）」；在「状态推进记录：」列表末尾加一行：`- <执行当天日期> #9 的下限从半宽 6.5 / 通栏 5.5 提到 9：6.5 在标准 viewBox 下就是 6.5px，比正文下限 10px 还小。运行时字号同步改为刻度 9、类目名与数值 10，gallery 里 26 张图重排；gallery.py 的探针新增文字重叠与越框。`
5. `npx prettier --write skills/show-me-html/references/charts.md skills/show-me-html/references/anti-patterns.md`

**Verify**: `make check` → exit 0；`grep -c '6\.5' skills/show-me-html/references/charts.md` → `0`；`grep -c '9 / 10 / 10' skills/show-me-html/references/charts.md` → `1`。

### Step 11: 冻结场景轮次

`MAINTENANCE.md`「联动规则」要求改 `build.py` 后跑五个冻结场景。五个场景页都没有数据图，这一步确认下限改动没有连带改坏别的检查。

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-16-7454494-base
NEW=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-017
mkdir -p "$NEW"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$NEW/" && python3 skills/show-me-html/scripts/build.py "$NEW/$n.html" | tail -2
done
node skills/show-me-html/scripts/probe_round.mjs "$NEW" "$PREV"
```

**Verify**: 五次构建各打印 `自检通过。`；探针五行 `无问题`。`scenarios/rounds/` 在 `.gitignore` 里，不进提交。

## Test plan

- 改现有的 `test_render_check_flags_chart_text_below_font_floor`（Step 8）：8 号字报 ERROR，9 号字通过。
- 不新增单元测试。字号变化本身由 gallery 探针覆盖（Step 3、Step 9），探针的重叠与越框检查用 Step 1 的三处既有缺陷验证过：改档前恰好报出这三处。
- 误报面：Step 9 的 gallery 完整构建（59 张图）、Step 11 的五个冻结场景。

## Done criteria

- [ ] `grep -n 'type: { tick: 9, label: 10, value: 10' skills/show-me-html/assets/charts.js` → 一行
- [ ] `grep -n 'floor = 9' skills/show-me-html/scripts/build.py` → 一行
- [ ] `grep -nE '"font-size": *[0-8](\.[0-9]+)?[,} ]' skills/show-me-html/assets/gallery/*.html` 无输出
- [ ] 全量单元测试 → `OK`，`Ran 48 tests`
- [ ] Step 9：只有「超过 400 KB」一条 WARN，`问题    0 条`
- [ ] `make check` exit 0
- [ ] Step 11 五个场景 `自检通过。`，探针五行 `无问题`
- [ ] `git status --short` 只列出 Scope 里的文件
- [ ] 汇报里附 26 张图的改前 / 改后截图路径
- [ ] `plans/README.md` 本计划状态行已更新

## STOP conditions

- Drift check 有输出，或摘录对不上。
- Step 1 的探针报出的不是那三条：重叠判据可能在这台机器上表现不同，汇报实际列表，不要调判据去凑。
- Step 3 的问题数与 30 相差超过 2 条，或涉及的图不在那 26 张里：汇报实际列表。
- 某张图不改数据编码就放不下，且减量加 hover 也不合适：停在这张图，汇报原因和截图，其余图继续。
- 探针报的重叠在截图里看不出来（误报），或截图里明显重叠而探针没报（漏报）：汇报这张图和截图，不要改判据。
- 任何已有单元测试失败，修一次仍不过。

## Maintenance notes

- **旧页面重新构建会拿到新字号。** `build.py` 会把内联的运行时换成新的 `charts.js`，旧页面里用 `tick()` / `label()` / `value()` 的图字会变大，原来的排法可能出现重叠；用了写死小字号（< 9）的图会因为新下限报 ERROR。`MAINTENANCE.md` 的约定是历史页面默认不动，要重建时按本计划的通用改法修页面。维护者 2026-10-21 那页（bedrock 仓库，进房全球基线）advisor 试过：F12 用的是辅助函数，重建后字号是 9/10，不报字号问题。
- **下限按 viewBox 单位，前提是图按约 1:1 显示。** 60rem 版心下半宽卡 1.07 倍、通栏 1.15 倍；72rem 版心约 1.3–1.4 倍；48rem 版心（各类 explainer）里 `.charts` 双栏的半宽卡只有 0.84 倍，9 号字渲染后约 7.5px。计划 019 会对超出 0.8–1.5 倍的图报 WARN，48rem 的情况在它的阈值之内，是已知的余量不足。
- **窄屏不在本计划范围。** 500px 视口下 gallery 的 9 张通栏图字号渲染后只有 3.3–4.8px（本计划之后约 4.8–5.4px），因为 800 宽的 viewBox 被压到约 430px。这是既有问题，记在 `plans/README.md` 的「未规划」里。
- 重叠探针只看水平文字，旋转的字（L12 菜名）要人眼看截图。15% 的阈值在改档前的图库里恰好只报出三处真缺陷；以后有新图型误报，先看截图再决定是否调整。
- 审阅时重点看：Step 4–7 的 diff 只动了点名的图块；没有改 `fill` 颜色；没有改数据数组（L12 的 `MENU` 除外）；行距改成了按 `G.type` 算，而不是换一个写死的新数。
