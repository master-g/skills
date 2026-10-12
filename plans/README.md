# Implementation Plans

由 improve 技能于 2026-10-12 生成（基线 commit `547eeac`），起因是把 Firefox 仓库的 `AGENTS.md`（`https://github.com/mozilla-firefox/firefox/blob/main/AGENTS.md`）与本仓库的 `bootstrap-claude` 技能对比。按下表顺序执行，除非依赖关系另有说明。每个执行者：先读完整份计划，遵守其 STOP conditions，完成后更新自己那一行。

六个发现写成五份计划：发现 #3（模板写死 `~/.claude/` 路径）与 #4（模板缺不可推导事实的槽位）合并为 003，因为两者都要升模板标记号，合并后用户只做一次约定升级。

## Decisions recorded (2026-10-12, by the maintainer)

- **AGENTS.md 是唯一真源；CLAUDE.md 永远只是一行 `@AGENTS.md`；不再创建任何 symlink。** 旧布局（CLAUDE.md 为真实文件、AGENTS.md 为 symlink）由脚本自动迁移。这是 Firefox 的布局，也是 Claude Code 文档推荐的共享写法。落在 Plan 002。
- 模板文件名 `assets/CLAUDE.template.md` 暂不改名（牵连多处引用，收益只是名字）。

## Execution order & status

| Plan | Title                                                                           | Priority | Effort | Depends on | Status                                                                                                                           |
| ---- | ------------------------------------------------------------------------------- | -------- | ------ | ---------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 001  | 章节识别支持英文别名，统一 ensure 与 validate 的判定                            | P1       | S      | —          | DONE（2026-10-12，main 6edb481）                                                                                                 |
| 002  | AGENTS.md 为真源，CLAUDE.md 只写一行 `@AGENTS.md`，不再使用 symlink；迁移旧布局 | P1       | M      | 001        | DONE（2026-10-12，main 2ce03f6；done criterion「evals.json 无 symlink」原文有误，四处命中均为「not a symlink」否定句，视为满足） |
| 003  | 模板 v3：去掉个人路径、新增「导航」「工作流与陷阱」、maintain 加「晋升」        | P1       | M      | 001, 002   | DONE（2026-10-12，main 2c0c9f4）                                                                                                 |
| 004  | `--validate` 对上下文文件加 200 行门禁                                          | P3       | S      | 002        | DONE（2026-10-12，main 29c94e0）                                                                                                 |
| 005  | eval 3 的「今天」改为相对表述                                                   | P3       | S      | —          | DONE（2026-10-12，main 9df616c）                                                                                                 |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with one-line reason) | REJECTED (with one-line rationale)

## Dependency notes

- 002 依赖 001：两者都改 `setup_context.py` 与测试文件，001 先落地避免合并冲突；002 的新用例引用 001 保留的 `BASE` 常量。
- 003 依赖 001：新增的两个必填章节必须登记进 001 引入的 `SECTION_ALIASES`，否则 `match_section` 会 `KeyError`。依赖 002：003 的 eval 措辞与端到端验证都以 AGENTS.md 为真源。
- 004 依赖 002：都改 `cmd_validate`，且测试以 AGENTS.md 为真源。
- 005 与 002/003 改同一个 `evals.json` 的不同条目，任意顺序。

## Verification baseline (recorded 2026-10-12)

- `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`；`python3 skills/bootstrap-claude/scripts/test_memory.py` → `test_memory: ok`。两者是脚本式 assert 测试，不是 unittest；仓库未安装 pytest。
- `make check`（`node scripts/check-skills.mjs`）是文档链接与「按编号引用章节」的门禁，pre-commit 也跑它。它只扫 `skills/`、`README.md`、`CLAUDE.md`，不扫 `plans/`。
- 复现发现 #1/#2 的实验（只读）：把 Firefox 的 `AGENTS.md` 放进临时目录，加一个内容为 `@AGENTS.md` 的 `CLAUDE.md`，跑 `setup_context.py --dir` → `CONFLICT ... exit=2`；只放 `AGENTS.md` 跑 → 追加五个中文占位章节，`--validate` 5 FAIL。

## Open decisions for the maintainer (not planned)

- **英文模板（`--lang en`）？** 001 之后英文仓库的已有章节能被识别，但缺失章节仍以中文追加。维护第二份模板意味着约定块比对也要分语言。等有真实英文仓库需求再谈。

## Findings considered and rejected

- 回写约定块放在仓库文件里而不是技能里（每次会话都占上下文）：有意为之，没装技能的 agent 也要遵守；不改。
- 模板里的 HTML 提示注释：Claude Code 注入上下文前会剥掉块级 HTML 注释，零运行成本；是优点不是问题。
- 模板用中文：用户的选择；问题只在缺别名（001）。
- `_待填写_` 占位符门禁与 PROJECT_MEMORY 24 KB 字节门禁：Firefox 没有的优势，保留。
- Firefox 的「用 Read 工具而不是 cat 打开子目录 AGENTS.md」：官方文档现已说明 `cat` 单文件也算读取，该 workaround 对本技能无意义。
- 子目录指令文件的脚本支持（`--nested`）：按最小改动原则先用 003 的手写指引，没有真实需求不加脚本。
