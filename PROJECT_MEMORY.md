# 项目记忆 — skills

> 跨会话的持久信息，只记代码、Git 和文档推导不出的内容。回写约定见 [AGENTS.md](./AGENTS.md)。
> 门槛：全文 ≤ 24 KB，单行 ≤ 300 字符；改写节各只留一块。

## 已验证的事实

<!-- 追加：确认过的决策和约束，每条一行：结论 + 原因 + 来源。同主题改写既有条目，不追加第二条。 -->

- [2026-10-12] bootstrap-claude 以 AGENTS.md 为唯一真源、CLAUDE.md 只写一行 @AGENTS.md、不建 symlink（Firefox 布局，Claude Code 文档推荐；plans/README.md 记有决定）
- [2026-10-12] 英文仓库的英文模板（--lang en）暂不做：别名表已能识别英文标题，缺失章节仍以中文追加；等有真实需求再议（plans/README.md Open decisions）

## 失败尝试

<!-- 追加：走不通的路径及原因，每条一行。 -->

## 上次会话

<!-- 整块改写：分支、验证命令及实际结果、停在何处；任务细节只留一行指向证据目录。 -->

- [2026-10-12] main；improve 计划 001–006 全部合入（006 修 marked 约定块升级静默丢块内自定义行，起因是 DopaManga v2→v3 丢了 @PROJECT_MEMORY.md 导入），已 make install；未推送
  验证：两组 test_*.py ok、make check 通过、用 DopaManga HEAD:AGENTS.md 复现确认被丢行已打印

## 下次运行

<!-- 整块改写：接下来的任务和优先级，含仍受阻的项。 -->

- [2026-10-12] 推送 main（含 006）；其他旧布局项目装新版后各跑一次 setup_context.py，看 git diff，填「导航」「工作流与陷阱」或写明暂无；已升到 v3 的仓库核对约定块内自定义行是否丢失
