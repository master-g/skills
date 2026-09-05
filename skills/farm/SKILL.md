---
name: farm
description: 用户调用 /farm 时，将明确的实施任务交给选定 worker CLI，并独立验证结果。
disable-model-invocation: true
---

# farm — 把活派给便宜的 worker

orchestrator(当前模型)只做四件事:计划、写 brief、定验收门禁、独立复验。
worker 只做一件事:按 brief 实施并写报告。

## 0. 前置

任务已有方案或明确目标才派发。没有就先规划,farm 不做探索。

## 1. Preflight

运行本技能目录(与 SKILL.md 同目录)下的 `preflight.sh`,读 JSON:

- `mux`: `herdr` | `tmux` | `none` — 决定派发方式
- `clis`: 可用的 worker CLI
- `pairs`: orchestrator→worker 对(用户配置 `~/.config/farm/pairs` 优先,否则技能自带默认)
- `warnings`: 如 herdr integration outdated(提示用户跑 `herdr integration install <cli>`,可继续,但 agent 状态判定可能失真——显式告知用户)

完成标准:JSON 到手且 pairs 非空。否则报告缺什么(CLI / 配置),停止。

## 2. 选定 pair

你知道自己是谁(host + 模型名):从 pairs 取匹配项,无匹配取 `*` 兜底项,向用户确认后定案。
无匹配且无 `*`:列出全部 pairs 让用户选。

每次实际调用外部模型都遵守当前环境与用户的授权边界；pair 选择不代替调用授权，修正轮次需要新进程时也一样。

红线:无头 worker 只允许 **pi**(用户调用本技能即接受 pi 无头改文件)。claude / codex 当 worker 只能在 herdr pane 里跑,审批弹窗必须用户可见。

## 3. 派发

先写 brief 到 `.farm/<task>-brief.md`:

```markdown
# <task>

## 目标

<一句话>

## 背景与相关文件

<路径 + 各一句为什么相关>

## 边界

可改:<...>;不可改:<...>

## 验收命令

<一条可执行命令,退出码 0 = 通过>

## 报告

把结果写入 .farm/<task>-report.md:完成了什么 / 改动文件列表 / 验收命令输出 / 未决问题。

## 停止条件

验收命令连试 2 轮仍不过,或需要超出边界的改动 → 把现状写进报告并停止。
```

worker 的 prompt 永远是同一句:`读 <$PWD/.farm/<task>-brief.md> 并执行,报告按其中要求落盘`。

按 mux 选一行执行( `<cli>` `<model>` 来自选定 pair):

| mux   | 派发                                                                                                                                                                                                                                                                |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| herdr | `herdr pane split --current --direction right --cwd "$PWD" --no-focus`(从返回 JSON 的 `.result.pane.pane_id` 读 pane id)→ `herdr agent start <task> --kind <cli> --pane <pane-id> -- <modelflag>` → `herdr agent prompt <task> "<prompt>" --wait --timeout 1800000` |
| tmux  | `tmux new-window -n farm-<task> "cd '$PWD' && <cli> <modelflag-headless> '<prompt>' 2>&1 \| tee .farm/<task>.log"`                                                                                                                                                  |
| none  | `cd "$PWD" && <cli> <modelflag-headless> '<prompt>' > .farm/<task>.log 2>&1 &`,轮询 log                                                                                                                                                                             |

modelflag(pane 交互 / 无头):

| cli    | herdr pane        | 无头                 |
| ------ | ----------------- | -------------------- |
| pi     | `--model <model>` | `-p --model <model>` |
| claude | `--model <model>` | 禁用(见红线)         |
| codex  | `-m <model>`      | 禁用(见红线)         |

`herdr agent start` 返回 `agent_not_ready`:用 `herdr agent get <task>` 查看,通常是登录或 trust 提示,报告用户处理。

完成标准:此阶段仅确认 worker 已启动且 brief 已落盘；整个任务必须完成第 4 节的独立验收。

## 4. 门禁循环

worker 结束(herdr:`agent prompt` 返回;tmux/none:log 出现报告路径且进程退出)后:

1. 读 `.farm/<task>-report.md`。报告缺失:抓 worker 输出(log,或 `herdr agent read <task> --source recent-unwrapped --lines 120`),判断 worker 是死了还是违约,显式报告给用户。
2. **独立重跑验收命令**,不信 worker 自述。
3. 通过 → 向用户汇报:改动摘要(git 仓库用 `git diff --stat`)+ 门禁输出。
   不过 → 把失败输出写成修正 brief 再派一轮(herdr:对同一 agent 再 `agent prompt`;无头:`pi -p -c` 继续会话)。**最多 3 轮**;仍失败则保留现场,带报告与门禁输出升级给用户。

## 失败处理

任何一步失败都显式说明:哪一步、为什么、现场在哪(log / 报告 / pane 名)。不静默重试,不替 worker 宣布完成。

建议把 `.farm/` 加入项目 `.gitignore`。
