# show-me-html

把素材做成一个**自包含的静态 HTML 页面** —— 一个文件，无构建、无依赖、离线可开、发给谁都能直接看。

视觉层由自有 `show-me.css` 提供：一墨一纸，所有灰由墨纸两极派生，一个橙色落点；标题用 Newsreader，正文用 IBM Plex Sans。21 个配方通过几何和证据载体区分，不靠换色。公式写 LaTeX，构建时编译成 MathML。每一页固定带：

- **light / dark / system 三态主题切换**，选择记在 localStorage，首屏前生效，不闪。
- **「复制为 Markdown」按钮**，一键把整页变成 GFM，能贴进文档、粘进 IM、喂给别的模型。

## 安装

使用 skills CLI 安装：

```bash
npx skills add master-g/skills --skill show-me-html -g
```

需要 Python 3（合成脚本用标准库，无第三方包）；页面含 LaTeX 公式时还需要 Node.js（Temml 已 vendor，不用 npm install）。项目级共享放 `<repo>/.claude/skills/`。

## 用法

**点名调用** —— 打 `/show-me-html`，后面跟想看到什么（Claude Code 也可能在你明确要一个页面或可视化交付时自动调用）：

```
/show-me-html 把这个分支的改动做成一个评审页
/show-me-html 把这三个缓存方案并排比一下
/show-me-html 给这次故障做一个复盘页
```

产出一个 `.html`，直接双击打开。

`agents/openai.yaml` 把 Codex 调用策略设为 `allow_implicit_invocation: false`，因此 Codex
只在用户明确调用时使用该技能。其他 Agent 是否自动调用取决于对应宿主的技能策略。

## 目录

| 路径                          | 作用                                                                     |
| ----------------------------- | ------------------------------------------------------------------------ |
| `SKILL.md`                    | 流水线：意图 → 调度 → 材料 → 合成 → 自检 → 交付                          |
| `assets/shell.html`           | 页面骨架（工具条、目录容器、防闪烁主题脚本）                             |
| `assets/shell.js`             | 骨架行为脚本（主题切换、目录、Markdown 导出、代码工具条），构建时注入    |
| `assets/show-me.css`          | 自有 token、主题、组件状态、配方几何、打印样式，以及数据图外壳与入场动画 |
| `references/visual-system.md` | 视觉所有权、组件状态和配方家族约束                                       |
| `references/components.md`    | 稳定组件 markup、设计 token、分类色                                      |
| `references/layouts.md`       | 21 条版式配方及五项视觉契约                                              |
| `references/interactions.md`  | 拖拽、键盘翻页、旋钮联动等交互代码                                       |
| `references/charts.md`        | 数据图选型：数据形状决策树、硬规则、图型目录                             |
| `assets/charts.js`            | 数据图运行时（页面有 `data-chart` 时内联）                               |
| `assets/gallery/`             | 59 张图型的参考实现，按家族四个页面                                      |
| `scripts/build.py`            | 内联资产 + 自检                                                          |
| `scripts/gallery.py`          | 59 张图拼成一页总览，`--shots` 逐张截图供评估                            |
| `tests/`                      | 构建契约、组件状态和 21 配方 fixture                                     |
| `scripts/math.mjs`            | LaTeX → MathML 编译（Temml）                                             |
| `scripts/probe_round.mjs`     | 冻结场景轮次探针：主题、动效、三档宽度截图、真实键盘、打印与场景判据     |
| `assets/vendor/`              | basecoat 行为 JS、lucide sprite、speed-highlight、Temml                  |

## 视觉系统

所有页面使用同一视觉层，不再提供 `--style` 风格包。要调整方向，修改 `assets/show-me.css`，并同步 `references/visual-system.md` 与视觉 fixture；不要在单页叠一套主题。旧命令会明确报错并给出迁移提示。

## 与 effective-html 的关系

effective-html 已弃用并由本 skill 取代，历史内容存于仓库的 `skills/deprecated/effective-html/ARCHIVE.md`。

## 第三方组件

| 组件                                                                                                           | 版本    | 许可                                                  | 位置                                       |
| -------------------------------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------- | ------------------------------------------ |
| [basecoat](https://basecoatui.com)（只保留 JS 行为层）                                                         | 1.0.2   | MIT © Ronan Berder                                    | `assets/vendor/LICENSE-basecoat.md`        |
| [lucide](https://lucide.dev) 图标                                                                              | 1.31.0  | ISC © Lucide Contributors                             | `assets/vendor/LICENSE-lucide.txt`         |
| [Temml](https://temml.org) 公式编译                                                                            | 0.13.5  | MIT © Ron Kok                                         | `assets/vendor/LICENSE-temml.txt`          |
| [lieflat-charts](https://github.com/larashero3-dotcom/lieflat-charts) 图型（`assets/gallery/` 中 28 个衍生块） | eace082 | PolyForm Noncommercial 1.0.0 © 躺在废墟里，**非商用** | `assets/gallery/LICENSE-lieflat-charts.md` |

它们的代码都以内联形式进入产出的 HTML，转发页面即在转发这些代码，许可条款随之适用。
