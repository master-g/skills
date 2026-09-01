# show-me-html

把素材做成一个**自包含的静态 HTML 页面** —— 一个文件，无构建、无依赖、离线可开、发给谁都能直接看。

视觉层由自有 `show-me.css` 提供：暖灰纸面、深蓝墨色、钴蓝主强调，标题用 Newsreader，正文用 IBM Plex Sans。20 个配方通过几何和证据载体区分，不靠换色。每一页固定带：

- **light / dark / system 三态主题切换**，选择记在 localStorage，首屏前生效，不闪。
- **「复制为 Markdown」按钮**，一键把整页变成 GFM，能贴进文档、粘进 IM、喂给别的模型。

## 安装

使用 skills CLI 安装：

```bash
npx skills add master-g/skills --skill show-me-html -g
```

需要 Python 3（合成脚本用标准库，无第三方包）。项目级共享放 `<repo>/.claude/skills/`。

## 用法

**只能手动调用** —— 打 `/show-me-html`，后面跟想看到什么：

```
/show-me-html 把这个分支的改动做成一个评审页
/show-me-html 把这三个缓存方案并排比一下
/show-me-html 给这次故障做一个复盘页
```

产出一个 `.html`，直接双击打开。

`agents/openai.yaml` 把 Codex 调用策略设为 `allow_implicit_invocation: false`，因此 Codex
只在用户明确调用时使用该技能。其他 Agent 是否自动调用取决于对应宿主的技能策略。

## 目录

| 路径                          | 作用                                                  |
| ----------------------------- | ----------------------------------------------------- |
| `SKILL.md`                    | 流水线：意图 → 调度 → 材料 → 合成 → 自检 → 交付       |
| `assets/shell.html`           | 页面骨架（工具条、主题切换、Markdown 导出、行为脚本） |
| `assets/show-me.css`          | 自有 token、主题、组件状态、配方几何和打印样式        |
| `references/visual-system.md` | 视觉所有权、组件状态和配方家族约束                    |
| `references/components.md`    | 稳定组件 markup、设计 token、分类色                   |
| `references/layouts.md`       | 20 条版式配方及五项视觉契约                           |
| `references/interactions.md`  | 拖拽、键盘翻页、旋钮联动等交互代码                    |
| `scripts/build.py`            | 内联资产 + 自检                                       |
| `tests/`                      | 构建契约、组件状态和 20 配方 fixture                  |
| `assets/vendor/`              | basecoat 行为 JS、lucide sprite                       |

## 视觉系统

所有页面使用同一视觉层，不再提供 `--style` 风格包。要调整方向，修改 `assets/show-me.css`，并同步 `references/visual-system.md` 与视觉 fixture；不要在单页叠一套主题。旧命令会明确报错并给出迁移提示。

## 与 effective-html 的关系

两者都输出单文件 HTML，但视觉系统和交互契约独立：effective-html 面向通用可视化交付；本 skill 的页面固定带三态主题切换和 Markdown 导出，并用 20 个任务配方服务团队内转发。

两者都装时的分工：effective-html 自动触发，是默认；要主题切换或 Markdown 导出就打 `/show-me-html` 点名。

## 第三方组件

| 组件                                                   | 版本   | 许可                      | 位置                                |
| ------------------------------------------------------ | ------ | ------------------------- | ----------------------------------- |
| [basecoat](https://basecoatui.com)（只保留 JS 行为层） | 1.0.2  | MIT © Ronan Berder        | `assets/vendor/LICENSE-basecoat.md` |
| [lucide](https://lucide.dev) 图标                      | 1.31.0 | ISC © Lucide Contributors | `assets/vendor/LICENSE-lucide.txt`  |

两者的代码都以内联形式进入产出的 HTML，转发页面即在转发这些代码，许可条款随之适用。
