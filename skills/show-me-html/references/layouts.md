# 版式配方

每条配方给的是**章节顺序 + 用哪些组件 + 读者能操作什么**。骨架和组件已经定死，配方只管结构。
按 SKILL.md 的调度表选中一条，照着搭；材料不够的章节直接删，不要留空壳。

所有配方共用的页面骨架（`assets/shell.html`）已含：顶部工具条（与版心对齐）、主题三态切换、复制为 Markdown（单图标按钮）、右侧目录（自动生成）、`<main id="doc">`。
配方描述的是 `<main>` 里的内容。

## 全局版式约定

- 每个大节一个 `<section id="...">`，配 `<h2>`。`id` 供 TOC 锚点用。
- 页宽默认 `--page: 60rem`。读多写少的长文（讲解、复盘、方案）改成 `46rem`。
- 卡片网格：`display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(min(100%,18rem),1fr))`。
  `minmax` 里的 `min(100%, …)` 不能省，否则窄屏溢出。
- 首屏必须有一个「结论/摘要」块 —— 读者滚动前就该知道这页要他做什么判断。

### 间距节奏（骨架已实现，四级）

| 间距 | 用在哪 |
|---|---|
| 56px | 大节之间（`section` → `section`） |
| 40px | 新小节开始（任意块 → `h3`） |
| 20px | 不同类型的块之间（段落 → 表格 / 代码 / 卡片网格），以及 `h2` 到内容 |
| 12px | 同一组内（连续段落、`h3` 到它的第一块内容） |

层级靠这四级读出来，不靠分隔线，也不靠字号 —— `h3` 与正文同为 16px，
它之所以能被认出是小节标题，全靠前面那 40px。**长页面里这是唯一的分组信号。**

**自定义类里不要写 `margin: 0`。** 骨架的间距规则是 `main > section > * + *`（优先级 0,0,3），
一个类选择器（0,1,0）就能整条压掉，元素会紧贴上文。要清 `figure`、`blockquote`
这类元素的浏览器默认边距时，只清用得着的方向：

```css
figure.quote { margin-inline: 0; margin-block-end: 0; }  /* 不碰 margin-top */
```

同理，组件内部的间距要比外部紧。basecoat 有些组件（`.alert > section`）内部的 `p`
自带边距，与容器的 `gap` 叠加后会比正文段落还松 —— 骨架已针对 `.alert` 修掉，
自己搭的容器要自己检查一遍。

---

## 一、抉择类

### `approach-compare` · 在多个实现方案里选一个

摘要（一句话推荐 + 一句话理由）→ 判据表（每个方案一列，判据一行）→ 每方案一张卡（代码片段 + 优点 + 代价）→ 推荐与前提。

- 方案卡用 `.card`；推荐项的卡加 `style="border-color: var(--color-primary)"`，**只加一个**。
- 判据表用 `.table-container > .table`，✓/✗ 用 `.badge`。
- 代码用 `<pre><code class="language-ts">`。方案超过 3 个改用 `tabs`。

### `visual-directions` · 在几个视觉方向里选一个

摘要 → 方向卡片网格（每张卡内嵌真实渲染的样例，不是描述）→ 对比维度表 → 建议。

- 样例必须是**真的能看的 HTML**，不是文字描述 —— 这是这类页面存在的唯一理由。
- 主题切换按钮天然就是这类页的评估工具，提醒读者两种主题都看一遍。

---

## 二、代码类

### 结构视图（共用块）

读者要看的是**形状**而不是逐行内容时，用 `<pre>` 画结构，不要用散文描述，也不要贴整块代码。
四种载体，按问题选：

| 读者的问题 | 载体 |
|---|---|
| 这段逻辑怎么判断 | 伪代码 |
| 运行时谁调用谁 | 调用树 |
| 界面由哪些组件构成、状态在哪 | 组件树 |
| 哪个目录负责什么 | 浅文件树（只到承担职责的那一层） |

```html
<pre><code class="language-text">submitForm
  createSession
    persistPrompt
    launchAgent
  navigateToSession</code></pre>
```

组件树标出真实路径与状态钩子，文件树每行给一句职责说明：

```text
<SessionPage> (apps/example/src/routes/session.tsx)
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton> (packages/ui)

src/
├── commands/       # 解析用户动作
├── sessions/       # 持有会话状态
└── transport/      # 发 API 请求
```

**结构 diff** —— 形状已经存在、要说的是它怎么变时，在同一载体上加 `+` / `-`，
`<code>` 改成 `class="language-diff"`（「复制为 Markdown」会导出成 ```diff 围栏）：

```html
<pre><code class="language-diff"> src/
 ├── commands/
<span class="d-add">+│   └── show-me.ts       # 展开 slash command</span>
 ├── sessions/
<span class="d-del">-└── transport.ts</span>
<span class="d-add">+└── transport/</span></code></pre>
```

diff 行着色写进页面 CSS，四条代码类配方共用（负外边距是为了让底色铺满 `pre` 的 1rem 内边距）：

```css
.d-add, .d-del { display: block; margin-inline: -1rem; padding-inline: 1rem; }
.d-add { background: color-mix(in oklab, var(--color-primary) 12%, transparent); }
.d-del { background: color-mix(in oklab, var(--color-destructive) 12%, transparent); }
```

**不要用结构视图的情况**：形状大部分是新的、省略的上下文会让归属或顺序看不出来、
读者需要一份可复制的目标代码 —— 这三种情况贴整块代码。

`code-review`、`pr-writeup`、`code-understanding`、`implementation-plan` 都可以引用本块。

### `code-review` · 评审者视角看一次改动

改动摘要（文件数/增删行/风险等级）→ 关注点清单 → 按文件的 diff → 待确认问题。

- 摘要用一排统计块：`.card[data-size=sm]`，大号数字 + `.badge` 说明。
- 每个文件一个 `<details>`（`.accordion` 内），`summary` 放文件名 + 增删数。
- diff 行着色用「结构视图」里的 `.d-add` / `.d-del`，不要另写一套。
- 改动跨文件移动、改目录结构或改调用顺序时，在按文件的 diff 之前先放一个结构 diff。
- 待确认问题用带 checkbox 的 `.field`，读者能勾。

### `pr-writeup` · 作者视角讲一次改动

为什么做 → 做了什么（按主题分组，不按文件）→ 怎么验证 → 影响面与回滚。

与 `code-review` 的区别：叙事驱动，不是文件驱动。文件清单降级到末尾的一个 `.item-group`。

### `code-understanding` · 讲清这个仓库里某条流程

入口 → 时序图（内联 SVG 或编号步骤）→ 每步一节（真实代码 + 解释）→ 边界与坑。

- 代码片段必须来自真实文件，`<pre>` 上方标注 `path/to/file.ts:42-58`。
- 步骤编号用 `.item-group`，`figure` 里放数字而非图标。

### `design-system-ref` · 设计系统 / 风格指南

Token 表 → 每类组件一节（真实组件 + 用法说明 + markup 代码块）→ 使用禁忌。

- 组件区和代码块并排：左侧渲染真件，右侧 `<pre>`。窄屏堆叠。

### `component-variants` · 带旋钮对比组件变体

控制面板（`.field` 组）→ 实时预览区 → 生成的 markup（随旋钮更新）→ 变体矩阵表。

- 旋钮 → 预览的连线代码见 `interactions.md` 的「实时预览」。

---

## 三、原型类

### `animation-proto` · 试一段动效

预览舞台 → 参数旋钮（时长 / 缓动 / 位移）→ 触发按钮 → 缓动曲线并排对比。

- 尊重 `prefers-reduced-motion`：自动播放的动效必须在该媒体查询下停掉。

### `interaction-proto` · 试一个交互机制

场景说明 → 可操作区 → 状态回显（当前状态用 `.badge` 显示）→ 边界情况清单。

- 拖拽、键盘操作的现成代码见 `interactions.md`。
- **每个控件都要真的能用**；做不了的控件必须显式标注「本原型不含」。

---

## 四、沟通类

### `status-report` · 项目/团队状态速览

一行结论 → 指标块一排 → 分组进展（每组一个 `.item-group`）→ 风险 → 下一步。

- 指标块：`.card[data-size=sm]`，大数字 + 变化量（涨跌用 `.badge[data-variant]`）。
- 全页只读，不要放假按钮。

### `incident-report` · 复盘一次故障

影响面摘要 → 时间线 → 根因 → 为什么没早发现 → 改进项（带勾选框）→ 附录证据。

- 时间线用 `.item-group`，`figure` 放时刻，`section` 放事件。
- 根因写「原因未查明」比编一个解释好。
- 改进项每条给责任方与时限，缺就标 `[DATA NEEDED: 责任方]`。

### `implementation-plan` · 评估一份实施计划

目标与非目标 → 阶段卡（每阶段：产出 / 依赖 / 风险）→ 里程碑表 → 未决问题。

- 「非目标」这一节不要省，它是这类页面最有价值的部分。
- 阶段之间的依赖用内联 SVG 画，别用文字描述。
- 计划会改动目录结构或调用链时，用「结构视图」里的结构 diff 给出目标形状。

### `slide-deck` · 现场讲一遍

封面 → 每屏一个论点 → 结论。键盘左右翻页，右下角页码。

- 每屏一个 `<section class="slide">`，`height:100vh; display:grid; place-content:center`。
- 翻页代码见 `interactions.md`。
- **判断一次**：读者会自己慢慢看吗？会的话改用 `status-report` 或 `implementation-plan` —— 幻灯片对细读的人是折磨。

---

## 五、图解类

### `flowchart` · 逐节点追一条流程

流程总览 SVG（节点可点）→ 详情面板（点节点切换）→ 节点清单表。

- SVG 节点：圆角矩形 + `stroke: var(--color-border)` + `fill: var(--color-card)`，标签 `--font-mono` 10–11px。
- 点击换详情的代码见 `interactions.md`。

### `svg-illustrations` · 拿走一组示意图

每图一张卡：标题 → 渲染的 SVG → 用途说明 → 复制 SVG 源码按钮。

- 图形只用 token 颜色，这样两种主题下都成立。

### `feature-explainer` · 讲清一个功能 / API

它解决什么 → 最小可用例 → 参数表 → 常见用法（tabs 分场景）→ 陷阱。

### `concept-explainer` · 讲清一个概念（交互式教学）

直觉 → **可拖动的模型**（滑块驱动实时结果）→ 形式化定义 → 边界情形。

- 交互模型是这类页的核心，不是装饰。没有能做成交互的东西时，改用 `feature-explainer`。

---

## 六、编辑器类

### `triage-board` · 分拣 / 排优先级

筛选条 → 看板列（可拖卡片）→ 计数回显 → 导出 Markdown。

- 拖拽代码见 `interactions.md`。顶部工具条自带的「复制为 Markdown」已覆盖导出需求，不要再造一个。

### `config-editor` · 带约束地改配置

分组开关（`.fieldset` + switch）→ 依赖冲突提示（`.alert[data-variant=destructive]`）→ 变更预览（diff 形式）。

- 开关之间的依赖必须真的校验，不能只画一个警告框。

### `text-tuner` · 调文案 / 提示词并实时看结果

可编辑区（`contenteditable`）→ 变量槽高亮 → 实时渲染结果 → 版本对比。
