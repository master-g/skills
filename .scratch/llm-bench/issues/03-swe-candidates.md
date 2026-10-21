# 公开 repo 的 SWE 任务候选

Type: research
Status: resolved
Map: [地图](../map.md)
研究分支：`research/bench-swe-candidates`（本地，不推送）· 文件 `docs/research/2026-10-21-bench-swe-candidates.md`

## Question

`/Users/mg/github` 下的公开 repo 里，有哪些历史 issue 或 feature 能改造成可复现的 SWE 任务？范围：emukc、skills、cmg、kloud、pi-wingman、pi-usage-hud、herdr-panes、algebrica-zh、calculus-made-easy-zh，以及上游不属于用户的 algebrica（antoniolupetti）、dictionary-of-ai-coding（mattpocock）。

对每个 repo 先记：语言、规模、测试命令、本机能否跑通、单次测试耗时。再列候选：

- 修 issue：已关闭且能对应到修复提交的 issue（用 gh 查），修复提交是否带测试，父提交上这些测试是否失败（抽查前几条）；
- 实现 feature：带测试的功能提交，需求能否用几句话独立说清；
- 每条候选给出 repo@父提交、修复或功能提交、改动规模、有无现成测试可作 oracle、难度粗估。

只读：不动这些 repo 的工作区，要跑测试就 clone 到临时目录；不推送。候选按「能否作 oracle」排序，不替用户挑选。

## Answer

详见分支 `research/bench-swe-candidates`（95f6df2）的 `docs/research/2026-10-21-bench-swe-candidates.md`：主表 30 条（A–D 四级，附 repo@父提交、修复提交、链接、规模、实测与难度），其余在附表。

- 候选集中在 emukc，其次 skills、cmg、pi-wingman、algebrica-zh。抽查 66 对「父提交 → 修复提交」（把修复带的测试搬到父提交上跑）：31 对可直接作 oracle；28 对的测试用到修复新增或改签名的符号，要在题面写明接口；6 对受环境或混合提交牵制；1 对父提交上也通过，弃用。
- 只有 emukc 能把 GitHub issue 对上带测试的修复，issue 正文自带「What / Source / Done when」可原样当题面；抽查 30 个 issue，9 个可直接用、18 个要写明接口。cmg 有逐条验收的本地工单可作题面。
- emukc 的代价：测试大多要读 `.data/codex`（bootstrap 生成、16 MB、不在 Git 里，源自第三方游戏数据）；`emukc_bootstrap` 有联网测试且当前头上有 1 条失败，oracle 要按测试名或 crate 限定范围。
- 基本没有候选：algebrica 上游（只有 Markdown / SVG）、dictionary-of-ai-coding（只有无测试的 README 生成器）、kloud（公开分支只一条带测试的小功能）、calculus-made-easy-zh（译文与工具改动混在一个提交里）。
- 并行跑 Rust 任务要给每次运行单独的 `CARGO_BUILD_BUILD_DIR`：本机 `~/.cargo/config.toml` 固定了 `build-dir`，同名项目并行构建会互相覆盖，研究中出现过假编译错误。
- 未查清：`.data/codex` 能否随公开 bench 提交；全新容器冷编译 emukc 依赖的耗时；候选只各跑一次、未查 flaky；emukc #178 缺数据未验证；algebrica-zh 早期提交依赖未入库文件的原因。
