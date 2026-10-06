# skills

- 直接提交到 `main`，提交信息用 conventional commits 格式，scope 写技能名，如 `fix(farm): ...`。
- 技能文档之间按标题名引用章节（「门禁」），不按编号；`make check` 会检查这一条和失效的相对链接，pre-commit 也会跑。
- 弃用技能用 `make deprecate SKILL=<name>`，再按它打印的提示补完 ARCHIVE.md 和 README.md。
- 新增或改名技能时同步 README.md 的技能列表。
