# textkit — Claude 项目上下文

> 跨会话记忆见 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。

## 技术栈
- Python 3.11+，依赖管理用 poetry，lint 用 ruff。

## 命令
- 安装: `poetry install`
- 测试: `poetry run pytest`
- Lint: `poetry run ruff check src`

## 代码风格
- 行宽 100，类型标注必填。

## 禁止文件
- `poetry.lock`（由工具生成）

## 审查规则
- 合并前 pytest + ruff 必须通过。

## 项目记忆 (回写约定)
跨会话信息记录在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。完成任务后回写。
