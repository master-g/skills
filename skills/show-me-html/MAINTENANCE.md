# MAINTENANCE — show-me-html 维护规则

本文件面向**修改这个 skill 的人**（包括维护它的 agent），不进页面生成路径。
方法出处：Vercel《How our agents build on-brand pages with design.md》(2026-08-31) 的评测环方法。

## 纠正路由

评审或眼检发现一个失败时，把它落进**能稳定执行的最窄处**，一次只落一个主落点：

| 失败类型                     | 落点                                      | 例子                       |
| ---------------------------- | ----------------------------------------- | -------------------------- |
| 判断类（怎么写更好）         | `references/*.md` 散文                    | 「先写模型函数再写图」     |
| 可复用视觉（每个页面都该有） | `assets/show-me.css`                      | 滑块轨道、焦点、间距节奏   |
| 可复用行为                   | `assets/shell.js` 骨架脚本                | 主题、TOC、Markdown 导出   |
| 可机械核对                   | `scripts/build.py` 检查（ERROR/WARN）     | 配方名、写死颜色、横向溢出 |
| harness 自身的问题           | harness（build.py / 骨架的 TOC 与导出器） | TOC 吞掉卡片内标题         |
| 只有一个模型 / 只出现一次    | 观察名单（本文末尾），复现后再编码        | —                          |

**禁止调用方补丁**：失败出在骨架或导出器时，只在当页改标记绕过（加 skip、换标签），
同一失败会在下一页复发。页面层的绕过是止血，必须同时在名册登记并按上表安排根治。

## 毕业规则

眼检发现**同一失败第二次**出现 → 必须毕业为 `build.py` 检查（ERROR 或 WARN），
并把 `references/anti-patterns.md` 里对应条目的状态推进为 `已检查`。
命名过的失败倾向于不再出现——前提是它进了检查，而不是只留在记忆里。

## 联动规则

改 `assets/show-me.css`、`assets/shell.html`、`assets/shell.js`、`assets/reply.js` 或 `scripts/build.py` 后，先运行 `python3 -m unittest skills.show-me-html.tests.test_build`，再按 `scenarios/README.md` 的轮次流程跑五个冻结场景：`status-report`、`approach-compare`、`code-review`、`concept-explainer`、`triage-board`。检查 light / dark / system、390 / 500 / 1280px 几何、真实键盘、reduced motion、打印和 Markdown，由 `node scripts/probe_round.mjs <本轮> <上一轮>` 一次跑完，截图仍要人眼看。轮次产出存 `scenarios/rounds/<日期>-<git短sha>/`，不进 git。

改 `assets/charts.js`、`assets/gallery/*.html` 或 `show-me.css` 的图表段后，跑 `python3 scripts/gallery.py --shots`：它把四个 gallery 页拼成 `all-charts.html` 构建一遍（只该有两条 WARN：「超过 400 KB」，以及「500px 下数据图字号渲染后低于 8px」——后者列的是没画窄版的通栏图，图库只给宽版参考实现），再给每张图截 light/dark 两张 PNG，`index.md` 开头列出空图、控制台报错和低于下限的字号。逐张看改到的图，人也可以直接打开 `all-charts.html`，`#fig-编号` 直达、`?only=编号` 单看。`tests/test_build.py` 里的 gallery 测试只保证能构建、脚本能解析，外加 `setInterval` 都登记进了 `keep`。

回复能力（`components.md`「决定块」）分在四处，改一处要对照其余几处：

- 节的定义：`reply.js` 的评论入口、`shell.js` 的目录与 Markdown 导出共用一张组件容器排除表（`.card, .fig-box, …`），改一处三处一起改。
- 回复格式：`components.md`「回复」是契约，`reply.js` 的 `showMeReply` 实现它，`tests/test_build.py` 里 `reply_md` 系列用例逐字断言；SKILL.md「收到页面回复怎么处理」按它的开头和分节识别回复。改格式四处同步。
- 选项名：`reply.js`（回复、状态）、`shell.js` 的导出器和 `build.py` 的选项重名检查各取一次，规则都是 label 里去掉 `<input>`、`<small>` 和「建议」徽章后的文字。状态按选项名和节标题存（同名的节从第二个起带「（2）」序号，回复里写的也是它），改了取名规则，读者已存的作答和页面带的初始状态都会对不上。
- 标记契约：`build.py` 的 `check_decisions` 与 `components.md`「决定块」的 ERROR 清单一一对应。运行时的系统脚本标记 `data-show-me="reply"` 登记在 `SYSTEM_SCRIPT_RE`，开关只认 `<body>` 开标签上的 `data-reply`。

改这几处后跑 `python3 -m unittest skills.show-me-html.tests.test_build -k reply -k decision`，再用一个开启回复能力的页面跑 `--snap` 读 `reply.md`、`export.md` 与切片，`probe_page.mjs` 点一遍控件，并按 `interactions.md`「页面回复」在浏览器里核对存储、清空、键盘和打印。

图片内联（`components.md`「图片」）分在三处，契约是成品里的 `<img data-img-name="文件名" src="data:…">`：

- `build.py` 合成阶段把 `<img src>` 的本地文件内联，并检查格式与文件头、5 MB 上限、密钥目录、SVG 里的令牌、缺 `alt`，以及其他写法的本地资源引用（`srcset`、`<source>`、`<video>` / `<audio>`、SVG `<image>`、样式 `url()`）。整页检查前先把 `data:` 地址的数据换成短占位，图片数据不进任何检查正则。这些 ERROR 与 `components.md`「图片」的规则一一对应。
- `shell.js` 的 Markdown 导出读 `data-img-name` 写 `![alt](文件名)`，导出里不出现 `data:`。
- `show-me.css` 的 `img` 规则把图片压到容器宽、打印时不跨页。

改这几处后跑 `python3 -m unittest skills.show-me-html.tests.test_build -k image -k img`，再用一页带宽截图、长截图和行内小图的页面跑 `--snap`（看 390 / 1280 两种主题与 `export.md`）和 `--pdf`（看图和图注是否同页、长图是否缩进一页）。

改 `reveal` 的生命周期时另测常驻开销：用 `scripts/gallery.py` 拼好的 `all-charts.html`（59 图、约 20000px），无头 Chrome 滚到底，等入场动画沉降后静置 8s 取 `Performance.getMetrics` 的 `TaskDuration` 增量 —— 循环全停时应当接近 0；出现百分之几十说明有循环没被停掉。图滚出视口后开销不降反升，别拿视口外当安全区。

旧页面重新跑一遍 `build.py` 会拿到当前的 CSS 与骨架脚本（`shell.js`，旧页面里复制的骨架块按段首注释认出并替换）；
`shell.html` 的 HTML 结构（工具条、目录容器、`<head>` 里的防闪烁主题脚本）仍是生成时的副本，改它只影响今后合成的页面。历史页面默认不动。
旧页面的回归用 `--check-only` 验证新检查不误报即可。

## 版本规则

- `/Users/mg/github/skills` 是**唯一 source of truth**。改动先落在仓库并提交，再同步安装副本。
- 禁止只改 `~/.agents/skills/show-me-html`（安装副本）——2026-08 曾因此漂移 7 个文件，
  仓库丢掉 diagrams.md 与 46rem 规则近一周，无法做任何改动前后的对比。
- 同步命令（仓库 → 安装副本）：

  ```sh
  rsync -a --delete --exclude .git --exclude agents --exclude /README.md \
    --exclude scenarios/rounds --exclude .pytest_cache --exclude __pycache__ \
    /Users/mg/github/skills/skills/show-me-html/ ~/.agents/skills/show-me-html/
  ```

  （不用 `npx skills add . -g`：实测报「PromptScript does not support global skill installation」，
  文件虽复制但注册环节失败，不作为验证过的通道。）

  同步后用 `diff -rq skills/show-me-html ~/.agents/skills/show-me-html` 验证一致
  （`.git`、`agents/`、`README.md` 属仓库侧文件；`scenarios/rounds/` 是不进 git 的本地轮次产出，
  `.pytest_cache`、`__pycache__` 是测试缓存，都不进安装副本，差异属预期）。

## Vendor 升级

- Temml：`npm pack temml@<版本>`，取 `dist/temml.cjs` 与 `dist/Temml-Local.css` 覆盖 `assets/vendor/temml/`，更新 `README.md` 第三方表的版本。`math.mjs` 在运行时剥掉 CSS 里的 `@font-face`（外链 woff2）和 `math {}` 字体栈，升级后确认这两个正则仍能命中。
- pele（Mermaid 图编译）：用上游 npm 包 `pele` 的 `dist/pele.js` 覆盖 `assets/vendor/pele/pele.mjs`，更新 `README.md` 第三方表的版本；tufte-reader 技能 vendor 了同一个文件，两处一起升。升级后跑单元测试（`-k mermaid`），再构建 `tests/fixtures/mermaid-flow.html` 的副本加 `--snap`，两种主题、390 与 1280 各看一遍：布局参数（`scripts/mermaid.mjs` 的 `LAYOUT`）和 `show-me.css` 里按 pele 的 class 写的规则都依赖上游的输出结构。
- 图型目录与 lieflat-charts 的对应关系写在 `references/charts.md` 顶部；上游更新时按数据形状对比目录，不整页照搬（上游模板依赖 ECharts/Chart.js 与联网字体，本 skill 全部用 SVG 重做）。
- 改视觉方向只动 `show-me.css` 原语层（`--ink` / `--paper` / `--hero` / `--tone-*`）；派生层不写字面色。`tests/test_build.py` 有一条测试盯着这个数。

## 观察名单（复现后编码）

单一模型或单次出现的失败先记在这里，复现第二次再按纠正路由落点：

| 日期 | 失败描述 | 出现次数 |
| ---- | -------- | -------- |
| —    | —        | —        |
