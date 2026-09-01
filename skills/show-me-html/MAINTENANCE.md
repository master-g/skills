# MAINTENANCE — show-me-html 维护规则

本文件面向**修改这个 skill 的人**（包括维护它的 agent），不进页面生成路径。
方法出处：Vercel《How our agents build on-brand pages with design.md》(2026-08-31) 的评测环方法。

## 纠正路由

评审或眼检发现一个失败时，把它落进**能稳定执行的最窄处**，一次只落一个主落点：

| 失败类型                     | 落点                                      | 例子                              |
| ---------------------------- | ----------------------------------------- | --------------------------------- |
| 判断类（怎么写更好）         | `references/*.md` 散文                    | 「先写模型函数再写图」            |
| 可复用机制（每个页面都该有） | `assets/shell.html` 骨架                  | 滑块轨道填充、间距节奏            |
| 可机械核对                   | `scripts/build.py` 检查（ERROR/WARN）     | 斜线 `<line>`、写死颜色、横向溢出 |
| harness 自身的问题           | harness（build.py / 骨架的 TOC 与导出器） | TOC 吞掉卡片内标题                |
| 只有一个模型 / 只出现一次    | 观察名单（本文末尾），复现后再编码        | —                                 |

**禁止调用方补丁**：失败出在骨架或导出器时，只在当页改标记绕过（加 skip、换标签），
同一失败会在下一页复发。页面层的绕过是止血，必须同时在名册登记并按上表安排根治。

## 毕业规则

眼检发现**同一失败第二次**出现 → 必须毕业为 `build.py` 检查（ERROR 或 WARN），
并把 `references/anti-patterns.md` 里对应条目的状态推进为 `已检查`。
命名过的失败倾向于不再出现——前提是它进了检查，而不是只留在记忆里。

## 联动规则

改 `assets/shell.html` 或 `scripts/build.py` 后，提交前按 `scenarios/README.md` 的轮次流程
跑冻结场景（时间紧时至少 `status-report` + `concept-explainer` 两个：
一个验只读排版，一个验 JS 交互），改动前后各一轮，人工盲比。
轮次产出存 `scenarios/rounds/<日期>-<git短sha>/`，不进 git。

旧页面（骨架改动前生成的）不会自动获得新骨架行为 —— 它们携带的是生成时的骨架副本。
骨架修复只对今后从新 `shell.html` 起手的页面生效；历史页面不动。
旧页面的回归用 `--check-only` 验证新检查不误报即可。

## 版本规则

- `/Users/mg/github/skills` 是**唯一 source of truth**。改动先落在仓库并提交，再同步安装副本。
- 禁止只改 `~/.agents/skills/show-me-html`（安装副本）——2026-08 曾因此漂移 7 个文件，
  仓库丢掉 diagrams.md 与 46rem 规则近一周，无法做任何改动前后的对比。
- 同步命令（仓库 → 安装副本）：

  ```sh
  rsync -a --delete --exclude .git --exclude agents --exclude README.md \
    /Users/mg/github/skills/skills/show-me-html/ ~/.agents/skills/show-me-html/
  ```

  （不用 `npx skills add . -g`：实测报「PromptScript does not support global skill installation」，
  文件虽复制但注册环节失败，不作为验证过的通道。）

  同步后用 `diff -rq skills/show-me-html ~/.agents/skills/show-me-html` 验证一致
  （`.git`、`agents/`、`README.md` 属仓库侧文件，差异属预期）。

## 观察名单（复现后编码）

单一模型或单次出现的失败先记在这里，复现第二次再按纠正路由落点：

| 日期 | 失败描述 | 出现次数 |
| ---- | -------- | -------- |
| —    | —        | —        |
