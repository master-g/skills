# 各 CLI 加载技能的方式

Type: research
Status: resolved
Map: [地图](../map.md)
研究分支：`research/bench-skill-loading`（本地，不推送）· 文件 `docs/research/2026-10-21-bench-skill-loading.md`

## Question

tufte-reader、show-me-html 这类技能在 claude、codex、pi、cursor-agent、opencode 里能不能用、怎么用？查清：

- 每个 CLI 从哪些目录发现技能，`npx skills add -g`（本仓库 `make install`）实际装到了哪些 agent 目录；
- 带 `disable-model-invocation: true` 的技能（tufte-reader 有这条）在无头模式下能否由提示词触发，例如提示词以 `/tufte-reader` 开头；
- 技能依赖的脚本与运行时（python3、node、构建后打开浏览器）在无头运行里会不会卡住、需不需要关掉；
- 不支持技能的 CLI 有没有等价做法（把 SKILL.md 当上下文喂入），这样做还算不算「技能遵循」。

结论写成 CLI × 能力的矩阵，注明来源。约束同「[各 CLI 的无头调用、选模型与权限旗标](01-cli-headless.md)」：只跑 `--help` / `--version`。

## Answer

详见分支 `research/bench-skill-loading`（466eeb2）的 `docs/research/2026-10-21-bench-skill-loading.md`。调用写法除 claude 外都是读源码推断，未实跑。

- 五个 CLI 都原生支持技能，本机都能发现 tufte-reader 与 show-me-html：`make install` 复制到 `~/.agents/skills/<name>`（codex、pi、cursor-agent、opencode 读这里），另为 claude 建 `~/.claude/skills/<name>` 符号链接。
- 显式调用写法各不同：claude、cursor-agent `-p "/tufte-reader …"`；pi `-p "/skill:tufte-reader …"`；codex `exec '$tufte-reader …'`；opencode `run --command tufte-reader "…"`。五家都能显式调用只许用户触发的技能。
- `disable-model-invocation: true` 只有 claude、pi、cursor-agent 认；codex 看 `agents/openai.yaml`（两技能都设了不许自动调用）；opencode 1.19.3 不认，tufte-reader 可能被自动触发。所以「能否自动触发」不能横向比较。
- 无头运行不会卡在交互上；要注意构建的 `--open` 会弹浏览器（任务说明写「不要打开浏览器」即可），show-me-html 构建会跑无头 Chrome 检查，沙箱里起不来会让构建失败。
- 把 SKILL.md 当上下文喂入与显式调用拿到的信息相同，测得出照做程度、测不出自动触发；两种方式的结果不放进同一张对比表。
- 建议：两个技能场景一律显式调用；每次运行记录技能目录 hash 与 CLI 版本；任务目录里不放同名技能副本。
- 未查清：cursor-agent 服务端如何组装技能内容；claude `--bare` 下能否找到技能；沙箱内能否起无头 Chrome（归「运行隔离、联网与启动方式」）。
