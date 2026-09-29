# worker 池：k ≥ 2 个子任务

SKILL.md 第 0 节拆出 k 个子任务、并发上限为 N 时，按本文件执行派发与门禁。本文件只写与单 worker 不同的部分，其余规则仍按 SKILL.md 第 3、4 节。N = 1 也走本流程，逐个子任务派发和审计。原生子代理分支（App、Claude Code）只用本文件的「子 brief」「池」「审计」「集成门禁」，派发和等待用 app-worker.md 或 claude-code-worker.md 的工具。

## 子 brief

子任务 i 的任务名取 `<task>-<i>`，brief、报告和 headless 标记随之成为 `.farm/<task>-<i>-brief.md`、`.farm/<task>-<i>-report.md`、`.farm/<task>-<i>.{pid,exit,log}`。按第 3 节模板写，另外：

- 「边界」的可改范围就是该子任务负责的文件，与其他子 brief 互不重叠。
- 「边界」加一句：其他 worker 正同时修改边界外的文件；保留它们的改动，边界外文件不格式化、不回滚。
- 「验收命令」只覆盖本子任务的范围，如该模块的测试。全量测试、全项目类型检查和构建留给集成门禁。

再写 `.farm/<task>-plan.md`：子任务表（编号、负责文件、验收命令）和整体验收命令。

## 池

同时运行的 worker 不超过 N。开局派发前 min(N, k) 个子任务；某个 worker 通过审计后，它的槽位接下一个待办子任务。修正轮次继续占用原槽位。

- herdr：每个槽一个 pane。复用哪个、新开几个已在第 2 节确认屏定下，不再逐个询问：复用的按第 3 节「herdr pane 复用」第 2 步重置，新开的按第 3 步开，只关掉上一次 /farm 留下的 pane，不关当前池的其他槽。槽位接新子任务前先发 reset-cmd。派发用 `herdr agent prompt <pane-id> "<prompt>" --wait --until working --until blocked --timeout 15000`：确认已开工就返回，不等完成。
- tmux / none：按第 3 节命令派发，task 取 `<task>-<i>`，tmux 窗口名 `farm-<task>-<i>`。

## 等待

轮流检查未完成的 worker，哪个先结束就先审计哪个：

- herdr：`herdr agent wait <pane-id> --timeout 10000`。返回 idle / done 表示已结束；timeout 表示仍在运行；blocked 表示在等审批，告诉用户是哪个 pane，然后继续检查其他 worker。
- 无头：派发后先对每个子任务跑一次 `sh '<skill>/headless.sh' wait <task>-<i> 20`，用来识别 not-started；之后轮询用 `wait <task>-<i> 5`。返回值的处理同第 4 节。

单个 worker 累计运行超过 30 分钟的处理同第 4 节。

## 审计

某个 worker 一结束就审计它，不等其他 worker。这时工作树仍在被其他 worker 修改，所以只看它负责的范围，审计逐个进行：

1. 读 `.farm/<task>-<i>-report.md`，缺失时同第 4 节处理。
2. `git diff --stat -- <负责文件>`。
3. 独立重跑子 brief 的验收命令。

通过 → 释放槽位。不过 → 对同一 worker 发修正，做法同第 4 节，但无头修正不带 `-c`：同一目录里跑过多个 pi，`-c` 接上的“上一个会话”不一定是这个子任务的。修正内容已追加进子 brief，新会话读 brief 即可。每个子任务各自最多 3 轮。某个子任务需要升级给用户时，其他 worker 继续运行。

## 集成门禁

全部子任务通过审计、且没有修正轮次在运行时，独立运行 plan 里的整体验收命令。

- 通过 → 汇报每个子任务的改动摘要和审计结果、整体 `git diff --stat`、集成门禁输出。herdr 下询问是否关闭全部 worker pane。
- 不过 → 按失败输出找到出问题的文件属于哪个子任务，对该 worker 发修正，计入该子任务的 3 轮额度；修正后重新审计该子任务，再重跑集成门禁。失败跨越多个子任务的边界，说明拆分有误：保留现场，带失败输出升级给用户。
