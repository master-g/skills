# 工单 #9 随机本地图片实机验收

在项目根目录运行以下命令生成 [派发计划](plan.json)。[会话入口](session.json) 记录了当时的模型目录和取图接口。

```sh
python3 skills/farm/entry_plan.py .farm/vision9-1tlf848z-brief.md --session .farm/vision9-1tlf848z/session.json --named native codex --model gpt-6.1-terra --variant low --select native codex --reason '核对同一原生视觉组合能否经标准 brief 入口完成读图'
```

用户确认这一次调用后，编排者按计划通过 `collaboration.spawn_agent` 启动独立上下文的 `vision9_retest` worker（`fork_turns=none`）。worker 依据 [brief](vision9-1tlf848z-brief.md) 用 `view_image` 打开[本地 PNG](sample.png)，并将观察结果写入[报告](vision9-1tlf848z-report.md)。附件保留运行时路径。

派发前，编排者在工作区外保存随机生成的答案，并记录其 UTF-8 字节（无换行）的 [SHA-256](expected.sha256)。派发后，从落盘报告提取的 `MECPK9FPJ9` 与原始答案逐字一致，重新计算的 SHA-256 同样匹配。这次验收覆盖 Codex 原生入口、`gpt-6.1-terra`、`low` 和上述本地图像取得方式的一次调用。
