# harness 复用现成框架还是自建

Type: grilling
Status: resolved
Blocked by: 01, 04
Map: [地图](../map.md)

## Question

bench 的 harness 是直接用现成框架（「[现成 agent 评测框架与评分做法](04-existing-frameworks.md)」里最合适的那个），在它上面加场景与选手；还是按本仓库习惯用标准库脚本自建？要定：走哪条路；引入的依赖（Docker、Python 包等）能否接受；七个场景里哪些是现成框架装不下、需要扩展的。参考「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」判断框架对本机各 CLI 的覆盖。

## Answer

自建。2026-10-21 与用户逐项确认：

- 配置基线：选手用本机真实配置（登录、扩展、插件、hooks 原样），不用干净配置。用户接受代价：配置一变，旧结果的可比性下降；为此运行记录要带配置指纹（见地图「Not yet specified」的运行记录）。
- 不用 Docker：选手在本机直接跑。Harbor、BenchFlow、SWE-bench harness 因依赖容器出局；inspect_swe 把模型调用代理回框架 provider，与真实配置矛盾，也出局。
- 第三方包：只在 `bench/` 内可用，用 uv 管理；技能脚本仍只用标准库。
- 路线：在 `bench/` 里用 Python 自建 runner（临时任务目录 → 调用真实 CLI → 收转录与用量 → 跑 verifier / judge → 写结果）。不套 inspect_ai 或 promptfoo：在本机直跑模式下它们都只给 subprocess / exec 钩子，五家调用差异照样手写；自建还能让 judge 直接走 CLI 订阅，不必另配 API key。
- 从研究里借的做法（不借运行时）：SWE 用 F2P / P2P 判据；rubric 拆条、每条单独交给 judge；结果记录 CLI 版本、模型、token、花费与各阶段耗时；能对已有运行只重跑评分。
- 「七个场景里哪些框架装不下」随自建路线失效，不再需要回答。
- 新开「[用真实配置把 v1 的三个 CLI 各无头跑通一次](12-cli-smoke-run.md)」核实研究里未实跑的命令；「[运行隔离、联网与启动方式](06-isolation-network-launch.md)」按本结论改写（去掉配置基线与容器，加日常状态污染）。
