# show-me-html

把素材做成一个**自包含的静态 HTML 页面** —— 一个文件，无构建、无依赖、离线可开、发给谁都能直接看。

组件语言是 shadcn/ui，配色是 Anthropic 的调色板（ink `#141413` 配 canvas `#faf9f5`，主色 clay `#d97757`，
外加 8 个分类色）。每一页固定带：

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

| 路径 | 作用 |
|---|---|
| `SKILL.md` | 流水线：意图 → 调度 → 材料 → 合成 → 自检 → 交付 |
| `assets/shell.html` | 页面骨架（Anthropic 调色板、工具条、主题切换、Markdown 导出、排版 CSS） |
| `references/components.md` | basecoat 组件词表、设计 token、分类色 |
| `references/layouts.md` | 20 条版式配方 |
| `references/interactions.md` | 拖拽、键盘翻页、旋钮联动等交互代码 |
| `scripts/build.py` | 内联资产 + 自检 |
| `assets/vendor/` | basecoat CSS / JS、lucide sprite |

## 换视觉风格

basecoat 的 8 套风格包都已内置，markup 完全一致，只换圆角与组件细节：

```bash
python3 scripts/build.py page.html --style sera   # sera 是零圆角的直角风格
```

可选：`vega`（默认）、`nova`、`maia`、`lyra`、`mira`、`luma`、`sera`、`rhea`。

配色不随风格包变 —— 调色板写在 `assets/shell.html` 的 `<style data-show-me="palette">` 里，
优先级高于风格包。要换配色就改这一块，8 套风格包共用它。

## 与 effective-html 的关系

同一条流水线，同一套 Anthropic 配色，分工在交付形态：
effective-html 出的是单一主题的页面；本 skill 的页面自带三态主题切换和 Markdown 导出，
组件来自 basecoat，为团队内转发而做。

两者都装时的分工：effective-html 自动触发，是默认；要主题切换或 Markdown 导出就打 `/show-me-html` 点名。

## 第三方组件

| 组件 | 版本 | 许可 | 位置 |
|---|---|---|---|
| [basecoat](https://basecoatui.com)（shadcn/ui 的框架无关实现） | 1.0.2 | MIT © Ronan Berder | `assets/vendor/LICENSE-basecoat.md` |
| [lucide](https://lucide.dev) 图标 | 1.31.0 | ISC © Lucide Contributors | `assets/vendor/LICENSE-lucide.txt` |

两者的代码都以内联形式进入产出的 HTML，转发页面即在转发这些代码，许可条款随之适用。
