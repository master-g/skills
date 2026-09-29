# App 原生 worker 用例

适用于当前 GUI 会话提供原生代理或聊天管理工具的情况。本用例以 Codex 桌面 App 为例；普通 ChatGPT 网页若未提供这些工具，就不能照搬调用。

## 场景与选择

用户已明确方案，并要求：“/farm，按这个方案实现。你用 GPT-6 Astra 做编排，派 GPT-6 Sol high 或 xhigh 做实现，最后由你验收。”

当前模型若由会话信息确认为 `gpt-6-astra`，保留主聊天做计划、brief、验收和复验，实施交给 `gpt-6-sol`。不要仅凭本例推断自己的模型身份。

| 实施范围                                       | worker 推理档位  |
| ---------------------------------------------- | ---------------- |
| 方案已定、边界清晰的常规实现或修复             | `high`，默认选择 |
| 跨模块、复杂状态或并发逻辑，需要较多推理的实现 | `xhigh`          |

模型 ID、可用档位及参数名以当前工具说明为准。上表是本用例的分工约定，不代表价格或性能测量。指定组合不可用时，说明缺少什么并让用户选择，不静默换模型或改走外部 CLI。

用户已明确授权上述派遣时直接执行，不重复确认；k ≥ 2 且并发数没有由参数给出时，仍按 SKILL.md 第 0 节问一次并发数。只要求修改技能或讨论这个用例时，不启动 worker。`/farm` 的派遣授权仍受当前环境规则约束；额外外部 CLI 进程的授权与 App 原生代理分开处理。

## 当前聊天内派遣

当前任务中的实施子任务优先使用 `collaboration.spawn_agent`。worker 数按 SKILL.md 第 0 节「拆分与并发数」决定；k ≥ 2 时每个子任务调用一次 `spawn_agent`，子 brief、池、审计和集成门禁按 [worker 池](pool.md) 执行，下列步骤对每个 worker 各做一遍。

1. 核对实际项目目录与未提交改动，按 SKILL.md 第 3 节将 brief 写入项目的 `.farm/<task>-brief.md`。补充项目绝对路径、worker 负责的文件或模块、已有改动、可执行验收命令，以及哪些用户可见结果需要检查。明确告知 worker：你不是唯一修改代码的代理，保留他人改动并适配它们。报告也用绝对路径指定。
2. 确认 `spawn_agent` 当前支持指定模型和档位。显式覆盖模型时使用 `fork_turns: "none"`，把必要背景写入 brief；完整继承历史的 `fork_turns: "all"` 不接受模型覆盖。调用示例如下，执行前替换项目路径与任务名（多个 worker 时用 `farm_<task>_<i>`）：

```json
{
  "task_name": "farm_implementation",
  "agent_type": "worker",
  "model": "gpt-6-sol",
  "reasoning_effort": "high",
  "fork_turns": "none",
  "message": "在 /absolute/project 工作。读 /absolute/project/.farm/task-brief.md 并执行，报告按其中要求落盘。你负责 brief 指定的文件与模块。你不是唯一修改代码的代理，请保留他人改动并适配它们。"
}
```

3. 保存返回的 agent ID，等待该 worker 的消息和完成通知。可用 `collaboration.wait_agent` 等待，时长遵守当前环境的等待与进度更新要求；多个 worker 时哪个先完成就先审计哪个。主模型不同时修改 worker 负责的文件。需要澄清时用 `send_message`；worker 已结束且需要修正时用 `followup_task` 继续同一个代理。
4. 收到完成通知后，读取报告、检查实际 diff，并独立重跑 brief 的验收命令，核对约定的行为结果。按 SKILL.md 第 4 节的门禁要求处理报告缺失、失败修正和最多 3 轮的限制。App 分支以代理状态和消息判断运行情况，不读取 CLI 的 `.pid`、`.exit` 或 pane 状态。
5. 通过后汇报改动、实际验证结果和限制。代理创建成功、worker 自述完成都不等于验收通过。需要超出 brief 边界时保留现场，交用户决定。

## 用户明确要求侧栏新聊天时

只有用户明确说“新建一个 Sol 聊天来实现”等要求时，才用 `mcp__codex_app__create_thread`。当前任务的普通子任务使用上面的原生子代理。

- 项目实施先 `list_projects`，使用返回的项目 ID。默认 `target.environment.type` 为 `local`；用户明确要求独立 worktree 时才用 `worktree`，并确认项目为 Git 仓库。
- 用户明确指定 Sol 时，在 `create_thread` 中设置 `model: "gpt-6-sol"`、`thinking: "high"` 或 `"xhigh"`。这里的参数名是 `thinking`，与子代理的 `reasoning_effort` 不同。
- `prompt` 写明完整实施 brief、文件归属和报告位置。新聊天不继承主聊天历史；worktree 不会自动带入原目录的未提交 brief。使用 worktree 时把 brief 内容放进 prompt，并要求 worker 在其实际 checkout 落盘和报告路径。
- 创建返回 `threadId` 后，用 `wait_threads` 等待进展；后续传回上次 cursor，避免重复读取。若只返回 `clientThreadId`，等待设置完成并通过 `list_threads` 确认真正的 `threadId`，不要把临时 ID 传给等待或发消息工具。按 App 要求在最终回复展示创建聊天的 directive。
- 后续修正用 `send_message_to_thread`，前提是用户已授权给该聊天发消息或持续协调；创建聊天本身不扩大后续消息授权。复验在 worker 的实际 checkout 执行。独立 worktree 的结果尚需整合到目标 checkout 时，明确列为未完成事项，不把 worker 完成直接当成交付完成。

这条分支继续使用相同的报告、独立验收和修正轮次要求；保留新聊天供用户继续使用。
