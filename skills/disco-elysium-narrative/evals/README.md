# 评测与取证

写作时不用读这个目录。写作时用的脚本在 `scripts/`：`draw.py` 抽写作约束，`draft_check.py` 在交稿前检查成稿，两者只用标准库，不读语料。本目录的脚本要语料 `assets/raw.txt` 才能跑，它不入库。

- `check_quotes.py raw.txt file.md ...`：校验文档里的 `「原文」（行 N）` 是否逐字。
- `style_eval.py`：切留出集，生成声部量表和盲标题目，计分，比较仿写和语料的质地。子命令见文件开头。
- `corpus_stats.py dev.txt`：重算 `references/style.md` 和 `special-voices.md` 的语料比例。先用 `style_eval.py split` 生成 `dev.txt`。
- `ui_stats.py raw.txt`：统计任务行、道具卡与属性行、场景抬头、解锁思维，重算 `references/game-ui.md` 的数字。这些行不走发言格式，`parse()` 会把它们并进上一条发言。
- `voice-evidence/`：声音文件的完整取证版，含行号、接话计数和对旧说法的核对。`assets/skills/` 里的文件是从它删减来的。
- `style-evidence.md`：风格总论的取证版，含分母、完整分布表和从写作版删掉的引文。
- `thought-cabinet-entries.md`：53 条思维的完整表和取证说明。
- `cases.md`：成稿复测用的请求、判据和盲评流程。

解析规则：破折号前有空格才直接算发言，没有空格时要求说话人已知，否则硬换行切开的句子会变成假说话人。

## 评测时用 `scripts/` 的两个脚本

在技能根目录运行，测试是 `python3 scripts/test_draft_check.py`、`python3 scripts/test_draw.py`。

- `scripts/draft_check.py 成稿.md ...`：每篇一段报告。门槛是技能占比、单句、祈使开头、连词或语气词、方括号行，危机回复改查有没有提技能和规则、有没有界面行；技能台词不到 8 条的比例项报「样本太少，不判」。出场、失败、最后一行、思维阁开口、任务行、机构腔解答、派活收尾、常见道具只报不判。有门槛未通过时退出码 1。
- `--json`：每篇一行 JSON，供脚本汇总，键见文件开头。
- `--across`：同一版技能写出的多篇一起喂进去，打印技能出场篇数和没出场的技能、每篇的失败条数和技能、思维阁问题与解答的第一句、每篇最后一行的类型、在一半以上篇目的技能台词里重复的 4 字以上片段，以及全部技能台词合计的质地。危机回复不计入分母。
- 质地四项的判定照抄 `style_eval.py texture`。用同一组技能台词喂 `texture` 得到的「本批」单句%、指令起句%与它相同，连词或语气词是语气词%和连词%两个判定的并集；`test_draft_check.py` 会比对两边。
- `scripts/draw.py [--seed N]`：按语料占比抽思维阁五项、收尾、三个候选技能和一种失败形态。评测记下种子，就能复现写作的 agent 拿到的约束。
