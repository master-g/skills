# 冻结场景集 — show-me-html 评测环

方法出处：Vercel《How our agents build on-brand pages with design.md》(2026-08-31)。
七个提示词冻结成场景，指引是轮次之间唯一变化的东西 —— 输出的任何差异都能追溯到指引。

本目录是同一机制的最小版：**五个场景 + 一套轮次流程**。不需要模型评委、
不需要盲评工具，从「一个交付物 + 一次人工对比」起步。

## 场景清单

| 场景                 | 配方              | 覆盖的交互重量                   |
| -------------------- | ----------------- | -------------------------------- |
| `status-report/`     | status-report     | 纯只读，指标块 + 分组进展        |
| `approach-compare/`  | approach-compare  | 三卡对比 + 判据表                |
| `code-review/`       | code-review       | 结构 diff + 折叠 + 勾选框        |
| `concept-explainer/` | concept-explainer | 滑块驱动实时模型（先写模型函数） |
| `triage-board/`      | triage-board      | 拖拽 + 键盘替代 + 计数回显       |

## 轮次流程

改 `assets/shell.html` 或 `scripts/build.py` 之后（MAINTENANCE.md 联动规则）：

1. 记下当前 git 短 SHA：`git rev-parse --short HEAD`。
2. 让任一 agent 读本目录选中的场景文件，按其冻结材料生成页面，输出到
   `rounds/<日期>-<SHA>/<场景名>.html`（`rounds/` 不进 git，仅本地对比用）。
3. 每页跑 `python3 scripts/build.py <页面>`，ERROR 必须为零。
4. 与上一轮同名页面对比：结构、两套主题、名册三条自查（见 `references/anti-patterns.md`）。
5. 差异只能来自骨架 / 检查 / 指引的改动 —— 若不是，先怀疑场景材料被改过。

最小替代：时间紧时至少跑 `status-report` + `concept-explainer` 两个
（一个验只读排版，一个验 JS 交互与模型函数）。

## 场景文件契约

每个场景的 SCENARIO.md 冻结四样东西，**轮次之间不得改动**：

- 配方名与读者任务（意图四维中的「任务 / 读者」）
- mock 材料（全部数字、人名、事件 —— 生成时禁止编造材料之外的内容）
- 通过标准（机械关之外的人工判据）
- 版心与特殊约束（如有）

新增失败判例后可以加场景，但要新建场景而不是改旧场景 —— 旧场景是基线的一部分。
