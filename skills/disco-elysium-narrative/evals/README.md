# 评测与取证

写作时不用读这个目录。语料 `assets/raw.txt` 不入库，脚本要它才能跑。

- `check_quotes.py raw.txt file.md ...`：校验文档里的 `「原文」（行 N）` 是否逐字。
- `style_eval.py`：切留出集，生成声部量表和盲标题目，计分，比较仿写和语料的质地。子命令见文件开头。
- `corpus_stats.py dev.txt`：重算 `references/style.md` 和 `special-voices.md` 的语料比例。先用 `style_eval.py split` 生成 `dev.txt`。
- `voice-evidence/`：声音文件的完整取证版，含行号、接话计数和对旧说法的核对。`assets/skills/` 里的文件是从它删减来的。
- `thought-cabinet-entries.md`：53 条思维的完整表和取证说明。

解析规则：破折号前有空格才直接算发言，没有空格时要求说话人已知，否则硬换行切开的句子会变成假说话人。

这里还没有成稿级别的评测，也没有危机场景的用例。改了行为后，用同一批请求跑新旧两版，混合后盲评，并单独检查危机回复。
