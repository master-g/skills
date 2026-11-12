# Plan 032: show-me-html 的配方和反模式文字不再把连线图引向手写 SVG

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。索引 `plans/README.md` 由审阅者维护，你不要改它。
>
> **Drift check（先跑）**: `git diff --stat 5510e7e..HEAD -- skills/show-me-html/references/layouts.md skills/show-me-html/references/anti-patterns.md skills/show-me-html/references/visual-system.md` 应当没有输出。有输出就对照「Current state」的四段引文，任何一段对不上就 STOP。
>
> 本计划的全部改动在附件 `plans/032-show-me-html-mermaid-recipe-wording/032.patch` 里（advisor 在仓库的全新克隆上改好、跑过 prettier 后导出）。你的工作是套用补丁并逐项验证。补丁套不上就 STOP，不要手工改写。

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW（只改三份参考文档里的四句话，不动代码、样式和测试）
- **Depends on**: none（030、031 已在 `main` 上）
- **Category**: docs
- **Planned at**: commit `5510e7e`, 2026-11-12

## Why this matters

show-me-html 是一个把素材做成单文件 HTML 页面的技能，agent 照着 `references/` 下的文档写页面。2026-11-12 起（Plan 030），节点加连线的图（流程、架构、时序、状态等）改为写 Mermaid 源码、由构建器编译成 SVG，`references/diagrams.md` 的「类型路由」表和「Mermaid 图」一节是这条规则的权威出处。Plan 030 只改了 `flowchart` 一个配方的文字，另外有四处仍然写着「内联 SVG」或「另画窄版」，照着这几处写页面的 agent 会回到手写 SVG：多写几千字符的坐标，还要自己再画一版窄屏图。这份计划把这四处改成和 `diagrams.md` 一致。

## Current state

技能目录是 `skills/show-me-html/`（下文不带前缀的路径都相对这个目录）。四处原文（`5510e7e` 上）：

1. `references/layouts.md:186`，`code-understanding` 配方的章节顺序：

   ```
   入口 → 时序图（内联 SVG 或编号步骤）→ 每步一节（真实代码 + 解释）→ 边界与坑。
   ```

2. `references/layouts.md:260`，`implementation-plan` 配方的一条要点：

   ```
   - 阶段之间的依赖用内联 SVG 画，别用文字描述。
   ```

3. `references/anti-patterns.md:21`，名册表第 11 行「窄屏硬缩图」最后一格（修法）的开头：

   ```
   | 主流向能上下走就只画纵向版；横向更好读时按 diagrams.md「窄屏另画一版」加 `.diagram-narrow`，两版 id 前缀不同。build.py 在 500px 量窄版…
   ```

4. `references/visual-system.md:119`，响应式规则里一条的后半句：

   ```
   - 表格、图面和长标识符由局部滚动容器承接，禁止把整页撑宽；横向示意图可以另画窄版（diagrams.md「窄屏另画一版」）。
   ```

改后的四句（补丁里就是这些，列在这里供你核对）：

1. `入口 → 时序图（Mermaid `sequenceDiagram`，写法见 `diagrams.md`「Mermaid 图」；调用是一条直线时改用编号步骤）→ 每步一节（真实代码 + 解释）→ 边界与坑。`
2. ``- 阶段之间的依赖画成图（Mermaid `flowchart`，写法见 `diagrams.md`「Mermaid 图」），别用文字描述。``
3. 第 11 行修法的开头改为：``Mermaid 图的窄版由构建自动出（diagrams.md「Mermaid 图」），排不窄的构建报 WARN。手写的图：主流向能上下走就只画纵向版；横向更好读时按 diagrams.md「窄屏另画一版」加 `.diagram-narrow`，两版 id 前缀不同。`` 这一格后面的内容（`build.py 在 500px 量窄版…`）不变。
4. `…禁止把整页撑宽；横向示意图在窄屏换一版：Mermaid 图由构建自动出（diagrams.md「Mermaid 图」），手写的另画（diagrams.md「窄屏另画一版」）。`

要知道的仓库约定：

- 技能文档之间按标题名引用章节（「Mermaid 图」「窄屏另画一版」），不按编号；这两个标题都在 `references/diagrams.md` 里（`## Mermaid 图`、`## 窄屏另画一版`）。`make check` 会查引用和失效链接。
- Markdown 格式由 prettier 决定。`anti-patterns.md` 的名册是一张表，第 11 行那一格变长后 prettier 会把整张表的列宽重新对齐，所以这个文件的 diff 是 16 行对 16 行，只有第 11 行的文字真的变了，其余行只是补空格。这是预期的。
- 提交信息用 conventional commits，scope 写技能名，例如 `git log` 里的 `feat(show-me-html): clickable nodes for compiled Mermaid diagrams`。

## Commands you will need

都在仓库根目录运行。

| 用途     | 命令                                                                                                                                                             | 成功时                                       |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| 套补丁   | `git apply plans/032-show-me-html-mermaid-recipe-wording/032.patch`                                                                                              | exit 0，无输出                               |
| 格式     | `npx prettier --check skills/show-me-html/references/layouts.md skills/show-me-html/references/anti-patterns.md skills/show-me-html/references/visual-system.md` | `All matched files use Prettier code style!` |
| 文档门禁 | `make check`                                                                                                                                                     | exit 0，`技能文档引用检查通过（N 个文件）`   |
| 测试     | `python3 -m unittest skills.show-me-html.tests.test_build.VisualContractTests.test_layout_docs_define_every_visual_contract`（类名不对时改跑全量，见 Step 2）    | `OK`                                         |

`npx prettier` 和 pre-commit 需要根目录有 `node_modules`。你在 git worktree 里、根目录没有它时，执行 `ln -s /Users/mg/github/skills/node_modules node_modules`（不要 `npm install`，它会改 `package-lock.json`）；提交完用 `rm node_modules`（不带结尾斜杠）删掉这个链接，并确认它没有被提交。

## Scope

**In scope**（只改这三个文件，且只通过套补丁改）：

- `skills/show-me-html/references/layouts.md`
- `skills/show-me-html/references/anti-patterns.md`
- `skills/show-me-html/references/visual-system.md`

**Out of scope**（看着相关，不要动）：

- `skills/show-me-html/references/diagrams.md` —— 已经是对的，是另外四处要对齐的标准。
- `skills/show-me-html/references/charts.md:241` 的「通栏图在手机上要另画窄版」—— 讲的是数据图，数据图不走 Mermaid，这句是对的。
- `layouts.md` 里 `svg-illustrations` 配方和 `flowchart` 配方的文字 —— 前者本来就是手写示意图，后者 Plan 030 已改。
- `anti-patterns.md` 名册其余各行的文字和文件后半的日期记录 —— 这次没有改规则、没有新增检查，不加记录。
- `assets/`、`scripts/`、`tests/`、`scenarios/`、`SKILL.md`、`README.md`、`MAINTENANCE.md`、`plans/`、`PROJECT_MEMORY.md`。

## Git workflow

- 分支：`advisor/032-show-me-html-mermaid-recipe-wording`，从 `main` 开。
- 一个提交：`docs(show-me-html): point recipe and anti-pattern wording at Mermaid for node-link diagrams`。不加 trailer。
- 不要 push，不要合并到 `main`，不要运行 `make install`。

## Steps

### Step 1: 套补丁

```
git apply --check plans/032-show-me-html-mermaid-recipe-wording/032.patch
git apply plans/032-show-me-html-mermaid-recipe-wording/032.patch
```

**Verify**:

- `git diff --stat` → 恰好三个文件：`anti-patterns.md` 32 行（16 增 16 删）、`layouts.md` 4 行、`visual-system.md` 2 行，合计 `19 insertions(+), 19 deletions(-)`。
- `grep -c "内联 SVG" skills/show-me-html/references/layouts.md` → `0`（改前是 `2`）
- `grep -c "Mermaid" skills/show-me-html/references/layouts.md` → `4`（改前是 `2`）
- `grep -c "Mermaid" skills/show-me-html/references/anti-patterns.md` → `1`（改前是 `0`）
- `grep -c "Mermaid" skills/show-me-html/references/visual-system.md` → `1`（改前是 `0`）

### Step 2: 格式、门禁、测试

按「Commands you will need」表依次跑格式、文档门禁、测试三条。

测试那条如果报找不到类或方法，先用 `grep -n "def test_layout_docs_define_every_visual_contract" -B400 skills/show-me-html/tests/test_build.py | grep "^[0-9]*-class " | tail -1` 查出它所在的类名再跑；还是跑不起来就跑全量 `python3 -m unittest skills.show-me-html.tests.test_build`，预期 `Ran 72 tests` 和 `OK`（约一分钟，需要本机有 Chrome 和 node）。全量里 `test_interrupted_build_leaves_no_chrome_profile` 偶尔会失败于 `AssertionError: 0 != -2`，这是已知的偶发问题，与本计划无关：只有它失败时重跑一次，仍然只有它失败就在汇报里写明，不算本计划失败。

**Verify**: 三条都得到表里的成功输出。

### Step 3: 提交

```
git add skills/show-me-html/references/layouts.md skills/show-me-html/references/anti-patterns.md skills/show-me-html/references/visual-system.md
git commit -m "docs(show-me-html): point recipe and anti-pattern wording at Mermaid for node-link diagrams"
```

pre-commit 会跑 prettier 和 `make check`，补丁已经格式化过，不应产生额外改动。

**Verify**:

- `git show --stat HEAD` → 三个文件，`19 insertions(+), 19 deletions(-)`。
- `git status --short` → 无输出（建过 `node_modules` 链接的话先 `rm node_modules`）。

## Test plan

不新增测试：这次只改给 agent 读的说明文字，没有可以机械判定的行为。已有的 `test_layout_docs_define_every_visual_contract` 守着 `layouts.md` 里每个配方都有「视觉契约」一段，`make check` 守着章节引用，Step 2 都跑了。

## Done criteria

全部满足：

- [ ] `grep -c "内联 SVG" skills/show-me-html/references/layouts.md` → `0`
- [ ] `grep -c "Mermaid" skills/show-me-html/references/anti-patterns.md skills/show-me-html/references/visual-system.md` → 两个文件各 `1`
- [ ] `npx prettier --check` 三个文件通过
- [ ] `make check` exit 0
- [ ] `test_layout_docs_define_every_visual_contract` 通过（或全量 72 个 OK）
- [ ] `git diff --stat main..HEAD` 只有 In scope 的三个文件
- [ ] 提交相对 `main` 的 diff 与 `032.patch` 内容相同：`git diff main..HEAD -- skills | diff - plans/032-show-me-html-mermaid-recipe-wording/032.patch` → 无输出

## STOP conditions

停下汇报，不要自行处理：

- Drift check 有输出，且「Current state」的任何一段引文在文件里找不到。
- `git apply --check` 失败。不要手工把四句话改进去：补丁套不上说明文件变了，四句的措辞要由写计划的人重新核对。
- prettier 的 `--check` 报这三个文件需要格式化，或提交时 pre-commit 又改了文件内容。
- `make check` 失败（最可能是章节名引用对不上，说明 `diagrams.md` 的标题变了）。
- 需要改 In scope 之外的任何文件才能通过检查。

## Maintenance notes

- 这四处和 `flowchart` 配方的文字都指向 `diagrams.md` 的「Mermaid 图」和「窄屏另画一版」两个标题。以后给这两节改名，要同步这五处；`make check` 不一定能查出只写标题名、没有链接的引用。
- 以后新增会画连线图的配方时，画法一句话指向 `diagrams.md`「类型路由」或「Mermaid 图」，不要在配方里重写画法。
- 没有纳入本计划：`feature-explainer` 配方的「请求—处理—响应路径」没有写用什么画，不存在误导，没有改；在冻结场景里新增一个连线图场景的事见 `plans/README.md` 里 032 的规划记录。
- 合入后由维护者运行 `make install SKILL=show-me-html SOURCE=.`，本机安装的技能副本才会带上这次的文字。
