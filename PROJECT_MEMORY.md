# 项目记忆 — skills

> 跨会话的持久信息，只记代码、Git 和文档推导不出的内容。回写约定见 [AGENTS.md](./AGENTS.md)。
> 门槛：全文 ≤ 24 KB，单行 ≤ 300 字符；改写节各只留一块。

## 已验证的事实

<!-- 追加：确认过的决策和约束，每条一行：结论 + 原因 + 来源。同主题改写既有条目，不追加第二条。 -->

- [2026-10-12] bootstrap-claude 以 AGENTS.md 为唯一真源、CLAUDE.md 只写一行 @AGENTS.md、不建 symlink（Firefox 布局，Claude Code 文档推荐；plans/README.md 记有决定）
- [2026-10-12] 英文仓库的英文模板（--lang en）暂不做：别名表已能识别英文标题，缺失章节仍以中文追加；等有真实需求再议（plans/README.md Open decisions）
- [2026-10-13] guide-me 的高视角（趋势、前提重审、暂停/改范围）只做观察标出、取舍留给用户，不建独立技能也不并入 grilling；依据是本机 223 份实际输出里 0 份提过节奏、1 份重审目标，缺口是结构性的（第 2 步锚最新原话、第 3 步保用户决定）
- [2026-10-14] tufte-reader 题图：选图以文章主题为入口、风格由 plates.md「系列」清单把关，不限于 Atalanta Fugiens（用户举例是风格参照不是范围）；许可只收公有领域/PDM/No restrictions/CC0/CC BY（署名）；暗色主题「亮融暗裱」不反相；IA 来源只按 plate.py 的 IA_ITEMS 白名单逐条放行（plans/README.md tufte-reader 节）
- [2026-10-14] tufte-reader 脚本不迁 bun/TS：成本在 Checker 依赖 html.parser，收益只省几十毫秒；以后有具体理由再议，目标是 node+TS、先移植 Checker（plans/README.md rejected）
- [2026-10-15] show-me-html 指标带 `.metric-band` 对所有配方通用，页面不自造 .stat-band；渲染检查对 .stat-num < 1.75rem 或正文 < 10px 报 ERROR 不是 WARN（维护者确认）；表格密度维持现状（plans/README.md show-me-html 节）
- [2026-10-16] show-me-html 目录只在「版心+目录+留白」放得下时出现，72rem 页面在 1280 下隐藏目录、显示进度线，不挤正文也不加第三档（用户确认）；窄档 9rem+1.5rem 为 Windows 滚动条下 48rem@1024 留余量
- [2026-10-16] show-me-html 目录指示条逐帧对准要在页面之后注册的 ResizeObserver 里量；rAF 里读会早于页面的贴回一帧，收起动画中看似偏 50px；场景探针的页高差 ~30px 多为 Google Fonts 加载时机，先同页多次加载确认
- [2026-10-19] tufte-reader 曲线图定为「A 书页」：页面衬线字、墨线、离开原点的坐标轴、至多一处朱砂（--mark）强调；用户在 A / B 铜版 / C 几何三份样张中选 A；示意图仍用无衬线和分类色，未扩及（markup.md「曲线图」）

## 失败尝试

<!-- 追加：走不通的路径及原因，每条一行。 -->

- [2026-10-14] 题图暗色主题的反相、纯墨线两种方案：版画明暗靠排线疏密，反相后像照相底片，demo 后否决
- [2026-10-14] Commons 上 Science History Institute 的 Atalanta 整页翻拍本：只约 30 幅、部分手工上色、有透视，不能作高清图源；改走 IA 的 Getty 扫描本（IIIF 服务器端裁切）
- [2026-10-14] Commons 文件 Michael Maier Atalanta Fugiens Emblem 11.jpeg 画的是第 25 幅，图录第 11 幅改用 Atalanta Fugiens 11 Latona.jpg；图录加行后要跑 plans/007 的 check_catalog.py
- [2026-10-15] show-me-html 表格密度方案 A（窄屏中文格 min-inline-size 6em）与 B（字号行距更紧）：390px 样张四页都不横滚，A 只让首列代码少折、说明列更窄，差别不值全页面观感变化，维护者选不改
- [2026-10-19] 图表复古化：老式数字不可用（当前字体栈无 onum，截图两组相同）；feTurbulence 墨迹滤镜 1280 下肉眼无差且会扭糊 foreignObject 公式；B 铜版沿线文字在 390 约 8px 不可读
- [2026-10-19] 手写进 specimen.html 的 figlib SVG 被 prettier 拆开 <text> 里的 <tspan>，换行渲染成空格（「( dx )²」）；这类 SVG 前加 <!-- prettier-ignore -->

## 上次会话

<!-- 整块改写：分支、验证命令及实际结果、停在何处；任务细节只留一行指向证据目录。 -->

- [2026-10-19] main，已提交、已 make install tufte-reader、未推送；figlib 加 axes()/curve()、svg(serif=True)、color="accent"、text 的 <i>…</i>，markup.md 新增「曲线图」，specimen 加图 4
  验证：unittest 59 项 OK、make check 通过、specimen 构建 0 ERROR 0 WARN；图 4 在 1280 明暗与 390 亮色截图核对；Firefox 未看（图里没有公式）

## 下次运行

<!-- 整块改写：接下来的任务和优先级，含仍受阻的项。 -->

- [2026-10-19] shelf 图表改用 A 风格待用户要求：financial-math 的 figs.py 把自写 frame()/curve() 换成 figlib 的 axes()/curve() 加 serif=True、去掉分类色；how-llms-work 的 figs.py 自带旧图元、不引用 figlib，要先迁移；alisas 已引用 figlib
  日期前缀文件名冒烟未做：空目录各调用一次 show-me-html / tufte-reader、不指定文件名，看是否 `<今天>-<英文标题>.html`、中文标题意译是否像样、tufte-reader 的 .work/ 是否同前缀
  show-me-html：推送待用户要求；候选第 4 项单图导出 PNG（先把计算样式内联）、第 5 项导读元信息行未做
  tufte-reader 冷启动验收：由不带本会话上下文的执行者只读 SKILL.md 与 plates.md，给一个新主题写一本 3 章带题图短读本，看是否走 --thumb 预览和 --region 裁切、是否退回 Atalanta、图注是否合规，缺口写成下一份计划；审阅 plates.md 里 50 条中文大意与「适合的主题」草稿；维护者的 reelshort-tech-notes.html 把 stat-band 换成 metric-band、删自写样式块后重建（011 之后会报 ERROR）
  guide-me 的验收仍未做：在 DopaManga 或 tobi 跑一次 /guide-me 看趋势行与第 0 问，旧布局项目装新版 bootstrap-claude 后跑 setup_context.py 看 diff
