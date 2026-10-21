# 用真实配置把 v1 的三个 CLI 各无头跑通一次

Type: task
Status: resolved
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

## Answer

2026-10-21 18:55–19:00 用户在终端亲手执行 `bash .scratch/llm-bench/smoke/smoke.sh all`，16 次调用全部退出码 0，单次 7–46 秒；输出在本机 `~/.cache/bench-smoke/`，不入库。版本：Claude Code 2.1.306、codex-cli 0.163.0、pi 1.3.0。

- 无头命令：脚本里的写法都能无人值守跑完并改文件（claude `-p --permission-mode bypassPermissions --output-format stream-json --verbose`；codex `exec -C <目录> -m gpt-6-astra --json -o`，沿用配置里的 workspace-write 沙箱与 never 审批；pi `--mode json --model <provider/id>`，没有审批）。六个选手都只改了 notes.txt。
- 实际档位：Opus 5.5 xhigh、Fable 5.1 high、Sonnet 5.5 medium（Claude 转录的 `perTurnEffort`；「[v1 选手名册与预算](07-contender-roster.md)」推断 Fable 走 medium，实为 high）；gpt-6-astra medium（rollout 的 `turn_context`）；GLM-5.3 与 Kimi K3 都是 thinking max，pi 里 Kimi K3 的 id 是 `kimi-coding/k3`。Claude 的 init 消息不带档位，runner 要从转录读。
- 显式调用技能：claude `/show-me-html …`、codex `$show-me-html …`、pi `/skill:show-me-html …` 都生效，六个选手都答出 SKILL.md 的第一个二级标题。
- 构建：gpt-6-astra 用 show-me-html 做出 page.html，自己跑 `build.py --no-render` 通过；脚本事后在沙箱外跑 `--check-only` 也通过，含 500 / 1024 / 1280 渲染检查。它主动跳过了渲染，所以 codex 沙箱里能否起无头 Chrome 仍未验证。
- 评委看图：Fable（Read 工具读 PNG）、gpt-6-astra（`-i`）、Kimi K3（`@shot.png`）都答出「7429、红色」，Kimi 的运行里没有 image omitted。
- 用量字段：claude 结果有 `total_cost_usd` 与分模型 `modelUsage`，每次运行还输出一条 `rate_limit_event`，带 5 小时与 7 天窗口的小数用量；codex 的 `turn.completed.usage` 只有 token，rollout 的 `token_count.rate_limits` 带周窗口 `used_percent`；pi 每条消息有 token 与按价目表折算的 cost。Kimi 与智谱的额度只能从各自接口读，都是整数百分比。
- 单次开销：真实配置让每次调用先带 3–9 万 token 的固定上下文（Claude 加载 164 个技能、10 个插件、2 个 MCP 服务器）。七次 Claude 调用按 API 价折算共约 2.4 美元（Fable 每次约 0.58、Opus 0.22、Sonnet 0.11），7 天窗口从 0.11 到 0.12；codex 构建那次让周用量从 27% 到 28%；智谱 5 小时窗从 0 到 1%，Kimi 周用量不变。
- 日常状态（运行期间 3321 个文件有改动，其余来自同时在跑的其他会话）：每次会话的转录；codex 每在一个新目录运行就往 `~/.codex/config.toml` 追加一条 `[projects."<任务目录>"]` 信任记录（这次 3 条，配置文件 hash 因此改变），启动时还刷新 `~/.codex/.tmp/marketplaces`（约 3100 个文件）；pi 的 hermes 记忆扩展把会话记进 `sessions.db`，context-mode 扩展写了 86 个会话文件（USER.md 未改）；Claude 每次触发 6 个 SessionStart hook，其中一个往会话注入「PONYTAIL MODE ACTIVE」。codex memories 没有变化，任务目录里没有 pi-lens 残留。
- 额度插曲：Claude 的周用量在同一窗口（10-16 12:00 起）里，从 14:03 缓存的 60% 变成 18:54 刷新后的 12%，Fable 单独额度从 6% 归零，原因未知（推测官方重置或调整）。下面 Comments 里 Max 的「每 1% 约 9.9M」以 60% 为分母，已不可靠；Kimi、智谱、Codex 的换算不受影响，Kimi 仍是瓶颈。

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
