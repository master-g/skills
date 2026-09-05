---
name: bootstrap-claude
license: MIT
description: 创建或修复项目的 CLAUDE.md、AGENTS.md 与 PROJECT_MEMORY.md，或在用户要求时维护项目记忆。
---

# bootstrap-claude

帮助后续会话读取项目指令与必要的历史决策。仅因文件缺失或普通任务结束，不触发初始化与回写。

## 选择模式

- 用户要求初始化或修复项目指令：读 [初始化与兼容](references/bootstrap.md)。运行 `scripts/setup_context.py`，再用当前仓库的真实事实填充所需章节。
- 用户要求记录决策、更新进度，或项目已有明确回写约定：读 [项目记忆维护](references/maintain.md)。只更新有关条目和发生变化的命令；不顺带运行初始化脚本。
- 两个请求都有时，先处理指令文件，再维护记忆。已有明确的源文件选择不重复询问。

## 保持的约定

- CLAUDE.md 与 AGENTS.md 共用一个真实文件。两个独立文件冲突时展示差异，由用户选源文件；不得自行覆盖。
- 项目命令与约束来自当前代码、配置和文档。没有测试时写明事实，不创建测试体系来填满模板。
- 按任务需要读历史记录、选择检查。记录既有失败，不要求先修复无关基线。
- 记忆只保留难以从代码或 Git 推导的决策、失败原因和交接证据。未验证的信息明确标注。
- `setup_context.py` 为已有文件追加缺失章节，不自动替换已有项目规则。用户要求迁移旧规则时，先检查对应段落再定点编辑。

## 验收

初始化后运行 `python3 <skill>/scripts/setup_context.py --dir <workspace> --validate`。
检查真实文件/符号链接关系和所填内容，不把占位符当成完成。维护模式按需运行
`python3 <skill>/scripts/memory.py status <workspace>/PROJECT_MEMORY.md`，回读本次写入，确认原有事实未被覆盖。

项目生成的“完成判定”适用于约定交付物及相关验证，不要求运行所有命令或修复其他任务的问题。

## 工具与模板

`<skill>` 为本 SKILL.md 所在目录。

- `scripts/setup_context.py`：初始化、兼容处理和只读 `--validate`。
- `scripts/memory.py`：`add`、`status`、`compact`；具体用法见维护模式。
- `assets/CLAUDE.template.md`、`assets/PROJECT_MEMORY.template.md`：新建文件的模板。
