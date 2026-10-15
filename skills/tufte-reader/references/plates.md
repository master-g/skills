# 题图

用户要求配题图时使用（「配题图」「加插图开题」「用版画做卷首」之类）。题图是读本作者加的旧版画插图：扉页一幅卷首图，另外挑主题最贴切的几章各配一幅章首图，不必每章都配。原文没有这些图，构建把它们单独统计为「题图」，不计入「图」。

## 选图

选图从章节的主题出发，风格由「系列」一节把关：16–18 世纪的铜版画、蚀刻和木刻，炼金术、自然哲学、博物、解剖、机械一类的书籍插图，黑线条印在纸上。_Atalanta Fugiens_（1618）是这种风格的代表，不是唯一的来源。

1. 读结构清单，给扉页和准备配图的几章各写一两个主题词：扉页取全书主旨，章首取这一章最核心的意象或动作（结合、拆解、观察、循环、传输……）。
2. 按主题词找画面：先看「系列」表里哪些系列的主题对得上，到那几个分类里搜；炼金寓意类的主题也查「图录」的「适合的主题」一栏。搜法见「系列」一节末尾；选图前用 `--thumb` 取缩略图总览看一眼，不要只凭文件名和尺寸挑。寓意对不上就不配这一章，不要为了配图而牵强。
3. 候选图过三道筛：许可（公有领域、无已知版权限制、CC0、CC BY，取图脚本会再查一次）；分辨率（题图在页面上约 480 CSS 像素宽，高分屏需要 1000px 以上的图源，600px 的图会发虚）；画面（线条清楚、未手工上色、不带大段正文文字）。整页扫描只要画面完整就能用：取图时给 `--region` 按百分比裁出画面，Commons 和 IA 的图都可以裁。
4. 一本读本里的题图风格要统一：同一时代、同一技法（都是铜版画，或都是木刻），不必出自同一本书。
5. 选定后写进结构清单：扉页用哪一幅，哪几章配题图、各用哪一幅、各自的许可。

## 系列

同一类风格、已在 Commons 上核实过的系列（2026-10-14）。「规模」是分类里的文件数；许可按前 50 个文件统计，同一分类里常混有博物馆上传的 CC BY 和 CC BY-SA 文件，每幅都要过取图脚本的许可检查。CC BY 的图注要署名。

铜版画与蚀刻：

| 系列                                                                                                                                                          | 年代        | Commons 分类                                                                                           | 规模与许可                                                    | 适合的主题                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- | -------------------------------------------------------- |
| Michael Maier, _Atalanta Fugiens_（Merian 刻）                                                                                                                | 1618        | Category:Atalanta Fugiens                                                                              | 292 文件，几乎全部公有领域；50 幅徽章逐幅见「图录」           | 寓意画，覆盖面最广：孕育、结合、分解、循环、提纯、观察…… |
| Michael Maier, _Symbola aureae mensae_                                                                                                                        | 1617        | Category:Symbola aureae mensae duodecim nationum                                                       | 9 文件，公有领域为主                                          | 十二位各国的炼金士，传统、流派、对话                     |
| _Musaeum Hermeticum_                                                                                                                                          | 1678        | Category:Musaeum Hermeticum                                                                            | 24 文件，公有领域为主，1000–2000px                            | 炼金寓意、龙与火、变化与循环                             |
| _Lambspring_（收入 Musaeum Hermeticum）                                                                                                                       | 1625        | Category:Lambspring                                                                                    | 20 文件，全部公有领域，4000px 以上                            | 对偶、父与子、内在冲突、动物寓意                         |
| Heinrich Khunrath, _Amphitheatrum sapientiae aeternae_                                                                                                        | 1595/1609   | Category:Amphitheatrum sapientiae aeternae                                                             | 38 文件，公有领域与 CC BY 各半，2000px 以上                   | 实验室与祈祷室、知识的殿堂、总览式的大图                 |
| _Mutus Liber_                                                                                                                                                 | 1677        | Category:Mutus Liber                                                                                   | 13 文件，公有领域为主，约 600px                               | 无字的步骤图、过程、流程                                 |
| Robert Fludd, _Utriusque Cosmi … Historia_                                                                                                                    | 1617–1621   | Category:Utriusque Cosmi                                                                               | 410 文件，公有领域为主                                        | 宏观与微观、系统总览、层级、和声、记忆术                 |
| Athanasius Kircher 各书：_Ars magna lucis et umbrae_、_Musurgia universalis_、_Mundus Subterraneus_、_Phonurgia nova_、_Oedipus Aegyptiacus_ 等，各在子分类里 | 1646–1680   | Category:Athanasius Kircher                                                                            | 各书 20–400 文件，公有领域为主                                | 光学、声学与音乐、地下世界与火山、符号与语言、机械装置   |
| Robert Hooke, _Micrographia_                                                                                                                                  | 1665        | Category:Micrographia, or, Some physiological descriptions of minute bodies made by magnifying glasses | 171 文件，公有领域为主                                        | 显微、细节、尺度、观察                                   |
| Johannes Hevelius, _Selenographia_                                                                                                                            | 1647        | Category:Selenographia                                                                                 | 12 文件，公有领域为主                                         | 天文、月面、望远镜与仪器                                 |
| Francis Bacon, _Novum Organum_（扉页的过海之船）                                                                                                              | 1620        | Category:Novum Organum                                                                                 | 18 文件，公有领域为主，约 900px                               | 方法、越过边界的探索、新知                               |
| Agostino Ramelli, _Le diverse et artificiose machine_                                                                                                         | 1588        | Category:Agostino Ramelli                                                                              | 25 文件，公有领域为主，1000px 以上                            | 机械、装置、工程、杠杆与齿轮                             |
| Theodor de Bry 出版的航海与寓意版画                                                                                                                           | 1590–1630   | Category:Theodor de Bry                                                                                | 382 文件加 27 个子分类，公有领域为主                          | 航海、新大陆、探险、相遇                                 |
| Matthäus Merian 的版画                                                                                                                                        | 1620–1650   | Category:Engravings by Matthäus Merian                                                                 | 595 文件加 33 个子分类，公有领域为主                          | 城市与地景、圣经场景、事件图                             |
| Jan Jonston, _Historiae naturalis_（Merian 刻）                                                                                                               | 1650–1657   | Category:Historiae naturalis de quadrupedibus libri                                                    | 50 文件，全部公有领域，3000px 以上                            | 动物、博物、分类                                         |
| Comenius, _Orbis sensualium pictus_                                                                                                                           | 1658 及后印 | Category:Orbis pictus                                                                                  | 70 文件，公有领域                                             | 百科式的物与名、教学、日常器物                           |
| J. J. Scheuchzer, _Physica sacra_                                                                                                                             | 1731–1735   | Category:Physica sacra, by Scheuchzer                                                                  | 32 文件，几乎全部 CC BY（要署名）                             | 自然史、化石与地层、带装饰边框的巴洛克构图               |
| Wellcome Collection 的版画                                                                                                                                    | 1500–1900   | Category:Engravings in the Wellcome Collection                                                         | 3085 文件加 5 个子分类，全部 CC BY 4.0（要署名），2000px 以上 | 医学、炼金士与学者、器具、讽刺画；用 `deepcat:` 搜       |
| Johannes Hevelius, _Machina coelestis_                                                                                                                        | 1673        | Category:Machina Coelestis by Johannes Hevelius                                                        | 10 文件，公有领域，约 850px（偏小）                           | 观测、仪器操作、望远镜与象限仪                           |
| Stradanus 设计、Collaert 等刻, _Nova Reperta_（《新发现》）                                                                                                   | 1590 年代   | Category:Nova Reperta                                                                                  | 38 文件，CC0 与公有领域为主，3500px                           | 发明与工艺：印刷、蒸馏、磁针、航海、火药                 |
| Abraham Bosse 的蚀刻                                                                                                                                          | 1630–1650   | Category:Abraham Bosse                                                                                 | 237 文件加 11 个子分类，CC0 为主，3500px                      | 作坊与工序、印刷、日常与职业                             |

木刻（线条更粗、更古拙，一本读本里不与铜版画混用）：

| 系列                                            | 年代 | Commons 分类                        | 规模与许可                      | 适合的主题               |
| ----------------------------------------------- | ---- | ----------------------------------- | ------------------------------- | ------------------------ |
| Hieronymus Brunschwig, _Kleines Destillierbuch_ | 1500 | Category:Kleines Destillierbuch     | 270 文件，公有领域，2500px 以上 | 蒸馏器具、工艺步骤、作坊 |
| Andreas Vesalius, _De humani corporis fabrica_  | 1543 | Category:De humani corporis fabrica | 66 文件，CC BY 为主（要署名）   | 结构、解剖、拆解一个系统 |
| _Rosarium philosophorum_                        | 1550 | Category:Rosarium philosophorum     | 32 文件，公有领域为主，约 900px | 结合、对偶、阶段         |
| Georgius Agricola, _De re metallica_            | 1556 | Category:De re metallica            | 27 文件，公有领域为主           | 采矿、机械、工艺、流程   |

跨系列的大池子，搜主题时用 `deepcat:` 连子分类一起搜：Category:17th-century engravings（1356 文件、61 个子分类）、Category:Frontispieces（670 文件）、Category:Emblem books（180 个子分类）、Category:Scientific illustrations（403 文件、33 个子分类，许可混杂）。

搜图用 `scripts/find_plate.py`：关键词加 `--cat <分类>`（`--deep` 连子分类一起搜；只给 `--cat` 就列出整个分类），一次取回尺寸和许可，只列出许可可用且宽度不小于 1000px 的图，按宽度从大到小排，同一幅的 `.tif`/`.jpg` 重复只留最宽的。加 `--thumb <目录>` 把列出的图下载成缩略图并拼一张总览（按表格顺序，每行 5 幅），整页扫描、带正文的页面一眼能看出来：

```sh
python3 <skill-path>/scripts/find_plate.py dragon --cat "Musaeum Hermeticum" --thumb /tmp/cand
python3 <skill-path>/scripts/find_plate.py alchemist --cat "Engravings in the Wellcome Collection" --deep
python3 <skill-path>/scripts/find_plate.py --cat "Agostino Ramelli" --thumb /tmp/cand
```

没有合格结果时加 `--all` 看不合格的原因（许可、宽度、不是图片），再放宽 `--min-width`、换关键词或换分类。「系列」表之外的主题（天文仪器、工序、航海……）到 Category:17th-century engravings 或 Category:Frontispieces 用 `--deep` 搜，关键词用英文或拉丁文。「文件」一列直接作 `plate.py` 的参数。分类名不确定时，用 Commons 的搜索 API `list=search&srnamespace=14&srsearch=<关键词>` 搜分类，不要猜。

Science History Institute、Wellcome Collection、Biodiversity Heritage Library、Rijksmuseum 也有大量同类图。在这些站点看中的图，先在 Commons 上找同一幅；Commons 上没有的，按「取图」一节的规则处理，没有列出的来源就不用。

## 取图

在页面所在的目录里运行。Atalanta Fugiens 用图录「高清版」表里的参数，从 Internet Archive 取 1000px 的高清版（shell 里用单引号，`$` 不能被展开）：

```sh
python3 <skill-path>/scripts/plate.py 'ia:atalantafugiensh00maie$185' --region pct:2.9,18.1,75.5,52.8 -o figures/plates --name atalanta-42
```

其他图从 Wikimedia Commons 取，写文件名：

```sh
python3 <skill-path>/scripts/plate.py "File:<Commons 上的文件名>" -o figures/plates --name <文件名>
```

- Commons 的图：脚本读这个文件的许可字段，只接受公有领域、无已知版权限制（No restrictions，图书馆批量上传的古籍插图常这样标）、CC0 和 CC BY。其余许可（包括 CC BY-SA、NC、ND）或字段缺失时拒绝并以退出码 3 结束：换一幅图，不要绕过脚本手动下载。整页扫描加 `--region pct:x,y,w,h` 在本地裁出画面（需要 ImageMagick），百分比看缩略图估一次、取出来看成品再微调。
- Internet Archive 的图：IA 的元数据没有许可字段，脚本只放行 `plate.py` 里 `IA_ITEMS` 白名单登记过的条目，许可依据写在白名单里；目前只有 Atalanta Fugiens 的 Getty 扫描本，别的 IA 条目报退出码 3。`--region` 是画面在整页上的百分比位置，由 IIIF 服务器裁出来，不需要本地裁切工具。
- 要用 IA 上别的扫描本（「系列」里的 Fludd、Kircher、Hooke 等在 IA 上都有）：按 `plate.py` 里 `IA_ITEMS` 上方注释的三条标准确认原作与扫描都属公有领域，请维护者认可后加一条登记，并在 `tests/test_plate.py` 里加一行断言。
- 产出 `figures/plates/<name>.png`（有 ImageMagick 时拉伸色阶、压成 4 级灰度 PNG；macOS 没有 ImageMagick 时用 sips 转成 JPEG，纸面保留扫描的灰色，亮色主题下会露出一块浅灰底）、`<name>.json`（出处、许可、作者、取图日期），并打印一段可以直接粘贴的 `<figure class="plate">`。
- 默认宽 1000px，单幅一般在 80–250 KB。超过 300 KB 时脚本发 WARN，加 `--width 800` 重取。
- 图录主表里 Commons 的单幅文件只有约 600px 宽，在高分屏上发虚，只在 IA 取不到时作退路。
- 成品几乎是一片纯色（透明底、空白页、裁错区域）时脚本报 ERROR 并删掉成品，退出码 1；`<name>.json` 里记有图源尺寸和裁切区域。

## 写法

把脚本打印的写法放到位置上，再改掉所有 `TODO-题图`：构建在页面里看到 `TODO-题图` 就报 ERROR。

- **扉页题图**：放在 `header.titlepage` 里、`p.byline` 之后。
- **章首题图**：放在该章 `<h2>` 后面那个 `<section>` 的里面，作为它的第一个子元素（`<h2>` 和 `<section>` 之间不放，`<p>` 里也不放）。
- **图注**：`题图　` 加出处（书名、页码或幅次）、图题或箴言的译文（有的话）、刻工与年份，最后是脚本生成的图源与许可。例：「题图　《逃离的阿塔兰忒》第 42 幅：『行于化学者，当以自然为向导，理性为手杖，经验为眼镜，阅读为明灯。』Matthäus Merian 刻，1618。图源 Wikimedia Commons，公有领域。」CC BY 的图要写署名，脚本取不到干净的署名时留了 `TODO-题图：署名`，到文件页面上查实再填。
- **alt**：描述画面本身（人物、动作、器物），不写寓意。
- `data-source` 和 `data-license` 由脚本写好，不要删：构建靠它们检查题图有没有出处。
- 读本说明里写一句：题图是译者（原创撰写时是撰写者）所加，列出各幅的来源与许可。
- 分章派发时，子 agent 不放题图；主 agent 拼接完各章后统一放。

## 图录

_Atalanta Fugiens_（《逃离的阿塔兰忒》），Michael Maier 著，Matthäus Merian 刻，Oppenheim：Johann Theodor de Bry，1618（初版 1617）。五十幅徽章，每幅配一句拉丁箴言，题为「论自然的奥秘」（De secretis Naturae）。取图默认用「高清版」表的 IA 参数；主表的文件在 Commons 的 `Category:Atalanta Fugiens` 里，是约 600px 的单图，作退路和对照。

箴言的拉丁文按 1618 年版校订；中文是大意，写进图注前可以再润色。「适合的主题」是选图的提示，不是限定。

| 幅  | 文件                                               | 箴言                                                                                                                 | 大意                                                                         | 适合的主题                               |
| --- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------- |
| 1   | File:Michael Maier Atalanta Fugiens Embleme 1.jpeg | Portavit eum ventus in ventre suo.                                                                                   | 风把它怀在腹中。                                                             | 孕育、潜伏的状态、在传输中成形           |
| 2   | File:Michael Maier Atalanta Fugiens Emblem 02.jpeg | Nutrix ejus terra est.                                                                                               | 大地是它的乳母。                                                             | 哺育、基础与环境、数据与预训练、基础设施 |
| 3   | File:Michael Maier Atalanta Fugiens Emblem 03.jpeg | Vade ad mulierem lavantem pannos, tu fac similiter.                                                                  | 去看洗衣的妇人，照她那样做。                                                 | 清洗、预处理、照范例做                   |
| 4   | File:Michael Maier Atalanta Fugiens Emblem 04.jpeg | Conjunge fratrem cum sorore & propina illis poculum amoris.                                                          | 让兄妹结合，递给他们爱的杯。                                                 | 结合、对偶、连接、融合                   |
| 5   | File:Michael Maier Atalanta Fugiens Emblem 05.jpeg | Appone mulieri super mammas bufonem, ut ablactet eum, & moriatur mulier, sitque bufo grossus de lacte.               | 把蟾蜍放到妇人胸前让她哺乳；妇人死去，蟾蜍因乳而肥。                         | 汲取与转移、蒸馏、寄生、代价             |
| 6   | File:Michael Maier Atalanta Fugiens Emblem 06.jpeg | Seminate aurum vestrum in terram albam foliatam.                                                                     | 把你们的金子种进白色的叶状土里。                                             | 播种、初始化、投入与回报                 |
| 7   | File:Michael Maier Atalanta Fugiens Emblem 07.jpeg | Fit pullus a nido volans, qui iterum cadit in nidum.                                                                 | 雏鸟飞离巢，又落回巢中。                                                     | 循环、反馈回路、回流、递归               |
| 8   | File:Michael Maier Atalanta Fugiens Emblem 08.jpeg | Accipe ovum & igneo percute gladio.                                                                                  | 取一枚蛋，用火焰之剑劈开。                                                   | 拆分、分解问题、破题、攻坚               |
| 9   | File:Michael Maier Atalanta Fugiens Emblem 09.jpeg | Arborem cum sene conclude in rorida domo, & comedens de fructu ejus fiet juvenis.                                    | 把树和老人同关进露水之屋，老人吃了树上的果子便返老还童。                     | 更新、重构、焕新旧系统                   |
| 10  | File:Michael Maier Atalanta Fugiens Emblem 10.jpeg | Da ignem igni, Mercurium Mercurio, & sufficit tibi.                                                                  | 以火予火，以汞予汞，这就够了。                                               | 同类相加、自指、同构                     |
| 11  | File:Atalanta Fugiens 11 Latona.jpg                | Dealbate Latonam & rumpite libros.                                                                                   | 漂白拉托娜，撕掉书本。                                                       | 净化、抛开成说、从实践出发               |
| 12  | File:Atalanta Fugiens 12 Helicon.jpg               | Lapis, quem Saturnus pro Jove filio devoratum evomuit, pro monumento in Helicone mortalibus est positus.             | 萨图恩当作儿子朱庇特吞下又吐出的那块石头，立在赫利孔山上，作为给世人的纪念。 | 纪念、存档、遗产、历史回顾               |
| 13  | File:Michael Maier Atalanta Fugiens Emblem 13.jpeg | Aes Philosophorum hydropicum est, & vult lavari septies in fluvio, ut Naaman leprosus in Jordane.                    | 哲人之铜患了水肿，要在河里洗七次，如同麻风病人乃缦在约旦河里那样。           | 反复迭代、多轮训练、去噪                 |
| 14  | File:Michael Maier Atalanta Fugiens Emblem 14.jpeg | Hic est Draco caudam suam devorans.                                                                                  | 这是吞食自己尾巴的龙。                                                       | 循环、自指、递归、自举、闭环             |
| 15  | File:Michael Maier Atalanta Fugiens Emblem 15.jpeg | Opus figuli, consistens in sicco & humido, te doceat.                                                                | 让陶工的手艺教你：它在干与湿之间。                                           | 工艺、构建、平衡两种状态                 |
| 16  | File:Michael Maier Atalanta Fugiens Emblem 16.jpeg | Hic leo, quas plumas non habet, alter habet.                                                                         | 这头狮子没有的羽翼，另一头有。                                               | 固定与挥发、静态与动态、互补             |
| 17  | File:Michael Maier Atalanta Fugiens Emblem 17.jpeg | Orbita quadruplex hoc regit ignis opus.                                                                              | 四重轨道主宰这火的工作。                                                     | 周期、四个阶段、调度                     |
| 18  | File:Michael Maier Atalanta Fugiens Emblem 18.jpeg | Ignire ignis amat, non aurificare, sed aurum.                                                                        | 火爱点燃，不爱造金；造金的是金。                                             | 各司其职、工具的边界、单一职责           |
| 19  | File:Michael Maier Atalanta Fugiens Emblem 19.jpeg | Si de quatuor unum occidas, subito mortuus omnis erit.                                                               | 四个里杀掉一个，全体立刻都死。                                               | 耦合、单点故障、依赖、容错               |
| 20  | File:Michael Maier Atalanta Fugiens Emblem 20.jpeg | Naturam natura docet, debellet ut ignem.                                                                             | 自然教自然去降服火。                                                         | 负反馈、自我调节、控制                   |
| 21  | File:Michael Maier Atalanta Fugiens Emblem 21.jpeg | Fac ex mare & foemina circulum, inde quadrangulum, hinc triangulum, fac circulum & habebis lapidem Philosophorum.    | 由男女作圆，再作方，再作三角，再作圆，你便得到哲人之石。                     | 几何、形式化、变换、证明                 |
| 22  | File:Michael Maier Atalanta Fugiens Emblem 22.jpeg | Plumbo habito candido fac opus mulierum, hoc est, Coque.                                                             | 得了白铅，就做妇人的活计：煮。                                               | 耐心、慢火、渐进、长时间运行             |
| 23  | File:Michael Maier Atalanta Fugiens Emblem 23.jpeg | Aurum pluit, dum nascitur Pallas Rhodi, & Sol concumbit Veneri.                                                      | 帕拉斯在罗得岛诞生、太阳与维纳斯同寝时，天降金雨。                           | 诞生、涌现、突破                         |
| 24  | File:Michael Maier Atalanta Fugiens Emblem 24.jpeg | Regem lupus voravit & vitae crematus reddidit.                                                                       | 狼吞下国王，狼被焚烧后国王复生。                                             | 消亡与复生、重启、恢复、回滚             |
| 25  | File:Atalanta Fugiens 25 Dragon.jpg                | Draco non moritur, nisi cum fratre & sorore sua interficiatur, qui sunt Sol & Luna.                                  | 龙不会死，除非与它的兄妹太阳和月亮一同被杀。                                 | 成对的条件、协同、合力                   |
| 26  | File:Michael Maier Atalanta Fugiens Emblem 26.jpeg | Sapientiae humanae fructus Lignum vitae est.                                                                         | 人类智慧的果实是生命之树。                                                   | 知识、学习、知识体系                     |
| 27  | File:Michael Maier Atalanta Fugiens Emblem 27.jpeg | Qui Rosarium intrare conatur Philosophicum absque clave, assimilatur homini ambulare volenti absque pedibus.         | 没有钥匙想进哲人玫瑰园的人，就像没有脚想走路的人。                           | 门槛、前置知识、入门、密钥               |
| 28  | File:Michael Maier Atalanta Fugiens Emblem 28.jpeg | Rex balneatur in Laconico sedens, atraque bile liberatur a Pharut.                                                   | 国王坐在蒸汽浴里，由法鲁特为他除去黑胆汁。                                   | 净化、调试、排错                         |
| 29  | File:Michael Maier Atalanta Fugiens Emblem 29.jpeg | Ut Salamandra vivit igne sic lapis.                                                                                  | 如火蜥蜴生于火中，石亦如此。                                                 | 韧性、极端条件、可靠性                   |
| 30  | File:Michael Maier Atalanta Fugiens Emblem 30.jpeg | Sol indiget luna, ut gallus gallina.                                                                                 | 太阳需要月亮，如公鸡需要母鸡。                                               | 互补、成对、主从                         |
| 31  | File:Michael Maier Atalanta Fugiens Emblem 31.jpeg | Rex natans in mari, clamans alta voce: Qui me eripiet, ingens praemium habebit.                                      | 国王在海中泅水，高声呼喊：救我者必得重赏。                                   | 危机、求救、事故响应                     |
| 32  | File:Michael Maier Atalanta Fugiens Emblem 32.jpeg | Corallus sub aquis ut crescit & aere induratur, sic lapis.                                                           | 珊瑚在水下生长、遇空气变硬，石亦如此。                                       | 环境改变性质、固化、部署                 |
| 33  | File:Michael Maier Atalanta Fugiens Emblem 33.jpeg | Hermaphroditus mortuo similis, in tenebris jacens, igne indiget.                                                     | 雌雄同体者如死者般躺在黑暗中，需要火。                                       | 冷启动、激活、唤醒                       |
| 34  | File:Michael Maier Atalanta Fugiens Emblem 34.jpeg | In balneis concipitur, & in aere nascitur, rubens vero factus graditur super aquas.                                  | 在浴中受孕，在空中诞生，变红之后行走于水上。                                 | 生命周期、阶段转换、发布                 |
| 35  | File:Michael Maier Atalanta Fugiens Emblem 35.jpeg | Ceres Triptolemum, Thetis Achillem, ut sub igne morari assuefecit, sic artifex lapidem.                              | 刻瑞斯让特里普托勒摩斯、忒提斯让阿喀琉斯习惯待在火下，匠人也这样对待石头。   | 磨炼、训练、渐进暴露                     |
| 36  | File:Michael Maier Atalanta Fugiens Emblem 36.jpeg | Lapis projectus est in terras, & in montibus exaltatus, & in aere habitat, & in flumine pascitur, id est, Mercurius. | 石被抛到地上，在山上被高举，住在空中，在河里得养，这就是汞。                 | 无处不在、普遍性、多种形态               |
| 37  | File:Michael Maier Atalanta Fugiens Emblem 37.jpeg | Tria sufficiunt ad magisterium, fumus albus, hoc est, aqua, leo viridis, id est, aes Hermetis, & aqua foetida.       | 三样就足以成就大业：白烟即水，绿狮即赫尔墨斯之铜，以及恶臭之水。             | 三要素、最小集合、配方                   |
| 38  | File:Michael Maier Atalanta Fugiens Emblem 38.jpeg | Rebis, ut Hermaphroditus, nascitur ex duobus montibus, Mercurii & Veneris.                                           | 二元体如雌雄同体者，生于墨丘利与维纳斯两座山。                               | 融合、混合、双亲                         |
| 39  | File:Michael Maier Atalanta Fugiens Emblem 39.jpeg | Oedypus Sphynge superata & trucidato Lajo patre matrem ducit in uxorem.                                              | 俄狄浦斯胜了斯芬克斯、杀了父亲拉伊俄斯，娶了母亲。                           | 谜题、推理、因果与代价                   |
| 40  | File:Michael Maier Atalanta Fugiens Emblem 40.jpeg | Ex duabus aquis, fac unam, & erit aqua sanctitatis.                                                                  | 两股水合成一股，便是圣水。                                                   | 合并、统一两条路线                       |
| 41  | File:Michael Maier Atalanta Fugiens Emblem 41.jpeg | Adonis ab apro occiditur, cui Venus accurrens tinxit rosas sanguine.                                                 | 阿多尼斯被野猪所杀，维纳斯奔来，用他的血染红玫瑰。                           | 牺牲、代价、转化                         |
| 42  | File:Michael Maier Atalanta Fugiens Emblem 42.jpeg | In Chymicis versanti Natura, Ratio, Experientia & lectio, sint Dux, scipio, perspicilia & lampas.                    | 行于化学者，当以自然为向导，理性为手杖，经验为眼镜，阅读为明灯。             | 方法、研究、阅读；多数读本的扉页         |
| 43  | File:Michael Maier Atalanta Fugiens Emblem 43.jpeg | Audi loquacem vulturem, qui neutiquam te decipit.                                                                    | 听那饶舌的秃鹫，它绝不骗你。                                                 | 倾听信号、信息来源、语言                 |
| 44  | File:Michael Maier Atalanta Fugiens Emblem 44.jpeg | Dolo Typhon Osyridem trucidat, artusque illius hinc inde dissipat, sed hos collegit Isis inclyta.                    | 提丰设计杀死奥西里斯，把他的肢体四散抛开，高贵的伊西斯把它们一一收回。       | 碎片重组、分片、恢复、重建               |
| 45  | File:Michael Maier Atalanta Fugiens Emblem 45.jpeg | Sol & ejus umbra perficiunt opus.                                                                                    | 太阳和它的影子成就这工作。                                                   | 光与影、对偶、残差                       |
| 46  | File:Michael Maier Atalanta Fugiens Emblem 46.jpeg | Aquilae duae, una ab ortu, altera ab occasu conveniunt.                                                              | 两只鹰，一只来自东方，一只来自西方，相会了。                                 | 汇合、通信、握手                         |
| 47  | File:Michael Maier Atalanta Fugiens Emblem 47.jpeg | Lupus ab Oriente & Canis ab Occidente venientes se invicem momorderunt.                                              | 东来的狼与西来的狗相互撕咬。                                                 | 对抗、竞争、冲突                         |
| 48  | File:Michael Maier Atalanta Fugiens Emblem 48.jpeg | Rex ab aquis potatis morbum, a medicis curatus sanitatem obtinet.                                                    | 国王喝水得病，经医生医治恢复健康。                                           | 缺陷与修复、诊断、复盘                   |
| 49  | File:Michael Maier Atalanta Fugiens Emblem 49.jpeg | Infans Philosophicus tres agnoscit patres, ut Orion.                                                                 | 哲人之婴认三位父亲，如俄里翁。                                               | 多源、集成、合作成果                     |
| 50  | File:Michael Maier Atalanta Fugiens Emblem 50.jpeg | Draco mulierem, & haec illum interimit, simulque sanguine perfunduntur.                                              | 龙杀死女人，女人也杀死龙，两者同浴于血。                                     | 终结、相互毁灭、终章与结语               |

第 11、12、25 幅的文件是整页扫描，含标题与箴言文字，竖幅；其余是只含画面的裁切图。Commons 上名为 `Michael Maier Atalanta Fugiens Emblem 11.jpeg` 的文件画的其实是第 25 幅，不要用。

**高清版**：Internet Archive 上 Getty 研究所的扫描本（`atalantafugiensh00maie`，500ppi，未上色），经 IIIF 按区域裁出画面，默认 1000px 宽，带刻版的边框。「来源」一列是 `plate.py` 的第一个参数，「区域」一列是 `--region` 的值。

| 幅  | 来源                              | 区域                     |
| --- | --------------------------------- | ------------------------ |
| 1   | `'ia:atalantafugiensh00maie$21'`  | `pct:3.7,12.6,73.9,53.0` |
| 2   | `'ia:atalantafugiensh00maie$25'`  | `pct:4.5,14.3,76.4,53.4` |
| 3   | `'ia:atalantafugiensh00maie$29'`  | `pct:7.7,14.4,75.8,51.7` |
| 4   | `'ia:atalantafugiensh00maie$33'`  | `pct:1.6,16.8,76.5,51.7` |
| 5   | `'ia:atalantafugiensh00maie$37'`  | `pct:3.1,16.9,80.6,50.6` |
| 6   | `'ia:atalantafugiensh00maie$41'`  | `pct:3.2,12.3,76.9,50.4` |
| 7   | `'ia:atalantafugiensh00maie$45'`  | `pct:5.1,10.8,77.3,51.5` |
| 8   | `'ia:atalantafugiensh00maie$49'`  | `pct:2.5,15.6,77.6,49.8` |
| 9   | `'ia:atalantafugiensh00maie$53'`  | `pct:3.5,15.1,73.6,53.1` |
| 10  | `'ia:atalantafugiensh00maie$57'`  | `pct:6.4,14.9,78.6,50.6` |
| 11  | `'ia:atalantafugiensh00maie$61'`  | `pct:7.3,12.9,74.9,53.3` |
| 12  | `'ia:atalantafugiensh00maie$65'`  | `pct:4.0,15.2,74.6,52.6` |
| 13  | `'ia:atalantafugiensh00maie$69'`  | `pct:5.5,17.6,73.9,51.1` |
| 14  | `'ia:atalantafugiensh00maie$73'`  | `pct:2.9,14.1,78.6,49.9` |
| 15  | `'ia:atalantafugiensh00maie$77'`  | `pct:5.6,12.8,75.0,48.5` |
| 16  | `'ia:atalantafugiensh00maie$81'`  | `pct:1.1,14.9,75.6,54.4` |
| 17  | `'ia:atalantafugiensh00maie$85'`  | `pct:5.7,16.0,74.2,53.5` |
| 18  | `'ia:atalantafugiensh00maie$89'`  | `pct:3.1,14.5,75.3,49.5` |
| 19  | `'ia:atalantafugiensh00maie$93'`  | `pct:2.9,12.6,76.4,50.6` |
| 20  | `'ia:atalantafugiensh00maie$97'`  | `pct:3.8,15.7,75.0,50.7` |
| 21  | `'ia:atalantafugiensh00maie$101'` | `pct:5.2,15.8,74.5,53.6` |
| 22  | `'ia:atalantafugiensh00maie$105'` | `pct:2.2,11.9,77.1,50.5` |
| 23  | `'ia:atalantafugiensh00maie$109'` | `pct:1.7,13.9,78.2,50.4` |
| 24  | `'ia:atalantafugiensh00maie$113'` | `pct:1.6,13.2,77.8,51.5` |
| 25  | `'ia:atalantafugiensh00maie$117'` | `pct:4.0,16.0,78.2,50.2` |
| 26  | `'ia:atalantafugiensh00maie$121'` | `pct:2.2,13.8,74.1,52.3` |
| 27  | `'ia:atalantafugiensh00maie$125'` | `pct:4.4,15.2,74.2,52.9` |
| 28  | `'ia:atalantafugiensh00maie$129'` | `pct:2.5,13.9,74.5,51.8` |
| 29  | `'ia:atalantafugiensh00maie$133'` | `pct:3.7,13.7,73.9,51.7` |
| 30  | `'ia:atalantafugiensh00maie$137'` | `pct:2.7,14.7,73.3,50.7` |
| 31  | `'ia:atalantafugiensh00maie$141'` | `pct:1.4,15.6,78.2,51.6` |
| 32  | `'ia:atalantafugiensh00maie$145'` | `pct:1.4,14.1,76.2,52.0` |
| 33  | `'ia:atalantafugiensh00maie$149'` | `pct:5.5,12.8,74.7,53.0` |
| 34  | `'ia:atalantafugiensh00maie$153'` | `pct:5.1,16.4,74.9,52.8` |
| 35  | `'ia:atalantafugiensh00maie$157'` | `pct:6.4,17.1,76.9,51.6` |
| 36  | `'ia:atalantafugiensh00maie$161'` | `pct:3.2,16.4,76.1,53.8` |
| 37  | `'ia:atalantafugiensh00maie$165'` | `pct:3.5,15.2,74.8,53.9` |
| 38  | `'ia:atalantafugiensh00maie$169'` | `pct:5.2,16.0,75.5,52.8` |
| 39  | `'ia:atalantafugiensh00maie$173'` | `pct:6.2,15.2,75.5,53.0` |
| 40  | `'ia:atalantafugiensh00maie$177'` | `pct:2.2,13.6,75.3,53.0` |
| 41  | `'ia:atalantafugiensh00maie$181'` | `pct:7.3,17.3,73.4,52.7` |
| 42  | `'ia:atalantafugiensh00maie$185'` | `pct:2.9,18.1,75.5,52.8` |
| 43  | `'ia:atalantafugiensh00maie$189'` | `pct:3.9,14.3,73.7,52.5` |
| 44  | `'ia:atalantafugiensh00maie$193'` | `pct:2.4,14.4,75.8,53.5` |
| 45  | `'ia:atalantafugiensh00maie$197'` | `pct:7.7,14.8,75.0,53.0` |
| 46  | `'ia:atalantafugiensh00maie$201'` | `pct:2.5,14.3,75.3,53.0` |
| 47  | `'ia:atalantafugiensh00maie$205'` | `pct:7.1,14.4,74.9,53.5` |
| 48  | `'ia:atalantafugiensh00maie$209'` | `pct:6.2,16.4,75.3,53.2` |
| 49  | `'ia:atalantafugiensh00maie$213'` | `pct:7.7,13.8,74.8,53.5` |
| 50  | `'ia:atalantafugiensh00maie$217'` | `pct:8.4,13.7,75.5,53.5` |
