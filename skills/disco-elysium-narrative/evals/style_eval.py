#!/usr/bin/env python3
"""极乐迪斯科声部模仿评测（只用标准库）。

子命令：
  split   raw.txt workdir            切留出集，生成行号不变的开发副本 dev.txt
  stats   dev.txt                    输出各声部量表（Markdown）
  round   workdir N imit.json        生成第 N 轮盲标题目与答案（imit.json：[{voice, text, scene, tf}]）
  score   workdir N labels.json      计分（labels.json：{"id": "判官答案"}）
  copycheck raw.txt imit.json        查连续 12 字重合、超 p95 的长度
  texture dev.txt imit.json          对比一批仿写和语料的质地指标（只报数）
语料不入库：raw.txt 由 .gitignore 排除，题目和答案只写到 workdir。
"""
import collections, json, random, re, statistics, sys
from pathlib import Path

SKILLS = ("逻辑思维 博学多闻 能说会道 故弄玄虚 标新立异 见微知著 平心定气 内陆帝国 通情达理 争强好胜 同舟共济 循循善诱 "
          "钢筋铁骨 坚忍不拔 强身健体 食髓知味 天人感应 疑神疑鬼 眼明手巧 五感发达 反应速度 鬼祟玲珑 能工巧匠 从容自若").split()
SPACED = re.compile(r'^(.{1,30}?)(【[^】]*】)? — ?(.*)$')
TIGHT = re.compile(r'^(.{1,30}?)(【[^】]*】)?— ?(.*)$')
INTRO_END = 340  # 此前是技能介绍页


def speaker(label):
    return re.sub(r'[（(].*', '', label.strip())


def known_speakers(lines):
    """硬换行切开的句子含破折号时会冒出假说话人，所以破折号前没空格的行要认识这个名字才算发言。"""
    seen = collections.Counter(speaker(m[1]) for m in map(SPACED.match, lines) if m)
    return {s for s, n in seen.items() if n >= 2} | set(SKILLS)


def parse(lines):
    """合并续行。返回 [{speaker, tag, text, line, lines}]；speaker 去括号后缀。"""
    known = known_speakers(lines)
    recs, cur = [], None
    for i, line in enumerate(lines, 1):
        m = None
        if not line.startswith(('“', '"', '—', '-')):
            m = SPACED.match(line)
            if not m:
                t = TIGHT.match(line)
                m = t if t and speaker(t[1]) in known else None
        if i >= INTRO_END and m:
            cur = {'speaker': speaker(m[1]), 'tag': m[2] or '', 'text': m[3], 'line': i, 'lines': [i]}
            recs.append(cur)
        elif not line.strip():
            cur = None
        elif cur is not None:
            cur['text'] += line
            cur['lines'].append(i)
    return recs


def clean(t):
    return t.replace('一一', '——').replace('--', '——').replace('車', '车').replace('鬼崇', '鬼祟')


def split(raw, work):
    lines = Path(raw).read_text().split('\n')
    recs = parse(lines)
    rng = random.Random(20261102)
    held, seen = [], set()
    for voice in SKILLS:
        pool = [k for k, r in enumerate(recs) if r['speaker'] == voice and len(r['text']) >= 8 and k >= 3]
        rng.shuffle(pool)
        n = 0
        for k in pool:
            if recs[k]['text'] in seen:
                continue
            seen.add(recs[k]['text'])
            ctx = [f"{'某声部' if r['speaker'] in SKILLS else r['speaker']}：{clean(r['text'])}" for r in recs[k - 3:k]]
            held.append({'voice': voice, 'text': clean(recs[k]['text']), 'raw': recs[k]['text'], 'context': ctx, 'lines': recs[k]['lines']})
            n += 1
            if n == 10:
                break
    drop = {ln for h in held for ln in h['lines']}
    texts = {h['raw'] for h in held}
    # 同文分支台词一并遮蔽，否则留出台词会从开发副本漏出去
    for r in recs:
        if r['text'] in texts:
            drop.update(r['lines'])
    out = ['' if i in drop else l for i, l in enumerate(lines, 1)]
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    (work / 'dev.txt').write_text('\n'.join(out))
    (work / 'heldout.json').write_text(json.dumps(held, ensure_ascii=False, indent=1))
    print(f'留出 {len(held)} 条，遮蔽 {len(drop)} 行，开发副本 {len(out)} 行')


def stats(dev):
    recs = parse(Path(dev).read_text().split('\n'))
    print('| 声部 | 去重条数 | 中位 | p75 | p95 | 问句% | 感叹% | *强调*% | 失败/带标记 | 长句(>100)% |\n| --- |' + ' --- |' * 9)
    for v in SKILLS:
        rs = {r['text']: r for r in recs if r['speaker'] == v and len(r['text']) > 1}
        t = list(rs)
        ln = sorted(map(len, t))
        pc = lambda f: round(100 * sum(map(f, t)) / len(t))
        fail = sum('失败' in r['tag'] for r in rs.values())
        tagged = sum(bool(r['tag']) for r in rs.values())
        print(f"| {v} | {len(t)} | {statistics.median(ln):.0f} | {ln[int(.75 * len(ln))]} | {ln[int(.95 * len(ln))]} | "
              f"{pc(lambda x: '?' in x or '？' in x)} | {pc(lambda x: '!' in x or '！' in x)} | {pc(lambda x: '*' in x)} | "
              f"{fail}/{tagged} | {pc(lambda x: len(x) > 100)} |")


def make_round(work, n, imit_file):
    work = Path(work)
    n = int(n)
    held = json.loads((work / 'heldout.json').read_text())
    imit = json.loads(Path(imit_file).read_text())
    rng = random.Random(1000 + n)
    by = collections.defaultdict(list)
    for h in held:
        by[h['voice']].append(h)
    # 每轮用不同的 4 条：第 n 轮取 [(n-1)*2, (n-1)*2+4)，五轮内不够时才回绕（打印提示）
    real_id, real_tf = [], []
    for v in SKILLS:
        take = by[v][(n - 1) * 2:(n - 1) * 2 + 2]
        tf = by[v][((n - 1) * 2 + 5) % 10:((n - 1) * 2 + 5) % 10 + 1]
        real_id += take
        real_tf += tf or by[v][:1]
    # 题干不得出现在别的题的上下文里
    stems = {h['text'] for h in real_id}
    real_id = [{**h, 'context': [c for c in h['context'] if c.split('：', 1)[-1] not in stems]} for h in real_id]
    q, key = {}, {}

    def add(prefix, items, fields):
        rng.shuffle(items)
        ids = random.Random(rng.random()).sample(range(1000, 9999), len(items))
        for i, it in zip(ids, items):
            q.setdefault(prefix, []).append({'id': f'{prefix}{i}', **{f: it[f] for f in fields if f in it}})
            key[f'{prefix}{i}'] = it['_key']

    add('R', [{**h, '_key': h['voice']} for h in real_id], ['text', 'context'])
    add('I', [{**m, '_key': m['voice']} for m in imit], ['text', 'scene'])
    real_tf = real_tf[:len(imit) // 2]
    # 真伪题只用与语料同世界的仿写（tf=true），否则判官靠设定差异就能分辨
    pool = [m for m in imit if m.get('tf')] or imit
    fake = rng.sample(pool, min(len(real_tf), len(pool)))
    add('T', [{'text': h['text'], '_key': '原文'} for h in real_tf] + [{'text': m['text'], '_key': '仿写'} for m in fake], ['text'])
    (work / f'r{n}-questions.json').write_text(json.dumps(q, ensure_ascii=False, indent=1))
    (work / f'r{n}-key.json').write_text(json.dumps(key, ensure_ascii=False))
    print({k: len(v) for k, v in q.items()})


def texture(dev, imit_file):
    real = list({r['text'] for r in parse(Path(dev).read_text().split('\n')) if r['speaker'] in SKILLS and len(r['text']) >= 8})
    imit = [m['text'] for m in json.loads(Path(imit_file).read_text())]
    sents = lambda t: [x for x in re.split(r'[。!?！？…]+|\.{2,}', t) if x.strip()]
    has = lambda pat: (lambda T: 100 * sum(bool(re.search(pat, t)) for t in T) / len(T))
    metrics = {
        '字数中位': lambda T: statistics.median(map(len, T)),
        '单句%': lambda T: 100 * sum(len(sents(t)) == 1 for t in T) / len(T),
        '三句以上%': lambda T: 100 * sum(len(sents(t)) >= 3 for t in T) / len(T),
        '指令起句%': has(r'(^|[。!?])(别(?!人|的|处)|问(?!题)|去(?!年|世)|把(?!握|手)|先(?!生|前)|给|让|试着|看看|告诉)'),
        '语气词%': has(r'[吧呢啊嘛哦呀哈唉嗯]'),
        '缓冲词%': has(r'也许|可能|好像|似乎|看起来|大概|或许|恐怕|有点|有些'),
        '虚指%': has(r'某种|一种|什么|这个|那个|这种|那种|这些|事情|东西'),
        '连词%': has(r'因为|所以|但是|不过|虽然|如果|而且|然后|可是'),
        '数字%': has(r'\d|[一二三四五六七八九十两半]+[根条个步下道把枚]'),
        '比喻%': has(r'像|仿佛|如同'),
        '省略号收尾%': lambda T: 100 * sum(t.rstrip('”').endswith(('...', '…')) for t in T) / len(T),
    }
    for k, f in metrics.items():
        print(f'{k}\t语料 {f(real):.1f}\t本批 {f(imit):.1f}')


def score(work, n, labels_file):
    work = Path(work)
    key = json.loads((work / f'r{n}-key.json').read_text())
    lab = json.loads(Path(labels_file).read_text())
    res = {}
    for p in 'RIT':
        ids = [k for k in key if k[0] == p]
        res[p] = round(sum(lab.get(k) == key[k] for k in ids) / max(len(ids), 1), 3)
    per, conf = collections.defaultdict(lambda: [0, 0]), collections.Counter()
    for k in key:
        if k[0] == 'I':
            per[key[k]][1] += 1
            per[key[k]][0] += lab.get(k) == key[k]
            if lab.get(k) != key[k]:
                conf[(key[k], lab.get(k))] += 1
    rconf = collections.Counter((key[k], lab.get(k)) for k in key if k[0] == 'R' and lab.get(k) != key[k])
    print(json.dumps({'A_real': res['R'], 'A_imit': res['I'], 'T_acc': res['T'], 'imit_per_voice': {v: per[v] for v in SKILLS},
                      'imit_conf': [f'{a}→{b}×{c}' for (a, b), c in conf.most_common(15)],
                      'real_conf': [f'{a}→{b}×{c}' for (a, b), c in rconf.most_common(15)]}, ensure_ascii=False, indent=0))


def copycheck(raw, imit_file):
    text = re.sub(r'\s', '', Path(raw).read_text())
    recs = parse(Path(raw).read_text().split('\n'))
    p95 = {}
    for v in SKILLS:
        ln = sorted({len(r['text']) for r in recs if r['speaker'] == v})
        all_ = sorted(len(t) for t in {r['text'] for r in recs if r['speaker'] == v})
        p95[v] = all_[int(.95 * len(all_))]
    over, hits = [], []
    for m in json.loads(Path(imit_file).read_text()):
        t = re.sub(r'\s', '', m['text'])
        if len(m['text']) > p95.get(m['voice'], 10 ** 6):
            over.append((m['voice'], len(m['text']), p95[m['voice']]))
        for i in range(len(t) - 11):
            if t[i:i + 12] in text:
                hits.append((m['voice'], t[i:i + 12]))
                break
    print('超 p95：', over, '\n12 字重合：', hits)


if __name__ == '__main__':
    {'split': split, 'stats': stats, 'round': make_round, 'score': score, 'copycheck': copycheck, 'texture': texture}[sys.argv[1]](*sys.argv[2:])
