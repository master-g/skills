#!/usr/bin/env python3
"""重算 references/style.md 和 special-voices.md 引用的语料比例。用法：corpus_stats.py dev.txt"""
import collections, re, statistics as st, sys
from pathlib import Path

from style_eval import SKILLS, parse

QM, ELL, DASH, BANG = r'[?？]', r'\.\.\.|…', r'—|--|一一', r'[!！]'


def cat(s):
    return 'S' if s in SKILLS else 'Y' if s == '你' else 'K' if s.startswith('金') else 'N'


def pc(a, b):
    return round(100 * a / b, 1) if b else 0


def form(t):
    if '“' not in t:
        return '无引语'
    if not t.startswith('“'):
        return '动作开头'
    end = t.find('”')
    return '只有引语' if end < 0 or not t[end + 1:].strip() else '引语开头'


def sentences(t):
    return [x for x in re.split(r'[。!?！？…]+|\.{2,}', t) if x.strip()]


def has(pat, texts):
    return pc(sum(bool(re.search(pat, t)) for t in texts), len(texts))


def main(path):
    recs = parse(Path(path).read_text().split('\n'))
    uniq = list({r['text']: r for r in recs}.values())
    by = collections.defaultdict(list)
    for r in uniq:
        by[cat(r['speaker'])].append(r['text'])
    print('发言', len(recs), '去重', len(uniq), {k: len(v) for k, v in by.items()})

    count, unquoted = collections.Counter(), collections.Counter()
    for r in recs:
        count[r['speaker']] += 1
        unquoted[r['speaker']] += '“' not in r['text']
    narr = [s for s in count if unquoted[s] / count[s] >= .7 and count[s] >= 2]
    print('说话人', len(count), '只出现一次', sum(v == 1 for v in count.values()), '七成以上无引语(至少两条)', len(narr),
          '这些人的条数中位', st.median(count[s] for s in narr))

    for k in 'NK':
        f = collections.Counter(map(form, by[k]))
        print('形态', k, len(by[k]), {a: pc(b, len(by[k])) for a, b in f.items()})

    narration = [t for k in 'NK' for t in by[k] if '“' not in t]
    parts = [x for t in narration for x in sentences(t)]
    print('无引语', len(narration), '含你', has('你', narration), '你开头', pc(sum(t[0] == '你' for t in narration if t), len(narration)),
          '他她开头', pc(sum(t[:1] in ('他', '她') for t in narration), len(narration)), '了', has('了', narration), '着', has('着', narration),
          '中位', st.median(map(len, narration)), '单句中位', st.median(map(len, parts)), '单句p95', sorted(map(len, parts))[int(.95 * len(parts))])

    for name, pat in (('*强调*', r'\*'), ('省略号', ELL), ('破折号', DASH), ('感叹号', BANG), ('问号', QM)):
        print(name, {k: has(pat, by[k]) for k in 'SYKN'})

    seq = [cat(r['speaker']) for r in recs]
    print('占比', {k: pc(seq.count(k), len(seq)) for k in 'SYKN'})
    trans = collections.defaultdict(collections.Counter)
    for a, b in zip(seq, seq[1:]):
        trans[a][b] += 1
    for a in 'SYNK':
        print('下一条', a, {b: pc(v, sum(trans[a].values())) for b, v in trans[a].most_common()})
    prev = collections.Counter(a for a, b in zip(seq, seq[1:]) if b == 'K')
    print('金的前一条', {a: pc(v, sum(prev.values())) for a, v in prev.most_common()})
    tri = collections.Counter(''.join(seq[i:i + 3]) for i in range(len(seq) - 2))
    print('三元', {k: pc(v, len(seq) - 2) for k, v in tri.most_common(8)})
    runs, n = [], 0
    for x in seq:
        if x == 'S':
            n += 1
        elif n:
            runs.append(n)
            n = 0
    print('技能连发', {a: pc(b, len(runs)) for a, b in sorted(collections.Counter(min(x, 3) for x in runs).items())})

    skill = list({r['text']: r for r in recs if r['speaker'] in SKILLS}.values())
    tagged = [r for r in skill if r['tag']]
    fails = [r['text'] for r in tagged if '失败' in r['tag']]
    print('失败', len(fails), '/', len(tagged), pc(len(fails), len(tagged)), '中位', st.median(map(len, fails)),
          '成功中位', st.median(len(r['text']) for r in tagged if r['tag'] == '【成功】'), '15字内', pc(sum(len(t) <= 15 for t in fails), len(fails)))
    print('技能中位', st.median(map(len, by['S'])), '句数中位', st.median(len(sentences(t)) for t in by['S']),
          '单句中位', st.median(len(x) for t in by['S'] for x in sentences(t)))
    for name in ('金·曷城', '古老的爬虫脑', '边缘系统', '坤诺', '爱凡客', '艾弗拉特', '联盟战舰弓箭手号', '史蒂文', '雷内', '卡拉洁', '乔伊斯', '吊人'):
        texts = list(dict.fromkeys(r['text'] for r in recs if r['speaker'].startswith(name)))
        print(name, len(texts), '中位', st.median(map(len, texts)), '问', has(QM, texts), '省略', has(ELL, texts), '叹', has(BANG, texts), '星', has(r'\*', texts))


if __name__ == '__main__':
    main(sys.argv[1])
