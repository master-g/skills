#!/usr/bin/env python3
"""校验技能文档里的母本短引。用法：check_quotes.py corpus.txt file.md ...
引文写作 「原文」（行 123），原文须是该行起始那条发言（合并续行后）的连续子串，且不超过 40 字。"""
import re, sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text().split('\n')
pat = re.compile(r'「([^」\n]+)」[（(]行 ?(\d+)[)）]')
bad = total = 0
per_file = {}


def record(n):
    """取行 n 所在发言，含前后续行（硬换行约 36 字，向前后各看 8 行）。"""
    return re.sub(r'\s', '', ''.join(lines[max(0, n - 9):n + 8]))


for f in sys.argv[2:]:
    q = pat.findall(Path(f).read_text())
    per_file[f] = len(q)
    for text, n in q:
        total += 1
        n = int(n)
        if len(text) > 40:
            bad += 1
            print(f'超长 {f}:{n} {len(text)}字 {text[:20]}')
        if re.sub(r'\s', '', text) not in record(n):
            bad += 1
            print(f'不符 {f}:{n} {text}')
print(f'共 {total} 条，问题 {bad} 条')
print({Path(k).name: v for k, v in per_file.items()})
sys.exit(1 if bad else 0)
