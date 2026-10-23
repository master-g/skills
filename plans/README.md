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

**已确认（2026-10-22，维护者）**：018 的对比度检查报 ERROR（ERROR 能挡住带病交付，与图内字号下限一致；代价是重建旧页面时，页面自己写的淡色文字会让构建失败，`--open` 也不会打开）。同日维护者还定了：017 遗留的 F3「台风 / 闭园」并进 018（Step 5 第 3 小步，竖排单列）；执行顺序改为 020 → 018 → 019，见下一节。告急按钮在亮色主题下改为橙底深字（`--destructive-foreground: var(--ink-fixed)`，两种主题都是 5.1:1），维护者在派发 018 时确认；备选的「底色改 `--hero-text`、字仍用纸色」（亮 5.8:1、暗 8.1:1）没有采用，因为按钮会离开纯 `--hero`，多出一个危险色。

### Execution order & status

| Plan | Title                                                    | Priority | Effort | Depends on           | Status                                                                                                           |
| ---- | -------------------------------------------------------- | -------- | ------ | -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 017  | 图内字号升一档（9 / 10 / 10），下限改为任何文字不小于 9  | P1       | L      | —                    | DONE（2026-10-22 审阅通过并合入 main `bdbeae5..adfb03d`；遗留一处 F3 小瑕疵，见下方「017 执行记录」）            |
| 018  | 次要文字与图内文字对比度达到 4.5:1，构建加文字对比度检查 | P1       | M      | 017（建议顺序）、020 | DONE（2026-10-22 审阅通过，一轮 REVISE；快进合入 main `afcdb48..5820240` 共 5 个提交；见「018 执行记录」）       |
| 019  | 图被拉大或压小时构建报 WARN，charts.md 写清单张图怎么排  | P2       | S      | 017、018（建议顺序） | DONE（2026-10-22 审阅通过；执行中按 STOP 停过一次，计划修订后续跑；快进合入 main `63cb3f9`；见「019 执行记录」） |

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

### 018 执行记录（2026-10-22）

- **派发前**：advisor 在 `15d5ddc` 上核对过锚点；计划补了三条（测试数各加 1、F3 的引文换行不同、Step 7 改对 `2026-10-22-6d39fa5-printbreak`），执行者读的是这一版的只读快照。维护者确认告急按钮改为橙底深字。执行中途 API 超时断过一次，从断点续跑，没有丢改动。
- **工作清单**：首次构建报「等 31 组」，放开显示上限后是 33 组、25 张图（计划写 29 张图），没有表外的图。
- **REVISE（1 轮）**：L16 被并成四档（`40+`），副标题仍写「分五档」，改回五档 `I14 / I22 / I30 / I70 / 墨`，前三格的数字在 `I30` 及更浅的格上用墨色。G13 的 15m、30m 环标签先于扇形画、一直被 Editor 扇形盖住（main `15d5ddc` 上就是先画环、后画扇形），探针按盖住它的扇形量出低对比度，执行者只改了字色；改为扇形之后再画，字色按 12 点钟扇形 `byShare[0]` 选。两个新 token 的行尾注释被 prettier 拆行，挪到声明上一行。G16 数字的过渡从行内样式挪进 `show-me.css` 的 `.race-num`，并加进 reduced motion 列表。
- **接受的偏离**：B2 中心节点 `I60 / I45` 换成相邻的 `I70 / I30`（计划允许），节点字按底色选墨或纸。G16 的数字改成随条尖平移（`translateX`，与条宽同一 950ms 线性过渡），收缩途中不再压在条上。G21 主角色格里的字用 `--ink-fixed`。
- **advisor 在 `5820240` 上独立复跑**：50 个测试 OK；gallery `--shots` 118/118、`问题 0 条`、没有对比度报错（L16、G13、G16、G21、F3、B2 的亮暗截图看过）；五个冻结场景 `自检通过。`、探针 `无问题`、`probe.json` 与 printbreak 相同、打印页数不变；组件夹具加卡内链接按钮后 `自检通过。`；`make check`、prettier 通过。status-report 亮色截图层级清楚。
- **观察**：探针量 SVG 字的底色时不判断字是否被后画的图形盖住，被盖住的字会按盖住它的图形算（G13 就是这样暴露的）。G16 的 40px 年份水印按计划从 `I14` 改成 `I60`，从水印变成图里第二显眼的元素；维护者 2026-10-22 确认保留（动画里它是当前年份的唯一读数，大字要 3:1，`I45` 只有 2.8:1，`I60` 是最浅能过的一档）。执行者在 `15d5ddc` 基线上跑全量测试时 `test_render_check_measures_only_the_shown_diagram_variant` 两次失败（量到 485px，预期 500px），之后通过。差的 15px 正好是一条滚动条：`render_check` 是 `build.py` 里唯一没传 `--hide-scrollbars` 的 Chrome 调用，macOS 是否给滚动条留宽随系统设置和是否接鼠标变化，可能就是时有时无的原因（没有核实；021 的 CDP 运行器会替换这个调用点）；advisor 有一次 gallery 截图因 Chrome 很慢失败 15 张，重跑 118/118。

### 019 执行记录（2026-10-22）

- **派发前**：advisor 在 `c41e44e` 上核对锚点（018 已合入的那组），计划补了测试数、Step 6 改对 `2026-10-22-5820240-018`（从 018 执行者的 worktree 复制到主检出的轮次目录）、偶发测试只重跑不修。
- **STOP 与修订**：执行者在 Step 3 按 STOP 条件停下，新测试的单张图报 3.10 倍（计划预期 2.2–2.4）。原因在计划：`tests/fixtures/minimal-shell.html` 没有骨架包在 `<main>` 外面的 `<div class="layout">`，60rem 版心的宽度上限挂在 `.layout` 上，夹具内容在 1280px 下铺到约 1240px；并排两张也有 1.48 倍，离阈值太近。测试改为先套上 `.layout`（单张 856px、2.14 倍，并排 0.99 倍），STOP 范围改为 2.0–2.3；反例原来只查 `#solo`，并排用例的 id 是 left / right，误报会漏过去，改为断言输出里没有任何「显示倍率」。同一执行者按修订版续跑。
- **advisor 在 `63cb3f9` 上独立复跑**：51 个测试 OK，新测试单跑 OK；计划的 grep、语法检查、`make check` 通过；gallery 构建「显示倍率」0 处；冻结场景轮次 `2026-10-22-c41e44e-019`（建在执行者 worktree 里，已随清理删除）对 `2026-10-22-5820240-018`：30 张截图逐字节相同、`probe.json` 相同。`render_check` 只有 `main()` 一个调用方，返回值改成四项不影响别处。

### 未规划（记录在案，维护者决定是否另开计划）

- **窄屏上的通栏图**：500px 视口下，gallery 的 9 张通栏图（800 宽 viewBox 压到约 430px）字号渲染后只有 3.3–4.8px，017 之后约 4.8–5.4px；维护者那页的 G10 在 500px 下是 6–6.7px。示意图已有「窄屏另画一版」的机制（diagrams.md），数据图没有。也是这个原因，017 的字号下限与 019 的倍率检查都只在 1280px 报。
- **48rem 版心的双栏半宽卡**：各类 explainer 配方的 `.charts` 里，半宽卡只有约 334px，0.84 倍，9 号字渲染后约 7.5px。在 019 的阈值之内，属于已知余量不足。
- **SVG 文字被后画的图形盖住**：018 的对比度探针用 `elementsFromPoint` 取文字中心处最上面的填充图形当底色，不判断文字是否被盖住。被盖住的字会按盖住它的图形算，可能误报（G13 的环标签就是这样暴露的），也可能漏掉「字根本看不见」这一类问题。
- **语法高亮**：`--syn-comment`（`--ink-45`）与 `--syn-string`（`--ink-60`）在代码块底色 `--ink-8` 上只有 2.6–4.1:1，`.shj-syn-err` 用的主角色也不够。018 的检查跳过 `pre`，代码块观感留给维护者决定。
- **来源行里裸写的标识符被大写**：010 只给 `.src` 里的 `<code>` 免了大写，裸写的 `dt=20261020` 仍显示为 `DT=20261020`。
- **维护者那页本身**（不在本仓库）：三份计划合入后重建，F12 与来源行会自动变好；还要手改三处：页面脚本常量 `MUTED = I45` 改为 `"var(--color-muted-foreground)"`；G4 图例和 G10 主角数值的文字 `fill` 从 `HERO` 改为 `"var(--chart-hero-text)"`；F5 加 `.wide`、viewBox 改为 `0 0 800 …`、一根刻度改为 0.05 个百分点（也门 96 根）并按新宽度重算 `GAP`，单位行同步改写。
- **多卡 `--shot` 从第 2 张起截出来是空白**（021 冷读时发现，改前改后都一样）：`shoot_sheets` 用 `.sheet-stage:nth-of-type(k)` 隐藏其他卡，而 `nth-of-type` 按各自所在的 section 计数；按 layouts.md 的写法每张卡各占一个 section，于是除第 1 张以外的截图里，所有卡都被隐藏。
- **冻结场景探针的 PDF 是 Letter**（022 冷读时发现）：`probe_round.mjs` 调 `Page.printToPDF {}` 时没传 `preferCSSPageSize`，`_probe/*.pdf` 都是 612 × 792。所以它报的「打印页数」不是读者实际用 A4 打印时的页数。
- **最小夹具 `--pdf` 多出一张空白页**（022 冷读时发现）：原因已在 027 冷读时核实为 `body { min-height: 100vh }`，修法写进 027 的 Step 4。
- **`<div class="progress">` 没有填充色**（027 冷读时发现）：components.md「其余」写了 `<div class="progress"><span style="width:64%"></span></div>`，但 `show-me.css:805–822` 只给 `.progress` 写了底色，里面的 `span` 是行内元素、没有背景，屏幕上也看不到数值。要么补 `.progress > span { display: block; height: 100%; background: var(--color-primary); }`，要么从文档里删掉这种写法。
- **打印时代码块不换行，长行被裁**（027 复核时看到，改前就有）：approach-compare 的方案卡里 `SELECT … FOR UPDATE SKIP LOCKED` 在 PDF 里只剩 `SELECT … FOR UPDATE S`。屏幕上 `pre` 可以横向滚动，纸上不能；打印样式里可以给 `pre` 加 `white-space: pre-wrap`。
- **`cdp.mjs` 不处理信号**（025 冷读时发现）：直接跑 `probe_round.mjs` 时被 Ctrl-C 之外的信号（例如命令超时的 SIGTERM）打断，Chrome 会成孤儿进程、配置目录留下。`build.py` 调运行器时有进程组兜底；025 的 `probe_page.mjs` 自己接了信号。要统一修，就在 `launch()` 里接 SIGINT / SIGTERM。
- **卡住的网络请求拖住虚拟时间**（022 复核时遇到一次）：运行器按 `pauseIfNetworkFetchesPending` 等待，某个请求（多半是字体）一直不返回时，虚拟时间预算永远用不完，任务要等 90 秒真实超时后才失败，重跑就好。改前的 `--virtual-time-budget` 也是同样的语义。如果以后变得常见，可以考虑给虚拟时间加一个真实时间上限，到点后改为放行。
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

2026-10-23 维护者决定：打印和 `--pdf` 都不打背景色，`--pdf` 不打开 `printBackground`；承载含义的底色（diff 增删行 `.d-add` / `.d-del`、代码块 `pre`、进度条 `progress`）在打印样式里用 `print-color-adjust: exact` 保留，并入 027 的 Step 3。依据：advisor 用 code-review 冻结场景页对比，不打背景时 diff 只剩 `+` / `-` 号，加这条规则后增删行底色和代码块灰底都保留，装饰性底色照常省掉。

2026-10-23 维护者决定：024 提到 023 前面，先由 advisor 在临时目录做 024 的 Step 1–2 样张交维护者选；维护者看样张期间做 023 的冷读审阅。依据：交接调研里 7 轮返工有 4 轮出在被压成竖条的长标识符，024 是剩余计划里对应返工最多的一项，且它的必停点要等维护者。同日维护者看过样张选 d：表格内 `code` 改成 `overflow-wrap: break-word`，components.md 教作者在标识符的 `_`、`/` 后插 `<wbr>`；没插时整表横向滚动。

以下由 advisor 定，维护者可改：渲染检查在 reduced motion 下量、运行器总是模拟 `prefers-color-scheme`（021，理由见其 Maintenance notes）；越框文字报 WARN（023）；看板打印固定两列、`.card` 在打印时一律整块换页（027）；快照切片高度 1500 / 1600px（021）；021 审阅后补定：Node 早于 22 与没有 node 同样报「未运行」，`cdp.mjs` 保留 `--no-sandbox`，`--shot` 读到卡片被缩放就报错、不交出缩小的图。

**已确认（2026-10-22，维护者）**：`--snap` 默认宽度保留 500，按 390、500、1280 三种拍。500 是 500–900px 中等宽度（例如看板变成两列的样子）唯一的默认截图。

### Execution order & status

| Plan | Title                                                                            | Priority | Effort | Depends on    | Status                                                                               |
| ---- | -------------------------------------------------------------------------------- | -------- | ------ | ------------- | ------------------------------------------------------------------------------------ |
| 020  | 无头 Chrome 走环境变量里的代理，修正折叠与侧栏两处文档                           | P1       | S      | —             | DONE（2026-10-22 审阅通过，快进合入 main `cbfff66` + `21aaae9`；见「020 执行记录」） |
| 021  | 一次构建只启动一个 Chrome：渲染检查、快照切片与定尺卡截图改走 CDP 运行器         | P1       | L      | 020、018、019 | DONE（2026-10-23 审阅通过，快进合入 main `d134ce1` + `47a158d`；见「021 执行记录」） |
| 022  | gallery 截图改走运行器，`build.py` 加 `--pdf`                                    | P2       | S      | 021           | DONE（2026-10-23 审阅通过，快进合入 main `45326da` + `b52953a`；见「022 执行记录」） |
| 023  | 构建报出越出 SVG 图框、会被裁掉的文字（WARN）                                    | P2       | S      | 018、019、021 | DONE（2026-10-23 审阅通过，拣到 main 为 `a99b310`；见「023 执行记录」）              |
| 024  | 表格里的长标识符不再被压成竖条：表格内 `code` 不在词中断开，文档教作者插 `<wbr>` | P2       | S      | —             | DONE（2026-10-23 维护者选 d；审阅通过，拣到 main 为 `f580de6`；见「024 执行记录」）  |
| 025  | 单页交互探针 `probe_page.mjs`                                                    | P3       | M      | 021           | DONE（2026-10-23 审阅通过，拣到 main 为 `ae5fa79`；见「025 执行记录」）              |
| 026  | Markdown 导出带上图的 `<desc>`                                                   | P3       | S      | —             | TODO                                                                                 |
| 027  | 打印时卡片不从中间劈开，看板的列按纸宽排下，有含义的底色保留，短页不多出空白页   | P2       | S      | 022           | TODO（2026-10-23 冷读审阅后改写，维护者确认保留 Step 4，已派发；见「027 审阅记录」） |

018、019 的行在上一节。完整顺序：020 → 018 → 019 → 021 → 022 → 024（样张）→ 023 → 025；024 选定后的实现、026 不依赖别的计划，可以穿插在任何位置；027 用 022 的 `--pdf` 验证，022 已合入，也可随时做。

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

### 021 审阅记录（2026-10-23）

- **冷读**：一个没有本会话上下文的子代理把初版计划原样套到 `a2c1798` 的副本上跑了一遍。初版计划自带的验证全部能过，交付物却有两处错误，都已复现：
  - `render.mjs` 写完 stdout 立刻 `process.exit`。macOS 上写管道是异步的，超过 64 KB 的部分丢失，gallery 总览页的默认 `--snap` 因此 `JSONDecodeError`。初版只用五个场景页验证，它们的 export.md 只有 1–2 KB，测不出来。
  - `--shot` 的卡被 `shell.js` 的 `fit()` 缩到 0.947 倍，右侧和底部露白。`SHOT_CSS` 追加在文件末尾，`fit()` 执行时还没生效；改前靠 `--window-size` 之后的一次 `resize` 掩盖了，CDP 不会触发这次 resize。
- **其余问题**：
  - Node 早于 22 时构建失败，还留下孤儿 Chrome。
  - Chrome 配置目录从不删除。`probe_round.mjs` 在 HEAD 上就有同样的泄漏：本机 `$TMPDIR` 已有 22 个 `probe-round-*`，共 1.8 GB。
  - 漏了 `--no-sandbox`。
  - Step 4 的 subprocess 计数写错。
  - gallery 对照的第 1 行含路径。
  - Step 9 的「数据图已画出」在五个场景页上无从检查，因为它们一张数据图都没有。
  - 轮次目录没指定，跨代码块用了变量，Git 工作流与新旧对照互相矛盾。
- **修订**：
  - 运行器等 stdout 写完再退出；`close()` 等 Chrome 退出后删配置目录；`launch()` 先查 `WebSocket`，失败时先收拾再抛错。
  - `run_jobs` 让运行器单独成一个进程组，超时或 Ctrl-C 时连同 Chrome 一起结束；进程组恰好已经退出时忽略 `ProcessLookupError`，否则它会盖掉原来的 `KeyboardInterrupt`（复跑时撞到过）；用 UTF-8 解码；输出不是 JSON 时报错，不再崩溃。
  - 390 那一档没返回结果时报 WARN。
  - `SHOT_CSS` 移进 `<head>`，每个截图任务读出卡片的 `transform`，有缩放就报错。
  - 新增两个测试：64 KB 以上的输出、`--shot` 不缩放。计划要求对后者做一次反证。
  - Step 9 改用 gallery 总览页检查首屏外的数据图，新增新旧 `--shot` 对照，轮次固定对 `2026-10-22-5820240-018`。
  - Scope 加技能 `README.md` 目录表的两行。
- **advisor 把修订版代码块原样套到 HEAD 副本上复跑**：
  - 静态检查：`py_compile` 和三个 `node --check` 通过，计划里的 grep 计数全部命中。
  - 测试：`Ran 56 tests`、OK，用时 26 秒；`--shot` 测试在样式改回文末时失败（`scale(0.946667)`），改回后通过。
  - Step 2：`--no-experimental-websocket` 下退出码 3；运行前后 `show-me-cdp-*` 目录数不变。
  - gallery 总览页默认 `--snap` 出 111 个文件，含渲染检查共 44.7 秒，首屏外切片里的数据图已画出。
  - Step 1：新旧 `probe_round` 对 018 轮，五页 `无问题`，`probe.json` 相同，30/30 张截图逐字节相同（`--no-sandbox` 不影响截图），新版不再留下 `probe-round-*` 目录。
  - 中断：任务进行中模拟 Ctrl-C，抛出 `KeyboardInterrupt`，之后没有残留的 Chrome 或 node。

### 021 执行记录（2026-10-23）

- **执行**：一次完成，没有 STOP，没有 REVISE。执行者为装 git 钩子在 worktree 里跑了 `npm install`，它改动的 `package-lock.json` 已还原，没进提交。
- **advisor 复核，代码**：把计划代码块原样套到 `main` 的副本上，与分支逐字比对。
  - `test_build.py` 相同。
  - 三个 `.mjs` 按仓库 prettier 配置格式化后相同。
  - `build.py` 只在「整页快照」一节前多一个空行。
  - 文档改动与计划一致。
- **advisor 复核，验证**：
  - `Ran 56 tests` OK，34.7 秒。执行者在改前的 `main` 上跑同一套 51 个测试用了 238 秒。
  - 计划里的 grep 全部命中，三个 `node --check` 通过，`make check` 通过。
  - Step 9.1 七页加 gallery 都「相同」，没有新的 390 WARN，也没有滚动条宽度造成的差异。
  - 运行后没有 `show-me-cdp-*` 残留；新增的 4 个 `probe-round-*` 是改前版本在对照时留下的。
- **截图字节差异**：
  - 执行者 Step 1 第一次对照是 29/30（`code-review-light-1280`），重跑两次都是 30/30。
  - 轮次 `2026-10-23-47a158d-021` 对 018 轮也是 29/30（`concept-explainer-light-500`）。advisor 用 ImageMagick 逐像素比对，只差 1 个像素（AE=1），属于抗锯齿噪声。
- **耗时**：status-report 的 `--snap`（390/500/1280 × 两个主题）用 10.99 秒。
- **没改**：`visual-system.md:130` 的「390px 人工截图」说的是冻结场景流程，计划没要求改。
- **合入**：维护者 2026-10-23 确认，快进合入、推送并 `make install`。轮次 `2026-10-23-47a158d-021` 已复制到主检出，作为下一轮的对照基线。执行者的 worktree、分支，以及对照时留下的 4 个 `probe-round-*` 都已删除。

### 022 审阅记录（2026-10-23）

- **冷读**：子代理把初版计划原样套到 `be84c43` 的副本上跑了一遍。初版自带的检查全部通过，但它复现出一处交付错误：`--pdf` 打出的 PDF 里，首屏以下的数据图是空白的。
  - 原因是 `charts.js` 的 reveal 只在图滚入视口时才画。初版的测试夹具和五个冻结场景页都没有数据图，所以测不出来。
  - 证据：不补画时，`pdftotext` 只读得到首屏那张图的标签；gallery 的 basics 页打印时，17 个 SVG 里 15 个是空的。
  - 只补画、不开 reduced motion 时，打出来的是动画第一帧。
- **其余问题**：
  - 完成条件「`chrome_proxy_args` 计数全为 0」做不到：`cdp.mjs:7` 的注释提到它，而 `cdp.mjs` 不在 Scope 里。执行者还可能把这行注释当成「另有调用方」而停下。
  - 没写在哪个检出目录里工作。
  - 回归步骤拿 Letter 纸的 `_probe/*.pdf` 比 A4 的页数。
  - 截图批次整体失败时，运行器报的错误原因会丢。
  - `tail -6` 看不到要核对的那几行；变量跨代码块使用。
  - MediaBox 断言失败时，会把整份 PDF 字节打印出来。
  - 没跑冻结场景轮次。
- **修订**：
  - 运行器加 `drawAll()`，切片和 PDF 共用；`print_pdf` 传 `reduced`。
  - 新增 `test_pdf_draws_charts_below_the_fold`（用 `pdftotext`），计划要求做一次反证。
  - `cdp.mjs` 注释进 Scope；Git 工作流照搬 021。
  - 截图批次失败时直接退出，并打印运行器的错误；给出与旧版对照的完整命令。
  - Step 6 改为只验 A4，另用 gallery 页出 PDF、人眼看末帧，再跑一轮冻结场景轮次。
- **advisor 把修订版代码块原样套到 HEAD 副本上复跑**：
  - 静态检查：语法检查通过，计划里的 grep 计数全部命中。
  - 测试：`Ran 58 tests` OK，34.9 秒。反证时去掉 `pdf` 分支的 `drawAll()`，新测试失败（PDF 里只有 TOPLABEL），改回后通过。
  - gallery `--shots`：118/118，`问题 0 条`，34.99 秒。
  - PDF：approach-compare 是 A4、2 页；gallery PDF 第 4–6 页的图都已画出，是末帧。
  - 运行后没有 `show-me-cdp-*` 残留。

### 022 执行记录（2026-10-23）

- **执行**：一次完成，没有 STOP，没有 REVISE。执行者把 Step 1 并进了第一个提交，把 Step 3、Step 5 并进了第二个提交，这只是提交的切分方式。
- **advisor 复核，代码**：把计划代码块原样套到 `main` 的副本上，与分支逐字比对，6 个文件全部相同（`.mjs` 和 `SKILL.md` 按仓库 prettier 配置格式化后比对）。
- **advisor 复核，验证**：
  - `Ran 58 tests` OK，计划里的 grep、语法检查、`make check` 都通过。
  - gallery `--shots`：118/118，`问题 0 条`，44.5 秒。执行者那次 40.6 秒。
  - approach-compare 的 PDF 是 A4、2 页；gallery PDF 第 4–9 页的图都已画出，是末帧。
  - 冻结场景轮次 `2026-10-23-b52953a-022` 对 021 轮：`probe.json` 相同，29/30。不同的一张是 `concept-explainer-light-500`，只差 1 个像素（AE=1），属于抗锯齿噪声。
  - 运行后没有残留的 Chrome 配置目录。
- **偶发超时**：advisor 复跑时，gallery 页的 `--pdf` 有一次报「等 `Emulation.virtualTimeBudgetExpired` 超时」。紧接着连跑 3 次都成功，每次约 4 秒。那一轮全量测试也比平时慢（52.8 秒，平时约 35 秒），推测是某个字体请求卡住，虚拟时间一直停着不走。改前的 `--virtual-time-budget` 等的是同一个条件，所以这不是 022 引入的问题，记进「未规划」。
- **合入**：维护者 2026-10-23 确认，快进合入、推送并 `make install`。轮次 `2026-10-23-b52953a-022` 已复制到主检出，作为下一轮的对照基线。执行者的 worktree、分支和审阅用的 /tmp 副本都已删除。

### 024 样张记录（2026-10-23）

advisor 在 `90fb8af` 上按计划 Step 1–2 做样张（临时目录，不进仓库），另加两页对照：d 是分支 B 的规则加 `<wbr>`，e 是只给含 `code` 的格子设 `min-width: 12ch`。用运行器量表格（容器宽 388px 时）：

| 样张             | 390px 表格宽 / 高 | 键名、模块列宽 | 1280px                     | 看到的                                             |
| ---------------- | ----------------- | -------------- | -------------------------- | -------------------------------------------------- |
| a-base           | 388 / 847         | 67 / 70        | 不横滚，标识符行尾任意处断 | 每行 4–5 个字符的竖条                              |
| b-break-word     | 994 / 655         | 361 / 408      | 不横滚，标识符各占一行     | 整表横向滚动，首屏只看得到键名列                   |
| c-wbr            | 388 / 983         | 67 / 70        | 同 a                       | 和 a 一样是竖条：`anywhere` 仍允许词中断开         |
| d-break-word-wbr | 444 / 701         | 98 / 120       | 在 `_`、`/` 处断           | 在 `_`、`/` 处断开，最后一列需要拖一点             |
| e-min-width      | 423 / 724         | 99 / 99        | 同 a                       | 每行约 12 个字符，词中任意处断，最后一列需要拖一点 |

计划的分支 A（只在文档里让作者插 `<wbr>`）在现行 CSS 下没有效果，c 证明了这一点；要让 `<wbr>` 起作用，必须同时有分支 B 的规则（即 d）。

维护者选 d。advisor 把 024 改写成单一路径（样张阶段并入 Step 1 与 Step 4 的列宽对照，用运行器的 `eval` 量，给出数值范围），套到 `90fb8af` 的副本上跑通：改前两页的键名列都是 67px；改后不插 `<wbr>` 的一页 994 / 361，插了的一页 444 / 98 / 120；58 个测试 OK，`make check` 通过；冻结场景轮次对 `2026-10-23-b52953a-022`：五页 `无问题`，`probe.json` 相同，30/30 张截图逐字节相同（五个场景页的表格里没有 `code`）。按 advisor 复核又改了两处：生成样张的脚本写成 `$S/gen.py`，Step 4 直接重跑它，免得执行者重开临时目录；索引由审阅者维护，执行者不改 `plans/README.md`。改后的 Step 1、Step 4 原文在副本上重跑，数值相同。

### 023 审阅记录（2026-10-23）

- **冷读**：子代理把计划原样套到 `90fb8af` 的副本上执行，全部 Verify 满足，没有 BLOCKER / MAJOR。测试 58 → 59 个 OK；五个场景页、两个夹具、gallery 总览页的越框计数都是 0；`status-report` 改前改后各构建 3 次，耗时 2.1–2.8 秒，两组重叠。
- **advisor 复核**：副本里的新测试单跑 OK；gallery 总览页（59 张数据图）完整构建，越框 0；往 `status-report` 第一个 figure 的 SVG 里注入一段越出 viewBox 的文字，构建报出 `WARN 文字越出图框…`，`自检通过（1 个警告需逐条判断）`。五个场景页里没有 `figure[data-chart]` 数据图，误报的主要检验是 gallery 总览页，已写进 Step 4 的 Verify。冷读唯一没验证的一句（测试页那张半宽图在 1280px 下 019 另报倍率 WARN）也核对过：同时报 `显示倍率 … 3.10 倍` 和越框两条 WARN。
- **改了什么**：Step 4 的轮次目录原来用 `ls -d …/rounds/*/ | tail -1` 挑，靠字典序碰巧选中基线，改为写死 `2026-10-23-b52953a-022`（仍用主检出的绝对路径，因为 `rounds/` 只在主检出里），并说明用 bash 跑；gallery 那行从 `head -3` 改为 `grep -c '文字越出图框'`；charts.md 两处行号 148 / 292 → 149 / 293；页首加了审阅说明。

### 023 执行记录（2026-10-23）

- **执行**：一次完成，没有 STOP，没有 REVISE。执行者的 worktree 从 origin/main（`bdc10b6`）开出，不含本地 main 上两个未推送的计划提交；计划读的是只读快照，不受影响。
- **advisor 复核**：分支只改了计划范围内的 4 个文件；`build.py`、`test_build.py` 新增的代码与计划代码块逐行相同，两份文档的改动与 Step 5 原文相同。在 worktree 里重跑：59 个测试 OK，三条 grep 都是 1，`make check` 通过；Step 4 七个页面越框计数都是 0、`rc=0`、`自检通过。`，gallery 也是 0。新测试断言越框时报出确切的 WARN 文本、不越框时不报，两种情况构建都不失败。
- **合入**：维护者 2026-10-23 确认，`0bc1153` 拣到 main 为 `a99b310`。

### 024 执行记录（2026-10-23）

- **执行**：一次完成，没有 STOP，没有 REVISE。只改 `show-me.css`（+7）和 `components.md`（+2），与计划代码块逐行相同。
- **advisor 复核**：在 worktree 里按 Step 1 的脚本重新生成样张并量：不插 `<wbr>` 的一页 994 / 361，插了的一页 444 / 98 / 120，与计划预期相同；390 截图里键名在 `_` 后断、路径在 `/` 后断，没有词中断开。58 个测试 OK，`make check` 通过。冻结场景轮次 `2026-10-23-bdc10b6-024` 对 022 轮，执行者和 advisor 各跑一次探针：五页 `无问题`，`probe.json` 相同，30/30 张截图逐字节相同。
- **合入**：维护者 2026-10-23 确认，`2a86696` 拣到 main 为 `f580de6`；拣入后的 main 上 59 个测试 OK，推送并 `make install`。轮次 `2026-10-23-bdc10b6-024` 已复制到主检出，作为下一轮的对照基线；两个执行者的 worktree、分支和审阅用的 /tmp 副本都已删除。

### 025 审阅记录（2026-10-23）

- **冷读**：子代理把原计划套到 `3cf064c` 的副本上，Step 1–3 的 Verify 全部满足（triage-board 19 个控件 29.5 秒、code-review 2 个折叠加 3 个复选框、concept-explainer 390px 2 个滑块、坏按钮页退出码 1；筛选前后截图确有差别），没有 BLOCKER。MAJOR 4 条，advisor 逐条核实：
  - 脚本末尾 `close(); process.exit(...)` 没等 `close()`，每次运行留下一个 15–24 MB 的 Chrome 配置目录（021 之后 `close()` 是 Promise，原计划写于 021 之前）。
  - 页面路径不存在时 Chrome 打开错误页，探针报 `0 个控件`、退出码 0。
  - 运行中被 SIGTERM / SIGKILL 杀掉时 Chrome 成了孤儿进程，配置目录也留下。
  - 粘贴的 `.mjs` 不是 prettier 格式，提交钩子会整段改写，与「原样粘贴」冲突。
- **改了什么**：`existsSync` 前置检查，页面不存在退出 2；Chrome 起不来也退出 2 并给出原因；接 SIGINT / SIGTERM 去 `close()`，退出码 130 / 143；主体包进 try / finally，`await close()` 后再退出；配置目录前缀改为 `probe-page-cdp-`，输出目录改为 `probe-page-out-`，数残留时不混；js 代码块换成 prettier 格式，Step 1 后跑一次 prettier；Step 1 加三种错误用法的 Verify，Step 2 加残留计数和 SIGTERM 检查；轮次目录写死 `2026-10-23-bdc10b6-024`；`Current state` 写明 `close()` 是 Promise、`cdp.mjs` 不处理信号；索引由审阅者维护。
- **advisor 复跑**：改后的计划原文套到 `3cf064c` 的新副本上：三种错误用法都退出 2；四次实跑结果与上面相同，`exit=0 / 1` 符合预期；运行前后和 SIGTERM（退出 143）之后，`probe-page-cdp-*` 目录和 Chrome 进程都是 0；文档两处改完后 prettier 无改动，`grep -c 'probe_page.mjs'` 为 1，文档门禁通过。
- **没采纳**：冷读建议把「交互先跑 probe_page.mjs」移出「没有交互浏览器时」那一段。探针和 `--snap` 一样用无头 Chrome，正是给没有交互浏览器的 agent 用的，放在这段里没有问题。给 `cdp.mjs` 统一加信号处理（`probe_round.mjs` 也没有）另记，不在本计划里做。

### 025 执行记录（2026-10-23）

- **执行**：一次完成，没有 STOP，没有 REVISE。只改了 `probe_page.mjs`（新建）和 `compose-and-check.md`；脚本与计划代码块逐字节相同，prettier 没有改动。
- **advisor 复核**：在 worktree 里重跑：三种错误用法都退出 2；四次实跑与计划 Verify 一致（triage-board 19 个控件、code-review 2 个折叠加 3 个复选框、concept-explainer 390px 2 个滑块、坏按钮页 `exit=1`）；运行前后和 SIGTERM（退出 143）之后，配置目录和 Chrome 进程都是 0；59 个测试 OK，文档门禁通过。只加了脚本，没碰 `show-me.css`、骨架和 `build.py`，按 MAINTENANCE.md 不跑冻结场景轮次。
- **合入**：维护者 2026-10-23 确认，`e781794` 拣到 main 为 `ae5fa79`，去掉了执行者加的 `Co-Authored-By` 行（仓库其他提交都没有）；推送并 `make install`。worktree、分支和审阅用的 /tmp 文件都已删除。

### 027 审阅记录（2026-10-23）

- **冷读**：子代理把计划原样套到 `ab64edc` 的副本上照做，没有 BLOCKER。改前三个问题都存在、改后都消失（看过改前改后的 PDF 图）；五页 A4 页数改前改后相同（2、2、2、2、4）；冻结场景轮次对 022 轮、024 轮各跑一次，`probe.json` 相同、30/30 截图相同。MAJOR 2 条，advisor 核实后采纳：Step 3 的 `grep -c 'print-color-adjust: exact'` 会同时命中 `-webkit-` 那行，实际是 2；对照轮次改用 024 轮。
- **新增 Step 4（维护者 2026-10-23 确认保留）**：「未规划」里那条「最小夹具 `--pdf` 多出空白第 2 页」冷读时查到原因：骨架 `body { min-height: 100vh }`，打印时 100vh 加上页边距比一页多一点。advisor 复核：在打印副本里加 `body { min-height: 0 }` 后夹具从 2 页变 1 页，五个场景页页数不变。它属于打印样式，改在同一个主打印块里，所以写进 027。
- **其他改动**：行号刷新到 `ab64edc`，写明 `show-me.css` 四个 `@media print` 块各是什么；`Current state` 补 `body` 最小高度、diff 行在 `pre > code` 里；Step 5 加六份 PDF 的页数预期；Step 6 说明字体加载造成的偶发截图差异先重跑；索引由审阅者维护；Maintenance notes 补泳道外框跨页、`body` 规则不影响 slide-deck。
- **advisor 复跑**：改后的计划原文套到 `ab64edc` 的新副本：prettier 无改动，四条 grep 为 2 / 1 / 1 / 1；六份 PDF 页数 2、2、2、2、4、1；看图：approach-compare 三张方案卡整块在第 2 页，triage-board 两列、「观察」在下一行、没有被裁，code-review diff 增删行浅红 / 浅蓝底、代码块灰底、徽章无底色；59 个测试 OK，文档门禁通过；冻结场景轮次对 024 轮第一次 28/30（status-report 390、500 两张只在标题中文衬线字形上不同），重跑 30/30，`probe.json` 相同。

### Findings considered and rejected

- **检查时屏蔽 Google Fonts**（调研建议 2b）：最快，但几何按兜底字体量，017 / 019 的阈值是在真实字体下定的；代理透传已经拿到大部分提速。
- **没有 node 时退回多次冷启动**：两条路径的等待机制不同，结果会分叉；维护者决定只留一条。
- **charts.md 顶部加「编号 → gallery 文件 → 块名」速查表**（调研建议 11）：读文档只占那次会话 2.6 分钟，「数据形状 → 候选」「运行时与查代码」两节已经承担这个作用。
- **`PROBE` 改为直接返回 JSON**：要同时改 017–019、023 的全部解析代码，收益只是代码整洁，以后单独做。
- **800 宽通栏数据图在窄屏过小**（调研第 7 条的「配套」）：与上一节「未规划」里的「窄屏上的通栏图」是同一件事，不重复登记。
