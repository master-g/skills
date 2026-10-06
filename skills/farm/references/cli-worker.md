# CLI 后端：worker CLI 进程

适用于会话没有原生子代理工具,或用户明确要求在 pane 里看 worker 的情况。worker 是 pi / claude / codex 的 CLI 进程,跑在 herdr pane 里或无头运行。SKILL.md「红线」决定哪个 CLI 能用哪种方式。宿主是 Claude Code 时 cli 固定为 `claude`,只走 herdr pane。

SKILL.md 四个动作在本后端的对应:

| 动作     | herdr pane                                                      | 无头(tmux / none,只限 pi)                                     |
| -------- | --------------------------------------------------------------- | ------------------------------------------------------------- |
| 启动     | `herdr agent start` + `herdr agent prompt`                      | `headless.sh run`                                             |
| 完成信号 | `agent prompt --wait` 返回                                      | `headless.sh wait` 返回 `done`                                |
| 取现场   | `herdr agent read <task> --source recent-unwrapped --lines 120` | `.farm/<task>.log`                                            |
| 修正     | 对同一 agent 再 `agent prompt`                                  | 修正追加进 brief,清标记后 `headless.sh run <task> <model> -c` |

## Preflight

运行本技能目录(与 SKILL.md 同目录)下的 `preflight.sh`,读 JSON:

- `mux`: `herdr` | `tmux` | `none` — 决定派发方式
- `clis`: 可用的 worker CLI
- `pairs`: orchestrator→worker 对,匹配规则见 SKILL.md「worker 模型」
- `warnings`: 如 herdr integration outdated(提示用户跑 `herdr integration install <cli>`,可继续,但 agent 状态判定可能失真——显式告知用户)

完成标准:JSON 到手且 pairs 非空。否则报告缺什么(CLI / 配置),停止。

SKILL.md「确认屏」里每个 worker 的运行位置写成:cli:model、无头,或 herdr 下复用哪个 pane / 新开。

## 派发

按 mux 选一行执行( `<cli>` `<model>` 来自选定 pair):

| mux   | 派发                                                                                                                   |
| ----- | ---------------------------------------------------------------------------------------------------------------------- |
| herdr | 先按下文「herdr pane 复用」拿到 agent 名(复用或新开)→ `herdr agent prompt <agent> "<prompt>" --wait --timeout 1800000` |
| tmux  | `tmux new-window -d -c "$PWD" -n farm-<task> "sh '<skill>/headless.sh' run <task> <model>"`                            |
| none  | `nohup sh '<skill>/headless.sh' run <task> <model> >/dev/null 2>&1 &`                                                  |

**无头派发**(tmux、none,以及任何在 pane 里跑 `pi -p` 的场景)一律经本技能目录的 `headless.sh` 启动(`<skill>` 为其绝对路径)。启动命令只由纯单词和单引号组成,fish/zsh/bash 都能解析;退出码、日志、pid 由脚本在 sh 里写入 `.farm/<task>.{exit,log,pid}`,手写 `; echo DONE_$?` 之类的 shell 哨兵在 fish 里会让整行不执行。每次派发前先 `rm -f .farm/<task>.pid .farm/<task>.exit` 清掉上一轮标记。

**herdr pane 复用**(单 worker 时一个 farm 会话只维护一个 worker pane;池见下文「池」):

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

已启动的判据——herdr:`agent prompt --wait` 没有返回 `agent_prompt_stalled`;无头:派发后立即开始下文的 `wait`,首次返回不是 `not-started`。

## 等待

worker 结束(herdr:`agent prompt` 返回;无头:`headless.sh wait` 返回 `done`)后进入 SKILL.md「门禁」。无头等待是分段的,每段最长 100 秒,按结果分支:

| `sh '<skill>/headless.sh' wait <task>` | 含义与动作                                                                                                                                                                        |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `done <code>`(退出码 0)                | worker 已退出,进入门禁                                                                                                                                                            |
| `running`(2)                           | 再调一次;累计超过 30 分钟仍 running → 读 `.farm/<task>.log` 尾部,向用户报告并问是否继续等                                                                                         |
| `not-started`(3)                       | 15 秒内脚本没写 pid,启动命令从未执行:查 tmux 窗口 / 后台命令输出 / pane 内容找原因,修正后重发(pane 里重发前先 `herdr pane send-keys <pane> ctrl+c` 清掉提示符残留),不计入修正轮次 |
| `dead`(4)                              | 进程消失且没写退出码(被杀或崩溃):读 log,按门禁的「报告缺失」处理                                                                                                                  |

## 收尾

herdr:汇报时问用户是否关闭 worker pane(`herdr pane close <pane-id>`);用户不回应则保留,但下次 /farm 新开 pane 前必关(见「herdr pane 复用」第 3 步)。

## 池

k ≥ 2 时在 [worker 池](pool.md) 之上补充本后端的做法。子任务 i 的 headless 标记是 `.farm/<task>-<i>.{pid,exit,log}`。

派发:

- herdr:每个槽一个 pane。复用哪个、新开几个已在确认屏定下,不再逐个询问:复用的按「herdr pane 复用」第 2 步重置,新开的按第 3 步开,只关掉上一次 /farm 留下的 pane,不关当前池的其他槽。槽位接新子任务前先发 reset-cmd。派发用 `herdr agent prompt <pane-id> "<prompt>" --wait --until working --until blocked --timeout 15000`:确认已开工就返回,不等完成。
- tmux / none:按「派发」的命令,task 取 `<task>-<i>`,tmux 窗口名 `farm-<task>-<i>`。

等待:轮流检查未完成的 worker,哪个先结束就先审计哪个。

- herdr:`herdr agent wait <pane-id> --timeout 10000`。返回 idle / done 表示已结束;timeout 表示仍在运行;blocked 表示在等审批,告诉用户是哪个 pane,然后继续检查其他 worker。
- 无头:派发后先对每个子任务跑一次 `sh '<skill>/headless.sh' wait <task>-<i> 20`,用来识别 not-started;之后轮询用 `wait <task>-<i> 5`。返回值的处理同「等待」。

单个 worker 累计运行超过 30 分钟的处理同「等待」。

修正:无头修正不带 `-c`。同一目录里跑过多个 pi,`-c` 接上的“上一个会话”不一定是这个子任务的。修正内容已追加进子 brief,新会话读 brief 即可。

集成门禁通过后,herdr 下询问是否关闭全部 worker pane。
