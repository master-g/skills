# 现成 agent 评测框架与评分做法

Type: research
Status: claimed
Map: [地图](../map.md)
研究分支：`research/bench-existing-frameworks`（本地，不推送）· 文件 `docs/research/2026-10-21-bench-existing-frameworks.md`

## Question

有没有现成框架能直接承载 bench？业界怎样给 agent 任务评分？查清：

- 能驱动 CLI agent 的评测框架：Harbor（Terminal-Bench）、inspect_ai（及 inspect_swe）、SWE-bench harness、promptfoo 等。各自支持哪些 agent（Claude Code、Codex、OpenCode、cursor-agent、pi）、隔离方式（Docker 等）、任务格式、评分扩展点、结果格式、许可证与活跃度；
- 评分做法：SWE 类的隐藏测试（FAIL_TO_PASS / PASS_TO_PASS）；写作与视觉产物的 rubric、LLM judge、成对盲评及已知偏差（自评偏好、位置偏差、长度偏差）；代码审查与问答有参考答案时怎么评；
- 本仓库已有的 `skills/*/evals/evals.json`（skill-creator 格式）能否复用。

结论写成框架对照表加三类评分做法摘要，每条注明一手来源。
