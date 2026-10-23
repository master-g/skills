# Plan 027: show-me-html 打印时卡片不从中间劈开，看板的列按纸宽排下，有含义的底色保留

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 2f0e439..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/references/visual-system.md`
> 计划 018 先合入时，这两个文件都会出现在输出里（018 改了 token、骨架颜色，以及 visual-system 的「Token 分层」「对比度」），属于预期。只要下面「Current state」里引用的打印样式和 visual-system 那一行原样还在，就继续；对不上就 STOP。另外确认计划 022 已合入：`grep -c 'def print_pdf' skills/show-me-html/scripts/build.py` → `1`，不满足也 STOP。
>
> 本文件里的 css / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。
>
> **2026-10-23 补充（advisor）**：
>
> - 维护者决定把「打印时保留有含义的底色」并入本计划，即 Step 3。
> - 原来打 PDF 的步骤用 Chrome 命令行，现在改用 022 新增的 `build.py --pdf`。
> - 本计划派发前还要做一次冷读审阅，届时按当时的 HEAD 刷新行号和 drift check。

## Status

- **Priority**: P2
- **Effort**: S（三处 CSS、一行文档）
- **Risk**: LOW（只影响 `@media print`）
- **Depends on**: `plans/022-show-me-html-gallery-shots-and-pdf.md`（已合入；验证用它的 `--pdf`）
- **Category**: bug
- **Planned at**: commit `2f0e439`, 2026-10-22；2026-10-23 在 `bdc10b6` 补充 Step 3

## Why this matters

show-me-html 的成品页自带打印样式。用户要 PDF 时，可以在浏览器里打印，也可以构建时加 `--pdf`。2026-10-22 的一轮回归（打印改 A4、标题随下文换页，提交 `7c94bce`）之后，五个冻结场景的 PDF 里还有两个问题没修：

- **approach-compare**：「三个方案的真实代价」有三张方案卡，每张约 534px 高。它们落在第 1 页底部，被分页从中间劈开：卡头在第 1 页，优缺点在第 2 页。
- **triage-board**：
  - 页面自己把看板写成三列，每列至少 16rem（`repeat(3, minmax(16rem, 1fr))`），三列加间距共 792px。
  - A4 纸减去页边距后，可打印宽度约 718px，而看板容器在打印时仍是 `overflow-x: auto`。
  - 结果是第三列「观察」右侧约 74px 被裁掉，计数徽标和右边框出界。

advisor 在 scratchpad 里把 Step 1、Step 2 的两条规则注入这两页的副本，用无头 Chrome 打印模拟（视口 718px、`media: print`）量过：

- 看板改为两列，各 353px；三列中的「观察」排到第二行，没有任何一列越界。
- 打印成 A4 PDF 后，approach-compare 的三张卡整块移到第 2 页，triage-board 不再有被裁的列。两页的页数都还是 2。

第三个问题是 2026-10-23 加进来的：**打印默认不印背景色**。浏览器打印对话框默认不勾「背景图形」，`--pdf` 也不打背景（`printBackground` 保持默认关）。大部分底色只是装饰，丢了也不要紧：徽章、提示框都还留着边框和彩色文字，数据图是 SVG 填色，不受影响。但有三类底色本身承载含义：

- **diff 的增删行**：`.d-add` / `.d-del` 的蓝、红底。
- **代码块** `pre`：灰底是代码块的边界。
- **进度条** `progress`：数值部分就是背景色。

advisor 用 code-review 冻结场景页对照过：

- 不打背景时，「先看结构变化」的 diff 只剩行首的 `+` / `-`，代码块也没了边界。
- 在打印样式里给这三类加上 `print-color-adjust: exact` 后，同样不打背景，增删行的底色和代码块的灰底都保留了。文件名小标签这类装饰性底色，仍然照常省掉。

维护者选了这个做法，而没有选「`--pdf` 打开全部背景」，因为这样浏览器打印和 `--pdf` 的结果一致。

## Current state

技能目录是 `skills/show-me-html/`，下文路径都相对这个目录。行号按 `2f0e439`，对不上时以引文为准；派发前的冷读审阅会刷新行号。

### `assets/show-me.css` 主打印块的末尾

这一段是 `7c94bce` 加的：

```css
  /* 标题跟着下文换页，不孤零零留在页底；列表行不从中间劈开 */
  :is(h2, h3, h4) {
    break-after: avoid;
  }
  .item {
    break-inside: avoid;
  }
  /* 条目组有边框，分页会落在边框内首行之前，页底只剩空框和标题；
     禁止首行前断，断点退回标题之前 */
  .item-group > :first-child {
    break-before: avoid;
  }
}
```

### `assets/show-me.css` 文件最后一个 `@media print` 块

这是配方的打印规则，开头是：

```css
@media print {
  [data-recipe="share-card"] .sheet {
    box-shadow: none;
    break-inside: avoid;
  }
```

同一块里已有「带边框的配方舞台整块换页」的 `break-inside: avoid` 规则，写法可参照。

### 看板的屏幕样式

```css
[data-recipe="triage-board"] .board,
.recipe-matrix > [data-recipe="triage-board"] .recipe-stage {
  display: grid;
  grid-template-columns: repeat(4, minmax(14rem, 1fr));
  gap: 0.75rem;
  overflow-x: auto;
  scroll-snap-type: x proximity;
  padding-block-end: 0.5rem;
}
[data-recipe="triage-board"] .lane {
  min-width: 14rem;
  …
}
```

冻结场景页 triage-board 在自己的 `<style>` 里写了 `[data-recipe="triage-board"] .board { grid-template-columns: repeat(3, minmax(16rem, 1fr)); }`。页面样式排在骨架之后、选择器相同，所以骨架的打印规则要用 `!important` 才压得过页面写死的列宽。`show-me.css` 里已有用 `!important` 压过页面写法的先例：`:1532` 附近的注释「!important 用来压过 .fig svg 的 display:block 和页面自己的 display 写法」。

### 有含义的底色在哪里定义

- `.d-add` / `.d-del` 写在**页面自己的** `<style>` 里，骨架 CSS 里没有，写法照抄 `references/layouts.md`「结构视图」：

  ```css
  .d-add {
    background: color-mix(in oklab, var(--color-primary) 12%, transparent);
  }
  .d-del {
    background: color-mix(in oklab, var(--color-destructive) 12%, transparent);
  }
  ```

  `print-color-adjust` 作用在元素上，与底色写在哪里无关，所以骨架打印样式里的一条规则就能管到页面里的这两个类。

- `pre { … background: var(--color-muted); }` 在 `show-me.css` 的代码块段。
- `progress` 的底和数值都用 `background`，在 `show-me.css` 的表单段（`progress::-webkit-progress-value { background: var(--color-primary); }`）。
- `print-color-adjust` 是继承属性：写在 `pre`、`progress` 上，`pre` 里的 `.d-add` 和 `progress` 的伪元素都会继承。

### `references/visual-system.md`「响应式与打印」的打印一行

```markdown
- 打印强制浅纸深字和 A4 纸，隐藏 chrome 和 TOC，展开静态阅读顺序；h2–h4 尽量与下文同页（`break-after: avoid`，下文比一页还高时照常断开），条目（`.item`）不从中间劈开。
```

### 冻结场景

主检出目录 `/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-b52953a-022/` 是最近一轮：五页 HTML，加上 `_probe/` 下的截图和 PDF。注意 `_probe/*.pdf` 是 Letter 纸，探针没传 `preferCSSPageSize`，所以只能看分页和版面，页数不能和 A4 比。

## Commands you will need

| Purpose  | Command                                                                 | Expected on success  |
| -------- | ----------------------------------------------------------------------- | -------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`              | 末行 `OK`            |
| 文档门禁 | `make check`                                                            | exit 0               |
| 出 PDF   | `python3 skills/show-me-html/scripts/build.py <页面> --no-render --pdf` | `已导出  <页面>.pdf` |
| PDF 转图 | `pdftoppm -r 50 -png <pdf> <前缀>`（本机 Homebrew 已装 poppler）        | 每页一张 PNG         |

## Scope

**In scope**：

- `skills/show-me-html/assets/show-me.css`（两处 `@media print`）
- `references/visual-system.md`（一行）
- `plans/README.md`（状态行）

**Out of scope**：

- 屏幕上的看板布局与列宽。
- 冻结场景页本身：不删页面写的列宽，也不改页面里的 `.d-add` / `.d-del`。
- 比一页还高的卡片：浏览器会照常分页，`break-inside: avoid` 不保证。
- `--pdf` 打开全部背景（`printBackground`）：维护者没选这个做法。
- 徽章、提示框、卡片等装饰性底色：打印时照常省掉。

## Git workflow

从本地 `main` 开分支 `advisor/027-show-me-html-print-cards-and-board`。提交信息例如 `fix(show-me-html): print keeps cards whole, fits the board to the page and keeps meaningful backgrounds`。pre-commit 会跑 prettier。不要 push。

## Steps

### Step 1: 卡片整块换页

把主打印块末尾那段改成下面这样。变化只有两处：注释和选择器，其余不动。

<!-- prettier-ignore -->
```css
  /* 标题跟着下文换页，不孤零零留在页底；列表行和卡片不从中间劈开（比一页还高的卡浏览器照常分页） */
  :is(h2, h3, h4) {
    break-after: avoid;
  }
  .item,
  .card {
    break-inside: avoid;
  }
```

**Verify**: `grep -c '列表行和卡片不从中间劈开' skills/show-me-html/assets/show-me.css` → `1`。

### Step 2: 看板按纸宽排

在文件最后一个 `@media print` 块里，`[data-recipe="share-card"] .sheet { … }` 之后加：

<!-- prettier-ignore -->
```css
  /* 看板在纸上不能横向滚动：A4 可打印宽约 718px，页面常把列宽写死（三列 16rem 就是 792px），超出的列被裁掉。
     打印时一律两列均分、换行排，压过页面自己的列宽；卡片整块换页由主打印块的 .card 规则负责 */
  [data-recipe="triage-board"] .board {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    overflow: visible;
  }
  [data-recipe="triage-board"] .lane {
    min-width: 0;
  }
```

**Verify**:

- `npx prettier --check skills/show-me-html/assets/show-me.css` 通过。不通过就 `--write`，再确认 diff 只有空白变化。
- 全量单元测试 → `OK`，测试数不变。`VisualContractTests` 会检查 CSS 的若干契约。

### Step 3: 有含义的底色打印时保留

在主打印块里、Step 1 改过的那段之后，紧接 `.item-group > :first-child { … }` 之后、主打印块的 `}` 之前，加：

<!-- prettier-ignore -->
```css
  /* 打印默认不印背景色（浏览器对话框默认不勾「背景图形」，build.py --pdf 也不打）。
     这三类底色承载含义，强制保留：diff 增删行（页面自己写的 .d-add / .d-del）、代码块的边界、进度条的数值。
     其余底色（徽章、提示框、卡片）是装饰，照常省掉 */
  .d-add,
  .d-del,
  pre,
  progress {
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }
```

**Verify**:

- `grep -c 'print-color-adjust: exact' skills/show-me-html/assets/show-me.css` → `1`。
- `npx prettier --check skills/show-me-html/assets/show-me.css` 通过。
- 全量单元测试 → `OK`，测试数不变。

### Step 4: 打出 PDF 看

以下命令在 worktree 根目录、同一个 shell 里运行：

```sh
R=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-b52953a-022
T=$(mktemp -d); echo "T=$T"
for n in approach-compare triage-board code-review; do
  cp "$R/$n.html" "$T/"
  python3 skills/show-me-html/scripts/build.py "$T/$n.html" --no-render --pdf | grep -E '已导出|未完成'
  pdftoppm -r 50 -png "$T/$n.pdf" "$T/$n"
done
ls "$T"/*.png
```

**Verify**：三行 `已导出`；然后逐张打开 PNG：

- **approach-compare**：「三个方案的真实代价」的三张卡没有被分页切开，卡头、代码块、优缺点在同一页。
- **triage-board**：「现在修」「本周修」并排两列，「观察」在下面一行。三列的右边框和计数徽标都完整可见，没有被裁。
- **code-review**：
  - 「先看结构变化」里，删除行（`-└── events.ts`）是浅红底，新增行（`+└── events/`、`+    └── emitter.ts`）是浅蓝底；
  - 代码块有浅灰底；
  - 文件名旁的 `+28 −9` 徽章没有底色，只有边框，这是预期。

### Step 5: 冻结场景轮次

按 `skills/show-me-html/scenarios/README.md` 的流程新建一轮，目录后缀 `-027`。五页复制上一轮的 HTML，用新的 `show-me.css` 重建，再跑探针：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-b52953a-022
RND=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-027
mkdir -p "$RND"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$RND/" && python3 skills/show-me-html/scripts/build.py "$RND/$n.html" | grep -E '^(ERROR|WARN)|自检通过'
done
node skills/show-me-html/scripts/probe_round.mjs "$RND" "$PREV" | grep -E '^[a-z-]+: |probe\.json|截图：|Markdown 不同|打印'
```

**Verify**：

- 五页 `自检通过`。
- 探针五行 `无问题`。
- 屏幕截图与上一轮逐字节相同，因为本计划只改打印样式；只是抗锯齿噪声的个别字节差异，列出文件名即可。
- `probe.json` 只有打印页数可能变化。把每页的打印页数写进汇报（advisor 实测 approach-compare、triage-board 改后仍是 2 页）。
- 另外三页的 PDF 也打开看一眼：有 `.card` 的地方，除了整块卡片挪页后留下的大片空白之外，不应有别的问题。出现了就在汇报里说明是哪页哪张卡。

### Step 6: 文档

`references/visual-system.md`「响应式与打印」的打印一行改为：

<!-- prettier-ignore -->
```markdown
- 打印强制浅纸深字和 A4 纸，隐藏 chrome 和 TOC，展开静态阅读顺序；h2–h4 尽量与下文同页（`break-after: avoid`，下文比一页还高时照常断开），条目（`.item`）和卡片（`.card`）不从中间劈开，看板按纸宽改为两列；背景色默认不印，diff 增删行、代码块和进度条的底色强制保留（`print-color-adjust: exact`）。
```

然后 `npx prettier --write skills/show-me-html/references/visual-system.md`。

**Verify**：

- `make check` → exit 0。
- `grep -c '看板按纸宽改为两列' skills/show-me-html/references/visual-system.md` → `1`。

## Test plan

不加单元测试：分页和打印底色只能靠 PDF 看。Step 4 覆盖三个已知问题，Step 5 用冻结场景兜底，确认屏幕样式不变、其他页面打印不出新问题。

## Done criteria

- [ ] Step 4 三份 PDF 看过，三个问题都不再出现
- [ ] Step 5 五页 `自检通过`、探针 `无问题`、屏幕截图与上一轮相同；打印页数写进汇报
- [ ] 全量单元测试 `OK`；`make check` exit 0
- [ ] `git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- 屏幕截图与上一轮出现非抗锯齿的差异：说明规则漏出了 `@media print`。
- 某页因为 `.card` 整块换页，页数比上一轮多出两页以上：汇报页数和是哪张卡，不要自行改成只对某个配方生效。
- triage-board 的 PDF 里仍有列被裁。
- code-review 的 PDF 里 diff 增删行没有底色：说明 `print-color-adjust` 没生效，汇报 Chrome 版本，不要改成给 `--pdf` 打开全部背景。

## Maintenance notes

- 看板打印固定两列。以后有四列以上、每列很窄也放得下的看板，可以再按列数分档；现在的冻结场景只有三列一种。
- `.card` 整块换页对很高的卡无效，浏览器会照常分页，也会在页底留下空白。若有页面因此多出很多空白页，再考虑只对配方里的卡片网格（如 `.comparison-grid > .card`）生效。
- 新增「颜色本身就是信息」的底色时，比如热力格、色块图例、高亮 `mark`，要把选择器加进 Step 3 那条 `print-color-adjust: exact` 规则，否则打印时会丢掉。装饰性底色不要加，打印照常省墨。
