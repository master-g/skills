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
| 006  | 约定块自动升级时打印被丢弃的块内旧行，新章节插在约定块之前                      | P1       | S      | 003        | DONE（2026-10-12，main c875250；Step 5 真实 DopaManga 复现由审阅者完成，执行者只跑了合成样例）                                   |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with one-line reason) | REJECTED (with one-line rationale)

## Dependency notes

- 002 依赖 001：两者都改 `setup_context.py` 与测试文件，001 先落地避免合并冲突；002 的新用例引用 001 保留的 `BASE` 常量。
- 003 依赖 001：新增的两个必填章节必须登记进 001 引入的 `SECTION_ALIASES`，否则 `match_section` 会 `KeyError`。依赖 002：003 的 eval 措辞与端到端验证都以 AGENTS.md 为真源。
- 004 依赖 002：都改 `cmd_validate`，且测试以 AGENTS.md 为真源。
- 005 与 002/003 改同一个 `evals.json` 的不同条目，任意顺序。
- 006 依赖 003：缺陷在 003 的 v2→v3 升级中暴露（2026-10-12 DopaManga 仓库丢了块内的 `@PROJECT_MEMORY.md` 导入行和一条 PR 回写规则，输出却称 preserved）；006 由 `plan` 变体单独写成，不来自原审计。

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

---

## tufte-reader（2026-10-14，基线 `55a66e8`）

由 improve 技能应维护者的两项请求生成：(1) 评估把脚本从 Python 迁到 bun + TypeScript 的投入产出；(2) 按文章主题给读本配风格接近 _Atalanta Fugiens_（1618）的旧版画题图（16–18 世纪的铜版画、蚀刻、木刻；炼金术、自然哲学、博物、机械一类），只用公有领域或宽松许可的图。(1) 的结论是不做，记在下面的 rejected 一节；(2) 写成 007（元素、样式、构建检查、取图脚本、图录）。advisor 在 scratchpad 的仓库副本里套用了 007 的全部改动并跑通（43 个测试 OK、specimen 0 ERROR、图录 55 个文件经 Commons 核对），附件在 `plans/007-tufte-reader-plates/`。之后据一条旁路提醒补了 008：单幅图只有约 600px，高分屏发虚，改从 IA 取高清版；调研中还发现 Commons 上标作第 11 幅的文件其实是第 25 幅，已在 007 的图录里改正。第二轮维护者指出第一轮把范围收窄到了 Atalanta 一本书，于是把图录的「选图」改成以主题为入口、「其他系列」扩成 22 个核实过的 Commons 分类（仍在 007 附件里），008 改为通用的 IA 来源机制，新增 009 的搜图脚本，并应旁路提醒放行了「No restrictions」许可。advisor 在 scratchpad 的仓库副本里跑通了三份计划叠加后的状态：50 个测试 OK，图录核对通过（007 版 55 个文件、008 版 50 个文件，分类 22 个），搜图脚本联网实测 3 组关键词。

### Decisions recorded (2026-10-14, by the maintainer)

- 题图在暗色主题下用「亮融暗裱」：亮色 multiply 融进页面，暗色裱在压暗的旧纸色衬底上。反相和纯墨线两种方案 demo 过，暗色下都像照相底片，否决。
- 题图放在扉页和挑选出的几章，只在用户要求时加。
- 许可只接受公有领域、PDM、无已知版权限制（Commons 的「No restrictions」，按公有领域处理）、CC0、CC BY（署名）；只从 Wikimedia Commons 取图（例外见下面的 IA 一条）。
- 选图以主题为入口，风格由系列清单把关（同一时代、同一技法），不限于 Atalanta Fugiens；Atalanta 图录保留为其中一个有逐幅索引的系列，文档里不给「默认用第 42 幅」一类的建议。
- 不迁移到 bun / TypeScript（见下）。
- 题图的高清图源：对 Internet Archive 放行一个条目 `atalantafugiensh00maie`（Getty 扫描，未上色，500ppi），许可依据写进 `plate.py` 的 `IA_ITEMS` 白名单；不用 Commons 上的 SHI 翻拍本（约 30 幅、部分上色、有透视）。落在 008。
- specimen 扉页题图用第 42 幅的 Commons 高清文件，按 1000px 取图（样张约 240 KB），保证高分屏上清楚。

### Execution order & status

| Plan | Title                                                                                                    | Priority | Effort | Depends on | Status                                     |
| ---- | -------------------------------------------------------------------------------------------------------- | -------- | ------ | ---------- | ------------------------------------------ |
| 007  | tufte-reader 支持公有领域铜版画题图（扉页与选定章节）                                                    | P2       | M      | —          | DONE（worktree 提交 f2b4c12，待合入 main） |
| 008  | plate.py 支持 Internet Archive 扫描本（IIIF 裁切），登记 Atalanta Fugiens 为首个条目并换成 1000px 高清版 | P2       | S      | 007        | TODO                                       |
| 009  | 加搜图脚本 find_plate.py：按主题词在 Commons 分类里找许可可用的高清题图                                  | P2       | S      | 007        | TODO                                       |

### Dependency notes

- 008 依赖 007：补丁以 007 的附件为基准，改的是 007 新建的 `plate.py`、`test_plate.py`、`plates.md`。
- 009 依赖 007（复用 `plate.py` 的许可白名单，改 `plates.md`「系列」末尾一段）；与 008 互不依赖，建议在 008 之后执行，计划里的测试数按这个顺序写。

### Findings considered and rejected

- **把 tufte-reader 的 Python 脚本迁到 bun + TypeScript**：投入大于收益，维护者确认没有具体的推动理由。本机实测：specimen（89 条公式）完整构建 0.14 秒，35 个测试 1.5 秒；`math.mjs` 换 bun 运行输出逐字节相同，只省约 60 毫秒；node 本来就是编译公式的硬依赖，node 26 能直接运行 `.ts`，所以 bun 不带来新能力。真正的成本在 `build.py` 的 `Checker`：它建在 `html.parser.HTMLParser` 上，Node 和 Bun 的标准库没有对应的 HTML 解析器，只能违反「Node 脚本只用标准库」的约定引入依赖，或者手写一个在不规范 HTML 上与原来行为一致的解析器。`figlib.py` 是子 agent 在 `.figs.py` 里 import 的写作接口，换语言要改写这套写法和所有写着 `python3` 的文档。以后出现具体理由（某个环境没有 python3、要用 TS 写图）再议；届时目标是 node + TS 而不是 bun，第一步移植 `Checker`，并以 specimen 构建输出逐字节一致作为门禁。
- **`$` 公式扫描在 `build.py` 和 `math.mjs` 里各有一份**：现有的端到端测试先用 node 编译、再用 Python 的 `leftover_dollars` 查漏，已经覆盖了两份实现跑偏的情况，不需要单独加对拍测试。
