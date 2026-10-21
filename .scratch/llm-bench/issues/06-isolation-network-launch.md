# 运行隔离、联网与启动方式

Type: grilling
Status: open
Blocked by: 05, 12
Map: [地图](../map.md)

## Question

一次运行在什么环境里跑、能碰到什么？「[harness 复用现成框架还是自建](05-harness-build-or-reuse.md)」已定：选手在本机直接跑、用真实配置、不用 Docker。在此前提下要定：

- 隔离：任务目录用临时 clone 还是 worktree；选手的自动放行权限怎样只作用于任务目录，名册里的三个 CLI 中 claude、codex 自带沙箱、pi 没有（见「[v1 选手名册与预算](07-contender-roster.md)」），沙箱开不开、pi 怎么约束；本机要能跑技能构建需要的 python3、node 与无头 Chrome（见「[各 CLI 加载技能的方式](02-skill-loading.md)」）；
- 日常状态污染：用真实配置跑，运行会写进日常状态（codex memories 会从 bench 运行里学习、hooks 会触发、`~/.claude/projects` 等处堆积转录），哪些要关掉、哪些要事后清理或隔开；
- 联网：SWE 任务的修复、代码审查题的修复提交与 issue 都在公开 GitHub 上，联网可能直接看到答案；产出物任务已定自带资料包、资料包外的事实算编造（见「[产出物类评分](09-grading-artifacts.md)」），剩下的是写作时要不要同时断网；
- 任务数据：emukc 的测试要读 `.data/codex`（bootstrap 生成、16 MB、源自第三方游戏数据、不在 Git 里），是随公开的 bench 提交、运行时从本地 emukc 拷入，还是在任务目录里重新生成（见「[公开 repo 的 SWE 任务候选](03-swe-candidates.md)」）；
- 启动：一轮运行由用户亲手启动的形式（make 目标或脚本），推进地图的代理不代为启动；超时与中途失败怎么处理。

实测依据见「[用真实配置把 v1 的三个 CLI 各无头跑通一次](12-cli-smoke-run.md)」。
