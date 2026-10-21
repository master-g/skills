# 运行隔离、联网与启动方式

Type: grilling
Status: open
Blocked by: 05
Map: [地图](../map.md)

## Question

一次运行在什么环境里跑、能碰到什么？要定：

- 隔离：临时 clone、worktree 还是容器；选手的自动放行权限只在隔离内生效；隔离环境里要能跑技能构建需要的 python3、node 与无头 Chrome（见「[各 CLI 加载技能的方式](02-skill-loading.md)」）；
- 联网：SWE 任务的修复就在公开 GitHub 上，联网可能直接看到答案；写作类（阿波罗读本）是给固定素材包，还是让选手自己查资料；
- 任务数据：emukc 的测试要读 `.data/codex`（bootstrap 生成、16 MB、源自第三方游戏数据、不在 Git 里），是随公开的 bench 提交、运行时从本地 emukc 拷入，还是在隔离环境里重新生成（见「[公开 repo 的 SWE 任务候选](03-swe-candidates.md)」）；
- 配置基线：选手用本机真实的全局配置（pi 的扩展包、opencode 插件、codex memories 与 hooks 等，见「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」），还是干净配置；「真实表现」与可重复、可比之间怎么取舍；
- 启动：一轮运行由用户亲手启动的形式（make 目标或脚本），推进地图的代理不代为启动；超时与中途失败怎么处理。

依赖「[harness 复用现成框架还是自建](05-harness-build-or-reuse.md)」：复用框架时先看它的隔离默认值。
