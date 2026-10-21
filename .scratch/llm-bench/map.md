# 地图：个人大模型测试套件（bench）

Label: wayfinder:map

## Destination

一份可交给实施的 `bench/` 规格：harness 怎么跑、任务怎么定义、七个场景各自怎么评分、v1 选手名册，加首批任务清单。用途是选型（每类任务默认用哪个选手，新模型发布时重跑对比），要求可重复、能跨时间对比。

## Notes

- 领域：LLM / agent 评测。术语见根目录 [GLOSSARY.md](../../GLOSSARY.md)（选手、场景、任务、运行），讨论中定下新术语就补进去。
- 按票的 `Type:` 行执行：grilling 票调用 grilling 与 domain-modeling；research 票调用 research；prototype 票调用 prototype。
- 跟踪器是本地 Markdown，约定见 `~/.claude/skills/setup-matt-pocock-skills/issue-tracker-local.md`；`Status:` 取 open / claimed / resolved。
- 项目目录定为仓库根的 `bench/`；不叫 evals（已被技能内部的 eval 占用）。
- 选手 = agent CLI + 模型 + 关键配置，允许「固定 CLI、只换模型」的对照组。本机有 claude、codex、pi、cursor-agent、opencode、ollama。
- v1 七个场景：tufte-reader 写阿波罗登月读本、修 issue、实现 feature、show-me-html 页面、代码审查、中文写作 / 文档、代码库理解 / 问答。harness 与任务格式要能容纳新场景。
- 任务只取自 `/Users/mg/github` 下的公开 repo（emukc、skills、cmg、kloud、pi-wingman 等），任务和产物都可提交。
- farm 的无头红线不约束 bench，bench 的运行可以无人值守；隔离与启动方式见「[运行隔离、联网与启动方式](issues/06-isolation-network-launch.md)」。
- 推进地图的代理不替用户启动选手运行：用户全局规则要求调用 claude / codex / cursor-agent 前逐次确认；研究时只许跑各 CLI 的 `--help` / `--version`。
- 研究结果放在本地 `research/<name>` 分支的 `docs/research/` 下，不推送、不合并。地图与票随 main 提交，不推送（仓库公开）。

## Decisions so far

<!-- 每张已关闭的票一行：[票名](issues/NN-slug.md)：一行要点 -->

## Not yet specified

- 各场景的首批任务：SWE 任务从候选里挑哪几个、各几道；阿波罗读本的 brief 与素材；show-me-html 用什么素材；中文写作出什么题；代码审查的缺陷 diff 从哪来；代码库问答的题目与参考答案。
- 运行记录：每次运行记哪些字段（模型 ID、CLI 版本、日期、耗时、token / 花费）、存哪、产物是否提交、怎么跨时间对比；结果查看页长什么样。
- judge 提示词与 rubric 的细节；每个任务重复跑几次、方差怎么呈现。
- 仓库接入：AGENTS.md 的导航与技术栈、README、Makefile 入口、`bench/` 的工具链约定（仓库现有脚本只用 Python / Node 标准库）。
- 新模型或 CLI 新版本发布时的重跑流程。

## Out of scope

- farm 技能：不作为测试对象，也不与 bench 集成（用户：「不测 farm」）。
- 私有 repo 的任务：本仓库公开，用户选择只用公开 repo。
- 公开排行榜、统计显著性检验：用途是个人选型。
