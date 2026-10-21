# 运行隔离、联网与启动方式

Type: grilling
Status: resolved
Blocked by: 05, 12
Map: [地图](../map.md)

## Question

一次运行在什么环境里跑、能碰到什么？「[harness 复用现成框架还是自建](05-harness-build-or-reuse.md)」已定：选手在本机直接跑、用真实配置、不用 Docker。在此前提下要定：

- 隔离：任务目录用临时 clone 还是 worktree；选手的自动放行权限怎样只作用于任务目录，名册里的三个 CLI 中 claude、codex 自带沙箱、pi 没有（见「[v1 选手名册与预算](07-contender-roster.md)」），沙箱开不开、pi 怎么约束；本机要能跑技能构建需要的 python3、node 与无头 Chrome（见「[各 CLI 加载技能的方式](02-skill-loading.md)」），冒烟时 gpt-6-astra 自己跳过了渲染检查，codex 沙箱里能否起无头 Chrome 仍未验证；
- 日常状态污染：用真实配置跑，运行会写进日常状态（codex memories 会从 bench 运行里学习、hooks 会触发、`~/.claude/projects` 等处堆积转录），哪些要关掉、哪些要事后清理或隔开；冒烟实测（「[用真实配置把 v1 的三个 CLI 各无头跑通一次](12-cli-smoke-run.md)」）：codex 往 `config.toml` 追加任务目录的信任记录并刷新插件市场，pi 的 hermes 记忆与 context-mode 扩展记下会话，Claude 的 SessionStart hook 往选手会话注入 ponytail 模式，codex memories 未变；
- 联网：SWE 任务的修复、代码审查题的修复提交与 issue 都在公开 GitHub 上，联网可能直接看到答案；产出物任务已定自带资料包、资料包外的事实算编造（见「[产出物类评分](09-grading-artifacts.md)」），剩下的是写作时要不要同时断网；
- 任务数据：emukc 的测试要读 `.data/codex`（bootstrap 生成、16 MB、源自第三方游戏数据、不在 Git 里），是随公开的 bench 提交、运行时从本地 emukc 拷入，还是在任务目录里重新生成（见「[公开 repo 的 SWE 任务候选](03-swe-candidates.md)」）；
- 启动：一轮运行由用户亲手启动的形式（make 目标或脚本），推进地图的代理不代为启动；超时与中途失败怎么处理；启动时机：一轮占周额度 25%，要在各订阅周用量够低时启动（Claude 10-21 下午显示 60%，傍晚刷新成 12%，原因未知），并跨至少两个 5 小时窗口；并发：同一订阅内串行，不同订阅之间能否按 CLI 分线并发（用户 10-21 问过冒烟为何不并发）（实际用量见「[用真实配置把 v1 的三个 CLI 各无头跑通一次](12-cli-smoke-run.md)」）。

实测依据见「[用真实配置把 v1 的三个 CLI 各无头跑通一次](12-cli-smoke-run.md)」。

## Answer

2026-10-21 与用户逐项确认。前提沿用「[harness 复用现成框架还是自建](05-harness-build-or-reuse.md)」：本机直跑、真实配置。下面两处是对真实配置的有意偏离，都要记进配置指纹：选手运行时关掉跨会话记忆；codex 关掉沙箱。

- 任务目录：每次运行在 `~/.cache/bench/` 下新建，从本地 repo 克隆，删掉起始提交之后的提交和 remote。选手能用 git log / blame，但看不到修复提交。目录在任何仓库之外，不会读到 skills 的 AGENTS.md。Claude 的自动记忆按目录路径存，路径不同就不会串。不用 worktree：worktree 共用 .git，`git log --all` 能看到修复提交。也不复用固定路径：Claude 的自动记忆会在同一选手的各道题之间串。
- 跨会话记忆：选手运行时读写都关。codex 按次把 `memories.generate_memories` 与 `memories.use_memories` 设为 false；pi 不加载 hermes 记忆扩展，会话用 `--session-dir` 存进 bench 自己的目录。原因：任务出自用户自己的 repo，修复多半就是用这几个 CLI 做的，日常记忆和历史会话搜索里可能直接有答案；反过来，bench 会话也会被记下。实测冒烟的 4 个 codex 线程 `memory_mode` 为 enabled，还排在记忆生成队列里（1515 个线程只处理了 39 个）。按次关闭后线程是否会被标为不生成，实施时核实。
- 沙箱：三家都不设沙箱。claude 用 bypassPermissions，codex 用 `--dangerously-bypass-approvals-and-sandbox`，pi 照原样，相当于「有人批准一切」的无头版本。2026-10-21 用户确认后用 `codex sandbox -P :workspace --log-denials` 实测（不调模型）：日常的 workspace-write 沙箱里，show-me-html 的 `build.py --check-only` 三个宽度的探针都没返回，Chrome 的 mach-lookup 被拒；curl 连本机代理 127.0.0.1:10920 被拒。冒烟时 codex exec 的 `turn_context` 也是 `network_access: false`，`.git` 只读。配置里顶层的 `network_access = "enabled"` 没有生效。日常交互时 codex 会请用户批准越出沙箱，无头运行的审批是 never，越不出去。防护靠两点：任务目录在仓库外、没有 remote；运行后 harness 核对源 repo 与各 CLI 的配置文件有没有被改，改了就在运行记录上标记。
- 联网：不拦。选手必须连模型 API，构建也要联网（cargo、npm、Google Fonts）。harness 扫转录，访问过题目 repo 的修复提交、issue 或 PR 页面，或执行过 git fetch 的运行，标为越界，计为未解决或不合格。产出物任务照资料包判编造，已在「[产出物类评分](09-grading-artifacts.md)」定下。
- emukc 数据：首次从本地 emukc 拷一份 `.data/codex` 快照到 bench 的本机数据目录，记下 hash，不入库。每次运行拷进任务目录，hash 对不上就拒跑。不入库是因为它是第三方游戏数据；不每次重新生成是因为 `emukc bootstrap` 要联网下载，数据随游戏更新而变，跨时间没法比。
- 并发：按订阅分四条线，线与线并行，线内串行。四条线是 Max（Opus、Fable、Sonnet，以及 Fable 评委）、Pro（astra，选手兼评委）、智谱（GLM）、Kimi（K3，选手兼评委）。评分等全部选手运行结束后，再按同样的线跑。Rust 任务每次运行用独立的 `CARGO_BUILD_BUILD_DIR`（见「[公开 repo 的 SWE 任务候选](03-swe-candidates.md)」）。耗时照记，并注明并发度。本机是 M5，10 核，32 GB。
- 超时与失败：超时由任务文件给，到点杀掉整个进程组，计为超时（未解决或不合格），不重试。限流、网络错误、5xx、CLI 崩溃且没有产出的，自动重试 1 次，重试也记进运行记录。撞到 5 小时窗就暂停该线，见「[v1 选手名册与预算](07-contender-roster.md)」。runner 中断后再启动，跳过已完成的运行。
- 清理：运行结束、产物与转录拷进运行记录之后，做三件事：从 `~/.codex/config.toml` 删掉指向本轮任务目录的 `[projects]` 段，只动这些段，改前备份；删掉任务目录；删掉 `~/.claude/projects` 下对应任务目录的文件夹。codex 的 rollout 不删，它在 codex 状态库里有登记，删了文件会留下悬空记录。codex 的插件市场缓存不处理。
- 启动：用户在终端亲手执行一条命令，跑整轮，入口名归地图上的仓库接入。runner 在前台运行、防休眠、按线打印进度。启动前先打印各订阅的周用量与重置时间，用户确认后才开跑。运行中某条线本轮累计用到周额度的 25%，就停下该线剩余的运行，记为「未跑：额度」。启动前还要检查本机有没有技能构建需要的 python3、node 与 Chrome。
- 不改的：Claude 的 6 个 SessionStart hook（其中一个往会话里注入 ponytail 模式），以及三家各约 5 KB 的全局指令文件（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.pi/agent/AGENTS.md`），都按真实配置保留。任务目录要不要放一份 AGENTS.md 盖住全局指令，交给「[任务定义样张](11-task-format-prototype.md)」。
