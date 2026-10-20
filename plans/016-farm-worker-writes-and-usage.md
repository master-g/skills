# Plan 016: farm 在 Claude Code 下按转录核对每个 worker 实际写了哪些文件，并汇报 worker 用量

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat a05d72d..HEAD -- skills/farm/SKILL.md skills/farm/references/claude-code-worker.md skills/farm/references/pool.md AGENTS.md`
> 预期无输出。有输出就把下面「Current state」的摘录与现行文件对照；对不上即为 STOP 条件。`skills/farm/subagent.py` 和 `skills/farm/test_subagent.py` 应当还不存在。

## Status

- **Priority**: P2
- **Effort**: M（两个新文件从附件复制，四份文档各改一到三处）
- **Risk**: MED（依赖 Claude Code 未公开的转录格式；脚本按「读不全就算失败」设计，见「Why this matters」）
- **Depends on**: none（与 015 改的文件不重叠，顺序任意）
- **Category**: bug
- **Planned at**: commit `a05d72d`, 2026-10-20

## Why this matters

本仓库是 Agent Skills 约定的 Markdown 技能文档仓库，每个技能是 `skills/<name>/`，agent 读 `SKILL.md` 照做。`farm` 技能让当前模型（orchestrator）把实现任务派给更便宜的 worker，再独立验收。在 Claude Code 里，worker 是用 Agent 工具起的后台子代理；任务能拆开时，几个 worker 同时改同一个工作树，每个只负责自己那批文件（「池」）。

这里有两个缺口：

1. **越界写入查不出来。** `SKILL.md` 规定通过的条件之一是「diff 在边界内」，但池里审计某个 worker 时，别的 worker 还在改工作树，所以 `references/pool.md` 只看 `git diff --stat -- <负责文件>`。一个 worker 改了边界外的文件，审计看不到；只能等最后的整体验收碰巧失败。Claude Code 给每个子代理单独存了一份转录 `~/.claude/projects/<项目>/<会话>/subagents/agent-<agent ID>.jsonl`，里面每次 Edit / Write 调用都带 `file_path`。按转录列出 worker 实际写过的文件，和它的边界比对，就能把越界写入归到具体的 worker。
2. **不知道派活省了多少。** farm 的出发点是把活交给便宜的模型，但汇报里没有 worker 的用量。同一份转录的每条助手消息都带 `usage`；按消息 id 去重后求和，就是这个 worker 的累计 token 消耗。

转录格式是 Claude Code 的内部格式，官方没有承诺不变。格式一变，脚本可能一条写入也读不到，看起来像「没有越界」，实际上根本没查。所以附件脚本把「读不全」当失败：一次工具调用都没读到、读到的次数和完成通知里的 `<tool_uses>` 对不上、或者 worker 又派了子代理（那些子代理的写入不在这份转录里），都返回退出码 2，该 worker 不能判为通过。另外在集成门禁加一道不依赖转录的 `git status` 核对，作为转录失效时的兜底。

advisor 在临时目录里验证过：附件测试 `test_subagent.py` 通过；拿本机一个真实子代理的转录（2026-10-14 执行 plan 007 的 sonnet worker）运行，读到 39 次工具调用，与它的完成通知 `<tool_uses>39</tool_uses>` 一致；按消息 id 去重后的用量是 input 54、cache_creation 66,857、cache_read 1,420,313、output 11,555。同一份完成通知里的 `<subagent_tokens>69354</subagent_tokens>` 只是结束时的上下文大小，不是累计消耗，所以用量只取脚本的 `usage`。

2026-10-20 执行 plan 015 的 sonnet 执行者给出了另一面：它的全部改动都用 Bash 完成（`cp` 一份脚本、python heredoc 改文档），转录核对读到 4 次工具调用、与完成通知一致，但 `written` 为空、退出码 0，三条写文件的命令只出现在 `bash_writes`。所以退出码 0 本身不等于没有越界：`bash_writes` 不为空时必须逐条核对，Step 2 的门禁文字按这个写。完成通知到达时转录已经写全，这次没有用到重跑。

## Current state

- `skills/farm/SKILL.md`（145 行）：六步流程。第 130–137 行是「汇报与下一步」：

```markdown
## 6. 汇报与下一步

向用户汇报：

- 每个子任务的状态（通过 / 升级）和用掉的修正轮次。
- 改动摘要（git 仓库用 `git diff --stat`）和门禁的实际输出。
- 限制：没运行的检查、worker 报告里的未决问题。
- 下一步建议：只列本次结果直接引出的事项，例如升级项需要用户决定什么、通过的改动是否提交、方案里还没派发的部分。
```

- `skills/farm/references/claude-code-worker.md`（50 行）：Claude Code 后端。要改的是「派发」一节的第 1、2、4 步，并在文件末尾加一节：
  - 第 34 行（第 1 步，整行）：

```markdown
1. 核对项目目录与未提交改动，按 SKILL.md 的 brief 模板把 brief 写入 `<项目绝对路径>/.farm/<task>-brief.md`。补充负责的文件、已有改动，并告诉 worker：你不是唯一修改代码的代理，保留他人改动并适配它们。brief 和报告一律用绝对路径，会话的工作目录可能已被切换。
```

- 第 42 行（第 2 步示例 JSON 里的 `prompt`，整行）：

```json
  "prompt": "在 /absolute/project 工作。读 /absolute/project/.farm/<task>-brief.md 并执行，报告按其中要求落盘。你负责 brief 指定的文件与模块。你不是唯一修改代码的代理，请保留他人改动并适配它们。"
```

- 第 47 行（第 4 步，整行）：

```markdown
4. 收到通知后按 SKILL.md「门禁」：读报告，看实际 diff，独立重跑验收命令。代理的最终回复只是自述，不算验收。报告缺失时以代理的最终回复作现场。
```

- 第 50 行（文件最后一行）：

```markdown
子代理沿用当前会话的权限设置。worker 因审批被拒或越界而停止时，按 SKILL.md「门禁」的报告缺失或升级给用户处理。
```

- `skills/farm/references/pool.md`（34 行）：k ≥ 2 个子任务时的派发与门禁。要改的三行：
  - 第 13 行：

```markdown
再写 `.farm/<task>-plan.md`：子任务表（编号、负责文件、验收命令）和整体验收命令。
```

- 第 23–25 行（「审计」一节的三步）：

```markdown
1. 读 `.farm/<task>-<i>-report.md`，缺失时同 SKILL.md「门禁」处理。
2. `git diff --stat -- <负责文件>`。
3. 独立重跑子 brief 的验收命令。
```

- 第 31 行（「集成门禁」一节第一段）：

```markdown
全部子任务通过审计、且没有修正轮次在运行时，独立运行 plan 里的整体验收命令。
```

- `AGENTS.md` 第 32 行（「命令」一节）：

```markdown
- 测试: 无统一测试；带脚本的技能自带 `python3 skills/<name>/scripts/test_*.py`（如 bootstrap-claude 的 `test_setup_context.py`、`test_memory.py`，各打印 `…: ok`）
```

- 附件（`plans/016-farm-worker-writes-and-usage/`）：
  - `subagent.py`：只用 Python 标准库。用法 `python3 subagent.py <agent ID> [--root DIR] [--allow PATTERN]... [--tool-uses N]`。在 `${CLAUDE_CONFIG_DIR:-~/.claude}/projects/*/*/subagents/agent-<agent ID>.jsonl` 找转录（必须恰好一个），打印一个 JSON：`transcript`、`model`、`tool_uses`、`written`（Edit / Write / NotebookEdit 写过的文件，在 `--root` 内的写成相对路径）、`outside`（没有任何 `--allow` 匹配的写入；`.farm/` 和系统临时目录总是放行，`--root` 之外的其他路径总是越界）、`bash_writes`（疑似写文件的 Bash 命令，前 200 字符）、`bash_total`、`nested`（Agent 调用次数）、`usage`（四项 token 按消息 id 去重后求和）。退出码：0 正常；1 找不到转录或不止一个；2 核对不完整（没读到工具调用、与 `--tool-uses` 不符、有嵌套 Agent 调用）；3 有越界写入。`--allow` 的匹配：等于该路径、在该目录下、或 `fnmatch` 匹配。
  - `test_subagent.py`：脚本式 assert 测试（仓库没装 pytest），在临时目录里造转录、设 `CLAUDE_CONFIG_DIR` 运行 `subagent.py`，结尾打印 `test_subagent: ok`。

仓库约定：

- Python 脚本只用标准库，测试是 `python3 test_*.py` 直接运行、结尾打印 `…: ok`，参照 `skills/bootstrap-claude/scripts/test_memory.py`。farm 的脚本放在技能根目录（与 `preflight.sh`、`headless.sh` 同级），新文件也放那里。
- `claude-code-worker.md`、`pool.md`、`SKILL.md` 正文用全角标点（`，` `：` `（` `）`）；改动处保持全角。章节引用写标题名（如「门禁」），不写「第 N 节」，`make check` 会拦。技能文档用正向措辞写默认做法（`AGENTS.md`「代码风格」）。

## Commands you will need

| Purpose  | Command                                                                                                                           | Expected on success                          |
| -------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| 单元测试 | `python3 skills/farm/test_subagent.py`                                                                                            | 最后一行 `test_subagent: ok`                 |
| 用法     | `python3 skills/farm/subagent.py --help`                                                                                          | exit 0，打印用法                             |
| 文档门禁 | `make check`                                                                                                                      | exit 0                                       |
| 格式化   | `npx prettier --write skills/farm/SKILL.md skills/farm/references/claude-code-worker.md skills/farm/references/pool.md AGENTS.md` | exit 0                                       |
| 格式检查 | `npx prettier --check skills/farm/SKILL.md skills/farm/references/claude-code-worker.md skills/farm/references/pool.md AGENTS.md` | `All matched files use Prettier code style!` |

## Scope

**In scope**（只改这些文件）：

- `skills/farm/subagent.py`（新建，从附件复制）
- `skills/farm/test_subagent.py`（新建，从附件复制）
- `skills/farm/references/claude-code-worker.md`（第 34、42、47 行，末尾加一节）
- `skills/farm/references/pool.md`（第 13、25、31 行）
- `skills/farm/SKILL.md`（「汇报与下一步」加一条）
- `AGENTS.md`（第 32 行）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**（看着相关，但不要碰）：

- `references/cli-worker.md`、`references/app-worker.md`：pi、codex 和 Codex App 的转录格式不同，这次只做 Claude Code 后端（维护者 2026-10-20 决定）。它们的用量写「未统计」，由 SKILL.md 新加的那一条覆盖。
- `skills/farm/SKILL.md` 的 brief 模板和「门禁」：通过条件「diff 在边界内」不变，新检查是落实它的手段。
- `skills/farm/headless.sh`、`preflight.sh`、`pairs`：属于 plan 015 或与本计划无关。
- 不把金额换算写进任何文件：价格会变，用量按原始 token 数报告。
- `PROJECT_MEMORY.md`：合并时由维护者回写。

## Git workflow

- 分支：`advisor/016-farm-worker-writes-and-usage`。
- 提交信息用 conventional commits，scope 写技能名（仓库已有的例子：`feat(farm): Claude Code native subagent workers, opus-5.5 → sonnet-5.5 pair`）。一个提交：`feat(farm): check each Claude Code worker's written files from its transcript, report token usage`。
- pre-commit 会跑 prettier 和 `make check`；prettier 可能重排表格对齐，属于预期。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`（合并后由维护者装到本机）。

## Steps

### Step 1: 加入脚本和测试

```sh
cp plans/016-farm-worker-writes-and-usage/subagent.py skills/farm/subagent.py
cp plans/016-farm-worker-writes-and-usage/test_subagent.py skills/farm/test_subagent.py
```

**Verify**:

- `python3 skills/farm/test_subagent.py` → 最后一行 `test_subagent: ok`
- `python3 skills/farm/subagent.py --help` → exit 0，第一行以 `usage: subagent.py` 开头
- `python3 skills/farm/subagent.py no-such-agent; echo $?` → stderr 含 `找到 0 个`，最后打印 `1`（fish 下用 `echo $status`）

### Step 2: claude-code-worker.md：边界写法、worker 提示、门禁接入

第 34 行整行替换为：

```markdown
1. 核对项目目录与未提交改动，按 SKILL.md 的 brief 模板把 brief 写入 `<项目绝对路径>/.farm/<task>-brief.md`。补充负责的文件、已有改动，并告诉 worker：你不是唯一修改代码的代理，保留他人改动并适配它们。brief 和报告一律用绝对路径，会话的工作目录可能已被切换。「边界」的可改范围写成相对项目根的路径、目录或 glob，逐项列出，审计时原样传给 `subagent.py` 的 `--allow`。
```

第 42 行整行替换为（只在「你负责 brief 指定的文件与模块」后加一句「所有改动由你亲自完成」，让 worker 的写入都留在它自己的转录里）：

```json
  "prompt": "在 /absolute/project 工作。读 /absolute/project/.farm/<task>-brief.md 并执行，报告按其中要求落盘。你负责 brief 指定的文件与模块，所有改动由你亲自完成。你不是唯一修改代码的代理，请保留他人改动并适配它们。"
```

第 47 行整行替换为：

```markdown
4. 收到通知后按 SKILL.md「门禁」：读报告，看实际 diff，按下文「核对实际写入与用量」读 worker 的转录，独立重跑验收命令。代理的最终回复只是自述，不算验收。报告缺失时以代理的最终回复作现场。
```

在文件末尾（第 50 行之后，空一行）追加下面整段：

````markdown
## 核对实际写入与用量

每个 worker 结束后、判定通过之前，用本技能目录（与 SKILL.md 同目录，下文记作 `<skill>`）下的 `subagent.py` 读它的转录：

```sh
python3 '<skill>/subagent.py' <agent ID> --root <项目绝对路径> --allow <可改项> --allow <可改项> --tool-uses <N>
```

`--allow` 逐项取 brief「边界」的可改范围；`<N>` 取完成通知 `<usage>` 里的 `<tool_uses>`。脚本打印 JSON，按退出码处理：

| 退出码 | 含义                                        | 动作                                                                                       |
| ------ | ------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 0      | Edit / Write 的写入都在边界内               | `bash_writes` 为空才继续 SKILL.md「门禁」；不为空先按下一段逐条核对                        |
| 3      | `outside` 列出了越界写入的文件              | 该子任务升级给用户，附 `outside` 列表；越界文件交给用户处理，它们可能正属于另一个 worker   |
| 1 或 2 | 找不到转录，或核对不完整（stderr 写明原因） | 隔几秒重跑一次（转录可能还没写完）；仍是 1 或 2，该子任务升级给用户，附 stderr，不判为通过 |

`bash_writes` 是 Bash 里疑似写文件的命令。worker 常用 `cp`、`sed -i`、heredoc 脚本改文件，这些写入不进 `written`：清单不为空时逐条看它写到哪里，写到边界外按退出码 3 处理；拿不准的命令，用 `git diff --stat -- <可改项>` 对照这个 worker 负责的文件。逐条看完才算核对完成。

转录是 Claude Code 的内部格式，没有公开承诺，升级后可能变化。脚本把读不全当成失败：读不到工具调用、次数与完成通知不符、worker 又派了子代理，都返回 2。

用量：汇报时每个 worker 列出 JSON 里的 `model`、`usage` 的四项 token 数（input、cache_creation_input、cache_read_input、output）和完成通知里的 `<duration_ms>`，按原始数字报告。累计消耗只取 `usage`；完成通知的 `<subagent_tokens>` 是结束时的上下文大小。
````

**Verify**:

- `grep -c '所有改动由你亲自完成' skills/farm/references/claude-code-worker.md` → `1`
- `grep -c '核对实际写入与用量' skills/farm/references/claude-code-worker.md` → `2`（第 4 步的引用、新节标题）
- `grep -c 'subagent.py' skills/farm/references/claude-code-worker.md` → `3`
- `tail -1 skills/farm/references/claude-code-worker.md` → 以 `用量：` 开头

### Step 3: pool.md：基线、审计接入、集成门禁兜底

从文件下方往上改，行号才不会被前面的插入挪动。三处按下面的顺序做。

第 31 行（「集成门禁」一节第一段，原文以 `全部子任务通过审计、且没有修正轮次在运行时` 开头）整行替换为：

```markdown
全部子任务通过审计、且没有修正轮次在运行时，先核对整体改动：再跑一次 `git status --porcelain --untracked-files=all`，去掉基线里已有的行和 `.farm/` 下的路径，剩下的每个路径都必须属于某个子任务的负责文件。有不属于任何子任务的路径，就保留现场，带这些路径升级给用户。这一步不依赖后端，转录核对失效时由它兜底；基线里已有改动的文件，后来又被谁改过，这一步分辨不出。核对通过后，独立运行 plan 里的整体验收命令。
```

在第 25 行（`3. 独立重跑子 brief 的验收命令。`）之后插入一行：

```markdown
4. 后端文件有「核对实际写入与用量」一节的（目前是 Claude Code 后端），按它核对这个 worker 实际写过的文件；越界或核对不完整都不判为通过。
```

第 13 行（原文以「再写 `.farm/<task>-plan.md`：子任务表」开头）整行替换为：

```markdown
再写 `.farm/<task>-plan.md`：子任务表（编号、负责文件、验收命令）、整体验收命令，以及派发前 `git status --porcelain --untracked-files=all` 的输出（基线）。
```

**Verify**:

- `grep -c 'untracked-files=all' skills/farm/references/pool.md` → `2`
- `grep -c '^4\. 后端文件有「核对实际写入与用量」' skills/farm/references/pool.md` → `1`
- `sed -n 23,26p skills/farm/references/pool.md` → 依次以 `1.`、`2.`、`3.`、`4.` 开头

### Step 4: SKILL.md：汇报里加用量

在「汇报与下一步」的 `- 改动摘要（git 仓库用 \`git diff --stat\`）和门禁的实际输出。` 这一行之后插入：

```markdown
- 每个 worker 的模型、token 用量和耗时：后端文件写了取法的按它取（Claude Code 后端见 [Claude Code 原生 worker 用例](references/claude-code-worker.md)「核对实际写入与用量」），其他后端写「未统计」。
```

**Verify**:

- `grep -c '每个 worker 的模型、token 用量和耗时' skills/farm/SKILL.md` → `1`
- `sed -n 134,138p skills/farm/SKILL.md` → 第三行是新加的这一条

### Step 5: AGENTS.md：登记测试命令

第 32 行替换为：

```markdown
- 测试: 无统一测试；带脚本的技能自带 `python3 skills/<name>/scripts/test_*.py`（如 bootstrap-claude 的 `test_setup_context.py`、`test_memory.py`，各打印 `…: ok`）；farm 的脚本在技能根目录，测试是 `python3 skills/farm/test_subagent.py`
```

**Verify**: `grep -c 'skills/farm/test_subagent.py' AGENTS.md` → `1`

### Step 6: 格式化、门禁、提交

```sh
npx prettier --write skills/farm/SKILL.md skills/farm/references/claude-code-worker.md skills/farm/references/pool.md AGENTS.md
make check
python3 skills/farm/test_subagent.py
```

**Verify**:

- `npx prettier --check skills/farm/SKILL.md skills/farm/references/claude-code-worker.md skills/farm/references/pool.md AGENTS.md` → `All matched files use Prettier code style!`
- `make check` → exit 0
- `git status --short` → 只有 Scope 里的文件（两个新文件显示为 `??`）

然后按「Git workflow」提交，把 `plans/README.md` 里 016 的状态改成 `DONE（<commit>）`。

## Test plan

- 新测试：`skills/farm/test_subagent.py`（从附件复制），结构参照 `skills/bootstrap-claude/scripts/test_memory.py`。它在临时目录里造转录并覆盖：同一条消息拆成多行时 `usage` 只算一次；Edit / Write 的路径转成相对路径；`.farm/` 下的报告与系统临时目录里的写入放行；`--allow` 目录前缀匹配；边界外写入返回 3；Bash 命令里 `sed -i` 进 `bash_writes`、`git status 2>&1 | tail` 不进；`--tool-uses` 不符返回 2；没有工具调用返回 2；嵌套 Agent 调用返回 2；`--root` 之外又不在临时目录的写入，`--allow '*'` 也判越界；找不到转录返回 1；转录末尾写到一半的行被跳过。
- 运行：`python3 skills/farm/test_subagent.py` → `test_subagent: ok`。
- 可选的真实数据检查（不进 done criteria）：在跑过 Claude Code 子代理的机器上，`ls ~/.claude/projects/*/*/subagents/agent-*.jsonl | head -1` 取一个 agent ID（文件名去掉 `agent-` 和 `.jsonl`），运行 `python3 skills/farm/subagent.py <ID> --root <它当时的项目目录>`，应能打印 JSON 且 `tool_uses` 大于 0。

## Done criteria

- [ ] `python3 skills/farm/test_subagent.py` 最后一行 `test_subagent: ok`
- [ ] `cmp plans/016-farm-worker-writes-and-usage/subagent.py skills/farm/subagent.py` 无输出
- [ ] `grep -c '核对实际写入与用量' skills/farm/references/claude-code-worker.md` 为 `2`；`grep -c 'untracked-files=all' skills/farm/references/pool.md` 为 `2`；`grep -c '每个 worker 的模型、token 用量和耗时' skills/farm/SKILL.md` 为 `1`；`grep -c 'skills/farm/test_subagent.py' AGENTS.md` 为 `1`
- [ ] `make check` exit 0；Step 6 的 prettier 检查通过
- [ ] `git status --short` 只有 Scope 里的文件
- [ ] `plans/README.md` 里 016 的状态行已更新

## STOP conditions

停下汇报，不要自行发挥：

- Drift check 有输出，且「Current state」的摘录与现行文件对不上；或 `skills/farm/subagent.py` 已经存在。
- `test_subagent.py` 失败，复制附件重跑一次仍失败。不要改附件让它通过；把完整输出贴进汇报。
- `make check` 报「按编号引用章节」：说明新增文字里有「第 N 节」写法，改成标题名后重跑；改完仍报就停。
- 需要改 Scope 之外的文件，或觉得应该把核对推广到 CLI / App 后端：停下，那是维护者另行决定的事。

## Maintenance notes

- **转录格式会变。** Claude Code 每周发多个版本，转录 `~/.claude/projects/*/*/subagents/agent-*.jsonl` 不是公开接口。出问题的表现是 `subagent.py` 频繁返回 2（读到 0 次或次数与完成通知不符）。那时先看一份新转录的 `assistant` 行结构，改 `subagent.py` 的 `read()`，再在 `test_subagent.py` 里补一份新格式的样例。集成门禁的 `git status` 核对不依赖转录，在此期间仍然有效。
- 用到的字段：每行 JSON 的 `type == "assistant"`、`message.id`、`message.model`、`message.usage` 的四个键、`message.content[]` 里 `type == "tool_use"` 的块（`id`、`name`、`input.file_path` / `input.notebook_path` / `input.command`）。另外依赖完成通知 `<usage>` 里的 `<tool_uses>` 和 `<duration_ms>`。
- 只读 Edit / Write 的核对覆盖不了用 Bash 改文件的 worker（见「Why this matters」里 2026-10-20 的实例）。以后若要把 Bash 写入也自动判定，比较可靠的做法是让 worker 在报告里列出改动文件、由 orchestrator 用 `git diff --stat` 逐个对照，而不是继续加正则。
- `bash_writes` 的正则是粗筛（`>`/`>>` 重定向、`tee`、`sed -i`、`perl -i`、`mv`/`cp`/`rm`/`mkdir`/`touch`/`ln`/`patch`/`truncate`、会改工作树的 git 子命令、`--write`、包管理器安装、heredoc）。通过 Bash 写到别的 worker 边界里的文件，只能靠人看这份清单；写到所有边界之外的，集成门禁的 `git status` 核对能抓到。
- 以后给 CLI 后端（pi）或 Codex App 后端加同样的核对，需要各自的转录读取方式；`pool.md` 第 4 步已经写成「后端文件有这一节的就按它做」，不必再改 `pool.md`。
- 审阅时重点看：`claude-code-worker.md` 新节的退出码表与 `subagent.py` 的退出码一致；升级时没有让 worker 回滚越界文件。
