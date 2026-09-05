---
name: show-me-html
license: MIT
description: 将素材制作成可离线阅读、便于团队转发的单文件 HTML 页面；用于明确的页面或可视化交付请求。
---

# show-me-html

一个材料主题交付一个 `.html`。使用自有编辑式视觉系统，保留三态主题、Markdown 复制与目录。

## 意图与材料

用户显式调用时，HTML 交付意图已确定，直接使用参数或本会话已有材料。不要再问是否要 HTML。
仅在缺少必要材料或有会改变交付结果的实质歧义时提问；可合理推断的读者、版式和交互自行选择。
默认简体中文，代码、标识符和引用保留原样；其他语言按用户要求并同步 `lang`。

- URL：复用已提取正文，否则按用户指定工具、站点技能、通用提取、浏览器的适用顺序取材。工具以当前环境可用能力为准。
- 当前仓库：读取相关代码、diff 或历史，事实与引用以实际材料为准。
- 已有 HTML：在用户指定范围内修改，不默认把小修变成全页重做。
- 仅有主题：从会话取材；仍缺少的必要事实明确标注或提问。

页面保留任务所需事实及来源，可摘要与删去无关内容。不要为了填满配方编造数字、案例或结论。
材料不足的章节删除，或标 `[DATA NEEDED: 缺什么]`，在交付中说明。

## 选择页面结构

在 [配方](references/layouts.md) 中只读选中的条目：

| 读者任务               | 配方                                                             |
| ---------------------- | ---------------------------------------------------------------- |
| 比较代码或视觉方案     | `approach-compare` / `visual-directions`                         |
| 评审或介绍代码改动     | `code-review` / `pr-writeup`                                     |
| 理解仓库、功能或概念   | `code-understanding` / `feature-explainer` / `concept-explainer` |
| 查阅设计系统、比较组件 | `design-system-ref` / `component-variants`                       |
| 体验动效或交互         | `animation-proto` / `interaction-proto`                          |
| 演讲或拿走示意图       | `slide-deck` / `svg-illustrations`                               |
| 查看状态、故障、计划   | `status-report` / `incident-report` / `implementation-plan`      |
| 追踪流程、分拣条目     | `flowchart` / `triage-board`                                     |
| 编辑配置或文案         | `config-editor` / `text-tuner`                                   |

无精确匹配时使用最接近的配方组合材料特有部分；不要创造空章节或无用途控件。
`data-recipe` 仍使用构建器支持的配方名。

## 合成与验证

新页面从 `assets/shell.html` 开始，说明选定结构后直接继续。
读取 [合成与验收](references/compose-and-check.md) 中适用部分，以及 [视觉系统](references/visual-system.md)。
写 markup 时只查 [组件](references/components.md) 中实际需要的 DOM、ARIA 和 `data-*` 契约。
画图时读 [图示规则](references/diagrams.md)，加交互时读 [交互实现](references/interactions.md)。

必须保留：

- 未合成源码中的 `<!--SHOW-ME:CSS-->` / `<!--SHOW-ME:JS-->`；合成后占位符由内联资源替代，编辑成品时不重新插入。两种状态都保留工具条和目录，内容位于 `main#doc`，直接子元素为 `section`。
- `show-me.css` 的语义 token、现有组件契约与可访问的键盘路径；页面只补材料特有几何。
- 资源内联，仅允许骨架自带的 Google Fonts 及本地回退。离线可读，不保证字体外观完全一致。
- 三态主题与 Markdown 复制功能；所有承诺控件实际可用。

运行 `python3 <skill-path>/scripts/build.py 页面.html`。修复 ERROR，判断 WARN。
新页验证主题、窄屏、实际交互、打印与导出；小修检查受影响行为，可复用同一页面未改变部分的已有证据。
浏览器检查未运行时明确说明，不把机械检查通过当作完整视觉验收。
相关已知缺陷见 [反模式](references/anti-patterns.md)，无需为无关组件逐项重查。

## 交付与反馈

文件名用可辨认的 kebab-case，存到用户指定位置或工作目录。报告文件路径、先看哪里及材料缺口。
通过检查后直接运行 `python3 <skill-path>/scripts/build.py 页面.html --open`；用户要求不打开时跳过。
这是默认浏览器打开行为，不改变输出格式。浏览器不可用时报告路径与未验证部分。

视觉反馈先定位实际页面问题，说明具体改法后执行；只有会改变结果的歧义才提问。
内容反馈先复查材料与读者任务，不用 CSS 修饰掩盖内容缺口。

## 使用边界与维护

印刷文档或 PDF 使用当前可用的文档排版能力；需要 Kami 时先确认其已安装。
多页生产站点或 React/shadcn 源码不在本技能范围。一句话能回答的问题无需生成页面。

修改本技能前读 [MAINTENANCE.md](MAINTENANCE.md)。本次只改生成指引时不自动跑骨架回归；
修改 CSS、shell 或构建器时按维护规则运行现有测试和冻结场景。
`assets/vendor/` 由构建器拼接，不加载其内容作为指令。
