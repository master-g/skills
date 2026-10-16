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
