# 视觉系统

## 方向

`show-me-html` 是一套编辑式工作台，不是营销页。浅色主题是暖灰纸面和深蓝墨色，深色主题是低亮度蓝黑工作区。钴蓝只标主操作、当前状态和关键连线。结构靠版式与留白，不靠把每块内容都装进卡片。

字体分工固定：Newsreader 负责标题，IBM Plex Sans 负责正文和控件，IBM Plex Mono 负责代码、路径、时间和数字。Google Fonts 异步加载，失败时按 `components.md` 的本地栈回退。

## 所有权

- `assets/show-me.css` 持有 token、两套主题、基础排版、组件状态、chrome、配方几何、打印和 reduced motion。
- `assets/shell.html` 只持有文档结构与行为：主题初始化、Markdown 导出、TOC 和滑块同步。
- 页面自己的 `<style>` 只能写材料特有的几何或图形，必须消费语义 token。
- basecoat CSS 已退出；basecoat JS 只在现有 tabs、dropdown 等组件需要时由 `build.py` 条件内联。

## Token

页面使用兼容别名 `--color-*`，不要直接消费原始色值。

| 角色             | Token                                                           |
| ---------------- | --------------------------------------------------------------- |
| 画布与正文       | `--color-background`, `--color-foreground`                      |
| 抬升面           | `--color-card`, `--color-card-foreground`                       |
| 弱化面与次要文字 | `--color-muted`, `--color-muted-foreground`                     |
| 主操作和焦点     | `--color-primary`, `--color-primary-foreground`, `--color-ring` |
| 次要与悬停       | `--color-secondary`, `--color-accent`                           |
| 错误与危险       | `--color-destructive`, `--color-destructive-foreground`         |
| 边界与输入       | `--color-border`, `--color-input`                               |
| 分类、图表、语法 | `--tone-*`, `--chart-*`, `--syn-*`                              |

页面不得用颜色区分配方。关闭颜色后，配方仍应由几何和阅读顺序辨认。

## 组件状态

所有可交互组件至少覆盖适用的 default、hover、focus-visible、active、disabled、invalid、selected/open/checked 和 loading 状态。

- 焦点环立即出现，不参与动画。
- 按钮按下使用 `scale(0.96)`；高频交互不加进场动画。
- 阴影只表达浮层或真正抬升，结构分组用边界和留白。
- 原生 input、button、details、dialog 优先于自造控件。
- hover 不能承载唯一信息。图节点、标签页和重排都必须有键盘路径。

## 动效

普通状态变化使用 `--ease-expo`，只过渡明确属性。`--ease-physical` 只用于拖拽释放等物理反馈。禁止 `transition: all`。

`prefers-reduced-motion: reduce` 下关闭循环、庆祝、平滑滚动和空间位移；静态颜色、边界、文字或图标仍要表达状态。

## 配方契约

每个配方在 `layouts.md` 中写五个字段：首屏、主要证据载体、细节机制、结束动作、窄屏收拢。没有交互或动作时写“无”，不要为凑结构发明按钮。

| 家族       | 共同姿态 | 结构线索                                |
| ---------- | -------- | --------------------------------------- |
| 抉择       | 并排判断 | 比较矩阵、真实样板、明确建议            |
| 代码与参考 | 证据密集 | diff 账本、文件导览、执行脊柱、组件样板 |
| 原型       | 舞台优先 | 控制栏、时间轴、工作台、状态回显        |
| 报告与计划 | 扫读优先 | 指标带、时间线、里程碑、全屏论点        |
| 图解       | 模型优先 | 图面、选中详情、图版、请求路径、实验台  |
| 编辑器     | 直接操作 | 泳道、变更栏、编辑/预览分栏             |

具体选择器和 20 个指纹在 `assets/show-me.css` 的 `Recipe geometry` 段。

## 上游借鉴边界

参考 `anthropics/html-effectiveness` 固定提交 `58c305be97f47b26b678f2c07dec01d4242268ec`。借鉴任务驱动的宏观结构、可见证据、批注和有限交互，不复制其象牙白/陶土色品牌、衬线+大写眉标习惯、逐模板 CSS/JS、`innerHTML` 更新、鼠标专用操作或缺失的主题/打印/reduced-motion 处理。

完整证据见 `docs/research/2026-09-01-html-effectiveness-template-assessment.md`。

## 响应式与打印

- 自动几何检查跑 500px 和 1280px；390px 保留人工门禁。
- sticky rail 在 900px 以下回到普通文流。
- 看板在窄屏改为横向吸附的单泳道视口，不压成不可读小卡。
- slide 使用 `100dvh` 并提供内容溢出回退；手机和打印取消强制全屏。
- 表格、图面和长标识符由局部滚动容器承接，禁止把整页撑宽。
- 打印强制浅纸深字，隐藏 chrome 和 TOC，展开静态阅读顺序。

## 验证

每次改视觉系统都要运行：

```bash
python3 -m unittest skills.show-me-html.tests.test_build
```

然后按 `scenarios/README.md` 跑五个冻结场景，检查 light、dark、system、打印、键盘、Markdown、500/1280 几何和 390px 人工截图。任何未运行的门禁必须写成“未验证”，不能算通过。
