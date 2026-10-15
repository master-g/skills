# Plan 012: show-me-html 表格密度，先做对比样张由维护者选方案，再实现所选方案

> **Executor instructions**: 本计划分两段：Step 1–2 做对比样张，然后**必须停下**，把截图交给维护者选方案；Step 3 以后只在 `plans/README.md` 的 show-me-html 一节记下维护者的选择之后才执行。每一步跑完验证命令并确认预期结果。遇到「STOP conditions」里的情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 55a66e8..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/references/components.md`
> 计划 010 / 011 合入后，这两个文件会出现在输出里，属于预期，它们不改 `.table`。核对方法：`grep -n -A12 '^\.table-container {' skills/show-me-html/assets/show-me.css` 的输出应与下面的摘录一致，不一致即为 STOP。

## Status

- **Priority**: P2
- **Effort**: S（样张约 30 分钟；所选方案的实现只有几行 CSS）
- **Risk**: MED（所有页面的表格观感都会变；而且骨架注释里记录过「宁折行不横滚」的取舍，见下文）
- **Depends on**: none（与 010、011 改的规则不重叠；建议排在它们之后，避免三份计划同时改 `show-me.css`）
- **Category**: tech-debt
- **Planned at**: commit `55a66e8`, 2026-10-14

## Why this matters

维护者反馈生成页面「表格编排密度不均衡」。advisor 用维护者的一份页面（46rem 版心，三张中文表格）实测，问题分两类：

- **宽屏 1280px**：`.table` 是 `width: 100%` 加自动列宽。三列表被拉满 736px，列宽由内容决定（长标识符那列最宽），这一点试过 CSS 修不了，见 Step 1。正文格是 14px，表头 12px 次要色，每行约 46px 高（14px 字、上下各 12px 内边距、行高 1.6）。表格比上下 16px 的正文段落小一号也松一档，整页读起来忽松忽紧。
- **窄屏 390px**：中文的最小内容宽度只有一个字，表格总是压缩到容器宽，不会出现横向滚动，于是格子两三个字就折一行。例如「弱网 / 未 / 登录默认」「能力位存 / 在，未见 / UI 入口」。

这件事没有唯一正确答案：骨架的注释（`show-me.css:519-521`）明确选择了「表格永远不比容器宽」，改动等于推翻或修正一个已有的设计决定。所以先做样张，由维护者选方案。

## Current state

技能目录 `skills/show-me-html/`；`assets/show-me.css` 是内联进每个页面的视觉系统；`assets/shell.html` 是新页面的骨架；`scripts/build.py <页面>` 把 CSS 内联进页面并自检。

- `assets/show-me.css:492-529`（当前）：

```css
.table-container {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-card);
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.table th,
.table td {
  padding: 0.75rem 0.875rem;
  text-align: start;
  vertical-align: top;
  border-block-end: 1px solid var(--color-border);
}
.table th {
  color: var(--color-muted-foreground);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  word-break: keep-all;
}
/* 中文的最小内容宽度只有一个字：不加约束时，窄屏下表头被挤成一字一行、格内 badge 折成多行药丸，
   表格永远不比容器宽，.table-container 的横向滚动也就不会出现。表头只在空格和标点处断行，
   badge 不断行；放不下时整表横向滚动，正文格照常折行。 */
.table .badge {
  white-space: nowrap;
}
.table tr:last-child > * {
  border-block-end: 0;
}
.table tbody tr:hover {
  background: color-mix(in oklab, var(--color-accent) 45%, transparent);
}
```

- `show-me.css` 约 1063 行另有 `.table { font-variant-numeric: tabular-nums; }`，与本计划无关，不要动。
- `references/components.md`「表格」一节（约 137-160 行）：给出 `.table-container > table.table` 的写法，说明「`.table-container` 提供横向滚动，宽表必须套」。
- 冻结场景 `approach-compare` 有一张 4 列、15 个 badge 的判据表，是表格改动最容易出问题的地方。
- 开发机的无头 Chrome 窗口最窄只能到 500px。要截 390px，用 CDP 的 `Emulation.setDeviceMetricsOverride`（`scripts/probe_round.mjs` 就是这样截 390 的），或者在一个 1280 宽的页面里放一个 390px 宽的 `<iframe>` 再截图。

## Commands you will need

| Purpose  | Command                                                          | Expected on success   |
| -------- | ---------------------------------------------------------------- | --------------------- |
| 构建样张 | `python3 skills/show-me-html/scripts/build.py <样张.html>`       | 末尾 `自检通过。`     |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`       | 末行 `OK`             |
| 文档门禁 | `make check`                                                     | exit 0                |
| 场景探针 | `node skills/show-me-html/scripts/probe_round.mjs <本轮> <上轮>` | 每个场景一行 `无问题` |

## Scope

**Step 1–2（样张）**：只在仓库外的临时目录建文件，例如 `$TMPDIR/table-demo/`。不改仓库里的任何文件。

**Step 3 以后（实现）**，只改：

- `skills/show-me-html/assets/show-me.css`（`.table*` 规则）
- `skills/show-me-html/references/components.md`（「表格」一节）

**Out of scope**：`.table .badge` 的 `nowrap`（保留）；`tabular-nums`；`scripts/build.py`；其他组件。

## Git workflow

- 分支：`advisor/012-show-me-html-table-density`。
- 样张不提交。实现提交用 conventional commits，例如 `fix(show-me-html): tables keep CJK cells readable on narrow screens`（按所选方案改写）。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`。

## Steps

### Step 1: 做样张页

用 `skills/show-me-html/assets/shell.html` 复制出 `$TMPDIR/table-demo/base.html`，`<body>` 的 `data-recipe` 设为 `feature-explainer`（46rem 版心，最能暴露短表被拉宽的问题）。把 `<title>` 和首个 `<h1>` 改成「表格密度样张」，骨架里的占位标题会让 `build.py` 报 ERROR。在 `main#doc` 下放一个 `<section>`，里面依次放三张表，都用 `.table-container > table.table` 包好：

1. **短三列表（参数表）**：表头「参数 / 值 / 作用」，6 行，第一列是行内 `<code>` 标识符（如 `startBufferMs`，有一行写两个：`connectTimeout` / `retryCount`），第二列是短值（「100 ms」「低端机 300 MB，其余 1 GB」），第三列是一句短说明（「起播缓冲门槛，首帧快慢的直接开关」）。
2. **中文三列表（档位表）**：表头「档位 / 谁在用 / 怎么到达」，4 行：`540p | 弱网 / 未登录默认 | 服务端下发；兜底档`、`720p | 默认档，也是自动档上限 | 登录且网络评级 ≥ 720 时开自动选轨`、`1080p | 会员 / 体验期内 | 手动选档 + 权益校验，切档埋点 quality_switch`、`1440p / 2160p | 能力位存在，未见入口 | 判定函数覆盖，预留档位`。
3. **两列长文表（特性表）**：表头「Feature / 实现要点」，4 行，第二列每格 40–60 字，夹一两个行内 `<code>`。

再复制三份，在 `</head>` 前各加一段 `<style>`，分别对应三个方案：

- `opt-a.html`，**A：窄屏中文格设最小宽度**。放不下时整表在容器里横滚，与注释里说的「放不下时整表横向滚动」一致：

  ```css
  .table td {
    min-inline-size: 6em;
  }
  ```

- `opt-b.html`，**B：行距收紧，正文格字号向正文靠拢**（15px 对 16px 正文，行高从约 46px 降到约 40px）：

  ```css
  .table {
    font-size: 0.9375rem;
  }
  .table th,
  .table td {
    padding: 0.55rem 0.75rem;
  }
  ```

  **不要**在样张里加调列宽的规则。advisor 试过两种，结果都更差：(1) 首列 `white-space: nowrap`，自动列宽仍会把余宽分给中间列，最后一列反而折到只剩一个字（「…的直接开 / 关」）；(2) 非末列 `width: 1%; white-space: nowrap`，`approach-compare` 的判据表最后一列留下大片空白，中间列又因为内容本身就宽而收不窄。宽屏下列宽不均主要来自内容（长标识符、长短值），不是 CSS 能修的。

- `opt-ab.html`：A 与 B 同时生效。

**Verify**: 四个文件分别跑 `python3 skills/show-me-html/scripts/build.py <文件>` → 都是 `自检通过。`（`base.html` 可能报 TOC 相关 WARN 以外的问题，就是页面写错了，修页面）。

### Step 2: 截图并交给维护者

对四个页面各截两张图：1280px（light）和 390px（light），共 8 张，放进 `$TMPDIR/table-demo/shots/`。再写一个 `index.md`，列出每张图的路径，以及每个方案在 390px 下每张表的 `.table-container` 的 `scrollWidth/clientWidth`（大于 1 表示出现了横滚）。

advisor 已实测的参考值（维护者的一份同类页面，390px）：不加样式时三张表都是 `356/356`，即不横滚、逐字折行；方案 A 下这三张表仍然放得下（`356/356`），但折行明显减少，第二列从 2–4 字一行变成 5–6 字一行。

**Verify**: `ls $TMPDIR/table-demo/shots/*.png | wc -l` → `8`。

**然后停下**：把 `index.md` 和截图路径交给维护者，请他选 base / A / B / A+B，或者给出别的方向（例如窄屏把行转成卡片，那是另一份计划）。在 `plans/README.md` 的 show-me-html 一节「Decisions recorded」下记下选择。

### Step 3: 实现所选方案（维护者选定后）

- 选 **base**：本计划改状态为 `REJECTED（维护者选择保持现状）`，结束。
- 选 **A**：在 `show-me.css` 的 `.table th { … }` 规则之后加：

  ```css
  /* 中文格的最小内容宽度只有一个字：窄屏下不设底线就两三个字一折。
     给正文格 6em 底线，放不下时由 .table-container 横滚，与上面的取舍一致 */
  .table td {
    min-inline-size: 6em;
  }
  ```

  并把 519-521 行注释的最后一句改为「badge 不断行、正文格至少 6em；放不下时整表横向滚动，正文格在 6em 以上照常折行。」

- 选 **B**：把 `.table`（492-530 行那块）的 `font-size: 0.875rem` 改为 `0.9375rem`，把 `.table th, .table td` 的 `padding` 改为 `0.55rem 0.75rem`。不加其他规则。

- 选 **A+B**：两者都做。

然后在 `references/components.md`「表格」一节最后一段之后补一句，说明新的行为（A：「正文格至少 6em，窄屏放不下时整表横滚，不必为此改写表格。」；B：不需要补文档，字号与行距不是写作契约）。跑 `npx prettier --write skills/show-me-html/references/components.md`。

**Verify**: `python3 -m unittest skills.show-me-html.tests.test_build` → `OK`；`make check` → exit 0。

### Step 4: 冻结场景轮次

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-09-23-bb65054
NEW=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-012
mkdir -p "$NEW"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$NEW/" && python3 skills/show-me-html/scripts/build.py "$NEW/$n.html" | tail -2
done
node skills/show-me-html/scripts/probe_round.mjs "$NEW" "$PREV"
```

**Verify**: 五次构建都是 `自检通过。`（`build.py` 会在 500/1280px 检查横向溢出，`.table-container` 内部的横滚不算溢出）；探针五行 `无问题`；`approach-compare` 的判据仍是 `"tableCols":4,"badgesInTable":15`。人眼看 `"$NEW"/_probe/approach-compare-light-390.png` 和 `…-1280.png`：判据表的 badge 没有折成多行，表格没有撑破页面。

## Test plan

不新增单元测试：这是观感取舍，现有测试保证构建正确，场景探针检查溢出与判据，截图交给人看。

## Done criteria

- 样张阶段：`$TMPDIR/table-demo/shots/` 有 8 张 PNG 和一份 `index.md`；维护者的选择已记在 `plans/README.md`。
- 实现阶段（选了 A / B / A+B 时）：
  - [ ] `python3 -m unittest skills.show-me-html.tests.test_build` → `OK`
  - [ ] `make check` exit 0
  - [ ] Step 4 五个场景 `自检通过。`，探针五行 `无问题`
  - [ ] `git status --short` 只列出 `show-me.css` 与 `components.md`
  - [ ] `plans/README.md` 状态行已更新

## STOP conditions

- 维护者还没选方案，就不要执行 Step 3。
- 样张里出现页面级横向溢出（构建报「视口横向溢出」）：这说明 `.table-container` 没有兜住，先汇报。
- `approach-compare` 的 badge 在方案 A/B 下折行，或判据表撑出容器。
- 维护者选了 Step 3 以外的方向（例如行转卡片）：把这一行状态记为 `BLOCKED（需要新计划：<方向>）`，然后停下。

## Maintenance notes

- 方案 A 让「宁折行不横滚」变成「6em 以上折行，再小就横滚」。以后有人报告「表格在手机上要横着滑」，这就是原因；阈值在 `.table td` 的 `min-inline-size`。
- 调列宽的两种 CSS 写法已经试过，都不行（见 Step 1）。以后有人想「让说明列吃掉余宽」，先看那段记录。
- 方案 B 改了表格字号，会影响所有含表格的页面，包括冻结场景 `approach-compare`。审阅时对比该场景前后的截图。
