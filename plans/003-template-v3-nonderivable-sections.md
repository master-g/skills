# Plan 003: 模板升级到 v3：去掉个人机器路径，新增「导航」「工作流与陷阱」两节，记忆维护加「晋升」步骤

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 547eeac..HEAD -- skills/bootstrap-claude/assets/CLAUDE.template.md skills/bootstrap-claude/references/bootstrap.md skills/bootstrap-claude/references/maintain.md skills/bootstrap-claude/evals/evals.json skills/bootstrap-claude/scripts/setup_context.py skills/bootstrap-claude/scripts/test_setup_context.py`
> Plan 001 和 002 应已落地，所以 `setup_context.py`、`test_setup_context.py`、`bootstrap.md`、`evals.json` 会有差异；对照时只看本计划「Current state」摘录的段落。`CLAUDE.template.md` 和 `maintain.md` 有任何差异即 STOP。

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW（模板变更通过既有的标记升级机制无损下发；标记号升一次，用户只做一次约定升级）
- **Depends on**: plans/001-section-aliases.md（必填章节要登记进别名表）、plans/002-import-pointer-compat.md（仅为避免同文件冲突）
- **Category**: tech-debt + docs
- **Planned at**: commit `547eeac`, 2026-10-12

## Why this matters

两件事合成一次模板升级，因为每次模板变更都要把结束标记的版本号加一，并让所有已初始化项目升级一次约定块；合并后用户只经历一次升级。

**第一件：模板里写死了个人机器路径。** `assets/CLAUDE.template.md:50` 要求 agent 运行 `python3 ~/.claude/skills/bootstrap-claude/scripts/memory.py check PROJECT_MEMORY.md`。这一节会被写进仓库、给全队和所有 agent 读；别人机器上这个路径不存在，没装技能的 agent 会执行一条必然失败的命令。提交 `606e47c` 曾以「`scripts/memory.py` 只存在于技能内」为由把技能路径从模板里删掉，后来 `9a35c1c` 又加了回来，提交信息没有说明推翻原因，视为回归。Firefox 的对应做法是只引用仓库内工具（`./mach`）。

**第二件：模板五节多数是「从环境就能查到的事实」，缺「只有踩过才知道」的槽位。** 对照 Firefox 73 行的 AGENTS.md：几乎全是工具用法与陷阱（慢命令输出重定向到 `artifacts/` 而不是管道过滤；只改前端用 `./mach build faster`）、授权边界（未经用户明确同意不提交到 Phabricator）、引用约定、子目录指令文件指针，每条都带原因（`DONTBUILD` 会让决策任务显绿但不排任何构建）。它的提交历史显示每一行几乎都是一次事故之后补上的。本仓库的 `writing-for-agents` 技能也写明：缓存 agent 查不到的东西，一条命令能查到的交给环境。模板目前没有「需要用户确认的操作」「已知陷阱与原因」「仓库导航与搜索方式」「子目录指令文件」的位置，agent 就不会去找这些证据。

**顺带：记忆到指令的晋升路径。** `references/maintain.md` 的 compound 四步只有「搬出到 docs/」，没有「晋升到指令文件」。一条反复出现、或每次会话都要先知道的失败尝试，归属是上下文文件而不是记忆。新增的「工作流与陷阱」正好是晋升目标。

## Current state

- `skills/bootstrap-claude/assets/CLAUDE.template.md` —— 52 行，中文模板，章节文字的唯一来源（脚本按 `## ` 切块）。
- `skills/bootstrap-claude/references/bootstrap.md` —— Step 2 列每节取证来源；Compatibility 节讲真源与伙伴文件。
- `skills/bootstrap-claude/references/maintain.md` —— 回写流程；「怎么写（compound 四步）」在第 22-27 行。
- `skills/bootstrap-claude/scripts/setup_context.py` —— `REQUIRED_SECTIONS`（第 35 行）与 Plan 001 加的 `SECTION_ALIASES` 决定哪些章节必填、怎么识别。
- `skills/bootstrap-claude/scripts/test_setup_context.py` —— `BASE` 常量（第 16 行）是测试用的「已填满」文件；Plan 001 加了 `BASE_EN`。
- `skills/bootstrap-claude/evals/evals.json` —— 四个 eval，期望里写了「五个标题」。

模板现状（节选，行号按 `547eeac`）：

```markdown
6: ## 技术栈
...
12: ## 命令
...
20: ## 代码风格
...
26: ## 禁止文件
...
32: ## 审查规则
...
38: ## 项目记忆 (回写约定)
39:
40:
41: 跨会话的持久信息记录在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)，只写代码、Git 和文档推导不出的内容。
42:
43: 收尾顺序：验证 → 回写记忆 → 提交 → 推送。回写与本次改动进同一个提交；不提交的任务在结束前回写。
44:
45: 回写是提炼，不是记录：
46:
47: - 「上次会话」「下次运行」整节改写成一块（分支、验证命令与实际结果、停在何处；接下来做什么），旧块直接删，历史由 Git 保存。
48: - 本次确认的决策追加到「已验证的事实」，走不通的路径及原因追加到「失败尝试」；每条一行，写结论、原因和来源或适用范围。能从 `git log`、代码或计划文档 30 秒内推出来的（commit SHA、进度状态、计划内容）不写，只留一行指向证据目录。
49: - 同主题已有条目就改写它，不追加；结论被推翻就删旧条。写不进两行的长期知识搬进 docs/ 后只留一行指针。
50: - 结束前运行 `python3 ~/.claude/skills/bootstrap-claude/scripts/memory.py check PROJECT_MEMORY.md`，不通过不算完成：全文 ≤ 24 KB，单行 ≤ 300 字符，改写节各一块。超限先 `compact` 压改写节，再合并或搬出事实；脚本不自动删追加节条目。
51:
52: <!-- bootstrap-claude convention v2 -->
```

每个章节的形态都是：`## 标题`、一行 `<!-- 提示 -->`、`- _待填写_`。HTML 注释在 Claude Code 注入上下文前会被剥掉，所以提示只给人看，零运行成本。

升级机制（`bootstrap.md:20-25`，脚本 `ensure_convention`）：有结束标记的块在下次运行脚本时**自动**替换为模板最新正文，标记之后的项目自定义行保留。所以改模板正文 + 把标记从 v2 改成 v3，已初始化项目下次 `setup_context.py` 一跑就升级，无需人工操作。无标记的旧块（legacy）仍需 `--upgrade-convention`。

`maintain.md:22-27` 现状：

```markdown
## 怎么写（compound 四步）

1. **筛**：把本次产出过一遍判定问句，留下的通常只有零到三条。
2. **查重与替换**：同主题已有条目就改写它，不追加第二条；结论被推翻就删旧条，不留「已失效」标记堆在旁边。
3. **搬出**：一条长期知识写不进两行时，它已经是文档而不是记忆——搬进 `docs/`（或项目既有的知识目录），记忆里只留一行指针。已完结的旧会话同理压成一行或删除。
4. **改写当前状态**：整块重写「上次会话」和「下次运行」。
```

`maintain.md:16` 表格「失败尝试」行：`| 失败尝试 | 追加 | 走不通的路径和原因，防止下次重走 |`。

测试对模板文字的依赖：`test_setup_context.py:38` 断言升级后的文件含 `"memory.py check"` 这个子串，新正文必须保留它。

eval 期望中涉及章节数的地方：eval 1 `"CLAUDE.md contains all five headings: 技术栈, 命令, 代码风格, 禁止文件, 审查规则"`；eval 2 `"AGENTS.md now contains the previously-missing headings: 命令, 代码风格, 禁止文件, 审查规则"`；eval 4 `"The section mentions `memory.py check` and the 24 KB / 300-character limits"`。

仓库约定：技能文档之间按**标题名**引用章节，不按编号，`make check` 会查失效链接和编号引用。

## Commands you will need

| Purpose           | Command                                                                                    | Expected on success      |
| ----------------- | ------------------------------------------------------------------------------------------ | ------------------------ |
| 脚本测试          | `python3 skills/bootstrap-claude/scripts/test_setup_context.py`                            | `test_setup_context: ok` |
| 记忆脚本测试      | `python3 skills/bootstrap-claude/scripts/test_memory.py`                                   | `test_memory: ok`        |
| 文档链接检查      | `make check`                                                                               | exit 0                   |
| evals.json 合法性 | `python3 -I -c "import json; json.load(open('skills/bootstrap-claude/evals/evals.json'))"` | exit 0                   |
| 模板章节数        | `grep -c '^## ' skills/bootstrap-claude/assets/CLAUDE.template.md`                         | `8`                      |

## Suggested executor toolkit

- 若环境里有 `writing-for-agents` 技能（`~/.claude/skills/writing-for-agents/SKILL.md`），写提示注释和约定正文前读一遍它的「Pruning」与「Leading words」两节：用正向措辞写目标行为，不堆禁止句。

## Scope

**In scope**:

- `skills/bootstrap-claude/assets/CLAUDE.template.md`
- `skills/bootstrap-claude/references/bootstrap.md`（Step 2 取证清单；Compatibility 节末新增一小节）
- `skills/bootstrap-claude/references/maintain.md`（compound 步骤；表格一行）
- `skills/bootstrap-claude/scripts/setup_context.py`（仅 `REQUIRED_SECTIONS` 与 `SECTION_ALIASES` 两处常量）
- `skills/bootstrap-claude/scripts/test_setup_context.py`（仅 `BASE` / `BASE_EN` 常量）
- `skills/bootstrap-claude/evals/evals.json`（仅与章节数、约定正文相关的期望）

**Out of scope**:

- `assets/PROJECT_MEMORY.template.md` —— 记忆文件的四节不变。
- `scripts/memory.py` —— 门槛数值与检查逻辑不变。
- `SKILL.md` —— 入口说明已经写明「结束前必须过 `scripts/memory.py check`」，这是对装了技能的会话说的，不矛盾。
- `evals/files/**` 夹具 —— 不要为新章节改夹具；eval 跑的时候由 agent 填。
- 把模板改成英文，或增加英文模板。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `bootstrap-claude`。示例：`feat(bootstrap-claude): convention v3 — drop home path, add 导航/工作流与陷阱 sections, promote recurring pitfalls`。
- 未经操作者指示不要提交、不要推送。

## Steps

### Step 1: 改模板正文并升到 v3

编辑 `assets/CLAUDE.template.md`：

1. 在「## 技术栈」块之后、「## 命令」之前插入：

```markdown
## 导航

<!-- 代码放在哪、开工前先读哪份文档、怎么搜（大仓库限定目录或用专用索引工具，而不是全仓 grep）、哪些子目录有自己的 CLAUDE.md / AGENTS.md。单包小仓库写一行即可。 -->

- _待填写_
```

2. 在「## 命令」块之后、「## 代码风格」之前插入：

```markdown
## 工作流与陷阱

<!-- 每条写做法 + 原因。需用户确认才能做的操作（推送、开 PR、跑付费 CI、改生产配置）；慢命令把输出重定向到文件再选读，不用管道过滤；按改动范围选构建 / 测试变体；检出过旧先同步；踩过的坑及其原因。 -->

- _待填写_
```

3. 第 49 行改为：

```markdown
- 同主题已有条目就改写它，不追加；结论被推翻就删旧条。写不进两行的长期知识搬进 docs/ 后只留一行指针；反复出现或每次会话都要先知道的陷阱，晋升到本文件「工作流与陷阱」后从记忆里删掉。
```

4. 第 50 行改为（去掉 `~/.claude/...` 路径，保留 `memory.py check` 子串）：

```markdown
- 结束前核对门槛：全文 ≤ 24 KB，单行 ≤ 300 字符，改写节各一块。装了 bootstrap-claude 技能的会话用它的 `scripts/memory.py check` 校验，`compact` 只压改写节；追加节条目由人合并或搬出，脚本不自动删。
```

5. 末行标记改为 `<!-- bootstrap-claude convention v3 -->`。

**Verify**: `grep -c '^## ' skills/bootstrap-claude/assets/CLAUDE.template.md` → `8`；`grep -n '~/.claude' skills/bootstrap-claude/assets/CLAUDE.template.md` → 无命中；`grep -n 'convention v3' skills/bootstrap-claude/assets/CLAUDE.template.md` → 1 处。

### Step 2: 登记两个新必填章节

`setup_context.py`：

- `REQUIRED_SECTIONS = ["技术栈", "导航", "命令", "工作流与陷阱", "代码风格", "禁止文件", "审查规则"]`（顺序与模板一致）。
- `SECTION_ALIASES` 加两条：

```python
    "导航":       ["导航", "navigation", "repo map", "where things live", "architecture", "directory layout"],
    "工作流与陷阱": ["工作流与陷阱", "工作流", "陷阱", "workflow", "gotchas", "pitfalls"],
```

`test_setup_context.py`：`BASE` 里补 `## 导航\n- src/\n\n## 工作流与陷阱\n- push 前先问\n\n`（放在 `## 命令` 块前后都行）；`BASE_EN` 补 `## Repo Map\n- src/\n\n## Workflow\n- ask before push\n\n`。

**Verify**: `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。特别留意第 36-38 行那个用例（v1 标记块自动升级）仍通过，说明 v3 正文能被 `convention_state` 识别为最新且含 `memory.py check`。

### Step 3: `bootstrap.md` Step 2 补取证来源，Compatibility 节末加「子目录指令文件」

在 `bootstrap.md` Step 2 的列表里（第 38-47 行）按模板顺序插入两条：

```markdown
- **导航** — top-level directory layout; the docs maintainers say to read first
  (`ARCHITECTURE.md`, `docs/` entry points, `CONTRIBUTING.md`); existing nested
  instruction files (`find . -name AGENTS.md -o -name CLAUDE.md -not -path './node_modules/*'`);
  any repo-specific search/index tool. A small single-package repo gets one line.
- **工作流与陷阱** — CI config for slow steps and build/test variants; `CONTRIBUTING.md`
  and PR templates for approval gates (what needs a human before it runs: push, publish,
  paid CI, production config); scripts that touch shared state. Every entry carries its
  reason — a rule without a reason reads as arbitrary and gets skipped. New repos
  legitimately start with only the approval-gate line; the rest accrues from incidents
  (see 项目记忆维护 → 晋升).
```

在 Compatibility 节末（第 85 行之后）新增：

```markdown
### Nested instruction files

Claude Code loads a subdirectory's `CLAUDE.md` / `AGENTS.md` on demand when it reads or
edits a file in that directory, and `.claude/rules/*.md` with a `paths:` frontmatter does
the same by glob. Use them for module-specific commands and gotchas in large repos so the
root stays under 200 lines. List in the root 「导航」 section which directories carry their
own file, and open each child file with one line saying the root still applies
(`../AGENTS.md 仍然适用`). Do **not** run `setup_context.py --dir <subdir>` to make one —
it would lay down a full root skeleton plus a second PROJECT_MEMORY.md. Write the child
file by hand.
```

**Verify**: `make check` → exit 0；`grep -n '### Nested instruction files' skills/bootstrap-claude/references/bootstrap.md` → 1 处。

### Step 4: `maintain.md` 加「晋升」步骤

第 22-27 行改为五步：

```markdown
## 怎么写（compound 五步）

1. **筛**：把本次产出过一遍判定问句，留下的通常只有零到三条。
2. **查重与替换**：同主题已有条目就改写它，不追加第二条；结论被推翻就删旧条，不留「已失效」标记堆在旁边。
3. **晋升**：一条失败尝试或事实若每次会话都要先知道，或已第二次命中，它是指令而不是记忆——写进上下文文件的「工作流与陷阱」（做法 + 原因），记忆里删掉。
4. **搬出**：一条长期知识写不进两行时，它已经是文档而不是记忆——搬进 `docs/`（或项目既有的知识目录），记忆里只留一行指针。已完结的旧会话同理压成一行或删除。
5. **改写当前状态**：整块重写「上次会话」和「下次运行」。
```

第 16 行表格「失败尝试」行改为：`| 失败尝试 | 追加 | 走不通的路径和原因，防止下次重走；第二次踩到同一个坑就晋升到上下文文件「工作流与陷阱」 |`。

**Verify**: `grep -rn '四步' skills/bootstrap-claude/` → 无命中（确认没有别处按旧标题引用）；`make check` → exit 0。

### Step 5: 同步 eval 期望

`evals.json`：

- eval 1 `expected_output` 中 "The five sections" 改为 "The seven sections"；expectations 里 `"AGENTS.md contains all five headings: ..."`（Plan 002 已把主语从 CLAUDE.md 改为 AGENTS.md）改为 `"AGENTS.md contains all seven headings: 技术栈, 导航, 命令, 工作流与陷阱, 代码风格, 禁止文件, 审查规则"`；新增一条 `"The 工作流与陷阱 section names at least one operation that needs user confirmation before running (e.g. push / publish) with a reason, or explicitly says 暂无 — not a bare placeholder"`。
- eval 2 expectations 里 `"...previously-missing headings: 命令, 代码风格, 禁止文件, 审查规则"` 改为 `"...previously-missing headings: 导航, 命令, 工作流与陷阱, 代码风格, 禁止文件, 审查规则"`。
- eval 4 expectations 新增两条：`"The 「项目记忆 (回写约定)」 section contains no '~/.claude/' path"`、`"The two v3 sections 导航 and 工作流与陷阱 were appended and are filled or explicitly marked 暂无"`；`expected_output` 末尾补 "The convention marker reads v3."

**Verify**: `python3 -I -c "import json; json.load(open('skills/bootstrap-claude/evals/evals.json'))"` → exit 0；`grep -c 'five headings' skills/bootstrap-claude/evals/evals.json` → 0。

### Step 6: 端到端：旧项目一跑即升级

```sh
rm -rf /tmp/v2proj && mkdir /tmp/v2proj
git show 547eeac:skills/bootstrap-claude/assets/CLAUDE.template.md | sed 's/{{PROJECT_NAME}}/demo/' > /tmp/v2proj/AGENTS.md
python3 skills/bootstrap-claude/scripts/setup_context.py --dir /tmp/v2proj
```

（Plan 002 之后 AGENTS.md 是真源，所以 v2 内容直接放进 AGENTS.md；放进 CLAUDE.md 也行，脚本会先迁移再升级。）

**Verify**: 输出含 `appended missing sections to AGENTS.md: 导航, 工作流与陷阱` 和 `convention: upgraded`；`grep -c 'convention v3' /tmp/v2proj/AGENTS.md` → 1；`grep -c '~/.claude' /tmp/v2proj/AGENTS.md` → 0。两个新章节会出现在**约定块之后**（`ensure_sections` 在 `ensure_convention` 之前运行且追加到文件末尾），这是既有行为、不是 bug：标记仍然正确地界定约定块。

## Test plan

- 现有六个以上用例（含 Plan 001/002 新增）全部通过，证明 v3 正文被识别为 `latest`、v1/v2 标记块自动升级且保留 `memory.py check` 子串。
- Step 6 的端到端手工验证：v2 模板生成的文件一跑即升 v3 并补两节。
- 本计划不新增自动化测试；章节数变化已被 `BASE` 更新后的既有用例覆盖。

## Done criteria

- [ ] `grep -c '^## ' skills/bootstrap-claude/assets/CLAUDE.template.md` → `8`
- [ ] `grep -rn '~/.claude' skills/bootstrap-claude/assets/` → 无命中
- [ ] `grep -n 'convention v3' skills/bootstrap-claude/assets/CLAUDE.template.md` → 1 处
- [ ] `python3 skills/bootstrap-claude/scripts/test_setup_context.py` 打印 `test_setup_context: ok`
- [ ] `python3 skills/bootstrap-claude/scripts/test_memory.py` 打印 `test_memory: ok`
- [ ] `grep -rn '四步' skills/bootstrap-claude/` → 无命中
- [ ] `make check` exit 0
- [ ] Step 6 端到端结果符合预期
- [ ] `git status --porcelain` 只列出 in-scope 六个文件（加 `plans/README.md`）
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- `CLAUDE.template.md` 或 `maintain.md` 与摘录不一致。
- `setup_context.py` 里没有 `SECTION_ALIASES`（Plan 001 未落地）。
- Step 2 之后第 36-38 行的用例失败且错误是 `"memory.py check" not in t`：说明你改掉了约定正文里的这个子串，恢复措辞而不是改测试。
- `make check` 报编号引用或失效链接，且修复需要改 out-of-scope 文件。

## Maintenance notes

- 对已初始化项目追加的新章节落在文件末尾，即约定块之后；想让它们回到正文顺序只能手工挪。要改这一点得让 `ensure_sections` 在约定块之前插入，本计划没做。
- 以后每次改约定正文都要把标记号加一；只改 HTML 提示注释不用（`_norm_body` 比对的是整段正文，注释也算，所以改注释同样要升号——这是现有行为，审阅者注意）。
- 审阅重点：新两节的提示注释是否用正向措辞；「工作流与陷阱」会不会被填成命令清单的重复（它要的是做法 + 原因，不是命令本身）。
- 新仓库的「工作流与陷阱」常只有一条授权边界，这是正常的；内容靠「晋升」步骤从记忆里长出来。
- 已推迟：`--validate` 不检查条目是否带原因；要做也只能靠 eval 评审，不靠脚本。
- 已推迟：子目录指令文件的脚本支持（`--nested`）。先用 Step 3 的手写指引，等出现真实需求再谈。
