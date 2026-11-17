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
- [2026-11-03] tufte-reader 的 Mermaid 图由 vendor 的 pele 1.13.0（obsidianmd，单文件 JS，MIT）编译成 SVG，替换了 10-20 引入的 ondine 0.0.1（用户 11-03 要求迁移）；源码留在页面里、每次构建重编，悬停出现纯 CSS 的源码开关、打印只出图；只用于结构图，数据图仍走 figlib 曲线图
- [2026-10-20] flopwire（代理间消息与转录检索）不接入 farm：子代理里的 hook 不投递、pi 不在支持列表、herdr pane 已能 agent prompt；借三点写成 plans/015（进程组收尾）、016（转录核对写入与用量，只做 Claude Code 后端）
- [2026-10-20] 用户清空了「下次运行」积压：guide-me 验收、tufte-reader 冷启动验收与 plates.md 审阅、日期前缀文件名冒烟、reelshort 页重建、show-me-html 单图导出 PNG 与导读元信息行、codebase-to-book 改用 ondine、真实 /farm 与 send-to-obsidian X 链接实测，都不再跟进，用户再提才做
- [2026-10-20] tufte-reader 配色定为暖底（亮 #fbf8f1、暗 #1c1b19）加 `--strong` 粗体色（暗色琥珀）：仓库历史里从无这套值，10-19 shelf 五页按安装副本重建，后来安装副本也回到旧值（推测是 install 覆盖，未证实）；用户选移植进仓库，值取自 shelf 已提交成品
- [2026-10-19] shelf 的 financial-math 已改成曲线图风格；how-llms-work 的 figs.py 自带旧图元、不引用 figlib，改风格要先迁移
- [2026-10-27] show-me-html / tufte-reader 语法高亮维持 vendor 的 @speed-highlight/core（最快：32 KB 1.5 ms，Kirari 4.0、Prism 2.2）；上游没有的 Kotlin 由 show-me-html 自写 `kt.js` 补，放在 vendor/shj/languages、升级覆盖时保留（用户 10-27 选不挪出 vendor）。页面常出现 JSX/TSX 或 C#/Swift/Ruby 时再换 Kirari；Shiki 要构建期 Node 或每页 72 KB+，排除
- [2026-10-21] bench 的规划以 `.scratch/llm-bench/map.md`（wayfinder 本地跟踪器）为准，决策细节在各票里；用户确认：只用公开 repo、farm 无头红线不约束 bench、研究分支不推送；推进地图的代理不替用户启动选手运行。main 上的 bench 提交已于 10-22 随 017 推到 origin
- [2026-10-20] 写书慢不在构建，也不缺分章派发：tufte-reader 自 64b7cbb（10-10）起就能分章派发，shelf 不用是因为它的 docs/books.md 规定一次写一章、自己写；shelf 四本书重建 0.3–1.0 s，how-llms-work 1014 个公式重编 0.8 s
- [2026-11-03] 本机无头 Chrome 不读 HTTP(S)_PROXY，系统代理关着，页面直连 Google Fonts/jsDelivr 单次 12～69s；加 `--proxy-server` 5～7s，屏蔽字体域名 4s；另外不给 `--user-data-dir` 每次启动多约 4s，给空 profile 后 figprobe 整次 2.6s。来源：docs/research/2026-10-22-show-me-html-build-time-handoff.md、figprobe 实测
- [2026-10-27] sharpen 的成稿模板是从 Anthropic「Prompting Claude Opus 5.5」里提炼的可迁移原则（点名具体行为与模式、动手前先探索、验收与停下时机写明、贴入材料用 pasted_content 标签），不链接该文档：它主要讲 harness 层（effort、thinking 显示、无人值守循环），且本地副本在未跟踪的 tmp/
- [2026-10-27] Claude Code 没有把文本回写到输入框的 API（`--bg`、`--resume`、`--fork-session` 都不是），sharpen 的交接改为 AskUserQuestion 三选项：本会话执行、写 $TMPDIR 文件并 pbcopy、先改；用户选的这个方案
- [2026-10-24] `xcrun simctl runtime delete` 返回后镜像空间在后台回收：紧接着的 df 只多 0.5 GiB，约 7 GiB 落进下一项的差值；storage 技能逐项记释放量时把这种差额记回 runtime 那一项。来源：storage 技能首跑
- [2026-11-02] disco-elysium-narrative 的 assets/raw.txt 按约 36 字硬换行，50.4% 的技能台词跨行：统计台词长度或摘引文前必须先合并续行，否则量到的是换行宽度（合并后中位 28、p95 74）；来源：本次审计脚本
- [2026-11-03] disco-elysium-narrative 语料解析：破折号前有空格才直接算发言，没空格须是已知说话人；不分情况会造出假说话人，一律要求空格又会丢掉真发言（失败数从 234 掉到 224）；来源：evals/corpus_stats.py 复算
- [2026-11-02] disco-elysium-narrative 里的原句样本会被模型照搬：把一句样本换成五种开口后，B 版解答 5 篇全部对应其一，只是从抄一句变成五选一；要教走法和文体，不给句子。来源：本次盲测
- [2026-11-03] disco-elysium-narrative 界面层（evals/ui_stats.py）：属性行 102/102 挂在衣物卡上，思维没有效果行；任务行是语料唯一派活处，其后 66% 接 NPC 或金，所以新任务放场景中段、不作结尾（放结尾时评委判多次收尾）；style_eval.parse() 会把界面行并进上一条发言
- [2026-11-03] disco-elysium-narrative 三版盲评（codex+fable，各 15 篇）：界面层改动、删「不复用」提示两项均分差都 ≤0.12，测不出；上一轮原作感 −0.4 未复现，属稿件随机差异；三版正文 12 字照抄都是 0，提示不影响照抄率。稿件在 /tmp/writing-desk
- [2026-11-08] disco-elysium-narrative 质地：写在 style.md 末尾的校准表不生效（技能行单句 0/38）；SKILL.md 加「写完：数一遍技能台词」后单句 49–55%、指令起句 21%→3%，但只给单句下限时 agent 靠加台词凑数，技能占比 35%→44%，须同时限占比、说「截短不加」。稿件 /tmp/de-review（根目录 v1，子目录 v2、v3）
- [2026-11-08] disco-elysium-narrative 4e31544 复测 7 篇：单句 40%、连词 19%、指令起句 2% 已贴语料；同家族单评委盲评新版 4 组赢 3，六项均分 4.21 对 3.92，差 0.29 约等于评委噪声 0.26，不算定论。稿件 /tmp/de-review/v4、blind
- [2026-11-10] disco-elysium-narrative：让模型「自己选类型」等于取表格第一行，改由 scripts/draw.py 按占比抽后同批 6 篇：平心定气 6/6→3/6、「你可以不」5/6→0、思维阁开口 5/5 同型→各不相同、出场技能 14→17；第一稿单句常为 0%，靠 draft_check 改到通过；来源：/tmp/writing-room/out 的 --across
- [2026-11-10] disco-elysium-narrative：Markdown 人物名不加粗、HTML 和终端加粗，思维阁标题条不带「」和 💭，是用户确认保留的介质差异，不要对齐；终端色板在白底对比度 1.9–3.7（实算），所以有 `--light`，环境变量里没有可判断主题的线索
- [2026-11-10] disco-elysium-narrative HTML：游戏对话框里只有技能名按属性上色（智力青、精神紫、体格红、身手黄），人物和物品名同为灰白，「你」偏冷灰蓝（约 #A5AFBB 对 #D0D0D0），检定标记暗灰不随结果变色；游戏原紫在暗底对比度仅 2.5，须提亮；来源：Steam 商店截图取样，/tmp/de-shots
- [2026-11-10] Claude Code 界面：回复正文只有粗体、斜体、行内代码淡紫和代码块高亮色，凑不出四种属性色；Bash 工具输出保留 ANSI 真彩色、粗体、斜体且整段显示，所以终端彩色版走 scripts/render_tui.py；来源：herdr 读相邻窗格的 ANSI 输出
- [2026-11-03] pele 在 node 里的内置字宽表比 -apple-system 窄（i 2.7px 对实测 4.4px），类图成员行会顶出框；mermaid.mjs 用按 Chrome 实测分档的自写 measurer，8 幅对比图文字离框 ≥11px。汉字它本来按 1em，不是问题；来源：/tmp/pele-cmp 探针
- [2026-11-12] show-me-html 的节点连线图默认写 Mermaid 源码、构建期由 pele 编译（用户看过两张真实手绘图的重做对比后定，理由是确定性的库更合惯例）；手写 SVG 只留给时间线、泳道、象限、层叠、循环和示意图。计划 plans/030、031，决定与否决项在 plans/README.md 同名节
- [2026-11-12] pele 默认排得松（200px 折行、层距约 50px），直链图比手绘高近一倍；源码首行注入 `%%{init}%%` 的 flowchart wrappingWidth 360、rankSpacing 20、nodeSpacing 20 后与手绘接近，但 init 不能放在 frontmatter 前（报 No diagram type）。来源：/tmp/smh-pele 对比
- [2026-11-14] tufte-reader 西文字体沿用 STIX Two Text，用户 11-14 决定先不换 EB Garamond，再提才做；实测（样张 /tmp/ebg-compare，临时目录可能已清）：x 高 0.400（STIX Two Text 0.473），原样排在中文旁偏小，`size-adjust: 112%` 后 400 字重与思源宋体相称，500 过重；默认数字是等高数字
- [2026-11-14] fontsource 的 eb-garamond 子集没有 onum/lnum/smcp，拉丁分片不含 U+2070–209F 和 →≤≈；带全部特性的在 octaviopardo/EBGaramond12 的 fonts/webfonts（每个 21–24 万字节，无 tag，要钉提交号）。Garamond-Math 只有 84 万字节的 OTF、无 tag、2022 年后未更新，x 高 0.450
- [2026-11-17] Claude Code 压缩后，项目根 CLAUDE.md、无 paths 的 rules 和自动记忆从磁盘重新注入；子目录指令文件和带 paths 的规则会被摘要掉，Read 过的文件最多重读 5 个且超 5,000 token 只留路径。所以规则的晋升目标应是根 AGENTS.md 或无 paths 的 rules（@ 导入的内容是否重新注入文档没明说，属推断），PROJECT_MEMORY.md 压缩后不保证还在。来源：code.claude.com/docs/en 的 context-window.md、memory.md，2026-11-17 核对原文
- [2026-11-17] bootstrap-claude 的条目去向检查按 plans/034 落地。eval（Opus 5.5，每组 3 次）只在「消失的条目有去向」上分出新旧版（0/3 对 3/3）；现行文字在规则首次出现时已经会晋升，所以分流文字没做。真实历史里「进指令文件的少」没被夹具复现，不算已解决。实测数字和脚本在 plans/034-bootstrap-claude-memory-removal-gate/
- [2026-11-17] 在本仓库用子 agent 跑技能 eval：子 agent 继承本仓库的 AGENTS.md，两组执行者都派出之后才能改它；夹具是普通目录，要先在副本里建基线提交；被测技能放中性路径并去掉 evals/，事后从运行记录核对实际跑的脚本路径。来源：plans/034 附件里的 eval-baseline.md

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
- [2026-11-12] pele 在 show-me-html 样式下不能用的图型：timeline 色块文字对比度 2.0–3.7（构建报 ERROR）、quadrantChart 轴名竖排且点用回退蓝、mindmap 不接受 accTitle；可用的是 flowchart、sequence、state、class、er
- [2026-11-12] show-me.css 注释里写了带尖括号的 pre.mermaid 开标签，CSS 内联进页面后被 mermaid.mjs 当成一幅图去编译；按文本找源码的脚本，样式和文档注释里都不要出现它要找的字面量

## 上次会话

<!-- 整块改写：分支、验证命令及实际结果、停在何处；任务细节只留一行指向证据目录。 -->

- [2026-11-17] main：issue #3 代码引用经集成分支 show-me-html-code-reference 快进合入（14 个提交），已 make install；两路审阅的发现由第二个实现者修完。未推送，issue #3 未关。
  验证：146 个单元测试全过；make check、prettier 通过；冻结场景完整重建后与 2026-11-17-hover 轮 probe.json 相同、30/30 截图相同；对齐实测与样例页在 /tmp/code-ref-check。

## 下次运行

<!-- 整块改写：接下来的任务和优先级，含仍受阻的项。 -->

- [2026-11-17] 等用户：推送 main 并关闭 issue #3（issue 正文仍是收窄前的 id_* 与 .env.* 规则，关前补一条评论）；ADR（路径按构建目录算）写不写。
  已知小缺口：代码引用「读不了」「不是文件」两条报错没有命令行测试。
