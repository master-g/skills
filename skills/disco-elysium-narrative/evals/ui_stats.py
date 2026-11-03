#!/usr/bin/env python3
"""统计语料里的游戏界面行：道具卡、属性行、任务行、场景抬头、解锁思维。用法：ui_stats.py raw.txt

这些行不走「说话人 — 文本」格式，style_eval.parse() 会把它们并进上一条发言，所以这里单独逐行识别。
道具描述从「获得道具」下一行起，合并续行，直到空行、发言行或下一条界面行。
"""
import collections, re, statistics as st, sys
from pathlib import Path

from style_eval import INTRO_END, SKILLS, SPACED, TIGHT, known_speakers, speaker

KINDS = {
    'item': re.compile(r'^获得道具[:：]\s*(.+)$'),
    'item_lost': re.compile(r'^失去道具[:：]\s*(.+)$'),
    'task_new': re.compile(r'^新任务[:：]\s*(.+)$'),
    'task_done': re.compile(r'^任务完成[:：]\s*(.+)$'),
    'task_hidden': re.compile(r'^隐藏任务完成[:：]\s*(.+)$'),
    'thought': re.compile(r'^解锁思维[:：]\s*(.+)$'),
    'header': re.compile(r'^Day\s?(\d+)\s+(\S+)\s+(.+)$'),
    'weekday': re.compile(r'^周[一二三四五六日]\s*$'),
    'modifier': re.compile(r'^([+-])\s?(\d+)\s?([^:：]{2,6})[:：]\s*(.*)$'),
}
PRICE = re.compile(r'\s*价格\s*✣\s*[\d.]+')
VERB = re.compile(r'^(找|走访|检查|追踪|打开|阅读|帮|确定|把|跟|让|向|替|归还|上报|拿到|执行|打给|洗掉|买下|质问|在|处理|询问|调查|解决|'
                  r'成为|组建|回转|与|返回|前往|设法|查看|查询|唱|探索|认清|追|为|堵|拿|返程|对峙|金不在场)')
TURN = re.compile(r'不过|但是?|可是|然而|只是|可惜|曾经|现在')


def pc(a, b):
    return f'{100 * a / b:.1f}%' if b else '—'


def q(xs):
    xs = sorted(xs)
    if not xs:
        return '—'
    return f'中位 {st.median(xs):g}，p25 {xs[len(xs) // 4]}，p75 {xs[3 * len(xs) // 4]}，最长 {xs[-1]}'


def plain(t):
    return re.sub(r'[\s*]', '', t)


def sentences(t):
    return [x for x in re.split(r'(?<=[。！？!?])|\.{3,}|…+', t) if x and x.strip()]


def classify(lines):
    """逐行标类型：界面行 kind、发言 'speech'（带说话人）、空行 'blank'、其余 'text'。"""
    known = known_speakers(lines)
    out = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        kind, m = None, None
        for k, p in KINDS.items():
            m = p.match(s)
            if m:
                kind = k
                break
        if kind:
            out.append((i, kind, m, s))
            continue
        if not s:
            out.append((i, 'blank', None, s))
            continue
        sp = None
        if not s.startswith(('“', '"', '—', '-')):
            sm = SPACED.match(s) or (lambda t: t if t and speaker(t[1]) in known else None)(TIGHT.match(s))
            sp = speaker(sm[1]) if sm else None
        out.append((i, 'speech', sp, s) if sp else (i, 'text', None, s))
    return out


def who(sp):
    return '技能' if sp in SKILLS else '你' if sp == '你' else '金' if sp.startswith('金') else '其他'


def main(path):
    lines = Path(path).read_text().split('\n')
    rows = [r for r in classify(lines) if r[0] >= INTRO_END]
    by = collections.defaultdict(list)
    for r in rows:
        by[r[1]].append(r)

    print('# 界面行统计\n')
    print(f'语料 {len(lines)} 行，第 {INTRO_END} 行之后计数。界面行不是发言，不进 style.md 的分母。\n')
    print('| 类型 | 条数 | 去重名称 |')
    print('| --- | --- | --- |')
    for k, label in [('item', '获得道具'), ('item_lost', '失去道具'), ('modifier', '属性行'), ('task_new', '新任务'),
                     ('task_done', '任务完成'), ('task_hidden', '隐藏任务完成'), ('thought', '解锁思维'),
                     ('header', 'Day 抬头'), ('weekday', '周几')]:
        g = {'modifier': 4, 'header': 3}.get(k, 1)
        names = {plain(PRICE.sub('', r[2][g] if r[2] and r[2].groups() else r[3])) for r in by[k]}
        print(f'| {label} | {len(by[k])} | {len(names)} |')

    # 道具卡
    items = []
    for idx, r in enumerate(rows):
        if r[1] != 'item':
            continue
        name = r[2][1]
        card = {'line': r[0], 'name': plain(PRICE.sub('', name)), 'price': bool(PRICE.search(name)),
                'desc': '', 'mods': [], 'next': None}
        for nr in rows[idx + 1: idx + 12]:
            if nr[1] == 'text' and not card['mods']:
                card['desc'] += nr[3]
            elif nr[1] == 'modifier':
                card['mods'].append(nr[2])
            else:
                card['next'] = nr[1] if nr[1] != 'speech' else who(nr[2])
                break
        items.append(card)
    with_desc = [c for c in items if plain(c['desc'])]
    descs = [plain(c['desc']) for c in with_desc]
    mods_all = [m for c in items for m in c['mods']]
    print('\n## 道具卡\n')
    print(f'- 名称字数：{q([len(c["name"]) for c in items])}；带价格 {pc(sum(c["price"] for c in items), len(items))}')
    print(f'- 有描述 {len(with_desc)}/{len(items)}（{pc(len(with_desc), len(items))}）；没有描述的，下一行多半直接是对话')
    print(f'- 描述字数：{q([len(d) for d in descs])}')
    print(f'- 描述句数：{q([len(sentences(c["desc"])) for c in with_desc])}')
    print(f'- 描述含“你” {pc(sum("你" in d for d in descs), len(descs))}；以“这”起句 {pc(sum(d.startswith("这") for d in descs), len(descs))}；'
          f'含转折或今昔词（不过、但、曾经、现在……） {pc(sum(bool(TURN.search(d)) for d in descs), len(descs))}')
    print(f'- 带属性行的道具 {sum(bool(c["mods"]) for c in items)}/{len(items)}；每张 {collections.Counter(len(c["mods"]) for c in items if c["mods"])}')
    nxt = collections.Counter(c['next'] for c in items)
    print(f'- 道具卡之后的下一行：{dict(nxt.most_common())}')

    # 属性行
    mods = by['modifier']
    in_item = len(mods_all)
    labels = [plain(m[2][4]) for m in mods]
    skills = collections.Counter(m[2][3].strip() for m in mods)
    print('\n## 属性行\n')
    print(f'- 共 {len(mods)} 行，挂在道具卡上的 {in_item}（{pc(in_item, len(mods))}）；加号 {sum(m[2][1] == "+" for m in mods)}，减号 {sum(m[2][1] == "-" for m in mods)}；'
          f'数值 {dict(collections.Counter(m[2][2] for m in mods))}')
    print(f'- 技能名是 24 技能之一 {pc(sum(s in SKILLS for s in skills.elements()), len(mods))}；最常见 {skills.most_common(8)}')
    print(f'- 短评字数：{q([len(l) for l in labels])}；以句号收尾 {pc(sum(l.endswith("。") for l in labels), len(labels))}；'
          f'带叹号 {pc(sum("!" in l or "！" in l for l in labels), len(labels))}；带星号强调 {pc(sum("*" in m[2][4] for m in mods), len(mods))}')
    pos = {r[0]: k for k, r in enumerate(rows)}
    after_desc = 0
    for m in mods:
        k = pos[m[0]] - 1
        while k >= 0 and rows[k][1] == 'modifier':
            k -= 1
        after_desc += rows[k][1] in ('text', 'item')
    print(f'- 紧跟在无标签描述或道具名之后（中间不隔发言、任务、思维行）{after_desc}/{len(mods)}；不挂「获得道具」的 {len(mods) - in_item} 行逐条看过，是省了前缀的衣物卡')
    pairs = [c for c in items if any(m[1] == '+' for m in c['mods']) and any(m[1] == '-' for m in c['mods'])]
    print(f'- 同一张卡一加一减 {len(pairs)} 张')

    # 任务行
    new, done = by['task_new'], by['task_done']
    names = [plain(r[2][1]) for r in new]
    print('\n## 任务行\n')
    print(f'- 新任务名字数：{q([len(n) for n in names])}')
    print(f'- 以问号收尾 {pc(sum(n.endswith(("?", "？")) for n in names), len(names))}；含专名或人名（含“·”或在他处作说话人）'
          f'{pc(sum("·" in n or any(sp and sp in n for sp in SPEAKERS) for n in names), len(names))}')
    heads = collections.Counter(n[:2] for n in names)
    print(f'- 前两字最常见：{heads.most_common(12)}')
    shape = collections.Counter('问句' if n.endswith(('?', '？')) else '祈使' if VERB.match(n) else '名词短语' for n in names)
    print(f'- 句型（按起首动词粗分）：{dict(shape.most_common())}')
    done_names = {plain(r[2][1]) for r in done}
    matched = [n for n in names if n in done_names]
    print(f'- 新任务后来有同名「任务完成」的 {len(set(matched))}/{len(set(names))}（语料按分支排列，只作粗计）')

    def ctx(target, step):
        c = collections.Counter()
        pos = {r[0]: k for k, r in enumerate(rows)}
        for r in target:
            k = pos[r[0]] + step
            while 0 <= k < len(rows) and rows[k][1] in ('blank',):
                k += step
            if 0 <= k < len(rows):
                nr = rows[k]
                c[who(nr[2]) if nr[1] == 'speech' else nr[1]] += 1
        return dict(c.most_common(6))

    print(f'- 新任务的前一行：{ctx(new, -1)}')
    print(f'- 新任务的后一行：{ctx(new, 1)}')
    accept = sum('接受任务' in rows[k - 1][3] for k, r in enumerate(rows) if r[1] == 'task_new' and k)
    print(f'- 前一行含“接受任务” {accept}')
    print(f'- 任务完成的前一行：{ctx(done, -1)}')

    # 场景抬头
    heads_ = by['header']
    times = collections.Counter(r[2][2] for r in heads_)
    locs = [plain(r[2][3]) for r in heads_]
    print('\n## 场景抬头\n')
    print(f'- 天数 {dict(collections.Counter(r[2][1] for r in heads_))}；时刻前五 {times.most_common(5)}')
    print(f'- 地点字数：{q([len(l) for l in locs])}；含空格分级（区域 + 具体处） {pc(sum(" " in r[2][3].strip() for r in heads_), len(heads_))}')
    pos = {r[0]: k for k, r in enumerate(rows)}
    first, runs, runlen = collections.Counter(), [], []
    for r in heads_:
        k, n, chars = pos[r[0]] + 1, 0, []
        while k < len(rows) and rows[k][1] in ('text', 'blank'):
            if rows[k][1] == 'text':
                n += 1
                chars.append(len(plain(rows[k][3])))
            k += 1
        runs.append(n)
        runlen += chars
        if k < len(rows):
            first[who(rows[k][2]) if rows[k][1] == 'speech' else rows[k][1]] += 1
    print(f'- 抬头后先出现无标签短行的 {pc(sum(n > 0 for n in runs), len(runs))}，行数 {q([n for n in runs if n])}，每行字数 {q(runlen)}')
    print(f'- 无标签短行之后第一个标签：{dict(first.most_common(6))}')

    # 解锁思维
    th = by['thought']
    print('\n## 解锁思维\n')
    print(f'- 名称字数：{q([len(plain(r[2][1])) for r in th])}')
    print(f'- 前一行：{ctx(th, -1)}；后一行：{ctx(th, 1)}')


SPEAKERS = set()

if __name__ == '__main__':
    _lines = Path(sys.argv[1]).read_text().split('\n')
    SPEAKERS = {s for s in known_speakers(_lines) if len(s) >= 2 and s not in SKILLS and s != '你'}
    main(sys.argv[1])
