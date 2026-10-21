# 用真实配置把 v1 的三个 CLI 各无头跑通一次

Type: task
Status: claimed
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
- 额度：跑前跑后各记一次各订阅的周额度快照，连同每次运行的 token 与花费字段；再结合本地历史转录换算「每 1% 周额度约多少 token」，估一轮在每个订阅 25% 的上限内能放几道题（含三个评委的评分），指出瓶颈订阅（2026-10-21 按用户要求加入，「v1 选手名册与预算」与「产出物类评分」的额度约束都还没有用量数字支撑）。

HITL：用户全局规则要求调用 claude / codex 前逐次确认，所以由代理写好逐条命令清单，用户亲手执行或逐条确认后执行。结果写进本票的 Answer。

## Comments

2026-10-21：命令清单写成脚本 [smoke/smoke.sh](../smoke/smoke.sh)，由用户亲手执行（`bash .scratch/llm-bench/smoke/smoke.sh all`，或按步骤逐条执行），输出在 `~/.cache/bench-smoke/`。

- 命令按已定决策拼：不传档位旗标，pi 不关扩展与技能。研究文档的「推荐命令」是为干净基线拼的，与「v1 选手名册与预算」的真实配置冲突。
- 技能一步只问 show-me-html 的 SKILL.md 第一个二级标题，不构建；只有 astra 真做一页并构建，验证 codex 的 workspace-write 沙箱里能否起无头 Chrome。
- 代理已用替身 CLI 干跑全流程，并实跑了不调用模型的 setup 与 quota 两步。各订阅接口给的都是整数百分比（Kimi 也是 25/100），单次冒烟的增量接不住，额度估算以历史换算为主。Claude 的快照读 `~/.claude.json` 的缓存，跑前跑后要先在交互会话里 `/usage` 刷新；Codex 的额度从运行的 rollout 里读。

2026-10-21 额度的历史换算（子代理只读本机转录与额度缓存，未调用模型；结票时并入 Answer）。「每 1% 周额度」按输入等价 token 计（input + 1.25×缓存写 + 0.1×缓存读 + 5×输出，Anthropic 价格比例，对其他家只是粗略权重）：

- Max：每 1% 约 9.9M（Opus 9.1–10.4M）；Fable 另有单独周限额（缓存 `limits[]` 里，上限是周额度的 50%，当时已用 6%），按快照字面推算 Fable 每 token 约是 Opus 的 5–8 倍，按 API 价格比是 2.5 倍，未定。advisor 调用推断不计入 Fable 份额。10-21 已用 60%，10-23 重置。
- Kimi：每 1% 约 0.56M，是瓶颈；K3 同时当选手和评委。
- 智谱：每 1% 约 0.87M。
- ChatGPT Pro：gpt-6-astra 每 1% 约 0.8M（是 gpt-6.1-sol 的 1/7–1/10）。额度表现异常、原因未查清：18 天里 7 天窗口提前归零 6 次，另有本地看不到对应用量的跳升。
- 5 小时窗口约等于周额度的 21–25%，一轮至少跨两个 5 小时窗口。
- 典型任务（本机 Claude Code 会话，含子代理）：读本一章 2.6–3.1M，show-me-html 一页 1.0–2.2M（pi 0.4–0.8M），emukc 修 bug 中位约 6M，一轮代码审查约 1M，代码库问答约 0.6M。
- 推算（每道题六个选手各跑一次、三个评委各判一次）：在 Kimi 上，一道 emukc 题约占 6–11%、读本 4–6%、单页 2–4%、审查 1–2%，25% 上限内大约只容得下每个场景一道题；Max 与 Pro 宽松一些（emukc 题 3–9 道）。评委用量按产出文字量估，没有算内嵌资源的整个 HTML。
- 误差：各家都是整数百分比；Kimi、智谱、Codex 若有本机以外的用量，估算偏保守。要定准 Fable 与 astra 的计费权重，需要每个选手各跑一道真题、记前后百分比的校准轮。
