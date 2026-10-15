# Plan 010: show-me-html 修好条目组分隔线、来源行里的代码与中文字号、图示分区框内的标签遮罩

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 55a66e8..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/references/components.md skills/show-me-html/references/diagrams.md`
> 预期无输出。有输出就把下面「Current state」的摘录与现行文件逐段对照；对不上即为 STOP 条件。

## Status

- **Priority**: P1
- **Effort**: S（CSS 两处、文档一处；验证要跑一轮冻结场景，约 10 分钟）
- **Risk**: LOW（只新增规则，不改已有规则；已知可见变化见「Why this matters」末段）
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `55a66e8`, 2026-10-14

## Why this matters

show-me-html 把素材做成单文件 HTML 页面，所有页面共用 `assets/show-me.css` 这一套视觉系统，构建时把它内联进页面。维护者反馈生成页面「排版密度不均衡」，审计在共用 CSS 里找到三处缺陷，任何模型生成的页面都会遇到：

1. **条目组的分隔线是一个小圆点。** `references/components.md` 教模型在 `.item-group` 的条目之间写 `<hr />`，CSS 却没有给这个 `hr` 写样式。浏览器默认的 `hr` 落在单列网格里，宽度缩成 0，只剩 2×2px 的 inset 边框，渲染成卡片中间的一个小点，上下还各多出 8px 外边距。`hr` 夹在两个 `.item` 之间，它们不再相邻，`.item + .item` 的分隔线也就不出现。实测：维护者的页面和冻结场景 `status-report`（5 个 `hr`）都是这样。
2. **来源行改写了标识符。** `.src` / `.fig-src` 带 `text-transform: uppercase`，会继承到行内 `<code>`，`<code>PlayerConfig</code>` 显示成 `PLAYERCONFIG`，大小写敏感的名字被改了。行内 code 自带的 0.8125rem 字号和底色在 0.64rem 的来源行里还显得大一号。中文来源行是 10.24px 加 0.08em 字距，汉字没有大小写，这样设置只会更难读。
3. **图示标签遮罩露出补丁。** `references/diagrams.md` 规定连线标签下面垫 `fill: var(--color-background)` 的遮罩。标签放在分区框（3% 前景色底）里时，遮罩比框底亮，会露出一块块浅色补丁。

修完后：条目之间是一条完整的分隔线，卡片高度回到正常；来源行里的代码保持原样；中文来源行 12px；分区框里的标签遮罩与框底同色。**可见变化**：用到 `.item-group` + `<hr>` 的页面会变矮。在冻结场景上实测（只套用本计划），`status-report` 在 1280px 宽度下从 2205px 变成 2120px，`concept-explainer` 从 2632px 变成 2598px；所有中文页面的 `.src` / `.fig-src` 从 10.24px 变成 12px。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。`SKILL.md` 是入口，`references/*.md` 是写作契约，`assets/show-me.css` 是内联进每个页面的视觉系统（约 2490 行），`scripts/build.py` 是构建与自检，`tests/test_build.py` 是 unittest 测试，`scenarios/` 是冻结场景评测环。

- `assets/show-me.css:545-549`（当前）：

```css
  padding: 0.875rem 1rem;
}
.item + .item {
  border-block-start: 1px solid var(--color-border);
}
```

- `assets/show-me.css:1650-1656`（当前；注释声称组件内的 hr 由组件层负责，但 `.item-group` 实际上没有对应规则）：

```css
  }
}
/* 只管正文里的分隔线；组件内部的 hr（.item-group、菜单、按钮组）交给自有组件层 */
main > section > hr {
  border: 0;
  border-top: 1px solid var(--color-border);
  margin-block: 2rem;
```

- `assets/show-me.css:1370-1377`（当前；行内 code 的通用样式，优先级 (0,0,2)）：

```css
/* 行内 code 用 manilla 淡底，卡片（--color-card）里也分得出来 */
:not(pre) > code {
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  background: var(--ink-8);
  padding: 0.125rem 0.375rem;
  border-radius: calc(var(--radius) - 2px);
}
```

- `assets/show-me.css:1456-1465`（当前；后面紧接 `.fig-status {`）：

```css
/* .src 是脱离 figure 的来源行：表格、指标带、引文下面也要交代来源 */
.fig-src,
.src {
  font-family: var(--font-mono);
  font-size: 0.64rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-45);
  margin-top: 0.75rem;
}
```

- `references/components.md:167-178`（当前；条目组契约，`<hr />` 写法要保留，旧页面都这么写）：

```html
<div class="item-group">
  <div class="item">
    <figure><i data-lucide="file-text"></i></figure>
    <section>
      <h4>auth/session.ts</h4>
      <p>+42 −8，重写会话续期逻辑</p>
    </section>
    <aside><span class="badge" data-variant="outline">已评审</span></aside>
  </div>
  <hr />
  <a class="item" href="#detail"> … </a>
</div>
```

- `references/diagrams.md:51-53`（当前）：

```markdown
**2. 标签与连线之间永远留 6–10px 可见间隙。** 标签不压线。标签下面垫一块不透明遮罩 rect
（`fill: var(--color-background)`，比文字四周各大 3–5px），遮罩底缘与描边之间至少 6px。
遮罩可以盖住线防止字糊，但遮罩与线之间的可见间隙保证读者追得到走向。间隙不够就把标签推到 8–10px。
```

同文件「分区框」一节（约 112-122 行）规定分区框填充是 `color-mix(in srgb, var(--color-foreground) 3%, transparent)`。框顶边线上的**框标签**垫 `var(--color-background)` 遮罩是对的（它压在边线上、跨在框外），这一句不要改。

**仓库约定（必须遵守）**：

- CSS 注释用中文，写「为什么」，风格参照上面 1650 行的注释。不写字面颜色，只用 `var(--…)` token；`tests/test_build.py` 的 `test_literal_colors_live_only_in_primitive_layer` 会数 `#rrggbb` 的个数。
- 文档章节按标题名引用（「分区框」），不按编号；`make check` 会检查这一条。
- Markdown 以简体中文为主，代码标识保持英文；格式由 prettier 决定（2 空格、80 列）。

## Commands you will need

在仓库根目录 `/path/to/skills`（含 `Makefile` 的那一层）执行：

| Purpose      | Command                                                                    | Expected on success                                    |
| ------------ | -------------------------------------------------------------------------- | ------------------------------------------------------ |
| 单元测试     | `python3 -m unittest skills.show-me-html.tests.test_build`                 | 末行 `OK`，`Ran 45 tests`（约 90 秒，需要本机 Chrome） |
| 文档门禁     | `make check`                                                               | exit 0                                                 |
| 格式化       | `npx prettier --write <改过的 .md 文件>`                                   | exit 0                                                 |
| 构建单页     | `python3 skills/show-me-html/scripts/build.py <页面.html>`                 | 末尾 `自检通过。`                                      |
| 场景轮次探针 | `node skills/show-me-html/scripts/probe_round.mjs <本轮目录> <上一轮目录>` | 每个场景一行 `无问题`（约 2–3 分钟）                   |

不要用 pytest（未安装）。

## Scope

**In scope**（只改这些）：

- `skills/show-me-html/assets/show-me.css`
- `skills/show-me-html/references/components.md`（只在「列表项（item）」一节补一句）
- `skills/show-me-html/references/diagrams.md`（只改规则 2 的遮罩颜色一句）

**Out of scope**（不要动）：

- `.item + .item` 规则：保留，不写 `hr` 的页面仍然靠它画线。
- `main > section > hr` 规则：正文分隔线，与本计划无关。
- `components.md` 示例里的 `<hr />`：旧页面都这么写，CSS 修好就行，不改契约。
- `.fig-id`、`.fig-sub` 等其他图注小字。
- 指标带 / `.stat-num` / 表格：由计划 011、012 处理，这里不碰，避免同一块 CSS 两份计划都改。
- `scripts/build.py`、`assets/shell.html`、`assets/shell.js`。
- `scenarios/rounds/**`：不进 git 的本地产物，只往里新建本轮目录。

## Git workflow

- 分支：`advisor/010-show-me-html-divider-src`。
- 提交信息用 conventional commits，scope 写技能名，例如仓库里已有的 `fix(show-me-html): L6 and L12 areas stay proportional; …`。本计划建议一个提交：`fix(show-me-html): item-group hr draws the divider, source lines keep code case, zone labels mask with zone fill`。
- pre-commit 会跑 prettier 和 `make check`；prettier 可能重排 Markdown，属预期。
- 不推送，不改 `PROJECT_MEMORY.md`（合并时由维护者回写），不跑 `make install`。

## Steps

### Step 1: 给 `.item-group > hr` 写分隔线样式

在 `assets/show-me.css` 的 `.item + .item { … }` 规则（545-549 行那块）之后紧接着插入：

```css
/* 文档示例在条目之间写 <hr />：它不是 .item，.item + .item 的分隔线不会出现，
   由它自己画这条线。不清掉默认样式时它是网格里一个 2px 的点，上下各多出 8px */
.item-group > hr {
  margin: 0;
  border: 0;
  border-block-start: 1px solid var(--color-border);
}
```

**Verify**: `grep -n -A4 '^\.item-group > hr {' skills/show-me-html/assets/show-me.css` → 打印出上面这条规则，行号约 550。

### Step 2: 来源行里的代码保持原样，中文来源行放大到 12px

在 `assets/show-me.css` 里找到 `.fig-src,\n.src {` 那块规则（1456-1465 行），在它的右花括号之后、`.fig-status {` 之前插入：

```css
/* 来源行里的标识符保持原样：大写变换会把 PlayerConfig 改成另一个名字；
   行本身已是 mono 小字，代码片不再加底色和放大 */
:is(.fig-src, .src) code {
  font-size: inherit;
  text-transform: none;
  letter-spacing: 0;
  background: none;
  padding: 0;
}
/* 汉字没有大小写，0.08em 字距和 10px 字号只会让它更难读 */
:lang(zh) :is(.fig-src, .src) {
  font-size: 0.75rem;
  letter-spacing: 0.02em;
}
```

优先级说明：`:is(.fig-src, .src) code` 是 (0,1,1)，高于 `:not(pre) > code` 的 (0,0,2)，所以无论规则先后都能覆盖。`:lang(zh) :is(…)` 是 (0,2,0)，高于 `.fig-src` / `.src` 的 (0,1,0)。

**Verify**: `grep -n -B1 -A3 ':is(.fig-src, .src) code {' skills/show-me-html/assets/show-me.css` 有输出；`grep -c ':lang(zh) :is(.fig-src, .src)' skills/show-me-html/assets/show-me.css` → `1`。

### Step 3: 单元测试

**Verify**: `python3 -m unittest skills.show-me-html.tests.test_build` → 末行 `OK`，`Ran 45 tests`。

### Step 4: 文档

1. `references/components.md`「列表项（item）」一节，在「`figure` 左侧图标、`section` 主体、`aside` 右侧。`<a class="item">` 是可点整行。」这一行后面另起一行加：

   ```markdown
   条目之间的 `<hr />` 由骨架画成整宽分隔线；不写 `hr` 时相邻条目也会自动加线，两种写法都行，不要给它补页面样式。
   ```

2. `references/diagrams.md` 规则 2 的第二行，把

   ```markdown
   （`fill: var(--color-background)`，比文字四周各大 3–5px），遮罩底缘与描边之间至少 6px。
   ```

   改为

   ```markdown
   （填充取标签下面那层的颜色：页面上用 `var(--color-background)`，分区框里用 `color-mix(in srgb, var(--color-foreground) 3%, var(--color-background))`，与框底同色；比文字四周各大 3–5px），遮罩底缘与描边之间至少 6px。
   ```

   这个 `color-mix` 是分区框半透明填充（3% 前景色叠在页面底色上）的不透明等价色，在 srgb 里逐分量相等。

3. 跑 `npx prettier --write skills/show-me-html/references/components.md skills/show-me-html/references/diagrams.md`。

**Verify**: `make check` → exit 0；`grep -c '与框底同色' skills/show-me-html/references/diagrams.md` → `1`；`grep -c '由骨架画成整宽分隔线' skills/show-me-html/references/components.md` → `1`。

### Step 5: 冻结场景轮次（MAINTENANCE.md「联动规则」要求）

改的只有 CSS。按 MAINTENANCE.md 的说法，旧页面重新构建就会拿到新 CSS，所以复用上一轮的五个场景页面，不用重新生成：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-09-23-bb65054
NEW=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-010
mkdir -p "$NEW"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$NEW/" && python3 skills/show-me-html/scripts/build.py "$NEW/$n.html" | tail -2
done
node skills/show-me-html/scripts/probe_round.mjs "$NEW" "$PREV"
```

`PREV` 是主检出目录里的绝对路径。`rounds/` 不进 git，在独立 worktree 里没有这个目录，所以必须用绝对路径；该目录不存在就是 STOP 条件。

**Verify**：

- 五次构建各打印 `自检通过。`。
- 探针五行都是 `<场景>: 无问题`。
- 「与上一轮对比」里，高度只在 `status-report`、`concept-explainer` 两个场景变化，且都是**变矮**（这两个场景用了 `.item-group` + `<hr>`）。advisor 实测：`status-report` 1280px 2205 → 2120、390/500px 2417 → 2332；`concept-explainer` 1280px 2632 → 2598。其他场景的高度不变。
- 多数或全部截图会报「字节不同」：五个场景都有中文 `.src` / `.fig-src`，字号变了，加上抗锯齿噪声，具体张数每次不同。这是预期，不是回归；以高度对比和人眼看图为准。
- 人眼看 `"$NEW"/_probe/status-report-light-1280.png` 和 `…-dark-1280.png`：「分组进展」各卡片里，条目之间是一条横贯卡片的细线，没有居中的小点。

## Test plan

本计划不新增单元测试。分隔线和来源行都是纯视觉规则：现有测试保证 CSS 能内联、构建能通过，Step 5 的探针截图负责核对外观。之所以不写断言 CSS 文本的测试，是因为那种测试只会重复规则本身。

## Done criteria

- [ ] `python3 -m unittest skills.show-me-html.tests.test_build` 末行 `OK`（45 个测试）
- [ ] `make check` exit 0
- [ ] `grep -c '^\.item-group > hr {' skills/show-me-html/assets/show-me.css` → `1`
- [ ] `grep -c ':is(.fig-src, .src) code {' skills/show-me-html/assets/show-me.css` → `1`
- [ ] Step 5 探针五行 `无问题`，`status-report` 截图无小点
- [ ] `git status --short` 只列出 Scope 里的三个文件（`scenarios/rounds/` 被 `.gitignore` 忽略，不会出现）
- [ ] `plans/README.md` 本计划状态行已更新

## STOP conditions

- Drift check 有输出，且「Current state」的摘录与现行文件对不上。
- `/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-09-23-bb65054/` 不存在或缺五个场景页之一：汇报，不要自己生成场景页（生成要按 `scenarios/README.md` 的轮次流程走，超出本计划）。
- Step 5 的高度对比里，除 `status-report` / `concept-explainer` 以外的场景高度也变了，或者有场景变高。
- 单元测试失败，且失败与本计划改动的规则有关，修一次仍不过。
- 发现 `.item-group` 里的 `hr` 已经有别处的规则（例如 grep 到 `.item-group hr` 或 `.item-group > hr`）：说明计划写成后有人改过，停下汇报。

## Maintenance notes

- `.item-group > hr` 和 `.item + .item` 两条规则并存：写 `hr` 的页面由 `hr` 画线，不写的由相邻选择器画线。以后若要改分隔线颜色或粗细，两处要一起改。
- `:lang(zh)` 依赖页面 `<html lang="zh-CN">`。骨架默认是这样，用户要求其他语言时会改 `lang`，英文页面保留原来的大写小字风格，这是有意为之。
- 审阅时看一眼 `gallery`：中文的 `.fig-src` 也放大到了 12px。改动没有碰 `charts.js` 和 gallery，MAINTENANCE 不要求重截 gallery；但如果审阅者想确认，可以跑 `python3 skills/show-me-html/scripts/gallery.py --out <临时目录>`，预期只有一条「超过 400 KB」的 WARN。
- 维护者那份触发本计划的页面（`reelshort-tech-notes.html`）重新构建后就能拿到这两处修复，因为 `build.py` 会替换内联 CSS。
