# v1 选手名册与预算

Type: grilling
Status: resolved
Blocked by: 01
Map: [地图](../map.md)

## Question

v1 拿哪些选手比较？要定：每个 CLI 配哪些模型与档位；要不要「固定 CLI、只换模型」的对照组（如 pi 或 opencode 换模型）；本地 ollama 模型进不进 v1；订阅额度与 API 花费的单轮上限。本机可用的模型与鉴权方式见「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」。

## Answer

2026-10-21 与用户逐项确认。

v1 名册，六个选手，一律用用户日常的默认档位（真实配置里的值，由 runner 读出并记入运行记录）：

| 选手                     | 鉴权与额度                      |
| ------------------------ | ------------------------------- |
| Claude Code + Opus 5.5   | Max 20x 订阅                    |
| Claude Code + Fable 5.1  | Max 20x（Fable 另有单独周限额） |
| Claude Code + Sonnet 5.5 | Max 20x，与 Opus 共用额度       |
| Codex + gpt-6-astra      | ChatGPT Pro                     |
| pi + GLM-5.3             | 智谱 GLM Coding Plan            |
| pi + Kimi K3             | Kimi coding plan                |

- 对照组：不单独设。Claude Code 里三个 Anthropic 模型可互比，pi 里 GLM 与 Kimi 可互比；跨家族比较就是选手之间的比较。用户没有选让 Claude Code 或 OpenCode 也接 GLM / Kimi。
- 档位：只跑日常默认档，每个模型一个选手。按本机配置推断 Opus 是 xhigh，Fable、Sonnet 走全局 medium，codex medium，pi 的 GLM 是 max；未实测，由「[用真实配置把 v1 的三个 CLI 各无头跑通一次](12-cli-smoke-run.md)」核实。
- 预算：一轮跑完全部选手和任务，单个订阅最多用掉周额度的 25%；撞到 5 小时窗时 runner 暂停等待、不算失败。任务数与重复次数按此上限反推。v1 没有按量计费的 API。
- 不进 v1：ollama 本地模型（服务未运行、未拉模型）、第三方中转（codex 的 rightcode / codesome / gptsapi、opencode 的 foxcode-aws，背后模型无法核实）、cursor-agent（团队账号、Auto 路由模型不固定、不出用量）。opencode 与 DeepSeek 用户未选。
- 条款风险，用户知情保留：智谱 GLM Coding Plan 的官方适用工具名单（docs.bigmodel.cn/cn/coding-plan/tool/others，2026-10-21 查）有 Claude Code、OpenCode、Cursor 等，没有 pi。
