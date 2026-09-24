---
name: mdxcn-term
license: MIT
description: 在终端回复里要画 ASCII 图时使用：时间线、清单、表格、对比矩阵、排名条、进度、甘特、目录树、步骤、提示框、diff 统计、漏斗等。用脚本生成带虚线框和 [ TITLE ] 的等宽框图，中文标签也能对齐；不要手画 ASCII 框。
---

# mdxcn-term

终端版 [mdxcn](https://github.com/keshav-exe/mdxcn)：同样的框图，由脚本生成，中文、全角字符和 emoji 按 2 列计算，框线对齐不靠手工数空格。

## 什么时候画

一句话能说清就不画。路径、一晚上的事故、矩阵、清单、改动统计这类结构化内容才画。一段回复最多两张图，图与图之间用文字衔接，先写结论再放图。

## 怎么画

```sh
echo '<props json>' | <本 skill 目录>/scripts/mdxcn <graph> [TITLE]
```

入口脚本优先用 bun，没有再用 node（需 24.2+）。输出已带 ``` 围栏，**原样**贴进回复，不改一个字符。JSON 里也可以写 `title`，命令行的 TITLE 优先。报错时按提示修 JSON，不要退回手画。

标题 1–2 个词（英文会转大写）；标签简短、小写或中文，不写 `AuthMiddleware Layer` 这类名字。

## 选图

| 内容               | graph                                                |
| ------------------ | ---------------------------------------------------- |
| 事故经过、里程碑   | `timeline`                                           |
| 分步操作           | `steps`                                              |
| 待办 `[x]` / `[ ]` | `check`                                              |
| 注意事项、警告     | `callout`                                            |
| A vs B 功能对比    | `compare`（布尔值画成 ✓ / –）                        |
| 两个维度的精确数字 | `matrix`                                             |
| 多行多列数据       | `table`；带分组标题用 `sheet`                        |
| 键值规格           | `spec`                                               |
| PR 改了什么        | `diff`，覆盖率前后对比接 `slope`                     |
| 排名、占比条       | `rank`；实际 vs 目标用 `bullet`                      |
| 单个进度 0–1       | `meter`；想要 100 格用 `waffle`                      |
| 组成部分           | `stack`（不用饼图）                                  |
| 转化流失           | `funnel`；累计增减用 `waterfall`                     |
| 两到四个数字       | `stat`；一个主数字加趋势用 `kpi`；只有趋势用 `spark` |
| 本周并行工作       | `gantt`                                              |
| 目录、组织结构     | `tree`                                               |
| 每日状态           | `uptime`                                             |
| 版本变更           | `changelog`；引用别人的话用 `quote`                  |
| 小网格、两组柱状   | `cells`、`bars`                                      |

## 字段

每种图的完整示例在 `scripts/examples.json`，字段不确定时先读对应条目。常用的：

- `timeline`：`events: [{date, label, state?: "done"|"now"|"next"}]`
- `steps`：`steps: [{title, body?}]`
- `check`：`items: [{label, done?, note?}]`
- `callout`：`type?: "note"|"tip"|"warning"|"danger"`, `body`
- `compare`：`columns: [..]`, `rows: [{label, values: [bool|string]}]`
- `table`：`headers: [..]`, `rows: [[..]]`, `footer?`, `align?: ["left"|"right"]`
- `spec`：`rows: [{label, value}]`
- `diff`：`rows: [{label, value, sign?: "add"|"remove"|"keep"}]`, `footer?`
- `rank`：`items: [{label, value, display?}]`
- `meter`：`value: 0..1`, `caption?`
- `stat`：`items: [{value, label, hint?}]`（value 是字符串）
- `gantt`：`items: [{label, start: 0..1, end: 0..1, complete?}]`, `ticks?`, `progress?`
- `tree`：`nodes: [{label, meta?, children?}]`

## 限制

- `● ○ │ █ ✓ →` 这类宽度不固定的符号按 1 列算，适合全角严格等于 2 个半角、上述符号为半角的等宽字体。
- 没有 flow、plot、heatmap、calendar 这类无法用字符画的图。需要流程图时用文字或 `steps`。
- 源自 mdxcn 的 `registry/default/graph-knap`（MIT，见 `LICENSE-mdxcn`），改动：按显示宽度补齐和截断、中文可逐字换行、甘特刻度按列放置。改代码后跑 `bun scripts/check.mts`（或 `node`）。
