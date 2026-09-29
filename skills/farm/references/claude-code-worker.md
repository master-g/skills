# Claude Code 原生 worker 用例

适用于当前会话由 Claude Code 发起、提供 Agent 工具的情况。Claude Code 下 worker 一律是 Claude，不用 pi。

## 执行方式

默认用 Agent 工具起原生子代理。原因：它不是外部 CLI 进程，/farm 加第 2 节确认屏就是派发授权；支持按次指定模型；后台运行、完成时自动通知；修正轮次能接着同一个代理继续。这些正好对应 brief → 报告 → 门禁 → 修正的循环，不需要 pid、退出码和 pane 状态。

只有用户明确要求在 pane 里看 worker 实时运行、随时插手时，才回到 SKILL.md 第 1 节走 herdr pane，此时 cli 固定为 `claude`，每次启动 `claude` 进程按用户的外部 CLI 授权规则单独确认。

不用 Workflow 工具：它需要用户明确要求多代理编排才能调用，而且 farm 的门禁需要 orchestrator 在轮次之间自己判断。

## 选定 pair

运行 `preflight.sh` 只为取 `pairs`，mux 和 clis 不影响本分支。匹配规则同 SKILL.md 第 2 节。例如当前模型为 `claude-opus-5-5` 时命中 `claude:opus-5.5 = claude:claude-sonnet-5-5`。

Agent 工具的 `model` 只接受模型族别名（`sonnet`、`opus`、`haiku`、`fable`）。pairs 写的是完整模型 ID，派发时传对应别名，并用会话信息里的模型列表核对该别名当前就是 pairs 指定的 ID；对不上就说明差异让用户选，不静默换模型。

确认屏照 SKILL.md 第 2 节列出，“将启动的每个 worker”写成“子任务、原生子代理、模型 ID”。

## 派发

worker 数按 SKILL.md 第 0 节决定；k ≥ 2 时子 brief、池、审计和集成门禁按 [worker 池](pool.md) 执行，下列步骤对每个 worker 各做一遍。

1. 核对项目目录与未提交改动，按 SKILL.md 第 3 节把 brief 写入 `<项目绝对路径>/.farm/<task>-brief.md`。补充负责的文件、已有改动，并告诉 worker：你不是唯一修改代码的代理，保留他人改动并适配它们。brief 和报告一律用绝对路径，会话的工作目录可能已被切换。
2. 调用 Agent 工具，不用 `fork`（fork 忽略模型覆盖并继承整段上下文）。池开局的 min(N, k) 个 worker 要在同一条消息里发出多个 Agent 调用，才会并发运行：

```json
{
  "description": "farm <task>",
  "subagent_type": "general-purpose",
  "model": "sonnet",
  "prompt": "在 /absolute/project 工作。读 /absolute/project/.farm/<task>-brief.md 并执行，报告按其中要求落盘。你负责 brief 指定的文件与模块。你不是唯一修改代码的代理，请保留他人改动并适配它们。"
}
```

3. 记下返回的 agent ID，等完成通知，不轮询、不猜结果。等待期间 orchestrator 不改 worker 负责的文件。某个 worker 通过审计后，它的槽位再发一次 Agent 调用接下一个子任务。
4. 收到通知后按 SKILL.md 第 4 节门禁：读报告，看实际 diff，独立重跑验收命令。代理的最终回复只是自述，不算验收。报告缺失时以代理的最终回复作现场。
5. 不过 → 用 SendMessage 向同一个 agent ID 发修正内容（SendMessage 是延迟加载工具，先 `ToolSearch` 查 `select:SendMessage`），计入 3 轮额度。代理已无法继续时，把修正追加进 brief，重新发一次 Agent 调用。

子代理沿用当前会话的权限设置。worker 因审批被拒或越界而停止时，按第 4 节「报告缺失」或升级给用户处理。
