# farm OpenCode 原生 worker 设计

## 目标

让 `/farm` 在提供 `subagent` 工具的 OpenCode V2 会话中使用原生 worker，并沿用现有 brief、报告、独立门禁和最多三轮修正流程。

## 方案

采用按次指定模型：在 `pairs` 中增加 `opencode:provider/model[#variant]` worker 类型，新增 OpenCode 专用后端文档。调用 `general` 子代理，单 worker 可前台等待，并发 worker 使用后台完成通知；通过 `sessionID` 继续同一 worker。

不采用专用 `farm-worker` agent：它会与 `pairs` 形成两个模型来源，并增加全局 agent 安装步骤。

## 配置与约束

- 用户在自己的 `~/.config/farm/pairs` 配置完整 OpenCode 模型引用；技能默认文件只提供注释示例，不绑定特定 provider。
- 模型必须来自当前项目可用的 OpenCode 模型列表；不可用或没有匹配项时停止并询问，不静默更换模型或后端。
- OpenCode 原生 worker 不是外部 CLI，不受无头 worker 只允许 pi 的限制。
- worker 最终回复只用于报告缺失时取现场，不代替 `.farm/<task>-report.md` 和独立验收。
- 当前 `subagent` 结果不提供可靠 token 与耗时统计时，汇报「未统计」。

## 改动范围

只修改 farm 的 `SKILL.md`、`pairs`，并新增 `references/opencode-worker.md`；不改通用流程、CLI 后端和转录脚本。验证后安装本机 farm 技能，提交到 `main`，不推送。
