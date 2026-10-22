# Plan 027: show-me-html 打印时卡片不从中间劈开，看板的列按纸宽排下

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 2f0e439..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/references/visual-system.md`
> 计划 018 先合入时这两个文件都会出现（018 改 token、骨架颜色和 visual-system 的「Token 分层」「对比度」），属于预期；只要下面「Current state」里引用的两段打印样式和 visual-system 那一行原样还在就继续，对不上就 STOP。
>
> 本文件里的 css / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P2
- **Effort**: S（两处 CSS、一行文档）
- **Risk**: LOW（只影响 `@media print`）
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 的成品页自带打印样式，用户要 PDF 时就打印它。2026-10-22 的一轮回归（打印改 A4、标题随下文换页，提交 `7c94bce`）在五个冻结场景的 PDF 里留下两个没修的问题：

- **approach-compare**：「三个方案的真实代价」三张方案卡（每张约 534px 高）落在第 1 页底部，被分页从中间劈开，卡头在第 1 页、优缺点在第 2 页。
- **triage-board**：页面自己把看板写成三列、每列至少 16rem（`repeat(3, minmax(16rem, 1fr))`），三列加间距共 792px；A4 纸减去页边距后可打印宽度约 718px，看板容器在打印时仍是 `overflow-x: auto`，第三列「观察」右侧约 74px 被裁掉，计数徽标和右边框出界。

advisor 在 scratchpad 里把下面两条规则注入这两页的副本，用无头 Chrome 打印模拟（视口 718px、`media: print`）量过：看板改为两列各 353px，三列中的「观察」排到第二行，没有任何一列越界；打印成 A4 PDF 后，approach-compare 的三张卡整块移到第 2 页，triage-board 不再有被裁的列，两页的页数都还是 2。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `2f0e439`，对不上时以引文为准。

- `assets/show-me.css` 主打印块的末尾（`:1929-1944`，`7c94bce` 加的）：

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

- `assets/show-me.css` 文件最后一个 `@media print` 块（配方的打印规则，`:2584` 起），它的开头：

  ```css
  @media print {
    [data-recipe="share-card"] .sheet {
      box-shadow: none;
      break-inside: avoid;
    }
  ```

  同一块里已有「带边框的配方舞台整块换页」的 `break-inside: avoid` 规则，写法可参照。

- 看板的屏幕样式（`:2493-2507`）：

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

  冻结场景页 triage-board 在自己的 `<style>` 里写了 `[data-recipe="triage-board"] .board { grid-template-columns: repeat(3, minmax(16rem, 1fr)); }`。页面样式排在骨架之后、选择器相同，所以骨架的打印规则要用 `!important` 才压得过页面写死的列宽。`show-me.css` 里已有用 `!important` 压过页面写法的先例（`:1532` 附近的注释「!important 用来压过 .fig svg 的 display:block 和页面自己的 display 写法」）。

- `references/visual-system.md`「响应式与打印」的打印一行（本计划写作的同一天已改成下面这样）：

  ```markdown
  - 打印强制浅纸深字和 A4 纸，隐藏 chrome 和 TOC，展开静态阅读顺序；h2–h4 尽量与下文同页（`break-after: avoid`，下文比一页还高时照常断开），条目（`.item`）不从中间劈开。
  ```

- 冻结场景：主检出目录下 `scenarios/rounds/` 里最近一轮（`ls -d /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/*/ | tail -1`），五页 HTML 和 `_probe/` 下的上一轮 PDF、截图。

## Commands you will need

| Purpose  | Command                                                          | Expected on success |
| -------- | ---------------------------------------------------------------- | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`       | 末行 `OK`           |
| 文档门禁 | `make check`                                                     | exit 0              |
| PDF 转图 | `pdftoppm -r 40 -png <pdf> <前缀>`（本机 Homebrew 已装 poppler） | 每页一张 PNG        |

## Scope

**In scope**：`skills/show-me-html/assets/show-me.css`（两处 `@media print`）、`references/visual-system.md`（一行）、`plans/README.md`（状态行）。

**Out of scope**：

- 屏幕上的看板布局与列宽。
- 冻结场景页本身（不删页面写的列宽）。
- 比一页还高的卡片：浏览器会照常分页，`break-inside: avoid` 不保证。

## Git workflow

从本地 `main` 开分支 `advisor/027-show-me-html-print-cards-and-board`；提交例如 `fix(show-me-html): print keeps cards whole and fits the board to the page`。pre-commit 会跑 prettier。不要 push。

## Steps

### Step 1: 卡片整块换页

主打印块末尾那段改为（注释与选择器两处变化，其余不动）：

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

**Verify**: `npx prettier --check skills/show-me-html/assets/show-me.css` 通过（不通过就 `--write` 后再看 diff 只有空白变化）；全量单元测试 → `OK`，测试数不变（`VisualContractTests` 会检查 CSS 的若干契约）。

### Step 3: 打出 PDF 看

```sh
R=$(ls -d /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/*/ | tail -1)
T=$(mktemp -d)
for n in approach-compare triage-board; do
  cp "$R/$n.html" "$T/"; python3 skills/show-me-html/scripts/build.py "$T/$n.html" --no-render > /dev/null
done
python3 - "$T" <<'PY'
import pathlib, runpy, subprocess, sys
T = pathlib.Path(sys.argv[1])
build = runpy.run_path("skills/show-me-html/scripts/build.py")
chrome = build["find_chrome"]()
extra = build["chrome_proxy_args"]() if "chrome_proxy_args" in build else []
for n in ("approach-compare", "triage-board"):
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=4000", *extra,
                    f"--print-to-pdf={T / (n + '.pdf')}", (T / (n + ".html")).as_uri()], capture_output=True, timeout=120)
    print(n, (T / (n + ".pdf")).exists())
PY
for n in approach-compare triage-board; do pdftoppm -r 40 -png "$T/$n.pdf" "$T/$n"; done
ls "$T"/*.png
```

**Verify**: 两个都打印 `True`；逐张打开 PNG：

- approach-compare：「三个方案的真实代价」的三张卡没有被分页切开，卡头、代码块、优缺点在同一页。
- triage-board：「现在修」「本周修」并排两列，「观察」在下面一行；三列的右边框和计数徽标都完整可见，没有被裁。

### Step 4: 冻结场景轮次

按 `skills/show-me-html/scenarios/README.md` 的流程新建一轮（目录后缀 `-027`），五页用新的 `show-me.css` 重建，再跑 `node skills/show-me-html/scripts/probe_round.mjs <本轮> <上一轮>`。

**Verify**: 五页 `自检通过`；探针五行 `无问题`；屏幕截图与上一轮逐字节相同（本计划只改打印样式）；打印页数逐页写进汇报（advisor 实测 approach-compare、triage-board 改后仍是 2 页）。另外三页的 PDF 打开看一眼，有 `.card` 的地方没有出现整块卡片挪页后留下大片空白以外的问题；出现了就在汇报里说明是哪页哪张卡。

### Step 5: 文档

`references/visual-system.md`「响应式与打印」的打印一行改为：

<!-- prettier-ignore -->
```markdown
- 打印强制浅纸深字和 A4 纸，隐藏 chrome 和 TOC，展开静态阅读顺序；h2–h4 尽量与下文同页（`break-after: avoid`，下文比一页还高时照常断开），条目（`.item`）和卡片（`.card`）不从中间劈开，看板按纸宽改为两列。
```

然后 `npx prettier --write skills/show-me-html/references/visual-system.md`。

**Verify**: `make check` → exit 0；`grep -c '看板按纸宽改为两列' skills/show-me-html/references/visual-system.md` → `1`。

## Test plan

不加单元测试：打印分页只能靠 PDF 看。Step 3 针对两个已知问题，Step 4 用冻结场景兜住屏幕样式不变、其他页面打印不出新问题。

## Done criteria

- [ ] Step 3 两份 PDF 看过，两个问题都不再出现
- [ ] Step 4 五页 `自检通过`、探针 `无问题`、屏幕截图与上一轮相同
- [ ] 全量单元测试 `OK`；`make check` exit 0
- [ ] `git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- 屏幕截图与上一轮出现差异（说明规则漏出了 `@media print`）。
- 某页因为 `.card` 整块换页，页数比上一轮多出两页以上：汇报页数与是哪张卡，不要自行改成只对某个配方生效。
- triage-board 的 PDF 里仍有列被裁。

## Maintenance notes

- 看板打印固定两列。以后有四列以上、每列很窄也放得下的看板，可以再按列数分档；现在的冻结场景只有三列一种。
- `.card` 整块换页对很高的卡无效（浏览器会照常分页），也会在页底留下空白。若有页面因此多出很多空白页，再考虑只对配方里的卡片网格（如 `.comparison-grid > .card`）生效。
