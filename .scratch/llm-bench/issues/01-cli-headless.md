# 各 CLI 的无头调用、选模型与权限旗标

Type: research
Status: resolved
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

## Answer

详见分支 `research/bench-cli-headless`（feda303）的 `docs/research/2026-10-21-bench-cli-headless.md`。推荐命令只按帮助与文档拼出，未实跑。

- 无头命令：`claude -p`、`codex exec`、`pi -p` / `pi --mode json`、`cursor-agent -p`（改文件加 `--force`，无头加 `--trust`）、`opencode run`。工作目录：claude、pi 靠进程 cwd，codex `-C`，cursor-agent `--workspace`，opencode `run --dir`。五个都能输出 JSONL。
- 档位：claude `--effort`；codex `-c model_reasoning_effort=`；pi `--thinking` 或模型名后缀 `:high`；cursor-agent 模型名里 `[effort=high]`；opencode `--variant`。
- 权限：claude `-p`、opencode run 默认拒绝待批调用，codex exec 不审批，三者都要显式放行；pi 没有审批机制；自带系统沙箱的只有 claude、codex、cursor-agent。
- 用量：claude 有 `total_cost_usd` 与分模型用量；pi、opencode 每步有 token 与 cost；codex 只有 token；cursor-agent 文档里都没有。转录分别在 `~/.claude/projects/`、`~/.codex/sessions/`、`~/.pi/agent/sessions/`、opencode 的 SQLite、`~/.cursor/projects/*/agent-transcripts/`。
- 鉴权：claude Max 5x 订阅、codex ChatGPT Pro、cursor 团队账号，pi / opencode 主要用各家 coding plan 的 API key；订阅额度按个人使用设计（5 小时窗或周限额），智谱 coding plan 限定官方支持的工具。claude `--bare` 只认 API key，订阅用不了。
- 本机配置会污染选手：pi 装了 23 个扩展包、opencode 挂了 superpowers 插件、codex 开着 memories 与 hooks；codex 沙箱被 config 改成 `workspace-write`，cursor 沙箱被关。claude `--safe-mode` 能干净运行但会连技能一起关掉。
- 副作用：`pi --help` 会让 pi-lens 扩展在当前目录写出 `.pi-lens-probe-home/`。`ollama list` 为空（服务未运行，没有本地模型）。
- 未查清：claude 文档里的 `--max-turns` 等旗标在 2.1.306 的 `--help` 里没有；cursor-agent 不加 `--force` 能否写文件；订阅 provider 下 cost 字段含义；pi 的 openai-codex 登录与智谱条款是否允许 pi。
