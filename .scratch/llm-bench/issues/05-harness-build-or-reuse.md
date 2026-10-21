# harness 复用现成框架还是自建

Type: grilling
Status: open
Blocked by: 01, 04
Map: [地图](../map.md)

## Question

bench 的 harness 是直接用现成框架（「[现成 agent 评测框架与评分做法](04-existing-frameworks.md)」里最合适的那个），在它上面加场景与选手；还是按本仓库习惯用标准库脚本自建？要定：走哪条路；引入的依赖（Docker、Python 包等）能否接受；七个场景里哪些是现成框架装不下、需要扩展的。参考「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」判断框架对本机各 CLI 的覆盖。
