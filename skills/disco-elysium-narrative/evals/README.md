# 评测与取证

写作时不用读这个目录。语料 `assets/raw.txt` 不入库，脚本要它才能跑。

- `check_quotes.py raw.txt file.md ...`：校验文档里的 `「原文」（行 N）` 是否逐字。
- `style_eval.py`：切留出集，生成声部量表和盲标题目，计分，比较仿写和语料的质地。子命令见文件开头。
- `corpus_stats.py dev.txt`：重算 `references/style.md` 和 `special-voices.md` 的语料比例。先用 `style_eval.py split` 生成 `dev.txt`。
- `ui_stats.py raw.txt`：统计任务行、道具卡与属性行、场景抬头、解锁思维，重算 `references/game-ui.md` 的数字。这些行不走发言格式，`parse()` 会把它们并进上一条发言。
- `voice-evidence/`：声音文件的完整取证版，含行号、接话计数和对旧说法的核对。`assets/skills/` 里的文件是从它删减来的。
- `thought-cabinet-entries.md`：53 条思维的完整表和取证说明。

解析规则：破折号前有空格才直接算发言，没有空格时要求说话人已知，否则硬换行切开的句子会变成假说话人。

- `draft_check.py draft.md ...`：成稿的机械检查，包括有没有思维阁、解答是否机构腔开口或派活收尾、常见道具、任务行条数、方括号结尾、危机回复有没有提技能和规则或写界面行。`test_draft_check.py` 是它的夹具测试。
- `cases.md`：成稿复测用的请求、判据和盲评流程。
