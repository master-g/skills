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

| mux   | 派发                                                                                                                   |
| ----- | ---------------------------------------------------------------------------------------------------------------------- |
| herdr | 先按下文「herdr pane 复用」拿到 agent 名(复用或新开)→ `herdr agent prompt <agent> "<prompt>" --wait --timeout 1800000` |
| tmux  | `tmux new-window -d -c "$PWD" -n farm-<task> "sh '<skill>/headless.sh' run <task> <model>"`                            |
| none  | `nohup sh '<skill>/headless.sh' run <task> <model> >/dev/null 2>&1 &`                                                  |

**无头派发**(tmux、none,以及任何在 pane 里跑 `pi -p` 的场景)一律经本技能目录的 `headless.sh` 启动(`<skill>` 为其绝对路径)。启动命令只由纯单词和单引号组成,fish/zsh/bash 都能解析;退出码、日志、pid 由脚本在 sh 里写入 `.farm/<task>.{exit,log,pid}`,手写 `; echo DONE_$?` 之类的 shell 哨兵在 fish 里会让整行不执行。每次派发前先 `rm -f .farm/<task>.pid .farm/<task>.exit` 清掉上一轮标记。

**herdr pane 复用**(一个 farm 会话只维护一个 worker pane):

1. `herdr agent list`,筛 `tab_id == $HERDR_TAB_ID` 且 `agent == <cli>` 且 `cwd == $PWD` 且 `agent_status` 为 `idle`/`done` 的 agent(排除 `pane_id == $HERDR_PANE_ID` 即自己)。
2. 命中 → 问用户:复用这个 pane(列出 pane_id / name / terminal_title)还是新开。复用时先重置会话再派发:`herdr agent prompt <agent> "<reset-cmd>" --wait --timeout 60000`,reset-cmd 见下表;`--wait` 返回 `agent_prompt_stalled` 属正常(斜杠命令不产生 working 态),继续即可。
3. 未命中或用户选新开 → `herdr pane split --current --direction right --cwd "$PWD" --no-focus`(从返回 JSON 的 `.result.pane.pane_id` 读 pane id)→ `herdr agent start <task> --kind <cli> --pane <pane-id> -- <modelflag>`。新开前若本会话已有自己开的 worker pane,先 `herdr pane close <旧 pane-id>`。
4. 后续 `agent prompt` 一律用 pane_id 做目标(复用的 pane 名字是旧任务名,不可靠);记住 pane_id,收尾要用。

worker CLI 通用斜杠命令(用 `agent prompt` 发送,等价于用户在 pane 里输入):

| 动作              | pi         | claude     | codex      |
| ----------------- | ---------- | ---------- | ---------- |
| 清空上下文/新会话 | `/new`     | `/clear`   | `/new`     |
| 压缩上下文        | `/compact` | `/compact` | `/compact` |
| 退出              | `/exit`    | `/exit`    | `/exit`    |

修正轮次上下文太长时,先发 `/compact` 再发修正 brief,不用重开 pane。

modelflag(pane 交互 / 无头):

| cli    | herdr pane        | 无头               |
| ------ | ----------------- | ------------------ |
| pi     | `--model <model>` | `headless.sh` 内置 |
| claude | `--model <model>` | 禁用(见红线)       |
| codex  | `-m <model>`      | 禁用(见红线)       |

`herdr agent start` 返回 `agent_not_ready`:用 `herdr agent get <task>` 查看,通常是登录或 trust 提示,报告用户处理。

完成标准:brief 已落盘,且 worker 确认已启动——herdr:`agent prompt --wait` 没有返回 `agent_prompt_stalled`;无头:派发后立即开始第 4 节的 `wait`,首次返回不是 `not-started`。整个任务必须完成第 4 节的独立验收。

## 4. 门禁循环

worker 结束(herdr:`agent prompt` 返回;无头:`headless.sh wait` 返回 `done`)后进入门禁。无头等待是分段的,每段最长 100 秒,按结果分支:

| `sh '<skill>/headless.sh' wait <task>` | 含义与动作                                                                                                                                                                        |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `done <code>`(退出码 0)                | worker 已退出,进入下面第 1 步                                                                                                                                                     |
| `running`(2)                           | 再调一次;累计超过 30 分钟仍 running → 读 `.farm/<task>.log` 尾部,向用户报告并问是否继续等                                                                                         |
| `not-started`(3)                       | 15 秒内脚本没写 pid,启动命令从未执行:查 tmux 窗口 / 后台命令输出 / pane 内容找原因,修正后重发(pane 里重发前先 `herdr pane send-keys <pane> ctrl+c` 清掉提示符残留),不计入修正轮次 |
| `dead`(4)                              | 进程消失且没写退出码(被杀或崩溃):读 log,按下面第 1 步「报告缺失」处理                                                                                                             |

1. 读 `.farm/<task>-report.md`。报告缺失:抓 worker 输出(log,或 `herdr agent read <task> --source recent-unwrapped --lines 120`),判断 worker 是死了还是违约,显式报告给用户。
2. **独立重跑验收命令**,不信 worker 自述。
3. 通过 → 向用户汇报:改动摘要(git 仓库用 `git diff --stat`)+ 门禁输出。herdr:汇报时问用户是否关闭 worker pane(`herdr pane close <pane-id>`);用户不回应则保留,但下次 /farm 新开 pane 前必关(见「herdr pane 复用」第 3 步)。
   不过 → 把失败输出写成修正 brief 再派一轮(herdr:对同一 agent 再 `agent prompt`;无头:把修正内容追加进 brief,清标记后 `headless.sh run <task> <model> -c` 继续会话)。**最多 3 轮**;仍失败则保留现场,带报告与门禁输出升级给用户。

## 失败处理

任何一步失败都显式说明:哪一步、为什么、现场在哪(log / 报告 / pane 名)。不静默重试,不替 worker 宣布完成。

建议把 `.farm/` 加入项目 `.gitignore`。
