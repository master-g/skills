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

由 improve 技能应维护者的两项请求生成：(1) 评估把脚本从 Python 迁到 bun + TypeScript 的投入产出；(2) 按文章主题给读本配风格接近 _Atalanta Fugiens_（1618）的旧版画题图（16–18 世纪的铜版画、蚀刻、木刻；炼金术、自然哲学、博物、机械一类），只用公有领域或宽松许可的图。(1) 的结论是不做，记在下面的 rejected 一节；(2) 写成 007（元素、样式、构建检查、取图脚本、图录）。advisor 在 scratchpad 的仓库副本里套用了 007 的全部改动并跑通（43 个测试 OK、specimen 0 ERROR、图录 55 个文件经 Commons 核对），附件在 `plans/007-tufte-reader-plates/`。之后据一条旁路提醒补了 008：单幅图只有约 600px，高分屏发虚，改从 IA 取高清版；调研中还发现 Commons 上标作第 11 幅的文件其实是第 25 幅，已在 007 的图录里改正。第二轮维护者指出第一轮把范围收窄到了 Atalanta 一本书，于是把图录的「选图」改成以主题为入口、「其他系列」扩成 22 个核实过的 Commons 分类（仍在 007 附件里），008 改为通用的 IA 来源机制，新增 009 的搜图脚本，并应旁路提醒放行了「No restrictions」许可。advisor 在 scratchpad 的仓库副本里跑通了三份计划叠加后的状态：50 个测试 OK，图录核对通过（007 版 55 个文件、008 版 50 个文件，分类 22 个），搜图脚本联网实测 3 组关键词。007–009 执行并合入后，advisor 派四个 sonnet worker 各写了一本带题图的 3 章样例读本（显微、机械、炼金、天文），四本都从主题出发选图、没有退回 Atalanta；它们共同撞上的脚本缺陷和文档含糊处写成 013。

### Decisions recorded (2026-10-14, by the maintainer)

- 题图在暗色主题下用「亮融暗裱」：亮色 multiply 融进页面，暗色裱在压暗的旧纸色衬底上。反相和纯墨线两种方案 demo 过，暗色下都像照相底片，否决。
- 题图放在扉页和挑选出的几章，只在用户要求时加。
- 许可只接受公有领域、PDM、无已知版权限制（Commons 的「No restrictions」，按公有领域处理）、CC0、CC BY（署名）；只从 Wikimedia Commons 取图（例外见下面的 IA 一条）。
- 选图以主题为入口，风格由系列清单把关（同一时代、同一技法），不限于 Atalanta Fugiens；Atalanta 图录保留为其中一个有逐幅索引的系列，文档里不给「默认用第 42 幅」一类的建议。
- 不迁移到 bun / TypeScript（见下）。
- 题图的高清图源：对 Internet Archive 放行一个条目 `atalantafugiensh00maie`（Getty 扫描，未上色，500ppi），许可依据写进 `plate.py` 的 `IA_ITEMS` 白名单；不用 Commons 上的 SHI 翻拍本（约 30 幅、部分上色、有透视）。落在 008。
- specimen 扉页题图用第 42 幅的 Commons 高清文件，按 1000px 取图（样张约 240 KB），保证高分屏上清楚。

### Execution order & status

| Plan | Title                                                                                                    | Priority | Effort | Depends on    | Status                                                                                |
| ---- | -------------------------------------------------------------------------------------------------------- | -------- | ------ | ------------- | ------------------------------------------------------------------------------------- |
| 007  | tufte-reader 支持公有领域铜版画题图（扉页与选定章节）                                                    | P2       | M      | —             | DONE（已合入，f2b4c12）                                                               |
| 008  | plate.py 支持 Internet Archive 扫描本（IIIF 裁切），登记 Atalanta Fugiens 为首个条目并换成 1000px 高清版 | P2       | S      | 007           | DONE（已合入，c51ac07）                                                               |
| 009  | 加搜图脚本 find_plate.py：按主题词在 Commons 分类里找许可可用的高清题图                                  | P2       | S      | 007           | DONE（已合入，de66080）                                                               |
| 013  | 题图脚本按四本样例的反馈打磨：透明底、Commons 裁切、缩略图预览、帮助与文档措辞                           | P2       | S      | 007, 008, 009 | DONE（已合入，8d8f2f6；计划里 `grep -c "no restrictions"` 的预期 1 是笔误，实际为 2） |

### Dependency notes

- 008 依赖 007：补丁以 007 的附件为基准，改的是 007 新建的 `plate.py`、`test_plate.py`、`plates.md`。
- 009 依赖 007（复用 `plate.py` 的许可白名单，改 `plates.md`「系列」末尾一段）；与 008 互不依赖，建议在 008 之后执行，计划里的测试数按这个顺序写。
- 013 依赖 007–009 全部合入（基线 `3b4c69d`）：覆盖 `plate.py`、`find_plate.py` 和两份测试，按锚点改三份文档。

### Findings considered and rejected

- **把 tufte-reader 的 Python 脚本迁到 bun + TypeScript**：投入大于收益，维护者确认没有具体的推动理由。本机实测：specimen（89 条公式）完整构建 0.14 秒，35 个测试 1.5 秒；`math.mjs` 换 bun 运行输出逐字节相同，只省约 60 毫秒；node 本来就是编译公式的硬依赖，node 26 能直接运行 `.ts`，所以 bun 不带来新能力。真正的成本在 `build.py` 的 `Checker`：它建在 `html.parser.HTMLParser` 上，Node 和 Bun 的标准库没有对应的 HTML 解析器，只能违反「Node 脚本只用标准库」的约定引入依赖，或者手写一个在不规范 HTML 上与原来行为一致的解析器。`figlib.py` 是子 agent 在 `.figs.py` 里 import 的写作接口，换语言要改写这套写法和所有写着 `python3` 的文档。以后出现具体理由（某个环境没有 python3、要用 TS 写图）再议；届时目标是 node + TS 而不是 bun，第一步移植 `Checker`，并以 specimen 构建输出逐字节一致作为门禁。
- **`$` 公式扫描在 `build.py` 和 `math.mjs` 里各有一份**：现有的端到端测试先用 node 编译、再用 Python 的 `leftover_dollars` 查漏，已经覆盖了两份实现跑偏的情况，不需要单独加对拍测试。

---

## show-me-html（2026-10-14，基线 `55a66e8`）

由 improve 技能应维护者的请求生成。维护者反馈用本技能生成的 `reelshort-tech-notes.html`（feature-explainer 配方）开头指标带字太小，「1s」的 s 几乎看不见，表格与内容的密度也不均衡，请求分析哪些属于模板问题。实测发现页面内联的 CSS 与仓库当前版本逐字相同，`build.py` 对这页零 WARN 通过。指标带的大数只有 12.8px、单位 6.4px，原因是页面自写的 `.stat-band p` 压过了骨架的 `.stat-num`；骨架缺一个通用指标带组件，模型只能自造。审计还发现：`.item-group` 文档里的 `<hr />` 没有样式，渲染成一个小点，冻结场景 bb65054 轮里也是这样；`.src` 的大写变换会改写行内代码。advisor 在 scratchpad 的仓库副本里套用了 010 和 011，单元测试 46 个 OK，五个冻结场景、两个夹具页、gallery 全图页都没有误报，前后截图核对过。

### Decisions recorded

- 010 / 011 的执行顺序与审计时的口头编号相反：零判断的 CSS 修正排在前面（010），指标带与检查排在后面（011）。
- 011 的新检查报 ERROR（与图内字号下限一致）；维护者 2026-10-15 确认。
- 012 的方案：维护者 2026-10-15 看过四页样张（base / A / B / A+B，1280 与 390）后选 base，不改表格。

### Execution order & status

| Plan | Title                                                              | Priority | Effort | Depends on      | Status                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------ | -------- | ------ | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 010  | 修好条目组分隔线、来源行里的代码与中文字号、图示分区框内的标签遮罩 | P1       | S      | —               | DONE（已合入，ea8fb6e）                                                                                                                                                                |
| 011  | 指标带成为通用组件，构建检查拦下被压小的大数与过小的正文字         | P1       | M      | 010（建议顺序） | DONE（已合入，04c7f74 + dc9a5b8；新检查按 ERROR，维护者 2026-10-15 确认）                                                                                                              |
| 012  | 表格密度：先做对比样张由维护者选方案，再实现                       | P2       | S      | —               | REJECTED（2026-10-15 维护者看过样张选 base 不改：四页 390px 都不横滚，A 只让首列代码少折、说明列更窄，B 只更紧凑，不值得全页面表格观感变化；样张留在 advisor 的 scratchpad，未入仓库） |

### Dependency notes

- 010 与 011 都改 `show-me.css`，规则位置不重叠。011 Step 6 的场景高度预期值是按「先 010 后 011」写的。
- 012 与两者没有规则重叠；排在最后，是为了避免三份计划同时改 `show-me.css`。012 有一个必停点：样张交给维护者选定方案之后才实现。
- 三份计划的场景轮次都复用主检出目录 `skills/show-me-html/scenarios/rounds/2026-09-23-bb65054/` 下的页面，重新构建即可，不用重新生成。

### Findings considered and rejected

- **在 `.stat-num` 上提高优先级（如 `p.stat-num`、`main .stat-num`）**：与页面的 `.stat-band p` 同为 (0,1,1)，页面 `<style>` 排在后面，照样会输；骨架有意让 `.stat-num` 保持低优先级。改为 011 的组件内加固（`.metric-band .stat-num`）加检查。
- **当页补丁 `.stat-band .stat-num { … }`**：MAINTENANCE.md 禁止调用方补丁。维护者那一页要单独修：把 `stat-band` 换成 `metric-band`，删掉页面自写的样式块。这不属于计划范围。
- **表格调列宽（首列 nowrap、非末列 `width:1%` + nowrap）**：两种在样张里都更差，见 012 Step 1。宽屏下列宽不均主要来自内容。
- **新增「调研笔记」配方 / 密度规则**：证据只有这一页（模型把调研笔记套进了 feature-explainer，一页里叠了指标带、暗卡、管线图、条目组和三张表），建议维护者记进 MAINTENANCE.md「观察名单」，复现后再定（improve 不改技能文件）。
- **图示 SVG 文字 9.5px**：符合 diagrams.md「任何文字不小于 9px」，不改。

---

## 输出文件名日期前缀（2026-10-16，基线 `84632f4`）

由 improve 技能的 `plan` 变体应维护者请求生成：show-me-html 与 tufte-reader 默认输出文件名补日期前缀，形如 `2026-10-16-<标题>.html`。只改两个 SKILL.md 各一段，脚本不动；截图名与 tufte-reader 工作区从页面名派生，自动继承前缀。

### Decisions recorded（2026-10-16，维护者确认）

- 格式 `YYYY-MM-DD-<kebab 标题>.html`，沿用 `scenarios/rounds/2026-09-23-…` 的 ISO 日期写法。
- 「默认」指用户没给完整文件名：给了完整文件名照用；只给目录时在该目录里用默认名。
- 日期取本机当天（文档写明 `date +%F`），不让模型凭记忆写。
- 修改、续写已有页面沿用原文件名，避免每轮反馈换名、tufte-reader 每天多一个 `.work/`。
- 标题部分用英文 kebab-case，中文标题意译成简短英文（不用拼音、不保留中文）。
- 冻结场景页、gallery 的 `all-charts.html`、specimen 保持固定名字。

### Execution order & status

| Plan | Title                                                       | Priority | Effort | Depends on | Status                            |
| ---- | ----------------------------------------------------------- | -------- | ------ | ---------- | --------------------------------- |
| 014  | 两个技能的默认输出文件名带日期前缀 `YYYY-MM-DD-<标题>.html` | P2       | S      | —          | DONE（已合入，763d3cb + 03890c2） |

---

## farm 借鉴 flopwire（2026-10-20，基线 `a05d72d`）

由 improve 技能的 `plan` 变体应维护者请求生成。起因是评估 [flopwire](https://github.com/flopwire/flopwire)（给 AI 代理用的消息总线与转录检索，Apache-2.0）对 farm 有没有借鉴意义。结论是不把 flopwire 接进 farm，但借三个做法：无头 worker 按进程组收尾（来自它的 `scripts/nightly-codex.py`）、从转录核对 worker 实际改了什么（来自它从 commit 反查会话的思路）、汇报 worker 用量（同一脚本按会话汇总 token）。advisor 在临时目录里复现了 015 的问题（按 `.pid` kill 后 pi 和它的子进程仍在运行），附件脚本跑通 16 项冒烟测试，现行脚本同一套测试 13 项 FAIL；016 的附件脚本对本机一个真实子代理转录读到 39 次工具调用，与完成通知一致。两份计划都在仓库导出的临时副本里按步骤执行过，全部验证命令的预期值已核对。

### Decisions recorded（2026-10-20，维护者）

- 先做进程组收尾（015），再做转录核对（016）。
- 转录核对只做 Claude Code 原生后端；pi、codex、Codex App 的转录格式不同，以后有需要再加。
- 转录格式没有公开承诺：读不到工具调用、次数与完成通知不符、worker 又派了子代理，都算核对失败，不判为通过（来自一条旁路提醒，维护者采纳）。
- 016 的集成门禁 `git status` 核对是 advisor 加的、不依赖后端的兜底，维护者可以删掉这一步而不影响其余部分。
- Claude Code worker 改文件用 Edit / Write，只能靠 Bash 改的把命令和路径列进报告（2026-10-20 合并后决定，写在 `claude-code-worker.md`「派发」）。依据：执行 015、016 的两个 sonnet 执行者工具调用全是 Bash（4 次、12 次），转录核对的 `written` 两次都为空，越界判断全靠人工看 `bash_writes`。

### Execution order & status

| Plan | Title                                                                    | Priority | Effort | Depends on | Status                                                        |
| ---- | ------------------------------------------------------------------------ | -------- | ------ | ---------- | ------------------------------------------------------------- |
| 015  | 无头 worker 能被完整停下：pi 自成进程组，`headless.sh` 加 `stop`         | P1       | S      | —          | DONE（审阅通过，2026-10-20 cherry-pick 到 main 为 `9be6618`） |
| 016  | Claude Code 下按转录核对每个 worker 实际写了哪些文件，并汇报 worker 用量 | P2       | M      | —          | DONE（审阅通过，2026-10-20 cherry-pick 到 main 为 `6f1a059`） |

### Dependency notes

- 015 改 `headless.sh` 和 `references/cli-worker.md`，016 改 `SKILL.md`、`references/claude-code-worker.md`、`references/pool.md`、`AGENTS.md` 并新建两个脚本，文件不重叠，顺序任意；按维护者的优先级先 015。

### Findings considered and rejected

- **把 flopwire 作为 farm 的依赖**：Claude Code 子代理里的 hook 不投递消息、子代理发出的消息算作父会话（flopwire `notes/message-bus/plan.md`），所以原生后端的 worker 收不到；pi 不在它支持的 harness 里；herdr pane 里的 worker 已能用 `herdr agent prompt` 发修正。farm 的设计也是 worker 之间不通信。
- **运行中插话（mid-turn steering）**：同上，到不了 farm 的 worker；farm 的修正在 worker 结束后发，够用。
- **pid 重用防护（记录进程启动时间）**：015 只在 `.exit` 已存在时拒绝 `stop`，剩下的窗口很小，写进 015 的 Maintenance notes，没有实现。

---

## show-me-html 图表字号、文字对比度与放大倍率（2026-10-21，基线 `fff32ba`）

由 improve 技能应维护者请求生成。维护者反馈 bedrock 仓库的一页报告 `docs/diagnosis/2026-10-21-enter-room-global-baseline.html`（`status-report` 配方，含 G4、F12、G10、F5 四张图）整体不错，但图表字太小、一些脚注颜色太淡、F5「每个国家的 300106」刻度之间太疏。现行构建对这页零 WARN 通过。实测三个问题都出在技能里：`G.type` 的 6.5 / 7.6 在标准 viewBox 下就是 6.5–8.2px，下限也按这个数定，gallery 59 张图在 1280px 下有 42 张最小字不到 8px（017）；来源行、图型标签、刻度字用 `--ink-45`，卡面上 2.82:1，主角色写字 2.65:1（018）；F5 是单张 400 宽 viewBox 的 `.fig`，被拉到整栏放大 2.30 倍，刻度间距从 8.2px 变成 12.4px，文档没写单张图会占满整栏（019）。

advisor 在 scratchpad 里导出 `fff32ba` 的副本，按 017 → 018 → 019 的顺序套用了三份计划里给出的全部代码改动（gallery 图块的逐张重排与逐张换色、各份的文档步骤除外，那是执行者的工作）：单元测试 50 个 OK；五个冻结场景页和组件夹具 `component-states.html` 都是 `自检通过。`；gallery 探针在 017 第 2 步之后恰好报出预测的 30 条问题，对比度检查在 018 第 5 步第 1 小步之后报出 33 组；gallery 总览页没有倍率 WARN；维护者那页重建后报出 F5 的 2.30 倍 WARN 和页面自写颜色的 4 组对比度 ERROR，与计划里写的一致。复核时发现两个骨架组件本身过不了新的对比度检查：告急按钮（纸色字压在橙底上 2.90:1）和卡片里的链接样式按钮（4.40:1），已并进 018 第 1 步（按钮字改用 `--ink-fixed`，`--link-accent` 改为 `--hero-text`）。

### Decisions recorded（2026-10-21，维护者）

- 三个问题都写成计划（017、018、019）。
- 图内字号用 B 档：刻度 9、类目名与数值 10（viewBox 单位）；下限为图内任何文字 ≥ 9，半宽与通栏相同。另一档 A（8 / 9 / 9）重排的图少一些（12 张对 18 张），但与 G 族写死的 9 / 10 仍差一档，两套字号继续并存。
- 次要文字全部 ≥ 4.5:1：新增明度阶 `--ink-65`，`--muted-foreground` 从 `--ink-60` 改到 `--ink-65`。
- 主角色写字加专用色 `--hero-text`（主角色掺四成墨），图形仍用 `--hero`。

以下几项由 advisor 定，维护者可改：对比度检查报 ERROR（018 Step 3 末尾写了改成 WARN 的做法）、只在亮色主题下量、跳过 `pre`；告急按钮的字改用固定深墨、`--link-accent` 改为 `--hero-text`（让骨架组件本身过检查）；倍率检查报 WARN、阈值 0.8–1.5、只在 1280px 报；文字重叠探针只放在 `gallery.py`，不进 `build.py`。

**已确认（2026-10-22，维护者）**：018 的对比度检查报 ERROR（ERROR 能挡住带病交付，与图内字号下限一致；代价是重建旧页面时，页面自己写的淡色文字会让构建失败，`--open` 也不会打开）。同日维护者还定了：017 遗留的 F3「台风 / 闭园」并进 018（Step 5 第 3 小步，竖排单列）；执行顺序改为 020 → 018 → 019，见下一节。

### Execution order & status

| Plan | Title                                                    | Priority | Effort | Depends on           | Status                                                                                                |
| ---- | -------------------------------------------------------- | -------- | ------ | -------------------- | ----------------------------------------------------------------------------------------------------- |
| 017  | 图内字号升一档（9 / 10 / 10），下限改为任何文字不小于 9  | P1       | L      | —                    | DONE（2026-10-22 审阅通过并合入 main `bdbeae5..adfb03d`；遗留一处 F3 小瑕疵，见下方「017 执行记录」） |
| 018  | 次要文字与图内文字对比度达到 4.5:1，构建加文字对比度检查 | P1       | M      | 017（建议顺序）、020 | TODO                                                                                                  |
| 019  | 图被拉大或压小时构建报 WARN，charts.md 写清单张图怎么排  | P2       | S      | 017、018（建议顺序） | TODO                                                                                                  |

### Dependency notes

- 三份都改 `scripts/build.py` 的渲染探针。017 只改字号下限那几行；018、019 各在 `PROBE` 末尾追加一段测量，在正则末尾追加一个命名分组（`contrast`、`scaled`），按名字取值，所以执行顺序换了也不会互相取错分组。两份计划都写了另一份先合入时锚点的样子。
- 018 在 017 之后：两份都改 gallery 图块，017 动排法，018 只动文字 `fill`；018 的 33 组工作清单是在 017 改档之后量的。先 018 再 017 也能做，但 017 的重排可能让个别字落到新的色块上，018 的清单就要重量。
- 019 不依赖另两份的结果，排在最后是为了少一次锚点核对。

### 017 执行记录（2026-10-22）

- **分支与基点**：执行者的 worktree 从远端 main（`1774cd5`）开出，分支 `advisor/017-show-me-html-chart-type-scale` 共 9 个提交（`29b6b68`…`c00ba9a`）。本地 main（`fff32ba`）比它多 17 个未推送的 bench 文档提交，那些提交没有动 `skills/show-me-html`。合入时把 `1774cd5..c00ba9a` rebase 或 cherry-pick 到本地 main 上；main 不能直接指向这个分支，否则那 17 个提交会丢。
- **审阅**：两轮 REVISE。第 1 轮：13 张图上下叠放的第二行偏移原来写死，改为按 `G.type.<role> * 1.25` 计算（计划 Step 4–7 通用改法第 1 条）。第 2 轮：L17 的「全年 … 公里」和「连跑 25 天」左右贴字（探针 15% 阈值漏报），汇总行挪到网格左缘。advisor 在 `c00ba9a` 上独立复跑：48 个测试 OK；gallery 带渲染构建只有一条体积 WARN，`问题 0 条`；`make check` 通过；五个冻结场景 `自检通过。`、探针 `无问题`。
- **冻结场景的 10 处 probe.json 差异**（页高、Tab 停靠数，相对 `2026-10-16-7454494-base`）在 `1774cd5` 上就已存在，与 017 无关。017 与 `1774cd5` 构建出的五个场景页逐字节相同。
- **遗留**：F3 的「台风 / 闭园」写在闭园那两天的空档里。空档宽 3P ≈ 18 个单位，10 号字两个字宽 20，所以两侧各压到相邻竖线约 1 个单位；探针只比字和字，看不到这种情况。可选的修法：改成竖排单列（四个字，每行 `G.type.label * 1.25`），或者挪出空档、用引线标注。两轮 REVISE 已用完，没有退回执行者，留给维护者决定。
- **派发 018 之前**：新开的 worktree 很可能还是从远端 main 开出，看不到只合进本地 main 的 017。执行者第一步要从本地 `main` 开分支（`git checkout -b advisor/018-… main`，worktree 与主仓库共享分支引用），并用 `grep -n 'type: { tick: 9' skills/show-me-html/assets/charts.js` 确认起点已含 017。

### 未规划（记录在案，维护者决定是否另开计划）

- **窄屏上的通栏图**：500px 视口下，gallery 的 9 张通栏图（800 宽 viewBox 压到约 430px）字号渲染后只有 3.3–4.8px，017 之后约 4.8–5.4px；维护者那页的 G10 在 500px 下是 6–6.7px。示意图已有「窄屏另画一版」的机制（diagrams.md），数据图没有。也是这个原因，017 的字号下限与 019 的倍率检查都只在 1280px 报。
- **48rem 版心的双栏半宽卡**：各类 explainer 配方的 `.charts` 里，半宽卡只有约 334px，0.84 倍，9 号字渲染后约 7.5px。在 019 的阈值之内，属于已知余量不足。
- **语法高亮**：`--syn-comment`（`--ink-45`）与 `--syn-string`（`--ink-60`）在代码块底色 `--ink-8` 上只有 2.6–4.1:1，`.shj-syn-err` 用的主角色也不够。018 的检查跳过 `pre`，代码块观感留给维护者决定。
- **来源行里裸写的标识符被大写**：010 只给 `.src` 里的 `<code>` 免了大写，裸写的 `dt=20261020` 仍显示为 `DT=20261020`。
- **维护者那页本身**（不在本仓库）：三份计划合入后重建，F12 与来源行会自动变好；还要手改三处：页面脚本常量 `MUTED = I45` 改为 `"var(--color-muted-foreground)"`；G4 图例和 G10 主角数值的文字 `fill` 从 `HERO` 改为 `"var(--chart-hero-text)"`；F5 加 `.wide`、viewBox 改为 `0 0 800 …`、一根刻度改为 0.05 个百分点（也门 96 根）并按新宽度重算 `GAP`，单位行同步改写。
- **未查明的观察**：advisor 在没有防闪烁脚本的测试夹具上强制暗色时，数据图有一次没有画出来；`recipe-matrix.html` 夹具在本机暗色外观下 `contenteditable` 的字与底色几乎相同（1.10:1）。两者都只出现在缺 `<head>` 主题脚本的夹具上，真实页面没有复现；018 把渲染检查固定在亮色，不受影响。

### Findings considered and rejected

- **字号下限改按渲染像素量（`getScreenCTM`）**：60rem 版心下标准 viewBox 大约按 1:1 显示，按 viewBox 单位核对已经等于按像素核对，而且与视口无关；改按像素量，每张通栏图都会在 500px 下失败。改为保留 viewBox 单位，由 019 的倍率检查守住「约 1:1」这个前提。
- **运行时按显示宽度动态换算字号**：字号随宽度变、排版几何不变，窄屏上必然互相压字。
- **CSS 给单张 `.fig` 限宽，让它保持半宽**：这是版式决定，维护者没有要求；单张图写成通栏更符合现有的阅读顺序。
- **把文字重叠检查放进 `build.py`**：用户页面的排法千差万别，误报代价高；先在 gallery 上积累，复现第二次再考虑毕业（MAINTENANCE.md「毕业规则」）。

## show-me-html 构建耗时（2026-10-22，基线 `2f0e439`）

由 improve 技能的 `plan` 变体应维护者请求生成。起因是维护者本机的一份调研（`docs/research/2026-10-22-show-me-html-build-time-handoff.md`，写作时未入库）：一页 status-report 报告做了 32 分钟，其中 20.5 分钟在等 `build.py` 的无头 Chrome。原因有两层：一次 `--snap` 冷启动 Chrome 11 次；Chrome 不读代理环境变量，每次直连 Google Fonts，单次 12～69 秒。另一半时间花在 7 轮返工上，4 轮出在表格里被压成竖条的长标识符；还有一处图内文字越出图框，构建和眼检都漏了。

advisor 在 scratchpad 里预演过各计划的关键代码：带代理的单次渲染 45.8 秒 → 8.3 秒（020）；021 的运行器与 `build.py` 改动套在 `2f0e439` 的副本上，全量单元测试 51 个 OK，status-report 的 `--snap` 266.8 秒 → 13.8 秒，五个冻结场景和两个夹具的 ERROR / WARN 与改前相同；022 的 gallery 截图 118/118 张、53 秒，`--pdf` 出 A4；023 在五个场景页、两个夹具和 gallery 上零误报；024 的样张复现了竖条；025 的探针在三个场景页和一个故意写坏的页面上跑通；026 只给 concept-explainer 的导出多出一行图摘要；027 在打印模拟下量过看板列宽，PDF 看过。

### Decisions recorded（2026-10-22，维护者）

- 执行顺序：020 → 018 → 019 → 021；其余在各自依赖之后。
- 018 的对比度检查报 ERROR；F3「台风 / 闭园」并进 018。
- 代理透传默认开启；检查时照常加载字体，不屏蔽（017 / 019 的阈值是在真实字体下定的）。
- 只留 CDP 一条路径：没有 node 与没有 Chrome 一样报「渲染检查未运行」。
- 渲染检查加 390px 手机视口，横向溢出只报 WARN。
- 表格长标识符先出样张，维护者看过再定（024 在 Step 2 停下）。
- 候选项全部纳入：打印的两个旧问题写成 027；`--pdf` 并进 022；`visual-system.md` 打印一行的措辞当天直接收窄（没有单独的计划）。

以下由 advisor 定，维护者可改：渲染检查在 reduced motion 下量、运行器总是模拟 `prefers-color-scheme`（021，理由见其 Maintenance notes）；越框文字报 WARN（023）；看板打印固定两列、`.card` 在打印时一律整块换页（027）；快照切片高度 1500 / 1600px（021）。

**已确认（2026-10-22，维护者）**：`--snap` 默认宽度保留 500，按 390、500、1280 三种拍。500 是 500–900px 中等宽度（例如看板变成两列的样子）唯一的默认截图。

### Execution order & status

| Plan | Title                                                                    | Priority | Effort | Depends on    | Status                                                                               |
| ---- | ------------------------------------------------------------------------ | -------- | ------ | ------------- | ------------------------------------------------------------------------------------ |
| 020  | 无头 Chrome 走环境变量里的代理，修正折叠与侧栏两处文档                   | P1       | S      | —             | DONE（2026-10-22 审阅通过，快进合入 main `cbfff66` + `21aaae9`；见「020 执行记录」） |
| 021  | 一次构建只启动一个 Chrome：渲染检查、快照切片与定尺卡截图改走 CDP 运行器 | P1       | L      | 020、018、019 | TODO                                                                                 |
| 022  | gallery 截图改走运行器，`build.py` 加 `--pdf`                            | P2       | S      | 021           | TODO                                                                                 |
| 023  | 构建报出越出 SVG 图框、会被裁掉的文字（WARN）                            | P2       | S      | 018、019、021 | TODO                                                                                 |
| 024  | 表格里的长标识符不再被压成竖条（先出样张，维护者选定后实现）             | P2       | S      | —             | TODO                                                                                 |
| 025  | 单页交互探针 `probe_page.mjs`                                            | P3       | M      | 021           | TODO                                                                                 |
| 026  | Markdown 导出带上图的 `<desc>`                                           | P3       | S      | —             | TODO                                                                                 |
| 027  | 打印时卡片不从中间劈开，看板的列按纸宽排下                               | P2       | S      | —             | TODO                                                                                 |

018、019 的行在上一节。完整顺序：020 → 018 → 019 → 021 → 022 → 023 → 025；024、026、027 不依赖别的计划，可以穿插在任何位置。

### Dependency notes

- 020 只给 `build.py` 三处 Chrome 启动加参数，不碰 018 / 019 的锚点（`PROBE` 末尾、正则、`render_check` 的返回值）。018、019 的 drift check 已补注：`7c94bce` 和 020 的改动属于预期，测试数各加 1。
- 021 只换「怎么拿到 `PROBE` 写进标题的结果」，约定和正则不动；放在 019 之后，是因为 390 的溢出要用 019 加的 `notes` 报成 WARN。
- 022、025 用 021 新建的 `scripts/render.mjs`、`scripts/cdp.mjs`。022 删掉 020 的 Python 版 `chrome_proxy_args`，测试改测 `cdp.mjs`。
- 023 在 `PROBE` 末尾再追加一段（`clipped`），需要 021 让渲染检查在 reduced motion 下量：不然 G11 力导向图在节点布局完成前被量到，20 个标签全被误报。
- 024、027 都改 `show-me.css`，改的段落不同；021 改 `compose-and-check.md` 的「渲染级」「眼睛关」几句，025 再改其中一句，018 改同文件末尾的「已知缺口」，互不重叠。

### 020 执行记录（2026-10-22）

- **审阅**：一次通过，无 REVISE。advisor 在分支上独立复跑：49 个测试 OK（比 main 多 1）；计划的 grep / `py_compile` / `node --check` 全部命中预期；`make check` 通过；diff 和提交说明里没有真实代理地址。冻结场景轮次 `2026-10-22-21aaae9-020`（建在执行者 worktree 里，清理后不留存）对 `2026-10-22-6d39fa5-printbreak`：30 张截图逐字节相同，`probe.json` 相同。`probe_round.mjs` 里的 `PROXY_ARGS` 被 pre-commit 的 prettier 拆成多行，逻辑与计划一致。
- **提速**：执行者 Step 4 量到带代理 41.99 秒、不带 41.81 秒，没测出差别。advisor 按顺序交替复测 status-report 的完整构建：带代理 43.3 / 30.3 秒，不带 119.3 / 106.9 秒；单次 `--dump-dom` 渲染 9～10 秒对 13 秒。直连的耗时随网络起伏很大，执行者那次的差别没有复现。
- **基线失败**：执行者在改动前的 main 上跑全量测试，`test_snap_renders_both_themes_and_exports_markdown` 两次失败于 `dark-500`（48 个里 1 个失败），改动后通过。很可能是直连时字体请求拖到截图超时，没有单独核实。018、019 的执行者若在没配代理的环境里跑，可能遇到同样的失败。

### Findings considered and rejected

- **检查时屏蔽 Google Fonts**（调研建议 2b）：最快，但几何按兜底字体量，017 / 019 的阈值是在真实字体下定的；代理透传已经拿到大部分提速。
- **没有 node 时退回多次冷启动**：两条路径的等待机制不同，结果会分叉；维护者决定只留一条。
- **charts.md 顶部加「编号 → gallery 文件 → 块名」速查表**（调研建议 11）：读文档只占那次会话 2.6 分钟，「数据形状 → 候选」「运行时与查代码」两节已经承担这个作用。
- **`PROBE` 改为直接返回 JSON**：要同时改 017–019、023 的全部解析代码，收益只是代码整洁，以后单独做。
- **800 宽通栏数据图在窄屏过小**（调研第 7 条的「配套」）：与上一节「未规划」里的「窄屏上的通栏图」是同一件事，不重复登记。
