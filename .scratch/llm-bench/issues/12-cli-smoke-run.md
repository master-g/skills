# 用真实配置把 v1 的三个 CLI 各无头跑通一次

Type: task
Status: open
Blocked by: 05, 07
Map: [地图](../map.md)

## Question

「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」与「[各 CLI 加载技能的方式](02-skill-loading.md)」给出的命令都只按帮助和文档拼出、没有实跑。「[v1 选手名册与预算](07-contender-roster.md)」定下的六个选手只用到 claude、codex、pi。在本机真实配置下，让六个选手各在一个临时目录里无头完成同一个最小任务（例如按提示改一个文件，再显式调用一次 tufte-reader 或 show-me-html 并要求不打开浏览器），记下实际结果：

- 命令能否无人值守跑完、退出码、自动放行旗标是否生效；
- 每个选手实际用的模型名与档位（Opus、Fable、Sonnet 在 Claude Code 里各是什么档；pi 里 Kimi K3 的模型名是什么、GLM-5.3 与 Kimi 的 thinking 档）；
- JSONL 输出里实际有哪些用量与花费字段，能否看出离 5 小时窗与周限额还有多远；
- 显式调用技能的写法是否生效；
- 跑完后日常状态里多了什么（转录、codex memories、扩展生成的文件，如 pi-lens 的 `.pi-lens-probe-home/`）；
- 评委看图：「[产出物类评分](09-grading-artifacts.md)」定下的三个评委（Claude Code + Fable 5.1、Codex + gpt-6-astra、pi + Kimi K3）各读一张截图并说出图里的内容，核实图确实送到了模型。写法按该票 Answer：`claude -p` 让 Read 工具读 PNG、`codex exec -i <file>`、`pi -p @shot.png`；pi 遇到不支持图像的模型会把图换成「image omitted」而不报错，所以要看回答内容，不能只看退出码。

HITL：用户全局规则要求调用 claude / codex 前逐次确认，所以由代理写好逐条命令清单，用户亲手执行或逐条确认后执行。结果写进本票的 Answer。
