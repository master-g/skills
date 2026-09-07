---
name: bootstrap-claude
license: MIT
disable-model-invocation: true
description: 创建或修复项目的 CLAUDE.md、AGENTS.md 与 PROJECT_MEMORY.md，或按要求维护项目记忆。
---

# bootstrap-claude

维护进仓库、供团队和任何 agent 共享的项目上下文：CLAUDE.md / AGENTS.md 记录操作事实，PROJECT_MEMORY.md 记录无法从代码或 Git 推导的决策与失败原因。它与 Claude Code 的个人自动记忆互不替代。

`<skill>` 为本 SKILL.md 所在目录。

## 分支

- 初始化或修复项目指令：读 [初始化与兼容](references/bootstrap.md)。
- 记录决策、更新交接：读 [项目记忆维护](references/maintain.md)。
- 两者都要时先指令文件，后记忆。

## 所有分支共用的不变量

只编辑脚本报告的真源文件（source of truth），已有内容一律保留，追加或定点修改。所有事实来自当前代码、配置和文档，找不到定义的命令不写入。
