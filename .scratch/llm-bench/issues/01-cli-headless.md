# 各 CLI 的无头调用、选模型与权限旗标

Type: research
Status: claimed
Map: [地图](../map.md)
研究分支：`research/bench-cli-headless`（本地，不推送）· 文件 `docs/research/2026-10-21-bench-cli-headless.md`

## Question

在本机版本上，claude、codex、pi、cursor-agent、opencode 各自怎样无人值守地跑完一个任务？逐个 CLI 查清：

- 非交互调用的命令形式，工作目录怎么指定，结束时的退出码含义；
- 选模型、选推理档位的旗标，本机已配置哪些模型与 provider（读配置文件，不打印密钥；ollama 用 `ollama list`）；
- 跳过审批、自动放行的权限旗标与沙箱选项；
- 能否输出结构化转录（JSON / stream-json）、token 用量与花费，转录默认存在哪；
- 鉴权方式（订阅还是 API key）及其对自动化批量调用的限制（条款、速率）。

约束：只许运行这些 CLI 的 `--help` / `--version`，不调用模型。结论写成 CLI × 维度的对照表，每格注明来源（帮助输出或官方文档链接）。
