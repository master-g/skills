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
- [2026-10-20] tufte-reader 的 Mermaid 图由 vendor 的 ondine 0.0.1（wevm，Rust→wasm，MIT）编译成 SVG；用户选 vendor 而非按需 npm 安装；源码留在页面里、每次构建重编，悬停出现纯 CSS 的源码开关（Lucide code/workflow 图标，画法同明暗切换按钮，用户看图确认）、打印只出图；只用于结构图，数据图仍走 figlib 曲线图
- [2026-10-20] flopwire（代理间消息与转录检索）不接入 farm：子代理里的 hook 不投递、pi 不在支持列表、herdr pane 已能 agent prompt；借三点写成 plans/015（进程组收尾）、016（转录核对写入与用量，只做 Claude Code 后端）
- [2026-10-20] 用户清空了「下次运行」积压：guide-me 验收、tufte-reader 冷启动验收与 plates.md 审阅、日期前缀文件名冒烟、reelshort 页重建、show-me-html 单图导出 PNG 与导读元信息行、codebase-to-book 改用 ondine、真实 /farm 与 send-to-obsidian X 链接实测，都不再跟进，用户再提才做
- [2026-10-20] tufte-reader 配色定为暖底（亮 #fbf8f1、暗 #1c1b19）加 `--strong` 粗体色（暗色琥珀）：仓库历史里从无这套值，10-19 shelf 五页按安装副本重建，后来安装副本也回到旧值（推测是 install 覆盖，未证实）；用户选移植进仓库，值取自 shelf 已提交成品
- [2026-10-19] shelf 的 financial-math 已改成曲线图风格；how-llms-work 的 figs.py 自带旧图元、不引用 figlib，改风格要先迁移
- [2026-10-21] show-me-html / tufte-reader 语法高亮维持 vendor 的 @speed-highlight/core：两技能页面只见 bash/sql/diff/text 和零星 py/ts/rs/go，无 JSX/TSX；它最快（32 KB 1.5 ms，Kirari 4.0、Prism 2.2）。页面常出现 JSX/TSX 或 C#/Kotlin/Swift/Ruby 时换 Kirari（TSX 分词好、接法相同），先等它稳定（10-18 才发布）；Shiki 要构建期 Node 或每页 72 KB+，排除（用户认同）
- [2026-10-21] bench 的规划以 `.scratch/llm-bench/map.md`（wayfinder 本地跟踪器）为准，决策细节在各票里；用户确认：只用公开 repo、farm 无头红线不约束 bench、研究分支不推送；推进地图的代理不替用户启动选手运行
- [2026-10-20] 写书慢不在构建，也不缺分章派发：tufte-reader 自 64b7cbb（10-10）起就能分章派发，shelf 不用是因为它的 docs/books.md 规定一次写一章、自己写；shelf 四本书重建 0.3–1.0 s，how-llms-work 1014 个公式重编 0.8 s

## 失败尝试

<!-- 追加：走不通的路径及原因，每条一行。 -->

- [2026-10-14] 题图暗色主题的反相、纯墨线两种方案：版画明暗靠排线疏密，反相后像照相底片，demo 后否决
- [2026-10-14] Commons 上 Science History Institute 的 Atalanta 整页翻拍本：只约 30 幅、部分手工上色、有透视，不能作高清图源；改走 IA 的 Getty 扫描本（IIIF 服务器端裁切）
- [2026-10-14] Commons 文件 Michael Maier Atalanta Fugiens Emblem 11.jpeg 画的是第 25 幅，图录第 11 幅改用 Atalanta Fugiens 11 Latona.jpg；图录加行后要跑 plans/007 的 check_catalog.py
- [2026-10-15] show-me-html 表格密度方案 A（窄屏中文格 min-inline-size 6em）与 B（字号行距更紧）：390px 样张四页都不横滚，A 只让首列代码少折、说明列更窄，差别不值全页面观感变化，维护者选不改
- [2026-10-19] 图表复古化：老式数字不可用（当前字体栈无 onum，截图两组相同）；feTurbulence 墨迹滤镜 1280 下肉眼无差且会扭糊 foreignObject 公式；B 铜版沿线文字在 390 约 8px 不可读
- [2026-10-19] 手写进 specimen.html 的 figlib SVG 被 prettier 拆开 <text> 里的 <tspan>，换行渲染成空格（「( dx )²」）；这类 SVG 前加 <!-- prettier-ignore -->
- [2026-10-20] beautiful-mermaid（pretty-mermaid 的底层）不适合读本：SVG 里 @import Google Fonts（外链）、写死 --bg:#FFFFFF 盖住页面变量、图型少；官方 Mermaid 要运行时 JS 或无头浏览器
- [2026-10-20] macOS 上复制出来的 /bin/sleep 一运行就被系统 kill，冒烟测试要找可按路径标记的子进程时改用 `perl -e "sleep 300" <标记路径>`（plans/015 的 smoke.sh）

## 上次会话

<!-- 整块改写：分支、验证命令及实际结果、停在何处；任务细节只留一行指向证据目录。 -->

- [2026-10-21] main：bench 地图（`.scratch/llm-bench/`）已关闭 4 张研究票与「harness 复用现成框架还是自建」「v1 选手名册与预算」「SWE 类评分」「产出物类评分」「标准答案类评分」五张 grilling 票；评委看图方式（GLM-5.3 不能看图、pi 会静默丢图）与审查题的缺陷候选（blame 追溯，未逐条人工核对）分别记在两张评分票的 Answer
  验证：pre-commit 的 prettier 与 make check 通过；CLI 调用写法与评委看图均未实跑
  停在：已认领「用真实配置把 v1 的三个 CLI 各无头跑通一次」，冒烟脚本 `.scratch/llm-bench/smoke/smoke.sh` 已干跑，等用户亲手执行
  推送：未推送；地图、research 分支都只在本地（仓库公开，用户要求研究分支不推送）

## 下次运行

<!-- 整块改写：接下来的任务和优先级，含仍受阻的项。 -->

- [2026-10-21] 推进 bench 地图：`/wayfinder .scratch/llm-bench/map.md`，每次会话解决一张票；前沿只剩「用真实配置把 v1 的三个 CLI 各无头跑通一次」（已认领；用户跑 `bash .scratch/llm-bench/smoke/smoke.sh all` 后，代理读 `~/.cache/bench-smoke/` 写 Answer 与额度估算），它解锁「运行隔离、联网与启动方式」，两者之后才轮到「任务定义样张」
  继续试用并优化 ad-astra（来自 TODO.md，10-12；ad-astra 最后一次提交在 10-10）
