---
name: bootstrap-claude
license: MIT
disable-model-invocation: true
description: 创建或修复项目的 CLAUDE.md、AGENTS.md 与 PROJECT_MEMORY.md，或按要求维护项目记忆。
---

# bootstrap-claude

维护进仓库、供团队和任何 agent 共享的项目上下文：CLAUDE.md / AGENTS.md 记录操作事实，PROJECT_MEMORY.md 记录无法从代码或 Git 推导的决策与失败原因。它与 Claude Code 的个人自动记忆互不替代。

`<skill>` 为本 SKILL.md 所在目录。

## 入口

任何时候先跑 `python3 <skill>/scripts/setup_context.py --dir <workspace>`，按输出走：

- 新目录（`created CLAUDE.md from template`）：按 [初始化与兼容](references/bootstrap.md) 填真实事实。
- 已初始化：看 `convention:` 一行。`latest` 不动；`upgraded` / `end marker added` 已自动升级到最新回写约定；`OUTDATED (legacy …)` 先读该节，再加 `--upgrade-convention` 重跑并把打印出的自定义行补回结束标记之后；`unmanaged` 说明项目自写了约定，只报告不改。
- 会话收尾回写、沉淀经验或压缩记忆：读 [项目记忆维护](references/maintain.md)。回写是提炼不是记录，结束前必须过 `scripts/memory.py check`。
- 两者都要时先指令文件，后记忆。

## 所有分支共用的不变量

只编辑脚本报告的真源文件（source of truth），已有内容一律保留，追加或定点修改。所有事实来自当前代码、配置和文档，找不到定义的命令不写入。
