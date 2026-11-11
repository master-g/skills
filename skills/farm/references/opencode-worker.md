# OpenCode 原生 worker 用例

适用于当前 OpenCode V2 会话提供 `subagent` 工具的情况。worker 是 OpenCode 子会话，不是外部 CLI 进程。

SKILL.md 四个动作在本后端的对应：

| 动作     | 工具或参数                                                                          |
| -------- | ----------------------------------------------------------------------------------- |
| 启动     | `subagent`，`agent` 取 `general`，`model` 取 pair 去掉 `opencode:` 后的完整模型引用 |
| 完成信号 | 前台调用返回；`background: true` 时由完成通知报告                                   |
| 取现场   | 前台返回或完成通知携带的该子会话最终回复                                            |
| 修正     | 调用 `subagent` 时传同一个 `sessionID`                                              |

## 配置与模型

运行本技能目录下的 `preflight.sh` 取 `pairs`，mux 和 clis 不影响本分支。按 SKILL.md「worker 模型」匹配 orchestrator，原生后端只接受以下 worker 值：

```text
opencode:<providerID>/<modelID>[#variant]
```

派发时只删除匹配值开头的后端前缀 `opencode:`，把剩余的 `<providerID>/<modelID>[#variant]` 原样传给 `subagent.model`。

例如，在 `~/.config/farm/pairs` 中配置：

```text
opencode:* = opencode:anthropic/claude-sonnet-5-5#high
```

这只是语法示例。provider、模型和 variant 以当前项目的 OpenCode 模型列表为准，ID 区分大小写。用户调用时点名的模型优先；否则用匹配到的 pair。`model` 参数只使用这两个明确来源，省略它会继承 orchestrator，不能实现 farm 的模型分工。

匹配结果是 `pi:`、`claude:`、`codex:`，或指定模型与 variant 当前不可用，都说明原生后端缺少有效配置。列出所需格式让用户选择或补充配置，不把 CLI 模型名改写成 OpenCode 模型，不静默改用其他后端。

确认屏列出后端 `OpenCode 原生子代理`、完整 worker 模型引用及其来源、每个子任务和并发数。

## 派发与等待

1. 核对项目目录与未提交改动，按 SKILL.md 的 brief 模板把 brief 写入 `<项目绝对路径>/.farm/<task>-brief.md`。补充负责的文件、已有改动和可执行验收命令，并告诉 worker：你不是唯一修改代码的代理，保留他人改动并适配它们。brief 和报告一律用绝对路径。
2. 调用 `subagent`。单 worker 用前台调用，返回即完成；池中的 worker 全部用 `background: true`，开局 min(N, k) 个调用在同一消息中并行发出。示例：

```json
{
  "agent": "general",
  "description": "farm <task>",
  "model": "anthropic/claude-sonnet-5-5#high",
  "background": true,
  "prompt": "读 </absolute/project/.farm/<task>-brief.md> 并执行,报告按其中要求落盘"
}
```

3. 保存每个 worker 返回的 `sessionID`。后台 worker 等完成通知，不轮询、不猜结果；哪个先完成就先审计哪个。等待期间 orchestrator 不改 worker 负责的文件，某个 worker 通过审计后才用它的槽位派发下一个子任务。
4. 收到完成信号后按 SKILL.md「门禁」读报告、看实际 diff、独立重跑验收命令。最终回复只是自述；报告缺失时把前台返回或完成通知携带的最终回复作为现场，显式报告给用户。通知未携带最终回复时，报告原始现场不可读取；再次 prompt 得到的重述不算原始现场。OpenCode 后端不使用 Claude Code 的 `subagent.py` 转录核对，池的集成门禁仍按 [worker 池](pool.md) 执行。

父代理的 `subagent` 权限决定能否启动 `general`，worker 使用自己的权限。worker 因审批或权限停止时，保留最终回复与报告现场，按门禁升级给用户。

## 修正

把门禁失败输出追加为修正 brief，再调用 `subagent` 并传入该 worker 的 `sessionID`，继续使用原 `agent` 和前后台方式；已存会话沿用原模型，无需重新选择：

```json
{
  "sessionID": "ses_...",
  "agent": "general",
  "description": "farm <task> 修正",
  "background": true,
  "prompt": "在 /absolute/project 工作。读 /absolute/project/.farm/<task>-brief.md 中追加的修正内容并继续执行，更新同一份报告。"
}
```

每个子任务仍最多 3 轮。会话已无法继续时，按 SKILL.md「检测环境与能力」的兜底规则，把修正内容留在 brief 并启动新 worker。

当前 `subagent` 完成结果未提供 farm 可核对的 token 用量和耗时，汇报时这两项写「未统计」。
