# Plan 007: tufte-reader 支持公有领域铜版画题图（扉页与选定章节）

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 55a66e8..HEAD -- skills/tufte-reader`
> 预期无输出（tufte-reader 自计划写成后没变）。有输出就把下面「Current state」的摘录与现行代码逐段对照；对不上即为 STOP 条件。

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW（新增元素与新脚本；对已有读本唯一的影响是统计行多一列「题图」）
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `55a66e8`, 2026-10-14

## Why this matters

维护者想给读本配与各章主题相称的旧版画题图：16–18 世纪的铜版画、蚀刻和木刻，炼金术、自然哲学、博物、解剖、机械一类的书籍插图（_Atalanta Fugiens_，1618 是他最喜欢的代表，不是唯一的来源），作扉页卷首图和章首题图，并且只用公有领域或宽松许可的图。现在的技能做不到这件事，原因有四：没有取图并检查许可的途径；`build.py` 把每个 `<figure>` 都计入「图」，题图会让统计和结构清单对不上；位图在暗色主题下统一铺浅色底，扫描的版画会变成一块刺眼的白卡；作者也无从判断哪幅寓意配哪个主题。

本计划补上完整链路：`references/plates.md` 负责按主题找图（选图流程、22 个核实过的 Commons 分类组成的系列清单、Atalanta Fugiens 的逐幅图录）；`scripts/plate.py` 从 Wikimedia Commons 取图，先按许可把关，再压成小体积灰度 PNG，并打印带出处的写法；新增 `figure.plate` 元素和对应样式；构建把题图单独统计为「题图」，没写出处或留着 `TODO-题图` 时报 ERROR；最后同步文档和 specimen 回归样张。

### 维护者已确认的决定（2026-10-14，不要改）

- **暗色主题的呈现是「亮融暗裱」**：亮色主题用 `mix-blend-mode: multiply` 把纸色融进页面底色；暗色主题裱在压暗的旧纸色衬底上，配 `brightness(0.82) sepia(0.15)`。**不做反相或纯墨线处理**：advisor 实测，版画的明暗靠排线疏密表现，浅色线条画在深色底上整幅明暗颠倒，看起来像照相底片。
- **位置**：扉页一幅，另外挑主题贴切的几章各配一幅章首图；只在用户要求配题图时才加，不是每本读本、每一章都配。
- **许可**：只接受公有领域、PDM、无已知版权限制（Commons 的「No restrictions」，图书馆批量上传的古籍插图常这样标，按公有领域处理、不要求署名）、CC0、CC BY，并且 CC BY 必须署名；CC BY-SA、NC、ND、许可字段缺失一律拒绝。
- **选图以主题为入口，不限于 Atalanta Fugiens**：图录的「选图」从章节主题出发，风格由「系列」清单把关（同一时代、同一技法，不必同一本书）；Atalanta Fugiens 是其中一个有逐幅索引的系列。文档里不给「默认用哪一幅」的建议。
- **只从 Commons 取图**：脚本只读 Commons 的许可字段。其他机构（Science History Institute、Wellcome 等）的图，先在 Commons 上找同一幅，找不到就不用。

## Current state

`skills/tufte-reader/` 是一个 Agent Skill：`SKILL.md` 是入口，`references/` 存放写作契约，`scripts/` 是 Python 标准库脚本（构建另外调用 node 编译公式），`assets/` 存放骨架、样式和回归样张，`tests/` 是 unittest 测试。

- `scripts/build.py`：构建与检查。`Checker` 类（`html.parser.HTMLParser` 子类）负责统计和结构检查，`check()` 函数补充整页检查。
  - `build.py:546`：`self.stats = {"章": 0, "小节(h3)": 0, "图": 0, "页边图": 0, "表": 0, "代码块": 0, …}`
  - `build.py:568-570`：
    ```python
            if tag == "figure":
                self.stats["图"] += 1
                self.stats["分步图"] += "steps" in cls
    ```
  - `build.py:637-640`（`check()` 里）：
    ```python
        if re.search(r"<p\b[^>]*>(?:(?!</p>).)*?<(div|figure|pre|table|ol|ul|section|blockquote|details)\b", html, re.S):
            errors.append("<p> 里嵌了块级元素：浏览器会提前闭合 <p>，边注与版心随之错位；把块级元素移到段落之外")
        if not re.search(r"<title>[^<]+</title>", html) or "中文标题 · 原文标题" in html:
    ```
  - `build.py:352-353`：`inline_images` 碰到 `src` 以 `data:` 开头的图片会原样跳过，所以 specimen 里可以直接写 data URI。
- `assets/tufte.css`：所有数值写在开头 `:root` 的 token 里，规则只引用 token（SKILL.md「修改本技能」的硬性约定）。
  - `tufte.css:32`：`--img-bg: transparent; /* 位图的底色：… */`（亮色 `:root`）
  - `tufte.css:117`：`--img-bg: #f3f2e8;`（`:root[data-theme="dark"]` 块）
  - `tufte.css:405-409`：`img { max-width: 100%; height: auto; background: var(--img-bg); }`
  - `tufte.css:440-442`：`figure.fullwidth img { width: 100%; }`
  - `tufte.css:785-789`：`@media (max-width: 760px) { :root { --text-body: …; --text-note: …; } …`，同一个 media 块里还有 `figure { max-width: 90%; }`（约 825 行）。
  - **陷阱**：不要给 `figure.plate` 设 `max-width: var(--col)`。窄屏下 `--col` 只有约 187px，它的优先级又高于窄屏规则里的 `figure { max-width: 90% }`，题图会缩到栏宽的四成。advisor 的 demo 实际踩过这个坑。
- `assets/specimen.html`：回归样张，涵盖全部元素。`tests/test_build.py` 里的 `test_specimen_builds_clean` 断言它的统计：
  ```python
          self.assertIn("图 3  页边图 0", out)
          self.assertIn("边注 2  旁注 6  脚注 2  块级公式 3  行内公式 80  图内公式 6  分步图 1  帧 3", out)
          self.assertEqual(html.count('<input type="checkbox"'), 8)
  ```
  specimen 扉页第 32 行：`      <p class="byline">Silvanus P. Thompson 著 · 1910 年初版，1914 年修订</p>`
- `tests/test_build.py`：用 `run(PAGE.replace("BODY", …), files)` 构建临时页面，返回 `(rc, html, out)`；`PNG_1PX` 是 1 像素 PNG 的 base64。新测试照 `test_dollar_amounts_are_not_math`（约 137 行）的结构写。
- 文档的约定：Markdown 用简体中文；章节按标题名引用（「题图」），不按编号；相对链接必须指向存在的文件。`make check` 会检查这两条。写法遵循正向措辞。

**附件**：`plans/007-tufte-reader-plates/` 里的文件都由 advisor 在仓库副本里写好并跑过，可以直接复制使用：

| 文件               | 用途                                                                                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plate.py`         | 成品，复制到 `skills/tufte-reader/scripts/plate.py`                                                                                                      |
| `test_plate.py`    | 成品，复制到 `skills/tufte-reader/tests/test_plate.py`（离线，5 个测试）                                                                                 |
| `plates.md`        | 成品，复制到 `skills/tufte-reader/references/plates.md`（已经过 prettier）                                                                               |
| `atalanta-42.png`  | specimen 扉页题图：第 42 幅高清版（`File:M.Maier. Atalanta Fugiens. 1618. Emblem XLII.JPG`）按 1000px 取图，4 级灰度，159 KB，公有领域；高分屏下排线清楚 |
| `spec_insert.py`   | 一次性工具：把上面的 PNG 以 data URI 插进 specimen 扉页                                                                                                  |
| `measure_plate.py` | 一次性工具：用 Playwright 量题图在 1280/390 宽、明暗主题下的宽度与样式                                                                                   |
| `check_catalog.py` | 一次性工具：联网核对 `plates.md` 里的 55 个文件和 22 个分类（存在、许可、箴言与 Commons 描述相符）                                                       |

advisor 在副本里套用本计划的全部代码改动后：`python3 -m unittest discover -s skills/tufte-reader/tests` 跑出 43 个测试全部 OK；specimen 构建 0 ERROR、0 WARN；`check_catalog.py` 输出「通过：文件 55 个，分类 22 个，0 处问题」。

## Commands you will need

| Purpose  | Command                                                                                                                | Expected on success                               |
| -------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 技能测试 | `python3 -m unittest discover -s skills/tufte-reader/tests`                                                            | 末行 `OK`；计划完成时 `Ran 43 tests`（基线是 35） |
| 文档门禁 | `make check`                                                                                                           | `技能文档引用检查通过（N 个文件）`，exit 0        |
| 格式     | `npx prettier --check <file>`                                                                                          | `All matched files use Prettier code style!`      |
| 构建样张 | `cp skills/tufte-reader/assets/specimen.html "$T/" && python3 skills/tufte-reader/scripts/build.py "$T/specimen.html"` | 末行 `通过：0 个 ERROR，0 个 WARN …`              |

`$T` 指一个临时目录：`T=$(mktemp -d)`（fish：`set T (mktemp -d)`）。测试用 `python3 -m unittest`，仓库里没装 pytest。

## Scope

**In scope**（只改这些）：

- `skills/tufte-reader/scripts/plate.py`（新建，复制附件）
- `skills/tufte-reader/tests/test_plate.py`（新建，复制附件）
- `skills/tufte-reader/references/plates.md`（新建，复制附件）
- `skills/tufte-reader/scripts/build.py`（三处改动，见 Step 2）
- `skills/tufte-reader/tests/test_build.py`（新增三个测试，改 specimen 测试里的三处断言）
- `skills/tufte-reader/assets/tufte.css`（token 与规则，见 Step 3）
- `skills/tufte-reader/assets/specimen.html`（扉页加一幅题图）
- `skills/tufte-reader/SKILL.md`、`references/markup.md`、`references/dispatch.md`、`references/style.md`（文档，见 Step 6）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**（不要碰）：

- `skills/tufte-reader/assets/vendor/**`、`LICENSE-tufte-css.txt`：第三方资产，只能整体更新。
- `scripts/figlib.py`、`figpreview.py`、`math.mjs`、`mathwidth.mjs`、`assets/shell.js`、`assets/shell.html`：题图不经过它们。
- 全局 `img { background: var(--img-bg) }` 规则：普通插图在暗色主题下的浅色底是有意的设计（commit `fe8fea6`），题图用自己的规则覆盖它。
- `README.md` 的技能列表：技能没有新增或改名。
- 把 Python 迁到 bun / TypeScript：已评估并否决（见 `plans/README.md` 的 rejected 一节）。
- `make install`：会改本机 `~/.claude/skills`，由维护者自己决定何时执行。

## Git workflow

- 仓库约定直接提交到 `main`，conventional commits，scope 写 `tufte-reader`。示例：`feat(tufte-reader): add public-domain engraving plates for frontispiece and chapter openers`。
- 未经操作者指示不要提交、不要推送。pre-commit 会跑 prettier 和 `make check`，prettier 可能重排 Markdown 表格，这是正常的。

## Steps

### Step 1：加入取图脚本和它的测试

```sh
cp plans/007-tufte-reader-plates/plate.py skills/tufte-reader/scripts/plate.py
cp plans/007-tufte-reader-plates/test_plate.py skills/tufte-reader/tests/test_plate.py
```

`plate.py` 做的事：用 Commons API（`action=query&prop=imageinfo&iiprop=url|size|mime|extmetadata&iiurlwidth=W`）读 `LicenseShortName` 和 `AttributionRequired`；许可不在白名单里就以退出码 3 结束，不下载任何东西。许可通过后下载 `thumburl`，有 `magick` 时拉伸色阶并压成 4 级灰度 PNG，否则用 `sips` 转 JPEG；然后写出处记录 `<name>.json`，并打印一段 `<figure class="plate" data-source=… data-license=…>`，图注和 alt 里留着 `TODO-题图` 给作者改写。

几处要知道的细节：Commons 的缩略图只按固定档位给，要 1000px 实际可能拿到 1280px，所以脚本下载后在本地再缩一次。原图比请求宽度小时，`thumburl` 返回的就是原图。User-Agent 必须写明工具名和联系地址，这是 Wikimedia 的规定。

**Verify**：`python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 40 tests`，`OK`。

### Step 2：构建把题图单独统计，并检查出处

在 `skills/tufte-reader/scripts/build.py` 里做三处改动。

(a) `Checker.__init__` 的 stats 字典，在 `"页边图": 0,` 后面加 `"题图": 0,`：

```python
        self.stats = {"章": 0, "小节(h3)": 0, "图": 0, "页边图": 0, "题图": 0, "表": 0, "代码块": 0, "边注": 0, "旁注": 0, "脚注": 0, "块级公式": 0, "行内公式": 0, "图内公式": 0, "分步图": 0, "帧": 0}
```

(b) 把 `handle_starttag` 里的 `if tag == "figure":` 那三行替换为：

```python
        if tag == "figure" and "plate" in cls:
            self.stats["题图"] += 1
            if not (a.get("data-source") and a.get("data-license")):
                self.errors.append("题图缺 data-source 或 data-license：用 scripts/plate.py 取图，它打印的写法带出处与许可")
        elif tag == "figure":
            self.stats["图"] += 1
            self.stats["分步图"] += "steps" in cls
```

(c) 在 `check()` 里、`<p> 里嵌了块级元素` 那条检查之后，`<title>` 检查之前，加：

```python
    if "TODO-题图" in html:
        errors.append("题图里还有 TODO-题图：图注写出处与图题（或箴言）的译文，alt 写画面，CC BY 的图补上署名")
```

然后在 `skills/tufte-reader/tests/test_build.py` 的 `def test_dollar_amounts_are_not_math(self):` 之前插入三个测试（缩进与所在类一致）：

```python
    def test_plate_counted_apart_from_figures(self):
        import base64

        img = '<img src="figures/a.png" alt="画面" />'
        body = (f'<figure class="plate" data-source="https://commons.wikimedia.org/wiki/File:X.jpeg" '
                f'data-license="Public domain"><span class="marginnote">题图　说明。</span>{img}</figure>'
                f'<figure><span class="marginnote">图 1　图题。</span>{img}</figure>')
        rc, html, out = run(PAGE.replace("BODY", body), {"figures/a.png": base64.b64decode(PNG_1PX)})
        self.assertEqual(rc, 0, out)
        self.assertIn("  图 1  ", out)
        self.assertIn("  题图 1  ", out)

    def test_plate_without_source_is_error(self):
        body = '<figure class="plate" data-license="Public domain"><img src="data:image/png;base64,AA" alt="画面" /></figure>'
        rc, html, out = run(PAGE.replace("BODY", body))
        self.assertEqual(rc, 1)
        self.assertIn("题图缺 data-source 或 data-license", out)

    def test_plate_todo_is_error(self):
        body = ('<figure class="plate" data-source="https://x" data-license="CC0">'
                '<img src="data:image/png;base64,AA" alt="TODO-题图：画面描述" /></figure>')
        rc, html, out = run(PAGE.replace("BODY", body))
        self.assertEqual(rc, 1)
        self.assertIn("题图里还有 TODO-题图", out)
```

`"  图 1  "` 前后各有两个空格，所以不会误匹配到 `题图 1` 里面的「图 1」。

**Verify**：

- `python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 43 tests`，`OK`（specimen 还没改，原有断言照常通过）。
- `grep -c '"题图"' skills/tufte-reader/scripts/build.py` → `2`。

### Step 3：题图样式

在 `skills/tufte-reader/assets/tufte.css` 里做四处改动，全部数值写成 token。

(a) 亮色 `:root` 里，在 `--img-bg: transparent; …` 那一行之后加：

```css
/* 题图（figure.plate）：亮色主题把扫描的纸色乘进页面底色；暗色主题裱在压暗的旧纸色衬底上。
     不反相：版画的明暗靠排线疏密，反相后像照相底片 */
--plate-width: 78%;
--plate-blend: multiply;
--plate-mount: transparent;
--plate-pad: 0;
--plate-filter: none;
```

(b) `:root[data-theme="dark"]` 里，在 `--img-bg: #f3f2e8;` 之后加：

```css
--plate-blend: normal;
--plate-mount: #e8e2d0;
--plate-pad: 0.9em;
--plate-filter: brightness(0.82) sepia(0.15);
```

(c) `figure.fullwidth img { width: 100%; }` 这条规则之后加：

```css
/* 题图居中；figure.plate 不另设 max-width，沿用 figure 的，窄屏下才能随 figure 放宽 */
figure.plate img {
  display: block;
  width: var(--plate-width);
  margin: 0 auto;
  box-sizing: border-box;
  padding: var(--plate-pad);
  background: var(--plate-mount);
  mix-blend-mode: var(--plate-blend);
  filter: var(--plate-filter);
}
.titlepage > figure.plate {
  margin: var(--space-block) 0 var(--space-chapter);
}
```

(d) `@media (max-width: 760px)` 里的 `:root { … }`，在 `--text-note: var(--text-note-narrow);` 之后加 `--plate-width: 100%;`。

**Verify**：

- `npx prettier --check skills/tufte-reader/assets/tufte.css` → 通过。
- `grep -n 'figure.plate' skills/tufte-reader/assets/tufte.css` → 4 行：两行注释（`:root` 里的「题图（figure.plate）…」和规则前的「题图居中…」），以及 `figure.plate img {`、`.titlepage > figure.plate {` 两条规则。
- `grep -c '^figure\.plate {' skills/tufte-reader/assets/tufte.css` → `0`（不存在给 `figure.plate` 本身设样式的规则，也就不会有 `max-width`）。
- 测试仍然 `Ran 43 tests`，`OK`。

### Step 4：specimen 扉页加题图

```sh
python3 -I plans/007-tufte-reader-plates/spec_insert.py skills/tufte-reader/assets/specimen.html plans/007-tufte-reader-plates/atalanta-42.png
npx prettier --write skills/tufte-reader/assets/specimen.html
```

`spec_insert.py` 会在扉页 `p.byline` 那一行之后插入一个 `<figure class="plate">`：图片是 data URI，图注写出处、第 42 幅箴言的译文、Merian 刻和 1618 年，并注明「图源 Wikimedia Commons，公有领域」，alt 描述画面。锚点行找不到时，脚本会因 `assert` 失败而退出。

然后把 `tests/test_build.py` 里 `test_specimen_builds_clean` 的三处断言改成：

```python
        self.assertIn("图 3  页边图 0  题图 1", out)
        self.assertIn("边注 2  旁注 7  脚注 2  块级公式 3  行内公式 80  图内公式 6  分步图 1  帧 3", out)
        self.assertEqual(html.count('<input type="checkbox"'), 9)
```

旁注多出的 1 条和 checkbox 多出的 1 个，都来自题图的 `marginnote` 图注。

**Verify**：

- `python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 43 tests`，`OK`。
- 构建样张（见命令表）→ 统计行包含 `题图 1`，末行 `通过：0 个 ERROR，0 个 WARN`。
- `ls -l skills/tufte-reader/assets/specimen.html` → 约 240 KB（原来 21.8 KB，多出的部分是 159 KB PNG 的 base64；样张是视觉回归基准，按维护者的决定用高清版）。
- `npx prettier --check skills/tufte-reader/assets/specimen.html` → 通过。

### Step 5：在浏览器里核对样式

需要 Playwright 的 Python 包。先找能 import 它的解释器：`python3 -c "import playwright"`；不行就试 `~/.local/pipx/venvs/playwright/bin/python -c "import playwright"`。另外要有本机 Chrome，脚本用的是 `channel="chrome"`。

用 Step 4 构建好的 `$T/specimen.html`：

```sh
<能 import playwright 的 python> -I plans/007-tufte-reader-plates/measure_plate.py "$T/specimen.html"
```

预期输出四行，每行格式是 `[[img 宽, 所在栏宽, mix-blend-mode, filter, background-color]]`：

```
1280 light [[480, 986, 'multiply', 'none', 'rgba(0, 0, 0, 0)']]
1280 dark [[480, 986, 'normal', 'brightness(0.82) sepia(0.15)', 'rgb(232, 226, 208)']]
390 light [[322, 358, 'multiply', 'none', 'rgba(0, 0, 0, 0)']]
390 dark [[322, 358, 'normal', 'brightness(0.82) sepia(0.15)', 'rgb(232, 226, 208)']]
```

判定标准：390 宽时 img 宽不小于栏宽的 0.85 倍；1280 宽时 img 宽在 440–520 之间；混合模式、滤镜、底色与上面一致。像素值可以有几个像素的出入。

再各截一张明暗主题的扉页，附在汇报里：`playwright screenshot --channel chrome --color-scheme dark --viewport-size 1280,820 "file://$T/specimen.html" "$T/plate-dark.png"`，亮色同理。亮色主题下题图四周**不应**看到灰色方框，因为纸面已经融进页面；暗色主题下是一块压暗的米色衬底。

找不到可用的 Playwright 时，在汇报里写明「Step 5 未运行」，其余步骤照常完成。

### Step 6：文档

(a) 复制图录：

```sh
cp plans/007-tufte-reader-plates/plates.md skills/tufte-reader/references/plates.md
```

(b) `skills/tufte-reader/SKILL.md` 改三处：

- 「1. 取材，列结构清单」最后一段（以「完成标准：拿到完整原文」开头）的末尾追加一句：`用户要求配题图时，结构清单另列题图：扉页用哪一幅，哪几章配、各用哪一幅（选法见 [题图](references/plates.md)）。`
- 「3. 逐章写读本」里，在「先写扉页和参考文献，再写各章。」这句之后另起一段：`用户要求配题图时，按 [题图](references/plates.md) 选图、取图：扉页题图随扉页写，章首题图在各章写完后统一放（分章派发时在拼接之后）。`
- 「4. 构建与核对」的例子列表里，在「插图里的公式标签单独计入「图内公式」」之前插入：`题图单独计入「题图」，不算在「图」里，它的图注计入「旁注」；`

(c) `skills/tufte-reader/references/markup.md`：在「## 分步图」整节之后、「## 表格」之前插入新的一节：

````markdown
## 题图

```html
<figure
  class="plate"
  data-source="https://commons.wikimedia.org/wiki/File:…"
  data-license="Public domain"
>
  <span class="marginnote"
    >题图　出处、图题或箴言的译文、刻工与年份。图源
    <a href="https://commons.wikimedia.org/wiki/File:…">Wikimedia Commons</a
    >，公有领域。</span
  >
  <img src="figures/plates/atalanta-42.png" alt="画面描述" />
</figure>
```

- 只在用户要求配题图时使用。写法由 `scripts/plate.py` 打印，选图、取图和图注的写法见 [题图](plates.md)。
- 扉页题图放在 `header.titlepage` 里、`p.byline` 之后；章首题图放在该章 `<h2>` 之后、第一个 `<section>` 的开头。
- 样式由 tufte.css 负责：亮色主题下扫描的纸色融进页面，暗色主题下裱在压暗的纸色衬底上。作者只写 `class="plate"`，不加别的样式。
- `data-source` 与 `data-license` 缺一个，或页面里留着 `TODO-题图`，构建都报 ERROR。构建统计里题图单独计为「题图」，不计入「图」。
````

(d) `skills/tufte-reader/references/dispatch.md`「## 拼接」里，「全部返回后：」下的编号列表在第 3 项之后加第 4 项：`4. 用户要求配题图时，按 [题图](plates.md) 放章首题图。题图由主 agent 统一放，子 agent 的交代里不提题图。`

(e) `skills/tufte-reader/references/style.md`「## 译者补充」的列表里，在「读本说明（扉页）写清：…」之前加一条：`- 题图（扉页和章首的版画插图）：图注以「题图」开头，读本说明写明是译者所加、各幅的来源与许可，见 [题图](plates.md)。`

**Verify**：

- `make check` → `技能文档引用检查通过`，exit 0。
- `grep -c 'references/plates.md' skills/tufte-reader/SKILL.md` → `2`；`grep -l '](plates.md)' skills/tufte-reader/references/*.md` → `dispatch.md`、`markup.md`、`style.md` 三个文件。
- `npx prettier --check skills/tufte-reader/SKILL.md skills/tufte-reader/references/*.md` → 通过（不通过就 `--write` 再检查）。

### Step 7：联网核对（可选；没网络时写「未运行」）

```sh
python3 -I plans/007-tufte-reader-plates/check_catalog.py skills/tufte-reader/references/plates.md
```

预期：`通过：文件 55 个，分类 22 个，0 处问题`。

再实际取一次图，并试一次被拒的许可（`<repo>` 换成仓库根目录的绝对路径）：

```sh
cd "$T"
python3 <repo>/skills/tufte-reader/scripts/plate.py "File:Michael Maier Atalanta Fugiens Emblem 02.jpeg" -o figures/plates; echo "rc=$?"
python3 <repo>/skills/tufte-reader/scripts/plate.py "File:Wikipedia-logo-v2.svg" -o figures/plates; echo "rc=$?"
```

第一条输出 `取图 … KB  许可 Public domain` 和一段 `<figure class="plate" …>`，`rc=0`，`figures/plates/` 里多出 `michael-maier-atalanta-fugiens-emblem-02.png`（小于 300 KB）和同名 `.json`。第二条输出 `ERROR 许可「CC BY-SA 3.0」不在可用范围…`，`rc=3`，`figures/plates/` 里不会多出文件。

## Test plan

- `tests/test_plate.py`（附件）：许可白名单（公有领域、PDM、无已知版权限制、CC0、CC BY 通过；BY-SA、NC、ND、GFDL、空值拒绝）；`plain()` 去掉标签和实体；PD 图的写法带 `data-source`、`data-license`、「公有领域」和 `TODO-题图`，且不带署名；CC BY 图干净的署名照用，含链接的署名改成 `TODO-题图：署名`；被拒许可时 `main()` 返回 3、不调用下载、不建输出目录。全部离线，网络调用用 `mock`。
- `tests/test_build.py` 新增三个测试（Step 2），结构照 `test_dollar_amounts_are_not_math`；改 `test_specimen_builds_clean` 的三处断言（Step 4）。
- 结果：`python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 43 tests`，`OK`。

## Done criteria

- [ ] `python3 -m unittest discover -s skills/tufte-reader/tests` 末行 `OK`，`Ran 43 tests`
- [ ] 构建 specimen 的临时副本：统计行含 `题图 1`、`图 3`，末行 `通过：0 个 ERROR，0 个 WARN`
- [ ] `make check` exit 0
- [ ] `npx prettier --check` 对所有改过的 `.md`、`.css`、`.html` 通过
- [ ] `grep -c '^figure\.plate {' skills/tufte-reader/assets/tufte.css` 输出 `0`
- [ ] Step 5 的四行测量满足判定标准，或者汇报里写明未运行
- [ ] `git status --porcelain` 只列出「Scope」里的文件（外加 `plans/README.md`）
- [ ] `plans/README.md` 中本计划的状态行已更新

## STOP conditions

遇到下列情况就停下汇报，不要自己想办法绕过：

- 漂移检查有输出，并且「Current state」里的摘录（stats 字典、`if tag == "figure":` 三行、`--img-bg` 两处、`figure.fullwidth img` 规则、specimen 的 byline 行）和现行代码对不上。
- `spec_insert.py` 的 `assert` 失败（specimen 的 byline 行变了）。
- Step 2 或 Step 4 之后测试数不是 43，或者有测试失败，修过两次仍然失败。
- Step 5 测得 390 宽时题图不到栏宽的 0.85 倍，或者亮色主题截图里题图四周有明显的灰框。这说明样式与 advisor 的验证结果不一致，不要自己调 token。
- `make check` 报出 plates.md 或新段落的链接问题，而原因不是笔误。
- 实现中发现需要改「Out of scope」里的文件，例如必须动全局 `img` 规则才能让题图正常显示。

## Maintenance notes

- **图录的扩充**：给 `plates.md` 加系列或加行之后，跑 `check_catalog.py`（它留在 `plans/007-tufte-reader-plates/`，需要联网）。「系列」表里的规模与许可分布是 2026-10-14 用 Commons API 探测的（许可按前 50 个文件统计），会随上传变化，只作选系列的参考；分类名由 `check_catalog.py` 核对存在。Commons 上名为 `Michael Maier Atalanta Fugiens Emblem 11.jpeg` 的文件画的其实是第 25 幅（advisor 用图像相关比对发现，又目视确认），图录第 11 幅已改用 `File:Atalanta Fugiens 11 Latona.jpg`；箴言已对照 IA 扫描页核实。50 条中文大意和「适合的主题」是 advisor 写的草稿，需要维护者审阅措辞。
- **单幅文件只有约 600px 宽**：在高分屏上发虚（advisor 在 2 倍像素密度下截图确认）。图录的「高清版」表暂时列了 5 幅 Commons 上的高分辨率文件；50 幅全部改用 Internet Archive 的 1000px 高清版由 `plans/008-tufte-reader-ia-plates.md` 完成，它以本计划的附件为基准打补丁。
- **没有 ImageMagick 的环境**：`plate.py` 退回用 sips 转 JPEG，不拉伸色阶，亮色主题下会露出一块浅灰色的纸面底；其他系统上两者都没有时保留原图。这些都是可用但不理想的退路。
- **审阅重点**：`figure.plate` 不能设 `max-width`（见「Current state」里的陷阱）；暗色主题的 token 不要改成反相；`TODO-题图` 检查是对整页做子串匹配，如果哪天读本正文需要讨论这个技能本身（例如在 `<code>` 里写到 `TODO-题图`），会被误报，到那时再改成只查 `figure.plate` 内部。
- **生效**：仓库改动要 `make install SKILL=tufte-reader SOURCE=.` 之后才进入 `~/.claude/skills`，由维护者执行。
