# diagrams.md — SVG 图规则

页面里的每一张 SVG 图（流程图、架构图、时序图、示意图）都按这份文件画。
它只管图本身；图外的 figure 外壳（编号 + 标题 + 操作提示 + 图注）见 `interactions.md`。

规则来源：cathrynlavery/diagram-design 的连线规则与预算体系，颜色与字体已换成本 skill 的 token。

## 什么时候画图

- **表格能讲清的不画。** 一张三列的表能装下的关系，用表。
- **超过预算就拆。** 一张图装不下时拆成「概览 + 细节」两张，不缩字号、不挤间距。
- 两个类型都像能用时，选承载主要关系的那一个，不混用两套布局语法。

动手前在布局说明（SKILL.md 第 4 步那 2–3 句）里点名：选了哪个类型、预算会迫使砍掉什么。

## 类型路由

| 要展示什么               | 类型             | 布局约定                                               |
| ------------------------ | ---------------- | ------------------------------------------------------ |
| 系统的组件与连接         | 架构图           | 按层或信任边界分组；主流向只有一个方向（左→右或上→下） |
| 决策逻辑、分支           | 流程图           | 菱形判断；每个分支标注条件；主线保持一条               |
| 角色之间按时间排序的消息 | 时序图           | 生命线 ≤5 条；消息水平、按序编号                       |
| 状态与迁移               | 状态机           | 迁移线上标触发条件；终态收口                           |
| 事件在时间上的位置       | 时间线           | 一根轴；事件上下交替，不并排堆叠                       |
| 跨角色的流程交接         | 泳道             | 一条道一个责任方；流向跨道，不在道内打转               |
| 两维定位、优先级         | 象限             | 两根轴各有名字和方向；项 ≤12                           |
| 分层结构                 | 层叠             | ≤6 层；调用方向全图一致                                |
| 层级归属                 | 树 / 组织图      | 深度 ≤4；同层等高对齐                                  |
| 自我强化的循环           | 循环 / 飞轮      | 3–6 个节点围成环；箭头沿切线，看得出方向               |
| 多来源汇入一点、瓶颈     | 数据流（汇入型） | 左入右出；瓶颈节点用焦点处理                           |

没有现成类型对得上时，取结构上最近的一种，在图注里说明。

## 连线六条硬规则

这六条不可商量。`build.py` 会拦第 1 条（斜线 `<line>` 报 ERROR），其余五条靠眼睛关。

**1. 不共轴的节点之间必须走圆角直角肘形线。** 斜线 `<line>` 与斜向直 path 一律判失败。
两端共 x 或共 y 时才允许用直线 `<line>`。肘形 path 公式（两段弯，r=8；拥挤处最小 r=6）：

```svg
<!-- 从 (x1,y1) 向右再向下到 (x2,y2)，mid = (x1+x2)/2 -->
<path d="M x1,y1 H mid-8 Q mid,y1 mid,y1+8 V y2-8 Q mid,y2 mid+8,y2 H x2"
      fill="none" stroke="var(--color-muted-foreground)" stroke-width="1.2"
      marker-end="url(#arrow-muted)"/>
```

向上走就把两个竖直段的符号反过来。端口选择：目的节点明显在上方或下方时，
从顶边 / 底边进出，用单弯 L 形 path；左右侧边只留给主要水平走向的连接。

**2. 标签与连线之间永远留 6–10px 可见间隙。** 标签不压线。标签下面垫一块不透明遮罩 rect
（`fill: var(--color-background)`，比文字四周各大 3–5px），遮罩底缘与描边之间至少 6px。
遮罩可以盖住线防止字糊，但遮罩与线之间的可见间隙保证读者追得到走向。间隙不够就把标签推到 8–10px。

**3. 连线互不重叠。** 两条线不得共用一段路径、不得平行贴合、不得有任何一段相压。
必须交叉时，在**较不重要**的那条上加桥（次要的、虚线的、回写的那条；永不两条都架桥）：

```svg
<!-- 水平线在 x=cx 处跨过一根竖线 -->
<path d="M x1,y H cx-8 a 8,8 0 0,1 16,0 H x2" fill="none" stroke="…" marker-end="url(#arrow)"/>
```

竖线跨水平线用 `a 8,8 0 0,0 0,16`。

**4. 不共享附着点。** 两条线不进同一个点的同一个边。错开端口，或错开进出边。

**5. 连线不穿过非端点节点的背后。** 绕行；节点不是桥洞。

**6. 标签遮罩不压在后绘制的节点上。** SVG 的绘制顺序就是层叠顺序，
统一按 **背景 → 分区框 → 连线与标签 → 节点** 的顺序写。遮罩完全落在节点内部时算徽章，合法。

虚线（可选 / 异步 / 回写）用 `stroke-dasharray="4,3"` + `stroke-width="1"`，
路由规则与实线完全相同 —— 虚线只表达语义权重，不换一套走线语法。

## 箭头 marker

每张图定义三个 marker，线与箭头同色：

```svg
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M 0,1 L 9,5 L 0,9 z" style="fill: var(--color-foreground)"/>
  </marker>
  <marker id="arrow-muted" …同上… style="fill: var(--color-muted-foreground)"/>
  <marker id="arrow-accent" …同上… style="fill: var(--chart-1)"/>
</defs>
```

`arrow-accent` 只给主干流向，一张图至多一处。marker 的 `id` 要带图自己的前缀（见「无障碍契约」），
同一页多张图时写成 `#flow-arrow` / `#seq-arrow`，避免撞 id。

## 节点语义 → 处理

每个节点的外观由它的语义决定。所有颜色写 `style="…"` 里用 token，两种主题都跟着变。

| 节点语义            | 填充                                                          | 描边                                                                  |
| ------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------- |
| 焦点（全图 1–2 个） | `color-mix(in srgb, var(--chart-1) 10%, transparent)`         | `var(--chart-1)`，1.6px                                               |
| 步骤 / 组件         | `var(--color-card)`                                           | `var(--color-border)`，1.2px                                          |
| 存储 / 状态         | `var(--color-muted)`                                          | `var(--color-border)`，1.2px                                          |
| 外部 / 第三方       | 无                                                            | `var(--color-muted-foreground)`，1px                                  |
| 可选 / 异步         | 无                                                            | `var(--color-muted-foreground)`，1px，`stroke-dasharray="4,3"`        |
| 信任边界 / 分区框   | `color-mix(in srgb, var(--color-foreground) 3%, transparent)` | `color-mix(in srgb, var(--color-foreground) 15%, transparent)`，0.8px |

文字：节点名继承正文字体（不写 `font-family`），11–12px，`fill: var(--color-foreground)`；
端口、命令、URL 这类技术标识符用 `var(--font-mono)`，10–11px；
次级说明 9–10px，`fill: var(--color-muted-foreground)`。任何文字不小于 9px。
圆角 6–10px，不超过 10px。

## 分区框

同层或同边界的 2 个以上节点用分区框归组，分区框画在箭头和节点**之前**：

```svg
<rect x="…" y="…" width="…" height="…" rx="8"
      style="fill: color-mix(in srgb, var(--color-foreground) 3%, transparent);
             stroke: color-mix(in srgb, var(--color-foreground) 12%, transparent)"
      stroke-width="0.8"/>
```

框标签（小号大写字距的 eyebrow 样式）垫 `var(--color-background)` 遮罩放在框顶边线上，
标签与框内第一个节点之间留 ≥16px。分区框最多 3 个，再多就是泳道，换类型。

## 复杂度预算

| 限制         | 数值 |
| ------------ | ---- |
| 节点         | ≤9   |
| 连线         | ≤12  |
| 焦点节点     | ≤2   |
| 分区框       | ≤3   |
| 时序图生命线 | ≤5   |
| 泳道         | ≤5   |
| 树深度       | ≤4   |
| 层叠层数     | ≤6   |
| 象限项       | ≤12  |
| 循环节点     | 3–6  |

超预算的处理只有一种：拆成概览图 + 细节图。不缩字号、不减间距、不并排行。

## 无障碍 SVG 契约

每张有语义的图：

```svg
<svg role="img" aria-labelledby="flow-title flow-desc" viewBox="…">
  <title id="flow-title">一句话说清这张图展示什么</title>
  <desc id="flow-desc">图中节点与流向的文字版</desc>
  <defs>…</defs>
  …
</svg>
```

- `<title>` 必须是 `<svg>` 的第一个子元素，在 `<defs>` 之前。
- `aria-labelledby` 同时指向 title 和 desc 的 id。
- id 带这张图自己的前缀（`flow-` / `seq-`），同一页多张图不许撞 id。
- 纯装饰的 SVG 写 `aria-hidden="true"`（lucide 图标由 `build.py` 自动带上，不用管）。

`build.py` 对缺 `role="img"` / `aria-labelledby` / `<title>` / `<desc>` 的图报 WARN。

## 反模式

| 反模式                   | 后果                                      |
| ------------------------ | ----------------------------------------- |
| 斜线直连                 | 自动判失败（规则 1，`build.py` 报 ERROR） |
| 标签压线、没有遮罩       | 字糊在线上，读不了                        |
| 遮罩贴住描边             | 连线看起来断了                            |
| 所有节点同一形状同一色   | 层级被抹掉                                |
| 焦点色超过 2 个节点      | 焦点不再是信号                            |
| 阴影、发光、渐变填充     | 与全页设计语言冲突                        |
| 竖排文字（writing-mode） | 读不了                                    |
| 图例浮在绘图区里         | 撞节点；图例固定在图下方横排              |
| 照抄 Mermaid 的自动布局  | 那是排版输出，不是设计                    |
| 圆角 >10px               | 廉价感                                    |

## 画完之后的自检

机械关（`build.py` 自动跑）：斜线 `<line>`、无障碍契约、写死颜色。
眼睛关（浏览器里两种主题各看一遍）：

- 每条连线追得动：没有重叠、没有穿节点背后、交叉处有桥。
- 每个标签：遮罩垫了、与线有可见间隙、没被后画的节点吃掉。
- 焦点色 ≤2 处；分区框 ≤3 个；节点 ≤9。
- 图注是一句独立成立的结论；交互图有句操作提示。
