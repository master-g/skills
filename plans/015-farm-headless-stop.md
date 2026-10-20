# Plan 015: farm 的无头 worker 能被完整停下：pi 自成进程组，`headless.sh` 加 `stop`

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat a05d72d..HEAD -- skills/farm/headless.sh skills/farm/references/cli-worker.md`
> 预期无输出。有输出就把下面「Current state」的摘录与现行文件对照；对不上即为 STOP 条件。

## Status

- **Priority**: P1
- **Effort**: S（一个脚本整份替换，一份文档改四行）
- **Risk**: LOW（只影响 pi 无头 worker；附件脚本已在 advisor 的临时目录里跑通 16 项冒烟测试）
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `a05d72d`, 2026-10-20

## Why this matters

本仓库是 Agent Skills 约定的 Markdown 技能文档仓库，每个技能是 `skills/<name>/`，agent 读 `SKILL.md` 照做。`farm` 技能让当前模型（orchestrator）把实现任务派给更便宜的 worker，再独立验收。worker 可以是无头运行的 `pi` CLI 进程，由 `skills/farm/headless.sh` 启动和等待。

现在无头 worker 没法可靠地停下来。`headless.sh run` 把外层 `sh` 的 pid 写进 `.farm/<task>.pid`，`pi` 只是它的普通子进程。按 `.pid` 去 kill 只结束外层 `sh`，`pi` 和它派生的进程继续在项目里改文件；`headless.sh wait` 这时报 `dead`，orchestrator 按「报告缺失」处理，甚至重新派发，于是两个 pi 同时改同一批文件。文档里也没有「停止」这个动作：worker 跑满 30 分钟后 orchestrator 会问用户还等不等，用户说不等了之后没有写怎么停。

advisor 在临时目录里用假 `pi`（派生一个孙进程后睡眠）复现了这个问题，并把修好的脚本作为附件放在本计划旁边。改完后：`pi` 在自己的进程组里运行；`headless.sh stop <task>` 先给整个进程组发 TERM，10 秒后还在就发 KILL；外层 `sh` 被关窗或被 kill 时也会先结束 `pi` 的进程组。

## Current state

- `skills/farm/headless.sh`（54 行）：无头 worker 的启动与分段等待，只有 `run`、`wait` 两个子命令。`run` 的现状（第 14–23 行）：

```sh
run)
  model="${3:?model required}"
  cont="${4:-}"
  mkdir -p "$d"
  echo $$ >"$d/$task.pid"
  # shellcheck disable=SC2086 # $cont 为空时应展开为无参数
  pi -p $cont --model "$model" "读 $(pwd)/$d/$task-brief.md 并执行,报告按其中要求落盘" \
    <"/dev/null" >"$d/$task.log" 2>&1
  echo $? >"$d/$task.exit"
  ;;
```

- `skills/farm/references/cli-worker.md`（101 行）：CLI 后端的文档，写明无头 worker 怎么派发、等待、修正。本计划要改的四行原文：
  - 第 37 行（「派发」一节，「无头派发」段，整行）：

```markdown
**无头派发**(tmux、none,以及任何在 pane 里跑 `pi -p` 的场景)一律经本技能目录的 `headless.sh` 启动(`<skill>` 为其绝对路径)。启动命令只由纯单词和单引号组成,fish/zsh/bash 都能解析;退出码、日志、pid 由脚本在 sh 里写入 `.farm/<task>.{exit,log,pid}`,手写 `; echo DONE_$?` 之类的 shell 哨兵在 fish 里会让整行不执行。每次派发前先 `rm -f .farm/<task>.pid .farm/<task>.exit` 清掉上一轮标记。
```

- 第 75 行（「等待」一节的表格，`running` 行）：

<!-- prettier-ignore -->
```markdown
| `running`(2)                           | 再调一次;累计超过 30 分钟仍 running → 读 `.farm/<task>.log` 尾部,向用户报告并问是否继续等                                                                                         |
```

- 第 77 行（同一表格，`dead` 行）：

<!-- prettier-ignore -->
```markdown
| `dead`(4)                              | 进程消失且没写退出码(被杀或崩溃):读 log,按门禁的「报告缺失」处理                                                                                                                  |
```

- 第 85 行（「池」一节第一段）：

```markdown
k ≥ 2 时在 [worker 池](pool.md) 之上补充本后端的做法。子任务 i 的 headless 标记是 `.farm/<task>-<i>.{pid,exit,log}`。
```

- 附件（advisor 已在 macOS 的 `/bin/sh`，即 bash 3.2 的 sh 模式下跑通）：
  - `plans/015-farm-headless-stop/headless.sh`：替换后的完整脚本。与现行版的差别只有四处：头部注释加 `stop` 的用法和 `.pgid`；新增函数 `end_group`（TERM，最多等 10 秒，再 KILL）；`run` 用 `set -m` 把 `pi` 放到后台作业里，使它自成进程组，把组 id 写入 `.farm/<task>.pgid`，`trap` 在外层 sh 收到 HUP/INT/TERM 时调用 `end_group`；新增 `stop` 子命令。`wait` 一行未改。
  - `plans/015-farm-headless-stop/smoke.sh`：冒烟测试，用假 `pi` 跑 16 项检查（退出码透传、`-c` 透传、stop 运行中的任务、kill 外层 sh、外层 sh 被 KILL 后的残留清理、忽略 TERM 的 worker、关闭 tmux 会话），结尾打印 `smoke: ok`。只用于验证，不进技能目录。

仓库约定（`AGENTS.md`「代码风格」）：技能文档以简体中文为主，命令和文件名保持英文。**`cli-worker.md` 正文用半角标点 `,` `:` `(` `)`**（看上面的摘录），改动处保持半角；`SKILL.md` 和 `pool.md` 用全角，本计划不改它们。章节引用写标题名（如「等待」），不写「第 N 节」，`make check` 会拦。

## Commands you will need

| Purpose    | Command                                                                   | Expected on success                          |
| ---------- | ------------------------------------------------------------------------- | -------------------------------------------- |
| 冒烟测试   | `sh plans/015-farm-headless-stop/smoke.sh "$PWD/skills/farm/headless.sh"` | 最后一行 `smoke: ok`，没有 `FAIL` 行         |
| 语法检查   | `sh -n skills/farm/headless.sh`                                           | exit 0，无输出                               |
| 文档门禁   | `make check`                                                              | exit 0                                       |
| 格式化     | `npx prettier --write skills/farm/references/cli-worker.md`               | exit 0                                       |
| 格式检查   | `npx prettier --check skills/farm/references/cli-worker.md`               | `All matched files use Prettier code style!` |
| 无残留进程 | `pgrep -fl 'perl -e sleep'`                                               | 无输出（exit 1）                             |

冒烟测试运行中 shell 会打印 `Killed: 9`、`Terminated: 15` 之类的行：那是假 worker 被结束时 shell 的提示，不是失败。判定只看 `PASS`/`FAIL` 行和最后一行。没装 tmux 时 tmux 那项打印 `SKIP`，其余 15 项仍要 PASS。一次运行约 40 秒。

## Scope

**In scope**（只改这些文件）：

- `skills/farm/headless.sh`（用附件整份替换）
- `skills/farm/references/cli-worker.md`（只改「Current state」列出的四行，Step 2 写明替换内容）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**（看着相关，但不要碰）：

- `skills/farm/SKILL.md`：六步流程与「门禁」不变；「停止」只是无头后端的补充手段，不加成第五个动作。
- `cli-worker.md` 第 7–12 行的四动作对照表：不加「停止」行，理由同上。
- `cli-worker.md` 里 herdr pane 的部分：pane 里的 worker 用户看得见，可直接在 pane 里中断，不需要 `stop`。
- `skills/farm/preflight.sh`、`skills/farm/pairs`、`references/claude-code-worker.md`、`references/app-worker.md`、`references/pool.md`。
- 不把 `smoke.sh` 拷进 `skills/farm/`：技能目录会整份装到用户机器上，测试夹具留在 `plans/`。
- `PROJECT_MEMORY.md`：合并时由维护者回写。

## Git workflow

- 分支：`advisor/015-farm-headless-stop`。
- 提交信息用 conventional commits，scope 写技能名（仓库已有的例子：`fix(farm): restore numbered steps in claude-code-worker after prettier merge`）。一个提交即可：`fix(farm): headless pi runs in its own process group, headless.sh stop ends it`。
- pre-commit 会跑 prettier 和 `make check`；prettier 可能重排表格对齐，属于预期。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`（合并后由维护者装到本机）。

## Steps

### Step 1: 换掉 headless.sh

```sh
cp plans/015-farm-headless-stop/headless.sh skills/farm/headless.sh
```

**Verify**:

- `sh -n skills/farm/headless.sh` → exit 0，无输出
- `cmp plans/015-farm-headless-stop/headless.sh skills/farm/headless.sh` → 无输出
- `grep -c 'set -m' skills/farm/headless.sh` → `2`（一行注释、一行命令）
- `sh plans/015-farm-headless-stop/smoke.sh "$PWD/skills/farm/headless.sh"` → 最后一行 `smoke: ok`
- `pgrep -fl 'perl -e sleep'` → 无输出

### Step 2: 改 cli-worker.md 的四行

逐行整行替换，保持半角标点，表格行先不管列对齐（Step 3 由 prettier 对齐）。

第 37 行替换为：

```markdown
**无头派发**(tmux、none,以及任何在 pane 里跑 `pi -p` 的场景)一律经本技能目录的 `headless.sh` 启动(`<skill>` 为其绝对路径)。启动命令只由纯单词和单引号组成,fish/zsh/bash 都能解析;退出码、日志、pid 和 pi 的进程组 id 由脚本在 sh 里写入 `.farm/<task>.{exit,log,pid,pgid}`,手写 `; echo DONE_$?` 之类的 shell 哨兵在 fish 里会让整行不执行。每次派发前先 `rm -f .farm/<task>.pid .farm/<task>.exit .farm/<task>.pgid` 清掉上一轮标记。要提前结束无头 worker,运行 `sh '<skill>/headless.sh' stop <task>`:它结束 pi 和它派生的全部进程(先 TERM,10 秒后仍在就 KILL),打印 `stopped` 或 `killed`;任务已结束时打印 `not-running`。
```

第 75 行（`running` 行）替换为：

```markdown
| `running`(2) | 再调一次;累计超过 30 分钟仍 running → 读 `.farm/<task>.log` 尾部,向用户报告并问是否继续等;用户决定不再等 → `sh '<skill>/headless.sh' stop <task>`,该任务按门禁的升级处理,附上 log 尾部 |
```

第 77 行（`dead` 行）替换为：

```markdown
| `dead`(4) | 外层 sh 消失且没写退出码(被 KILL 或崩溃),pi 可能还在运行:先 `sh '<skill>/headless.sh' stop <task>` 结束残留进程,再读 log,按门禁的「报告缺失」处理 |
```

第 85 行替换为：

```markdown
k ≥ 2 时在 [worker 池](pool.md) 之上补充本后端的做法。子任务 i 的 headless 标记是 `.farm/<task>-<i>.{pid,exit,log,pgid}`,提前结束用 `sh '<skill>/headless.sh' stop <task>-<i>`。
```

**Verify**:

- `grep -c "headless.sh' stop" skills/farm/references/cli-worker.md` → `4`
- `grep -c 'pgid' skills/farm/references/cli-worker.md` → `2`
- `grep -c -e '{exit,log,pid}' -e '{pid,exit,log}' skills/farm/references/cli-worker.md` → `0`

### Step 3: 格式化并过门禁

```sh
npx prettier --write skills/farm/references/cli-worker.md
make check
```

**Verify**:

- `npx prettier --check skills/farm/references/cli-worker.md` → `All matched files use Prettier code style!`
- `make check` → exit 0，输出含 `技能文档引用检查通过`
- `git diff --stat` → 只列出 `skills/farm/headless.sh` 和 `skills/farm/references/cli-worker.md`（以及 Step 4 之后的 `plans/README.md`）

### Step 4: 提交并更新索引

按「Git workflow」提交，再把 `plans/README.md` 里 015 的状态改成 `DONE（<commit>）`。

**Verify**: `git log -1 --format=%s` → `fix(farm): headless pi runs in its own process group, headless.sh stop ends it`

## Test plan

- 不新增仓库内测试：farm 的 shell 脚本一直没有测试文件，技能目录会整份装到用户机器上。行为由附件 `smoke.sh` 验证，它覆盖了这次改动的全部分支：正常退出码透传、`-c` 透传、对已结束任务 `stop` 返回 `not-running`（退出码 1）、`stop` 运行中的任务后 `wait` 报 `done 143` 且无残留、`kill` 外层 sh 后无残留且 `wait` 报 `done 143`、外层 sh 被 KILL 后 `wait` 报 `dead` 而 `stop` 能清掉残留、忽略 TERM 的 worker 10 秒后被 KILL（`killed`、`done 137`）、关闭 tmux 会话后无残留。
- 对照：同一个 `smoke.sh` 跑现行（未改）的 `headless.sh` 有 13 项 FAIL，说明测试确实能抓到这个问题。

## Done criteria

- [ ] `cmp plans/015-farm-headless-stop/headless.sh skills/farm/headless.sh` 无输出
- [ ] `sh plans/015-farm-headless-stop/smoke.sh "$PWD/skills/farm/headless.sh"` 最后一行 `smoke: ok`，没有 `FAIL` 行
- [ ] `pgrep -fl 'perl -e sleep'` 无输出
- [ ] `grep -c "headless.sh' stop" skills/farm/references/cli-worker.md` 为 `4`
- [ ] `make check` exit 0；`npx prettier --check skills/farm/references/cli-worker.md` 通过
- [ ] `git status --short` 只有 Scope 里的文件
- [ ] `plans/README.md` 里 015 的状态行已更新

## STOP conditions

停下汇报，不要自行发挥：

- Drift check 有输出，且「Current state」里的五段摘录与现行文件对不上。
- 冒烟测试有 `FAIL`，且换过附件脚本后重跑一次仍然 FAIL。不要修改附件或 `smoke.sh` 让它通过；把完整输出贴进汇报。
- 运行环境的 `/bin/sh` 不支持 `set -m`（报错 `set: -m: invalid option` 之类），或 `.farm/<task>.pgid` 里的数和 `ps -o pgid= -p <那个数>` 对不上。
- 冒烟测试结束后 `pgrep -fl 'perl -e sleep'` 仍有输出：用 `pkill -f 'perl -e sleep'` 清掉，并把这一情况写进汇报。
- 需要改 Scope 之外的文件才能完成。

## Maintenance notes

- `set -m` 让 `pi` 不再处在外层 sh 的前台进程组。关闭 tmux 窗口时，内核的 SIGHUP 只到前台组，所以现在靠 `trap … HUP` 转发结束 `pi`；以后改 `run` 时保留这个 trap，`smoke.sh` 的 tmux 一项专门测它。
- `stop` 在 `.exit` 已存在时直接返回 `not-running`，不按旧组 id 发信号，避免组 id 被系统重用后误杀别的进程。剩下一个窗口：外层 sh 被 KILL（没写 `.exit`）之后 pi 自己也退出了，几秒内组 id 被重用，这时 `stop` 会把信号发给别的进程组。概率很低，没有处理；要堵上的话，启动时把 `ps -o lstart= -p "$g"` 记在组 id 旁边，`stop` 前比对一致再发信号（flopwire 的设计文档用进程启动时间防 pid 重用，是同一个思路），改完重跑 `smoke.sh`。
- `pi` 的子进程如果自己另开进程组（例如以 detached 方式起的服务），不在 `stop` 的范围内。
- 审阅时重点看：`run` 里 `g=$!` 之前收到信号的处理（`trap` 里有 `[ -n "$g" ]` 判空）；`stop` 的退出码约定与头部注释一致。
