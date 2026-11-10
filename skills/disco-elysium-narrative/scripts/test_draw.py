#!/usr/bin/env python3
"""draw.py 的测试。用法：python3 test_draw.py"""
import collections, random, re, subprocess, sys
from pathlib import Path

from draw import NO_FAILURE, TABLE, draw
from draft_check import SKILLS

HERE = Path(__file__).resolve().parent
REFS = HERE.parent / 'references'
CABINET_TABLES = ('名字形状', '问题开口', '转折', '解答开口')


def cli(*args):
    return subprocess.run([sys.executable, str(HERE / 'draw.py'), *args], capture_output=True, text=True, check=True).stdout


def test_seed_reproducible():
    assert cli('--seed', '7') == cli('--seed', '7')
    assert len({cli('--seed', str(s)) for s in range(1, 6)}) > 1
    out = cli('--seed', '7')
    assert out.startswith('种子 7') and '先看这三个在场景里有没有戏：' in out and '写就写这一种' in out, out


def test_distribution():
    rng, n = random.Random(0), 1000
    picks = [draw(rng) for _ in range(n)]
    for group, rows in TABLE.items():
        total = sum(w for _, w, _ in rows)
        got = collections.Counter(p[group][0] for p in picks)
        for name, w, _ in rows:
            assert abs(got[name] / n - w / total) < 0.05, (group, name, got[name], w / total)
    seen = collections.Counter(s for p in picks for s in p['候选技能'])
    assert all(len(set(p['候选技能'])) == 3 for p in picks)
    assert all(abs(seen[s] / n - 3 / 24) < 0.05 for s in SKILLS), seen


def test_names_match_references():
    cabinet = (REFS / 'thought-cabinet.md').read_text()
    for group in CABINET_TABLES:
        assert sum(w for _, w, _ in TABLE[group]) == 53, group
        for name, w, how in TABLE[group]:
            row = re.search(rf'^\|\s*{re.escape(name)}\s*\|\s*{w}（.*$', cabinet, re.M)
            assert row, (group, name, w)
            assert [c.strip() for c in row[0].strip('|').split('|')][2] == how, (group, name, '简述与表格不一致')
    assert sum(w for _, w, _ in TABLE['安慰度']) == 53
    for name, w, _ in TABLE['安慰度']:
        assert f'{name} {w}（' in cabinet, name
    style = (REFS / 'style.md').read_text()
    for name, w, _ in TABLE['失败']:
        if name == NO_FAILURE:
            continue
        assert re.search(rf'{name}\s*（?{w}%', style), name


def main():
    for name, f in list(globals().items()):
        if name.startswith('test_'):
            f()
    print('test_draw: ok')


if __name__ == '__main__':
    main()
