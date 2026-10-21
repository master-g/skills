# 任务定义样张

Type: prototype
Status: open
Blocked by: 05, 06, 08, 09, 10
Map: [地图](../map.md)

## Question

一个任务文件长什么样？为三类场景（SWE、产出物、标准答案）各做一份粗糙样张：给选手的提示词、起始状态（repo@commit 或资料包；代码审查是截取后的引入提交，见「[标准答案类评分](10-grading-reference.md)」）、环境与超时、评判依据（隐藏测试 / rubric / 参考答案；产出物类还有评委核对事实用的资料包，见「[产出物类评分](09-grading-artifacts.md)」）、所属场景与版本号，让用户对着样张定字段。「[运行隔离、联网与启动方式](06-isolation-network-launch.md)」留给样张的字段：每道题的超时；要拷进任务目录的本机数据与 hash（如 emukc 的 `.data/codex` 快照）；判越界用的答案来源（修复提交、issue 与 PR 的 URL）；任务目录要不要放一份 AGENTS.md 盖住三家约 5 KB 的全局指令（真实配置原样保留，中文写作等场景的可比性会受全局指令影响）。样张作为资产链接在本票，不进 `bench/`。
