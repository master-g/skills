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

- [2026-10-20] main，已推送：url-to-kami、x-to-markdown 弃用；send-to-obsidian 直接调 xtomd.com 取 X 链接；farm 借鉴 flopwire 的 plans/015、016 经 improve execute 审阅后 cherry-pick 合入，Claude Code worker 改文件用 Edit / Write（claude-code-worker.md「派发」），已 make install SKILL=farm SOURCE=.，worktree 与临时分支已清理
  验证：make check 通过（119 个文件）；python3 skills/farm/test_subagent.py ok；plans/015 的 smoke.sh 对安装副本 16 项全过；安装副本与仓库 diff 为空；没跑过真实 /farm，send-to-obsidian 没实际写入 vault

## 下次运行

<!-- 整块改写：接下来的任务和优先级，含仍受阻的项。 -->

- [2026-10-20] 无排定任务。shelf 的 financial-math 已改成曲线图风格；how-llms-work 的 figs.py 自带旧图元、不引用 figlib，改风格要先迁移
