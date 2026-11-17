# Plan 034: bootstrap-claude 记忆条目消失时要交代去向，规则先进指令文件

> **Executor instructions**: 按 Step 1 到 Step 7 的顺序执行，每一步跑完验证命令并确认预期结果后再进下一步。每一步是一个独立的提交，做完任何一步都可以停。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**：`git diff --stat 2fec56b..HEAD -- skills/bootstrap-claude`
> 预期无输出。有输出就把「Current state」的摘录与现行文件逐段对照；对不上即为 STOP 条件。

## Status

- **Priority**: Step 1–3、Step 5 是 P1，Step 4、Step 6 是 P2，Step 7 是 P3
- **Effort**: M（Step 2 的核心函数和测试以附件提供并验证过；Step 1 的夹具和 Step 3、4 的文字由执行者按规格写）
- **Risk**: MEDIUM。Step 2 让 `memory.py check` 多一类 FAIL。本机另有仓库的提交钩子调用安装副本，`make install` 之后它们立刻用上新检查
- **Depends on**: 无
- **Category**: dx、docs
- **Planned at**: commit `2fec56b`, 2026-11-17

## Why this matters

2026-11-17 维护者担心写进 `PROJECT_MEMORY.md` 的规则没有及时移进指令文件，之后在压缩时丢失，要求分析并给出实施方案。调查用本机 5 个记忆文件贴着 24 KB 的仓库的 Git 历史做了实测，结论如下，每条注明性质。

1. **条目的消失集中在撞线时（实测）。** 迁移类提交除外，文件 ≥21.6 KB 时每次提交消失 0.35 条追加节条目，更小时 0.07 条。5 个仓库里有 1 个两档无差别。
2. **进指令文件的少（实测，样本不随机）。** 59 条消失的规则性条目里，脚本给 21 条找到去向。从其余 38 条挑 20 条按关键词手核：6 条在 AGENTS.md，7 条仍在记忆（被并改），6 条只在 docs，1 条部分找不到。
3. **去向无法核对（读代码确认）。** `memory.py check` 只查体积、行宽和改写节块数。`maintain.md` 的「追加类小节原有条目一条不少」只是文字。
4. **超限路径里没有晋升（读文档确认）。** `maintain.md` 的「完成标准」和 `memory.py` 的两处提示只写合并和搬出。
5. **晋升的条件没人计数（读文档确认）。** 条件是「每次会话都要先知道，或已第二次命中」，没有地方记命中次数。
6. **`bootstrap.md` 给的溢出去处压缩后不保留（对照官方文档确认）。** 它建议根文件超 200 行时搬进子目录文件或带 `paths:` 的规则。Claude Code 文档 `context-window.md` 写明这两类在上下文压缩后会被摘要掉，只有项目根 CLAUDE.md 和不带 `paths` 的规则从磁盘重新注入。
7. **门禁只在有人运行时生效（实测）。** 本机 12 个有记忆文件的仓库里，只有 2 个的提交钩子会跑 `memory.py check`。3 份超过 24 KB 的记忆文件所在的仓库都没有。本仓库也没有。

本计划做两件事。让「条目消失」变成可核对的：每条消失的条目都要在记忆文件里留一行去向，脚本检查。让规则在写入时就分流：每次都要照做的规则不进记忆。前者由脚本保证，后者只能靠文字，所以用 eval 验收。脚本检查要在提交时自动运行才算保证，所以本仓库的 pre-commit 加上它，初始化文档给出其他仓库的写法。

### 维护者的要求

- 2026-11-17 维护者看过调查结论和四项建议后，要求「制定一个实施方案」。四项是：消失的条目要有去向并由脚本核对；规则写入时先分流；超限时先晋升；补 eval。维护者没有逐条确认，下面一节的取舍都可以改。

### 制定计划时自行定下的（维护者可改）

- **去向写在「上次会话」那一块里**，每条一行 `移出：<条目开头> → <去向>`。这一节每次会话整块改写，所以声明只占当次的体积，历史在 Git 里（`git log -p -S'移出：' -- PROJECT_MEMORY.md`）。不需要新增小节，已有的记忆文件不用迁移。
- **没交代去向是 FAIL，不是警告。** 警告在收尾时最容易被跳过，调查里的问题正是出在收尾。
- **相似度 ≥0.5 算同一条的改写，不用声明。** 从历史里相似度 0.5–0.7 的 88 对中随机抽 30 对手标，全部是同一条的改写；另一次抽的 6 对里有 1 对是不同的事实。合计 36 对里 35 对判对。
- **去向文件的内容核验只设 5% 的关键词下限。** 手核确认已晋升的 6 条，对所在 AGENTS.md 的关键词覆盖率是 7%–42%，因为规则写进指令文件时会改述。304 条消失的条目（其中含已晋升的）对同一提交的 AGENTS.md 的覆盖率中位数是 0，p95 是 13%。门槛定高会把正确的晋升判成 FAIL，所以只拦「去向文件里完全没有这条」。
- **不按措辞自动识别规则。** 本仓库记忆里带「必须、不要、用户确认」的 14 条，逐条看只有约 2 条是每次要照做的规则，其余是决定和测量结果。
- **`setup_context.py --validate` 不跑去向检查。** 它是初始化后的只读验收，没有「上一次提交」这个基线的语义。
- **不让 `setup_context.py` 自动装提交钩子。** 各仓库的钩子体系不同（husky、pre-commit 框架、lefthook、裸 `.git/hooks`），改钩子会影响那个仓库的每一次提交，应当由那个仓库的人决定。本计划只在本仓库加钩子，并在 `bootstrap.md` 里写明做法，由执行初始化的 agent 向用户提出。
- **Step 7 在本仓库实际晋升两条 worktree 条目。** 作为新流程的真实验证，提交时也会经过 Step 6 加的钩子。维护者不想动本仓库记忆的话，删掉 Step 7 即可。
- **不默认 `@PROJECT_MEMORY.md` 导入。** 它保证每次加载，代价是每个会话多约 8 千 token（按 `memory.py` 注释的换算估计）。本机已有一个仓库自行这样做，约定块的结束标记之后可以放这一行。

## Current state

**`skills/bootstrap-claude/scripts/memory.py`**（236 行）

- `check_memory(text, max_bytes, max_line)`（88–113 行）返回 `[(ok, message)]`，`setup_context.py --validate` 也调用它。
- `cmd_check`（125–132 行）打印结果，有 FAIL 时在 stderr 提示：`超限时：先把 上次会话／下次运行 压成一块，再合并同主题事实或搬入 docs/ 留一行指针。`
- `cmd_compact`（140–167 行）末尾的提示：`追加节不自动淘汰：合并同主题条目，或搬入 docs/ 后只留一行指针。`
- `REPLACE_SECTIONS = ["上次会话", "下次运行", "Last Session", "Next Session"]`（27 行）。其余二级小节都按追加节处理。

**`skills/bootstrap-claude/references/maintain.md`**（50 行）

- 「怎么写（compound 五步）」（22–28 行）：筛、查重与替换、晋升、搬出、改写当前状态。晋升的条件是「每次会话都要先知道，或已第二次命中」。
- 「完成标准」（40–50 行）：`超限时按顺序处理：先 … compact …；仍超限就回到「搬出」和「查重与替换」`。末段 `回读本次写入：追加类小节原有条目一条不少（除非本次明确替换或搬出）`。

**`skills/bootstrap-claude/references/bootstrap.md`**

- 75 行：`gates the context file at 200 lines (… move module-specific material into nested files or .claude/rules/, see Nested instruction files)`。
- 「Nested instruction files」（101–110 行）没有提上下文压缩。

**`skills/bootstrap-claude/assets/CLAUDE.template.md`**

- 「项目记忆 (回写约定)」（51–64 行），四条要点，结束标记 `<!-- bootstrap-claude convention v3 -->`。

**`skills/bootstrap-claude/evals/evals.json`**

- 4 条 eval：`bootstrap`、AGENTS.md 已存在、`writeback`、约定升级。没有覆盖晋升和撞线。夹具在 `evals/files/{node-app,go-svc,py-lib}`，都是普通目录，没有 Git。

**附件 `plans/034-bootstrap-claude-memory-removal-gate/`**

- `removal_gate.py`：参考实现，纯函数。`diff_entries(old, new)` 返回改写与消失的条目，`parse_moves(text)` 读 `移出：` 行，`check_removed(old, new, root)` 返回 `[(ok, message)]`，`keep_moves(old_ledger, base, new)` 挑出改写「上次会话」时要保留的声明。
- `test_removal_gate.py`：18 个断言，覆盖四类去向、歧义的锚、一行多个锚、上次会话留下的旧声明、建议的锚避开分隔符号、未提交的声明在改写时保留。
- `replay.py`：在仓库的记忆历史上回放。计划时在 6 个本机仓库上跑过，共 1767 个版本。历史里没有 `移出：` 行，所以有条目消失的 120 个提交必然全部 FAIL，这不是检测正确的证据。回放说明三件事：真实文件都能解析；每次提交要交代的条数中位数是 1，最多 33；Step 2 移植后可以用它核对正式实现与参考实现输出一致。

## 数据形状

- **条目**：追加节里一个顶层 `- ` 及其续行。身份是整条文字。
- **基线**：上一次提交里的 `PROJECT_MEMORY.md`，默认 `git show HEAD:<路径>`。
- **改写**：基线里有、现在没有，但现在有一条新条目与它的相似度 ≥0.5。不用声明。
- **消失**：基线里有、现在没有，也不算改写。每条要有一行声明。
- **声明**：「上次会话」块里的一行 `移出：<锚> → <去向>`。锚是这条条目里的一段原文，在消失的条目中只对上一条。一行可以用 `；` 隔开多个锚，共用一个去向。
- **去向**四类：

| 写法                        | 类别 | 脚本核对什么                                                        |
| --------------------------- | ---- | ------------------------------------------------------------------- |
| `AGENTS.md「工作流与陷阱」` | 晋升 | 文件存在；写了「节名」就要有含该名的标题；文件里有这条 ≥5% 的关键词 |
| `docs/x.md`                 | 搬出 | 同上                                                                |
| `并入 <现存条目的开头>`     | 并入 | 正好对上一条现存条目                                                |
| `作废（原因）`              | 作废 | 原因不少于 4 个字                                                   |

- **未提交的声明**：回写后没有提交时，基线仍是原来的 HEAD，下一次会话改写「上次会话」不能把这些声明冲掉。`add` 改写这一节时，保留仍对得上消失条目的 `移出：` 行。

晋升指去向文件名是 `AGENTS.md`、`CLAUDE.md`，或路径在 `.claude/rules` 下。对不上任何消失条目的声明行忽略不报，因为上一次会话留下的行在提交后就是这种状态。

## Commands you will need

| 用途                 | 命令                                                                                                                          | 预期                                  |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| 记忆脚本测试         | `python3 skills/bootstrap-claude/scripts/test_memory.py`                                                                      | 末行 `test_memory: ok`                |
| 初始化脚本测试       | `python3 skills/bootstrap-claude/scripts/test_setup_context.py`                                                               | 末行 `test_setup_context: ok`         |
| 参考实现的测试       | `python3 plans/034-bootstrap-claude-memory-removal-gate/test_removal_gate.py`                                                 | `test_removal_gate: ok`               |
| 历史回放（参考实现） | `python3 plans/034-bootstrap-claude-memory-removal-gate/replay.py .`                                                          | 退出 0，`skills:` 一行写「全部 PASS」 |
| 历史回放（正式实现） | `PYTHONPATH=skills/bootstrap-claude/scripts python3 plans/034-bootstrap-claude-memory-removal-gate/replay.py --impl memory .` | 同上                                  |
| eval 文件合法        | `python3 -I -c "import json; json.load(open('skills/bootstrap-claude/evals/evals.json'))"`                                    | 退出 0                                |
| 文档门禁             | `make check`                                                                                                                  | 通过                                  |

`test_memory.py` 运行中会打印一行 `ERROR: append-sections take one line per entry`，那是负例的输出。

## Scope

**In scope**：

- `skills/bootstrap-claude/scripts/memory.py`、`scripts/test_memory.py`
- `skills/bootstrap-claude/references/maintain.md`、`references/bootstrap.md`（改 75 行那一句和「Nested instruction files」一节，Mode 1 新增一步提交钩子）
- `skills/bootstrap-claude/assets/CLAUDE.template.md`（只改约定块）、`assets/PROJECT_MEMORY.template.md`（只改「上次会话」的提示注释）
- `skills/bootstrap-claude/scripts/test_setup_context.py`（只在约定块文字变化导致断言失败时改）
- `skills/bootstrap-claude/evals/evals.json`、新增 `evals/files/memory-triage/`、`evals/files/memory-at-cap/`
- 本仓库的 `.husky/pre-commit`、`Makefile`（只改 `check` 目标）
- 本仓库的 `AGENTS.md`（Step 4 的约定块升级，Step 6 对 `make check` 的描述，Step 7 的两条规则）、`PROJECT_MEMORY.md`（Step 7 和收尾回写）
- `plans/README.md`（本计划的状态行和执行记录）、`plans/034-bootstrap-claude-memory-removal-gate/`（eval 结果）

**Out of scope**：

- `setup_context.py` 的逻辑。约定块升级走它现有的标记机制。
- `SKILL.md`。它的入口句「结束前必须过 `scripts/memory.py check`」仍然成立。
- `memory.py add` 写改写节时会删掉提示注释前后的空行（prettier 会补回）。这是已有的小毛病，与本计划无关，只记在「Maintenance notes」。
- 会话开头是否读记忆、SessionStart 或 PreCompact 钩子、按主题拆分记忆文件、条目命中计数。
- 其他仓库的任何文件，包括它们各自复制的 `memory.py` 和它们的提交钩子。
- `make install`、推送：由维护者决定。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `bootstrap-claude`。每步一个提交，示例见各步。
- 未经操作者指示不要提交、不要推送。pre-commit 会跑 prettier 和 `make check`。

## Steps

### Step 1：先写两条 eval，在现行技能上跑出基线（P1）

晋升是文字指引，只能用 eval 验收，所以 eval 排在改动之前。

**夹具 `evals/files/memory-triage/`**：一个小型 Python 项目。`AGENTS.md` 七个章节填好，约定块是现行 v3，`CLAUDE.md` 只有 `@AGENTS.md`。`PROJECT_MEMORY.md` 约 6 KB，8 条追加节条目，都是普通事实，与数据库、缓存、导出无关。

**eval 5 `rule-on-first-sight`** 的 prompt（英文，与现有 eval 一致）在收尾时说三件事，都是第一次出现：

- 一条规则：跑集成测试前要先 `make db-reset`，否则上次迁移的残留让 3 个用例假失败，这次为此花了半小时。
- 一条事实：导出接口的分页上限是 500。
- 一个决定：报表接口现在不加 Redis 缓存，p95 超过 2 秒再议。

期望：

- 规则写进了 `AGENTS.md` 的「工作流与陷阱」，带原因；`PROJECT_MEMORY.md` 里没有这条。
- 分页上限 500 在「已验证的事实」里，日期是运行当天。
- 不加缓存的决定在 `PROJECT_MEMORY.md` 里，带原因；`AGENTS.md` 的「工作流与陷阱」里没有它。这一条防的是过度晋升。
- 原有 8 条条目都在。
- `memory.py check PROJECT_MEMORY.md --base-file <夹具里的原文件>` 退出 0。

现行 `maintain.md` 要等「第二次命中」才晋升，所以第一条期望在基线上预计不通过。这是预测，以 Step 1 的实际结果为准。

**夹具 `evals/files/memory-at-cap/`**：同样的项目骨架。`PROJECT_MEMORY.md` 在 23,600–23,900 字节之间，现行 `memory.py check` 全 PASS。条目按下面的构成写，每条带一个不与别条重复的标识词，eval 的期望按标识词点名：

| 组  | 条数 | 内容                                                         | 正确去向                    |
| --- | ---- | ------------------------------------------------------------ | --------------------------- |
| R   | 3    | 每次都要照做的规则，写了做法和原因（发布、迁移、密钥各一条） | `AGENTS.md`「工作流与陷阱」 |
| D   | 6    | 同一个子系统的长条事实，每条接近 300 字符                    | 搬进 `docs/` 的一份文档     |
| S   | 4    | 已过期的状态，条目自己写明已被后来的修复取代                 | 作废                        |
| M   | 2 对 | 同主题的两条，后一条是前一条的补充                           | 并入                        |
| K   | 其余 | 仍然有效、互不相关的事实和失败尝试                           | 留在记忆                    |

**eval 6 `make-room-at-cap`** 的 prompt 让 agent 记一条约 250 字节的新事实，写入后文件超过 24 KB。期望：

- `memory.py check PROJECT_MEMORY.md --base-file <夹具里的原文件>` 退出 0，文件 ≤24,000 字节。
- R 组 3 条的内容都在 `AGENTS.md` 的「工作流与陷阱」里，没有只搬进 docs。
- 每条消失的条目都有 `移出：` 行。
- 声明为作废的只出现在 S 组。R、D、K 组没有一条被作废。
- K 组条目都在，或被改写后内容仍在。
- `AGENTS.md` ≤200 行。

**跑法**：按 `anthropic-skills:skill-creator` 的 eval 流程。每次运行前把夹具复制到临时目录并建好基线提交，让 agent 遇到的环境和真实仓库一样：

```bash
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.invalid commit -qm baseline
```

先 `cp -r skills/bootstrap-claude "$TMPDIR/bootstrap-claude-baseline"` 留一份现行技能。eval 5、6 各跑 3 次，都用这份基线技能。把每次运行每条期望的通过情况记进 `plans/034-bootstrap-claude-memory-removal-gate/eval-baseline.md`，写明用的模型。现行脚本不认识 `--base-file`，这一条和 eval 6 的 `移出：` 行那一条在基线上记为「不适用」。

**Verify**：eval 文件合法的命令退出 0；`eval-baseline.md` 里有 6 次运行的结果表；`python3 skills/bootstrap-claude/scripts/memory.py check skills/bootstrap-claude/evals/files/memory-at-cap/PROJECT_MEMORY.md` 全 PASS 且总大小在 23,600–23,900 之间。

**Commit**：`test(bootstrap-claude): evals for promotion and making room at the size gate`

### Step 2：`memory.py check` 核对消失条目的去向（P1）

1. 把 `removal_gate.py` 的函数搬进 `memory.py`：`sections` 用现有的 `parse_sections` 改写或直接搬入，`append_entries`、`tokens`、`shared`、`diff_entries`、`parse_moves`、`suggest_anchor`、`keep_moves`、`classify`、`check_removed` 原样搬入。常量 `REWRITE_RATIO = 0.5`、`MIN_SHARED = 0.05` 各带一行注释写明依据（见「自行定下的」）。
2. `check` 增加两个参数：`--base REF`（默认 `HEAD`）和 `--base-file PATH`（给了就用它，不查 Git）。
3. 基线的取法：`git -C <文件所在目录> rev-parse --show-prefix` 得到相对路径，再 `git -C <目录> show <REF>:<前缀><文件名>`。不在 Git 仓库里、没有 `git`、或该提交里没有这个文件时，输出一行 `PASS 无基线，跳过条目去向检查`。
4. `cmd_check` 在 `check_memory` 的结果后面接上 `check_removed(base, current, <仓库根目录>)` 的结果。仓库根目录用 `git rev-parse --show-toplevel`，取不到时用文件所在目录。`check_memory` 本身的签名和返回不变，`setup_context.py --validate` 不受影响。
5. `cmd_add` 改写「上次会话」（及其英文别名）之前，取基线，用 `keep_moves(<这一节现有的正文>, <基线>, <当前全文>)` 得到要保留的声明，接在新块后面作为续行，并打印 `kept N 条移出声明`。取不到基线时不保留。新写入的文字里已有同一行时不重复。
6. 两处提示改成同一句：`超限时：先把每次都要照做的规则晋升到 AGENTS.md，再把长条知识搬进 docs/、合并同主题条目、作废过期条目；每条消失的条目在「上次会话」里写一行「移出：<条目开头> → <去向>」。`
7. 模块开头 docstring 的 `check` 和 `add` 说明各补一句。
8. 把 `test_removal_gate.py` 的用例搬进 `test_memory.py`，改成调用 `m.check_removed`。再加一个用例：在临时目录里 `git init`、提交一份记忆、删掉一条后调用 `cmd_check`，预期 `SystemExit(1)`；补上 `移出：… → 作废（…）` 后预期 `SystemExit(0)`。再加一个用例：不在 Git 仓库的临时目录里 `cmd_check` 退出 0。再加一个用例：在那个临时仓库里删掉一条并写好声明、不提交，然后用 `cmd_add` 改写「上次会话」，预期原来的 `移出：` 行还在、`cmd_check` 仍退出 0。

**Verify**：记忆脚本测试 `test_memory: ok`；初始化脚本测试 `test_setup_context: ok`；历史回放（正式实现）退出 0，输出与参考实现相同；`python3 skills/bootstrap-claude/scripts/memory.py check PROJECT_MEMORY.md` 在本仓库全 PASS，并有一行 `追加节无条目消失`。

**Commit**：`feat(bootstrap-claude): check accounts for entries that leave the append sections`

### Step 3：`maintain.md` 写入时先分流，超限时先晋升（P1）

按下面的要点改写，保持现有的标题和表格结构，写法遵循 writing-for-agents。

1. **「写什么」**表格前加一段：先分流。今后每次都要照做的事是规则，规则不进记忆。能做成检查的做成检查（lint、测试、提交钩子），因为检查不靠人记得；不能的写进上下文文件的「工作流与陷阱」，写做法和原因。记忆只收事实、决定和走不通的路径。给一个对比例子：「发布前必须先跑 `make smoke`」是规则；「回滚脚本从 `make smoke` 写出的文件里读版本号」是事实。
2. **「怎么写」第 1 步「筛」**：在判定问句之后加分流这一问。
3. **第 3 步「晋升」**：保留「第二次命中」这个触发条件，补两点。晋升的去处必须是上下文压缩后还在的位置：根 `AGENTS.md`，或不带 `paths:` 的 `.claude/rules/*.md`（后者只有 Claude Code 读）。根文件接近 200 行时，把模块专属的内容搬去子目录文件，给规则腾位置，不要把规则搬过去。
4. **新增一步「交代去向」**，放在「搬出」之后：条目从追加节消失时，在「上次会话」里为它写一行，列出四类去向的写法（用「数据形状」里的表）。同主题的改写不用写。给一个 `memory.py add --section 上次会话` 的多行示例，其中带两行 `移出：`。说明 `check` 报 FAIL 时会打印可以照抄的那一行。说明用 `add` 改写这一节会自动保留还没提交的声明，直接手改文件时要自己留着。
5. **「完成标准」**：超限时的顺序改成 compact、晋升、搬出、并入、作废。末段「追加类小节原有条目一条不少」改成：`check` 会对比上一次提交，列出每条消失的条目和它的去向；作废只用于已被取代或已过期的条目。
6. `bootstrap.md` 75 行那一句和「Nested instruction files」一节各补一句：子目录文件和带 `paths:` 的规则在上下文压缩后会被摘要掉，等触发文件再被读到才重新加载，所以只放模块专属的内容，每次都要遵守的规则留在根文件。

**Verify**：`make check` 通过；`grep -c "移出：" skills/bootstrap-claude/references/maintain.md` ≥3；`grep -n "paths" skills/bootstrap-claude/references/bootstrap.md` 的命中里有提到压缩的那两句。

**Commit**：`docs(bootstrap-claude): rules go to the instruction file first, removals name a destination`

### Step 4：回写约定升到 v4（P2）

1. `assets/CLAUDE.template.md` 的约定块改成下面的要点，结束标记改为 `<!-- bootstrap-claude convention v4 -->`：
   - 新增第一条：先分流。今后每次都要照做的规则不进记忆，能做成检查的做成检查，不能的写进本文件「工作流与陷阱」。
   - 「上次会话」「下次运行」那一条不变。
   - 「已验证的事实」「失败尝试」那一条不变。
   - 第三条去掉后半句的晋升（已移到第一条），保留改写、删旧条、搬进 docs/ 留指针。
   - 新增一条：条目从追加节消失时，在「上次会话」里写一行 `移出：<条目开头> → <去向>`，去向是文件路径（可带「节名」）、`并入 <现存条目的开头>` 或 `作废（原因）`。
   - 最后一条：门槛不变；超限时先晋升规则，再搬出、合并、作废；`memory.py check` 校验门槛和每条消失条目的去向。
2. `assets/PROJECT_MEMORY.template.md` 的「上次会话」提示注释末尾加：`本次移出的条目各写一行「移出：<条目开头> → <去向>」。`
3. 跑两个测试脚本。`test_setup_context.py` 里以模板正文为依据的断言失败时，只改断言里的文字。
4. `evals.json` 的 eval 4 有一条期望 `The section mentions memory.py check and the 24 KB / 300-character limits`，v4 仍然满足，不改。
5. 在本仓库运行 `python3 skills/bootstrap-claude/scripts/setup_context.py --dir .`，预期输出里 `convention:` 一行是 `upgraded`。输出会列出被替换掉的旧行，其中属于 v3 模板原文的不要补回，只有本仓库自己加的行才补回结束标记之后。计划时本仓库的约定块与 v3 模板一致，预期没有要补的行。

**Verify**：两个测试脚本各自 `ok`；`python3 skills/bootstrap-claude/scripts/setup_context.py --dir . --validate` 报约定为 latest 且 0 FAIL；`grep -c "convention v4" AGENTS.md` 为 1；`wc -l AGENTS.md` ≤200。

**Commit**：`feat(bootstrap-claude): convention v4 separates rules from memory and records removals`

### Step 5：在新技能上重跑 eval，对比基线（P1）

用 Step 1 的跑法，技能换成仓库里的现行版本，eval 5、6 各跑 3 次。结果写进 `plans/034-bootstrap-claude-memory-removal-gate/eval-result.md`，与基线并排。

**通过标准**：

- eval 5 的「规则进了 AGENTS.md 且不在记忆里」和「决定留在记忆里、没进 AGENTS.md」在 3 次里都通过。
- eval 6 的「R 组 3 条都在 AGENTS.md」「每条消失的条目都有声明」「作废只出现在 S 组」在 3 次里都通过。
- 两条 eval 的「原有条目都在」类期望不低于基线。

没达到时不要继续加文字，见「STOP conditions」。

**Commit**：`test(bootstrap-claude): eval results for plan 034`

### Step 6：本仓库的 pre-commit 跑记忆门禁，初始化文档给出钩子写法（P2）

没有钩子时，去向检查只在 agent 记得运行时生效。

1. `Makefile` 的 `check` 目标加一行 `python3 skills/bootstrap-claude/scripts/memory.py check PROJECT_MEMORY.md`，目标的说明改成同时提到记忆门禁。本仓库用仓库里的脚本，不用安装副本。
2. `.husky/pre-commit` 的第二行由 `node scripts/check-skills.mjs` 改成 `make check`，两处从此是同一条命令。
3. `AGENTS.md` 里三处对 `make check` 的描述（「命令」「工作流与陷阱」「审查规则」）补上记忆门禁。
4. `references/bootstrap.md` 的 Mode 1 在 Step 3 之后加 `### Step 4: offer a commit hook`，要点如下：
   - 去向检查和体积门槛只在运行 `memory.py check` 时生效，提交钩子让它每次提交都运行。
   - 仓库已有钩子体系时，向用户提出把下面这条命令加进去，用户同意后再改。改钩子会影响每一次提交，属于要先确认的操作。
   - 给出命令，技能没装的机器上直接跳过：

     ```bash
     s="$HOME/.claude/skills/bootstrap-claude/scripts/memory.py"; [ -f "$s" ] || exit 0; python3 "$s" check PROJECT_MEMORY.md
     ```

   - 仓库没有钩子体系时只告诉用户有这个选项，不替它引入一套。

**Verify**：

- `make check` 通过，输出里有 `check: PROJECT_MEMORY.md` 和 `result: all PASS`。
- 钩子能拦住：在一个临时克隆里（`git clone -q . "$TMPDIR/hook-probe" && cd "$TMPDIR/hook-probe" && npm install --silent`）删掉 `PROJECT_MEMORY.md` 追加节的一条，`git commit -am probe` 预期失败，输出里有 `消失的条目没有去向` 和可照抄的 `移出：` 行。补上那一行（去向写 `作废（钩子验证）`）后同一条命令预期成功。验证完删掉临时克隆。
- `grep -c "memory.py" skills/bootstrap-claude/references/bootstrap.md` 比改动前多。

**Commit**：`chore(bootstrap-claude): run the memory gate in pre-commit and document the hook`

### Step 7：在本仓库用新流程晋升两条 worktree 条目（P3，可删）

本仓库记忆里有两条每次用 worktree 都要照做的规则，都是 2026-10-23 的条目：worktree 里软链 `node_modules` 且不要 `npm install`；Agent 工具的 worktree 分支基于 origin/main 而不是本地 main。

1. 把两条写进 `AGENTS.md` 的「工作流与陷阱」，各一行，写做法和原因。
2. 从 `PROJECT_MEMORY.md` 删掉这两条，在「上次会话」里各写一行 `移出：`，去向 `AGENTS.md「工作流与陷阱」`。
3. 跑 `memory.py check`。

**Verify**：`check` 全 PASS，输出里有两行 `晋升：` 和一行 `消失 2 条，已交代：晋升 2`；`make check` 通过；`wc -l AGENTS.md` ≤200。操作者让提交时，这次提交要正常经过 Step 6 的钩子，不加 `--no-verify`。

**Commit**：`docs: promote the two worktree rules from project memory to AGENTS.md`

## Test plan

- 每步的 Verify 就是该步的验收。全部做完后再跑一次两个测试脚本、历史回放（正式实现）和 `make check`。
- 脚本的正确性由单元测试验收。历史回放只验收两点：真实历史上的每个版本都能解析，正式实现与参考实现输出一致。分流和晋升的行为由 eval 5、6 验收，判据是与基线对比。
- 历史回放可以加上本机其他有 `PROJECT_MEMORY.md` 的仓库的路径一起跑。其他仓库的条目原文不要写进本仓库的任何文件。

## Done criteria

- 七步各自的 Verify 全部通过，或明确写出哪一步没做、为什么。
- `test_memory: ok`、`test_setup_context: ok`、`make check` 通过。
- 历史回放（正式实现）在本仓库退出 0。
- `eval-baseline.md` 和 `eval-result.md` 都在，Step 5 的通过标准逐条写明通过或未通过。
- `plans/README.md` 里本计划的状态行已更新。

## STOP conditions

- Drift check 有输出，且「Current state」的摘录与现行文件对不上。
- Step 1 的基线上，eval 5 的规则期望和 eval 6 的 R 组期望已经 3 次全过。说明现行文字已经够用：Step 3 的第 1、2 点和 Step 4 约定块的第一条不做，其余照做（Step 2 的脚本检查不依赖这个前提），并在汇报里写明。
- Step 2 之后历史回放有判定不符的提交，或正式实现的输出与参考实现不同。
- Step 4 需要改 `test_setup_context.py` 断言之外的测试逻辑，或需要改 `setup_context.py`。
- Step 6 的临时克隆里，删了条目的提交没有被拦下。
- Step 5 没达到通过标准。写明哪条期望在哪几次失败、agent 实际做了什么，不要自行再改文字重跑。
- 需要改 Scope 之外的文件才能通过验证。

## Maintenance notes

- 改完不会自动生效：`~/.claude/skills/bootstrap-claude` 是副本，要 `make install SKILL=bootstrap-claude SOURCE=.`，由维护者执行。
- **安装之后本机另外两个仓库的提交会用上新检查。** 一个仓库的 pre-commit 在 `PROJECT_MEMORY.md` 有改动时调用安装副本的 `memory.py check`，它的约定还是 v2；另一个仓库的 Makefile 有变量指向安装副本。那里的会话删掉条目却没写 `移出：` 行时，提交会被拦下，FAIL 输出里带着可以照抄的那一行。想让那些仓库的 agent 事先知道这条规则，在各仓库跑一次 `setup_context.py --dir .` 把约定升到 v4。
- Step 6 之后本仓库每次提交都跑记忆门禁。其他仓库仍然要靠各自的钩子或 agent 主动运行；本机现有 10 个仓库没有钩子，要不要加由维护者逐个决定，写法在 `bootstrap.md` 的 Step 4。
- 去向检查拦得住「没交代」，拦不住「交代得敷衍」。全部写成作废也能通过脚本。这一层靠 eval 6 的期望和维护者看提交里的 `移出：` 行。
- 改写不需要声明，所以把一条改短、丢掉原因，脚本只会提示 `改写后缩短 N%`，不报 FAIL。调查里按措辞粗筛，5 个仓库共有 25 条改写后不再带原因或来源的措辞。
- 5% 的关键词下限和 0.5 的相似度分界都来自本机几个仓库的历史，样本小。出现误报时先看 `removal_gate.py` 开头的常量。
- `memory.py add` 写改写节时会删掉提示注释前后的空行，prettier 会补回。本计划没有修。
- 附件目录里的 `removal_gate.py` 在 Step 2 之后与 `memory.py` 重复，留作回放的对照；`replay.py --impl memory` 跑的是正式实现。
