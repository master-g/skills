# 地图：个人大模型测试套件（bench）

Label: wayfinder:map

## Destination

一份可交给实施的 `bench/` 规格：harness 怎么跑、任务怎么定义、七个场景各自怎么评分、v1 选手名册，加首批任务清单。用途是选型（每类任务默认用哪个选手，新模型发布时重跑对比），要求可重复、能跨时间对比。

## Notes

- 领域：LLM / agent 评测。术语见根目录 [GLOSSARY.md](../../GLOSSARY.md)（选手、场景、任务、运行），讨论中定下新术语就补进去。
- 按票的 `Type:` 行执行：grilling 票调用 grilling 与 domain-modeling；research 票调用 research；prototype 票调用 prototype。
- 跟踪器是本地 Markdown，约定见 `~/.claude/skills/setup-matt-pocock-skills/issue-tracker-local.md`；`Status:` 取 open / claimed / resolved。
- 项目目录定为仓库根的 `bench/`；不叫 evals（已被技能内部的 eval 占用）。
- 选手 = agent CLI（连同本机实际配置）+ 模型 + 推理档位，在本机直跑、不用 Docker；允许「固定 CLI、只换模型」的对照组。本机有 claude、codex、pi、cursor-agent、opencode、ollama。
- v1 七个场景：tufte-reader 写阿波罗登月读本、修 issue、实现 feature、show-me-html 页面、代码审查、中文写作 / 文档、代码库理解 / 问答。harness 与任务格式要能容纳新场景。
- 任务只取自 `/Users/mg/github` 下的公开 repo（emukc、skills、cmg、kloud、pi-wingman 等），任务和产物都可提交。
- farm 的无头红线不约束 bench，bench 的运行可以无人值守；隔离与启动方式见「[运行隔离、联网与启动方式](issues/06-isolation-network-launch.md)」。
- 推进地图的代理不替用户启动选手运行：用户全局规则要求调用 claude / codex / cursor-agent 前逐次确认；研究时只许跑各 CLI 的 `--help` / `--version`。
- 研究结果放在本地 `research/<name>` 分支的 `docs/research/` 下，不推送、不合并。地图与票随 main 提交，不推送（仓库公开）。

## Decisions so far

<!-- 每张已关闭的票一行：[票名](issues/NN-slug.md)：一行要点 -->

- [各 CLI 的无头调用、选模型与权限旗标](issues/01-cli-headless.md)：五个 CLI 都能一条命令无头跑完并出 JSONL；差别在权限放行、用量字段（codex、cursor 无花费）与本机全局配置对选手的污染
- [各 CLI 加载技能的方式](issues/02-skill-loading.md)：五个 CLI 都原生支持技能且都能显式调用 tufte-reader / show-me-html，但写法各异、「只许显式调用」的规则不一，技能场景一律显式调用并记录技能 hash
- [公开 repo 的 SWE 任务候选](issues/03-swe-candidates.md)：候选集中在 emukc（issue 题面现成），抽查 66 对里 31 对可直接作 oracle、28 对要在题面写明接口；emukc 测试依赖不入库的 16 MB 第三方数据
- [现成 agent 评测框架与评分做法](issues/04-existing-frameworks.md)：Harbor 是唯一文档覆盖本机五个 CLI 的框架（Docker、订阅登录、可读 skills/、可重评）；评分做法：隐藏测试、rubric 拆条 + 跨家族 judge + 换序成对比较、审查按语义匹配算查准查全
- [harness 复用现成框架还是自建](issues/05-harness-build-or-reuse.md)：自建，`bench/` 里用 Python（uv，可用第三方包）；选手在本机用真实配置直跑，不用 Docker，现成框架只借评分做法
- [v1 选手名册与预算](issues/07-contender-roster.md)：六个选手——Claude Code + Opus / Fable / Sonnet、Codex + gpt-6-astra、pi + GLM-5.3 / Kimi K3，日常默认档；一轮每个订阅不超过周额度 25%
- [SWE 类评分](issues/08-grading-swe.md)：F2P + P2P 全过才算已解决、另列 F2P 比例；质量分与耗时花费单列；收 A、B 级（题面写明签名），不收 D 级；P2P 限定到相关 crate / 测试文件
- [产出物类评分](issues/09-grading-artifacts.md)：逐份评，rubric 拆成是非题；Fable 5.1、gpt-6-astra、Kimi K3 三家族评审团多数票，用户盲抽查校准；技能检查单列交付合格率；事实闭卷对照资料包；评分计入 25% 额度
- [标准答案类评分](issues/10-grading-reference.md)：审查用真实缺陷、截取引入提交出题，主分是已知缺陷在前 5 条里的命中率，误报单列；问答拆成要点与「不该出现的说法」是非题，引用文件行号并机械核对

## Not yet specified

- 各场景的首批任务：SWE 任务从候选里挑哪几个、各几道；阿波罗读本的 brief 与资料包；show-me-html 用什么资料包；中文写作出什么题、配什么资料包；代码审查从约 10 条真实缺陷候选里挑哪几条、各截取哪些文件（候选见「[标准答案类评分](issues/10-grading-reference.md)」）；代码库问答出哪些题。SWE 挑题时尽量选修复日期晚于各模型训练截止的，减少「背过答案」。
- 运行记录：每次运行记哪些字段（模型 ID、CLI 版本、日期、耗时、token / 花费）、存哪、产物是否提交、怎么跨时间对比；配置指纹（CLI 版本、扩展清单、配置文件 hash），让跨时间对比能发现配置漂移；结果查看页长什么样。
- 评委提示词与各任务 rubric 的条目；用户每轮抽查多少判决、不一致到什么程度要改 rubric；每个任务重复跑几次、方差怎么呈现。
- 仓库接入：AGENTS.md 的导航与技术栈、README、Makefile 入口、`bench/` 的工具链约定（仓库现有脚本只用 Python / Node 标准库）。
- 新模型或 CLI 新版本发布时的重跑流程。

## Out of scope

- farm 技能：不作为测试对象，也不与 bench 集成（用户：「不测 farm」）。
- 私有 repo 的任务：本仓库公开，用户选择只用公开 repo。
- 公开排行榜、统计显著性检验：用途是个人选型。
- v1 名册之外的选手：ollama 本地模型、第三方中转、cursor-agent，以及用户未选的 opencode 与 DeepSeek（见「[v1 选手名册与预算](issues/07-contender-roster.md)」）。
