# 公开 repo 的 SWE 任务候选

Type: research
Status: claimed
Map: [地图](../map.md)
研究分支：`research/bench-swe-candidates`（本地，不推送）· 文件 `docs/research/2026-10-21-bench-swe-candidates.md`

## Question

`/Users/mg/github` 下的公开 repo 里，有哪些历史 issue 或 feature 能改造成可复现的 SWE 任务？范围：emukc、skills、cmg、kloud、pi-wingman、pi-usage-hud、herdr-panes、algebrica-zh、calculus-made-easy-zh，以及上游不属于用户的 algebrica（antoniolupetti）、dictionary-of-ai-coding（mattpocock）。

对每个 repo 先记：语言、规模、测试命令、本机能否跑通、单次测试耗时。再列候选：

- 修 issue：已关闭且能对应到修复提交的 issue（用 gh 查），修复提交是否带测试，父提交上这些测试是否失败（抽查前几条）；
- 实现 feature：带测试的功能提交，需求能否用几句话独立说清；
- 每条候选给出 repo@父提交、修复或功能提交、改动规模、有无现成测试可作 oracle、难度粗估。

只读：不动这些 repo 的工作区，要跑测试就 clone 到临时目录；不推送。候选按「能否作 oracle」排序，不替用户挑选。
