# 用真实配置把五个 CLI 各无头跑通一次

Type: task
Status: open
Blocked by: 05
Map: [地图](../map.md)

## Question

「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」与「[各 CLI 加载技能的方式](02-skill-loading.md)」给出的命令都只按帮助和文档拼出、没有实跑。在本机真实配置下，让 claude、codex、pi、cursor-agent、opencode 各在一个临时目录里无头完成同一个最小任务（例如按提示改一个文件，再显式调用一次 tufte-reader 或 show-me-html 并要求不打开浏览器），记下实际结果：

- 命令能否无人值守跑完、退出码、自动放行旗标是否生效，cursor-agent 不加 `--force` 能否写文件；
- JSONL 输出里实际有哪些用量与花费字段；
- 显式调用技能的写法是否生效；
- 跑完后日常状态里多了什么（转录、memories、扩展生成的文件，如 pi-lens 的 `.pi-lens-probe-home/`）。

HITL：用户全局规则要求调用 claude / codex / cursor-agent 前逐次确认，所以由代理写好逐条命令清单，用户亲手执行或逐条确认后执行。结果写进本票的 Answer。
