# 运行隔离、联网与启动方式

Type: grilling
Status: open
Blocked by: 05
Map: [地图](../map.md)

## Question

一次运行在什么环境里跑、能碰到什么？要定：

- 隔离：临时 clone、worktree 还是容器；选手的自动放行权限只在隔离内生效；
- 联网：SWE 任务的修复就在公开 GitHub 上，联网可能直接看到答案；写作类（阿波罗读本）是给固定素材包，还是让选手自己查资料；
- 启动：一轮运行由用户亲手启动的形式（make 目标或脚本），推进地图的代理不代为启动；超时与中途失败怎么处理。

依赖「[harness 复用现成框架还是自建](05-harness-build-or-reuse.md)」：复用框架时先看它的隔离默认值。
