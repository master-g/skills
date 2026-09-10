# 项目记忆维护

`<skill>` 指本技能根目录。回写排在验证之后、提交之前，与本次改动进同一个提交；不提交的任务在结束前回写。每次改写「上次会话」「下次运行」两节；「已验证的事实」「失败尝试」只在本次产生了对应内容时追加。

## 写什么

只写代码和 Git 推导不出的内容：架构、目录结构、变更历史都能重新推导，不进记忆。每条写清 **why**：「换到 esbuild（webpack 在 CI runner 上 OOM）」值得留，「换了打包器」不值得。

| 小节         | 性质     | 内容                                                                       |
| ------------ | -------- | -------------------------------------------------------------------------- |
| 已验证的事实 | 追加     | 本次确认的决策或约束（"auth 用 cookie 里的 JWT，不是 header"）             |
| 失败尝试     | 追加     | 走不通的路径和原因，防止下次重走                                           |
| 上次会话     | 整节改写 | 停在哪个分支，验证命令与实际结果（"make test 通过" / "npm test 失败于 X"） |
| 下次运行     | 整节改写 | 接下来的计划与优先级                                                       |

追加类小节的新条目放在末尾，`- [YYYY-MM-DD]` 前缀。改写类小节每次只留最新一条，历史由 Git 保存。

## 怎么写

```bash
python3 <skill>/scripts/memory.py add <workspace>/PROJECT_MEMORY.md \
  --section "失败尝试" --text "试过用 X 做 Y，因为 Z 放弃，改用 W"
python3 <skill>/scripts/memory.py add <workspace>/PROJECT_MEMORY.md \
  --section "上次会话" --text "feat/x；make test 通过；停在补集成测试"
```

`add` 自动加当天日期（`--date` 可覆盖），对「上次会话」「下次运行」执行整节改写。直接编辑文件效果相同。

## 完成标准

回读本次写入：追加类小节原有条目一条不少，改写类小节只剩本次一条。有提交时，提交后 `git status` 里 PROJECT_MEMORY.md 没有未提交改动。文件超过 400 行时运行 `python3 <skill>/scripts/memory.py compact <workspace>/PROJECT_MEMORY.md`，它只淘汰最旧的「失败尝试」并逐条打印；若仍超限，手工把「已验证的事实」中多条窄事实合并为少数通用事实。
