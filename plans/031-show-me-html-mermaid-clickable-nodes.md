# Plan 031: show-me-html 的 Mermaid 图节点可以点开详情，手写图的可点示例对齐无障碍契约

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。索引 `plans/README.md` 由审阅者维护，你不要改它。
>
> **前置条件（先查）**: Plan 030 已经合入。`ls skills/show-me-html/scripts/mermaid.mjs skills/show-me-html/tests/fixtures/mermaid-flow.html` 两个文件都在，`grep -c '^\.pele \.pele-cluster > rect' skills/show-me-html/assets/show-me.css` → `1`。不满足就 STOP：本计划的补丁建在 030 之上。
>
> **Drift check**: 030 合入之后，`git log --oneline -- skills/show-me-html/references/interactions.md skills/show-me-html/assets/show-me.css skills/show-me-html/tests/test_build.py` 里除了 030 的提交不应有更新的提交；有的话对照「Current state」的引文，对不上就 STOP。
>
> 本计划的全部改动在附件 `plans/031-show-me-html-mermaid-clickable-nodes/031.patch` 里（advisor 在套过 030 的仓库副本上跑通后导出，已经过 prettier）。你的工作是套用补丁并逐项验证。

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW（一段只对 `role="button"` 节点生效的 CSS、一段文档、一个测试）
- **Depends on**: plans/030-show-me-html-mermaid.md
- **Category**: direction
- **Planned at**: commit `fdf3059`, 2026-11-12（补丁基于 030 套用后的状态）

## Why this matters

show-me-html 的 `flowchart` 配方是「流程图 + 点节点看详情」：读者点一个节点，旁边的详情栏换内容。Plan 030 之后流程图由 Mermaid 源码编译，SVG 每次构建都重新生成，作者没法像手写图那样在节点上写 `tabindex`、`role="button"`。这份计划给出页面脚本的标准写法（加载时按节点 id 给节点补上按钮属性），把悬停、聚焦、选中的样式放进骨架 CSS，并用一个浏览器测试守住它。顺带修正现有手写图示例：它用的是 `aria-label`，而技能自己的无障碍契约要求 `aria-labelledby` + `<title>` + `<desc>`，照示例写的页面会被构建报 WARN。

## Current state

技能目录是 `skills/show-me-html/`（下文不带前缀的路径都相对这个目录）。

- `references/interactions.md`「可点击的 SVG 节点」一节（`fdf3059` 上从第 818 行起）— 手写 SVG 的可点节点示例，开头是：

  ```html
  <svg viewBox="0 0 720 220" role="img" aria-label="请求处理流程">
    <g
      class="node"
      tabindex="0"
      role="button"
      data-node="ingress"
      aria-label="ingress 节点"
    ></g>
  </svg>
  ```

  这一节之后紧跟 `## 筛选 / 搜索`。本计划改示例的开标签，并在两节之间插入新的一节「可点击的 Mermaid 节点」。

- `references/diagrams.md`「无障碍 SVG 契约」要求的写法（`scripts/build.py` 的 `check_svgs` 对缺项报 WARN）：

  ```svg
  <svg role="img" aria-labelledby="flow-title flow-desc" viewBox="…">
    <title id="flow-title">一句话说清这张图展示什么</title>
    <desc id="flow-desc">图中节点与流向的文字版</desc>
  ```

- `assets/show-me.css` — Plan 030 加的 Mermaid 样式段，以这条规则结尾，本计划接在它后面：

  ```css
  .pele .pele-cluster > rect {
    stroke: color-mix(in srgb, var(--color-foreground) 15%, transparent);
    stroke-width: 0.8px;
  }
  ```

- Plan 030 之后编译产物的结构（本计划的脚本依赖它）：每幅图是 `<div class="mermaid-figure">` 里的一个或两个 `<svg class="[diagram-wide|diagram-narrow] pele pele-flowchart" role="img" …>`；每个节点是 `<g class="pele-node pele-shape-…" data-id="源码里的节点 id">`，第一个子元素是外形。横向图有宽窄两版，同一个节点 id 在两版里各出现一次。
- `tests/fixtures/mermaid-flow.html`（030 新建）— 一幅横向流程图（节点 id 为 A–I，出宽窄两版）加一幅时序图。
- `tests/test_build.py` — unittest。`run_build(page, *args)` 自带 `--no-render`；`runpy.run_path(str(BUILD))["run_jobs"]` 能拿到无头 Chrome 的运行器，`run_jobs([{"url", "width", "eval"}])` 返回 `(results, err)`，`results[0]["value"]` 是 `eval` 表达式的值（同文件 `test_runner_returns_long_output_whole` 有现成用法）。030 之后全量是 71 个用例。
- `--color-ring` 是 `show-me.css` 已有的 token（焦点环用色）。
- 仓库约定：技能文档按标题名引用章节，不按编号（`make check` 会查）；格式由 prettier 决定；提交信息 conventional commits，scope 写技能名。

## Commands you will need

命令都在仓库根目录跑。

| Purpose  | Command                                                                     | Expected on success                          |
| -------- | --------------------------------------------------------------------------- | -------------------------------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`                  | `Ran 72 tests`、末行 `OK`（执行前是 71）     |
| 只跑新增 | `python3 -m unittest skills.show-me-html.tests.test_build -k mermaid_nodes` | `Ran 1 test`、`OK`                           |
| 格式     | `npx prettier --check <文件>`                                               | `All matched files use Prettier code style!` |
| 文档门禁 | `make check`                                                                | exit 0，`技能文档引用检查通过`               |

需要 node 22+ 和本机 Chrome；没有的话新用例会被跳过（输出里有 `skipped=`），这种情况要在汇报里写明「浏览器测试未运行」。`test_interrupted_build_leaves_no_chrome_profile` 在基线上有偶发失败（`0 != -2`），遇到就单独重跑一次。

## Scope

**In scope**:

- `skills/show-me-html/references/interactions.md`
- `skills/show-me-html/assets/show-me.css`
- `skills/show-me-html/tests/test_build.py`

**Out of scope**:

- `skills/show-me-html/scripts/mermaid.mjs`、`scripts/build.py` — 按钮属性由页面脚本在运行时加，不进编译产物（构建的静态检查要求 `<svg role="img">`）。
- `skills/show-me-html/assets/shell.js` — 详情表是每页自己的内容，不进骨架脚本。
- 手写图示例的 JS 和 CSS 部分 — 只改它的 `<svg>` 开标签和加 `<title>` / `<desc>`。
- `skills/tufte-reader/**`、`plans/README.md`、仓库根的文档。
- 不运行 `make install`，不推送。

## Git workflow

- 分支 `advisor/031-show-me-html-mermaid-clickable-nodes`，从已含 030 的 `main` 开出。Agent 工具开的 worktree 基于 `origin/main`：030 只合进了本地 `main` 还没推送时，先 `git checkout -b advisor/031-show-me-html-mermaid-clickable-nodes main`。
- 一个提交：`feat(show-me-html): clickable nodes for compiled Mermaid diagrams`。
- pre-commit 会跑 prettier 和 `make check`；worktree 里没有 `node_modules` 时 `ln -s /Users/mg/github/skills/node_modules node_modules`，提交后 `rm node_modules`（不带结尾斜杠），确认它没被提交。
- 不要推送，不要开 PR。

## Steps

### Step 1: 套用补丁

```bash
git apply --check plans/031-show-me-html-mermaid-clickable-nodes/031.patch && git apply plans/031-show-me-html-mermaid-clickable-nodes/031.patch
```

**Verify**: `git status --short` 恰好列出 Scope 的三个文件。

补丁做了什么：

1. **`assets/show-me.css`**：在 `.pele .pele-cluster > rect` 规则后面加三条——`.pele .pele-node[role="button"]` 指针光标、去掉默认 outline；悬停或键盘聚焦时外形描边换成 `--color-ring`；`aria-pressed="true"` 时描边 `--color-ring`、2.5px。
2. **`references/interactions.md`**：
   - 「可点击的 SVG 节点」开头加一句分流（手写图看这一节，Mermaid 图看下一节）；示例的 `<svg>` 改成 `role="img" aria-labelledby="flow-title flow-desc"` 并加上 `<title>`、`<desc>`。
   - 新增「可点击的 Mermaid 节点」一节：源码示例（放在 `flowchart` 配方的版式容器 `.diagram-layout > .diagram-canvas` 里，旁边是 `aside.node-detail`，并说明别的配方里放进普通图框）、一段脚本（详情表以 Mermaid 节点 id 为键；有详情的节点加 `role="button"`、`tabindex="0"`、`aria-label`、`aria-pressed`，绑定点击与 Enter / 空格；按 id 选中，所以宽窄两版同时标记；含按钮的 `<svg>` 把 `role` 从 `img` 改成 `group`），以及四条说明。
3. **`tests/test_build.py`**：新增 `test_mermaid_nodes_become_buttons_in_both_variants`。

### Step 2: 跑测试与门禁

**Verify**（都要过）:

- `python3 -m unittest skills.show-me-html.tests.test_build -k mermaid_nodes` → `Ran 1 test`、`OK`（不是 `skipped`）
- `python3 -m unittest skills.show-me-html.tests.test_build` → `Ran 72 tests`、`OK`
- `make check` → exit 0
- `npx prettier --check skills/show-me-html/references/interactions.md skills/show-me-html/assets/show-me.css` → `All matched files use Prettier code style!`

### Step 3: 反证一次

临时把 `skills/show-me-html/assets/show-me.css` 里 `.pele .pele-node[aria-pressed="true"] > :first-child` 规则的 `stroke-width: 2.5px;` 改成 `stroke-width: 1.2px;`，跑 `python3 -m unittest skills.show-me-html.tests.test_build -k mermaid_nodes`。

**Verify**: 用例失败，断言差异里有 `'1.2px'` 与 `'2.5px'`。然后 `git checkout -- skills/show-me-html/assets/show-me.css` 会丢掉补丁对该文件的改动，所以**不要用 checkout 还原**，手工把这一行改回 `2.5px`，重跑 → `OK`；`grep -c 'stroke-width: 2.5px;' skills/show-me-html/assets/show-me.css` 与改之前的计数相同（改之前先记下这个数）。

### Step 4: 文档里的脚本与测试里的脚本一致

新一节的脚本和测试里内嵌的脚本应当是同一套逻辑（测试里只把详情表换成了夹具的节点 id）。

**Verify**: `grep -c 'g.closest("svg").setAttribute("role", "group");' skills/show-me-html/references/interactions.md skills/show-me-html/tests/test_build.py` → 两个文件各 `1`；`grep -c '^## 可点击的 Mermaid 节点' skills/show-me-html/references/interactions.md` → `1`；`grep -c 'aria-label="请求处理流程"' skills/show-me-html/references/interactions.md` → `0`。

## Test plan

`test_mermaid_nodes_become_buttons_in_both_variants`（需要 Chrome）：在 `mermaid-flow.html` 夹具的 `<!--SHOW-ME:JS-->` 前插入详情栏和文档里的脚本（详情表只给节点 `A` 和 `F`），构建后用 `run_jobs` 在 1280px 下打开页面并执行一段探针：

- 加载后：`role="button"` 的节点 4 个（A、F 各在宽窄两版里），`role="group"` 的 SVG 2 个（流程图的两版），`role="img"` 的 SVG 1 个（时序图没有可点节点，保持不变）。
- 点宽版里的 `F`：`aria-pressed="true"` 的节点 2 个，id 都是 `F`；详情栏文字是「灰度 5%观察 30 分钟。」；被点节点外形的计算样式是 `cursor: pointer`、`stroke-width: 2.5px`。

结构样板是同文件里其他用 `run_jobs` 的用例。

## Done criteria

- [ ] `python3 -m unittest skills.show-me-html.tests.test_build` → `Ran 72 tests`、`OK`，新用例没有被跳过
- [ ] `make check` exit 0
- [ ] Step 3 的反证失败过一次，还原后通过
- [ ] Step 4 的三条 grep 计数相符
- [ ] `git status --short` 只有 Scope 的三个文件
- [ ] 汇报里写明每条验证的实际输出

## STOP conditions

- 前置条件不满足（030 没合入），或 `git apply --check` 失败。
- 新用例被跳过而本机其实有 Chrome 和 node 22+（说明 `RENDERER` 判定有别的问题）。
- 探针里 `before` 不是 `[4, 2, 1]`：说明 030 的编译产物结构与本计划假设的不同（宽窄两版、`data-id`、`role="img"`），需要 advisor 重新核对。
- 需要改 Scope 之外的文件才能通过。

## Maintenance notes

- **合入后要重新安装技能才生效**：由维护者执行 `make install SKILL=show-me-html SOURCE=.`。
- **选择器依赖 pele 的输出**：`.pele-node[data-id]` 和「第一个子元素是外形」来自 pele 1.13.0。升级 pele 后这个用例会第一时间报出结构变化。
- **`role="group"` 的由来**：ARIA 规定 `img` 角色的子元素对辅助技术不可见，按钮放在 `role="img"` 的 SVG 里会读不到；构建的静态检查又要求示意图是 `role="img"`。所以编译产物保持 `img`，有可点节点的图由页面脚本在运行时改成 `group`。手写图的示例有同样的问题（`role="img"` 里放 `role="button"`），本计划只对齐了它的标题与描述，没有改它的角色：手写图的角色写在作者的静态标记里，改它要同时改 `check_svgs` 的判定，留给维护者决定是否另开计划。
- **审阅时重点看**：新一节的四条说明是否与脚本行为一致；测试里的脚本与文档里的脚本有没有漂移。
- **有意没做**：把这段脚本放进骨架 `shell.js` 自动生效。详情内容每页不同，骨架只能提供机制；等有两三页真实页面用过这一节，再看是否值得抽成 `data-*` 契约。
