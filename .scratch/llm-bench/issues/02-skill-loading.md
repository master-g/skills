# 各 CLI 加载技能的方式

Type: research
Status: claimed
Map: [地图](../map.md)
研究分支：`research/bench-skill-loading`（本地，不推送）· 文件 `docs/research/2026-10-21-bench-skill-loading.md`

## Question

tufte-reader、show-me-html 这类技能在 claude、codex、pi、cursor-agent、opencode 里能不能用、怎么用？查清：

- 每个 CLI 从哪些目录发现技能，`npx skills add -g`（本仓库 `make install`）实际装到了哪些 agent 目录；
- 带 `disable-model-invocation: true` 的技能（tufte-reader 有这条）在无头模式下能否由提示词触发，例如提示词以 `/tufte-reader` 开头；
- 技能依赖的脚本与运行时（python3、node、构建后打开浏览器）在无头运行里会不会卡住、需不需要关掉；
- 不支持技能的 CLI 有没有等价做法（把 SKILL.md 当上下文喂入），这样做还算不算「技能遵循」。

结论写成 CLI × 能力的矩阵，注明来源。约束同「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」：只跑 `--help` / `--version`。
