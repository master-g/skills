# 现成 agent 评测框架与评分做法

Type: research
Status: resolved
Map: [地图](../map.md)
研究分支：`research/bench-existing-frameworks`（本地，不推送）· 文件 `docs/research/2026-10-21-bench-existing-frameworks.md`

## Question

有没有现成框架能直接承载 bench？业界怎样给 agent 任务评分？查清：

- 能驱动 CLI agent 的评测框架：Harbor（Terminal-Bench）、inspect_ai（及 inspect_swe）、SWE-bench harness、promptfoo 等。各自支持哪些 agent（Claude Code、Codex、OpenCode、cursor-agent、pi）、隔离方式（Docker 等）、任务格式、评分扩展点、结果格式、许可证与活跃度；
- 评分做法：SWE 类的隐藏测试（FAIL_TO_PASS / PASS_TO_PASS）；写作与视觉产物的 rubric、LLM judge、成对盲评及已知偏差（自评偏好、位置偏差、长度偏差）；代码审查与问答有参考答案时怎么评；
- 本仓库已有的 `skills/*/evals/evals.json`（skill-creator 格式）能否复用。

结论写成框架对照表加三类评分做法摘要，每条注明一手来源。

## Answer

详见分支 `research/bench-existing-frameworks`（d3eecec）的 `docs/research/2026-10-21-bench-existing-frameworks.md`。以下均来自文档与源码，未实测。

- 框架：Harbor 是唯一文档覆盖本机全部五个 CLI（claude-code、codex、opencode、cursor-cli、pi）的框架；在 Docker 里跑 CLI 本体、可钉版本，支持 Claude 订阅令牌与 Codex `auth.json`，`--skill <org/repo>` 默认读仓库 `skills/`，有 `harbor job regrade` 与 `harbor run --diff` 便于跨时间对比。BenchFlow 兼容 Harbor 任务格式但缺 cursor；inspect_swe、promptfoo 缺 cursor 与 pi，且把选手变成「框架模型 + CLI 外壳」；SWE-bench harness 只给 patch 打分。
- SWE 评分：隐藏测试为主，FAIL_TO_PASS 与 PASS_TO_PASS 全过才算解决；评产出不评过程，给部分分，每次运行从干净环境开始。
- 产出物评分：rubric 拆条、每条单独交给 LLM judge，人工抽查校准；成对比较交换顺序、两次一致才算胜；judge 避开被评模型家族或用多家族评审团；长度偏差回归扣除。
- 参考答案类：代码审查按「是否同一问题」语义匹配算查准查全（预印本：预埋 bug 最佳 F1 0.847，真实 PR 仅 0.066）；问答对照参考答案分维度打分，或用必须项 +「不该出现的说法」两类 rubric。
- `evals.json`（skill-creator 格式）：数据可转成任务与 judge 检查项，运行器只能在 Claude Code 里跑，不能跨 CLI 复用。
- 未查清：Harbor 能否用 ollama 驱动各 CLI、cursor / opencode / pi 能否用订阅登录、BenchFlow 的 cursor 适配、macOS 上的实际开销；中文写作 judge 的一手研究没找到。
