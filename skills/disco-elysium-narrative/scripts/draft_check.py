#!/usr/bin/env python3
"""成稿检查（只用标准库，不读语料）。写作的 agent 交稿前运行。

  draft_check.py 成稿.md [更多.md ...]   每篇一段中文报告；有门槛未通过时退出码 1
  draft_check.py -                       从标准输入读一篇
  draft_check.py --json 成稿.md ...      每篇一行 JSON，退出码同上
  draft_check.py --across 成稿.md ...    跨篇汇总（评测用）：出场分布、失败、思维阁开口、收尾、重复短语

质地四项的判定与 evals/style_eval.py texture 相同，同一组技能台词两处算出同样的数。

JSON 键：
  cabinet       有没有思维阁
  bureau_answer 思维阁解答是不是机构腔开口（通告、通知、委员会……）
  todo_ending   解答最后一句是不是在给你派活（请、记得、尽快……）
  stock_props   命中的常见道具（凉咖啡、悬在回车上的手指……）
  crisis_leak   危机回复里有没有提技能、规则、声音
  task_lines    新任务、任务完成行的条数
  bracket_ending 有没有整行方括号（[雨刷还在摆] 这类语料里没有的结尾）
  crisis_ui_leak 危机回复里有没有界面行（任务、道具、抬头、思维、属性行）
  skill / you / world  技能、你、其他人物和物件（含斜体物件、爬虫脑这类特殊声音）的台词条数
  skill_share / single / imperative / connective  [命中, 分母]：技能占全部发言、单句、祈使开头、连词或语气词
  appearances   各技能出场次数
  failures      带【失败】的技能，按出现顺序
  ending        场景最后一行的类型
  question_open / answer_open  思维阁问题、解答的第一句
  failed        未通过的门槛
"""
import argparse, collections, json, math, os, re, sys, unicodedata
from fractions import Fraction as F
from pathlib import Path

SKILLS = ("逻辑思维 博学多闻 能说会道 故弄玄虚 标新立异 见微知著 平心定气 内陆帝国 通情达理 争强好胜 同舟共济 循循善诱 "
          "钢筋铁骨 坚忍不拔 强身健体 食髓知味 天人感应 疑神疑鬼 眼明手巧 五感发达 反应速度 鬼祟玲珑 能工巧匠 从容自若").split()
BUREAU = re.compile(r'^(通告|通知|公告|特此|兹|经审议|委员会|本办公室|本通告|.{0,12}(今日|正式)(通告|宣布|挂牌|公告))')
TODO = re.compile(r'(请(于|你|尽快|查阅|回复|把|去)|你(该|得|应该|需要)去?|记得|尽快|务必|别忘了|试着|去把)')
PROPS = {
    '凉掉的饮料': r'(咖啡|茶|美式|拿铁)[^。\n]{0,8}(凉|冷掉|没化|水渍)|凉(掉的|了的)?(咖啡|茶)',
    '悬在回车上的手指': r'(食指|手指|指尖)[^。\n]{0,10}(悬|停)[^。\n]{0,6}回车',
    '震到桌边的手机': r'震[^。\n]{0,12}(挪|推|移)[^。\n]{0,8}(边|沿)',
    '后颈': r'后颈',
    '没回头': r'没(有)?(回头|抬头)',
}
TASK = re.compile(r'^\s*(>\s*)?(新任务|(隐藏)?任务完成)[:：]', re.M)
BRACKET = re.compile(r'^\s*\[[^\]\n]+\]\s*$', re.M)
UI = re.compile(r'^\s*(>\s*)?(新任务|(隐藏)?任务完成|获得道具|失去道具|解锁思维)[:：]|^\s*Day\s?\d+\s|^\s*[+-]\s?\d\s?\S{2,6}[:：]', re.M)
LEAK = re.compile(r'SKILL|技能|规则|声音|极乐迪斯科|风格')

# 以下四个判定照抄 evals/style_eval.py texture；改一边要同步另一边，test_draft_check.py 会比对两边的数
def sents(t):
    return [x for x in re.split(r'[。!?！？…]+|\.{2,}', t) if x.strip()]


IMPERATIVE = re.compile(r'(^|[。!?])(别(?!人|的|处)|问(?!题)|去(?!年|世)|把(?!握|手)|先(?!生|前)|给|让|试着|看看|告诉)')
PARTICLE = re.compile(r'[吧呢啊嘛哦呀哈唉嗯]')
CONJUNCTION = re.compile(r'因为|所以|但是|不过|虽然|如果|而且|然后|可是')

# 分母不到 8 条时不判：按语料的单句比例随手写，4 条里一条单句都没有的机会是 17%，8 条时是 3%，
# 再少就分不清是质地跑偏还是条数太少。v4 的叙事稿技能台词是 8–11 条，下限再高会有一半稿子不判。
MIN_SAMPLE = 8
TEXTURE_GATES = (
    # 键, 名称, 门槛, 下限, 上限, 低于下限怎么改, 高于上限怎么改
    ('skill_share', '技能占比', '不到 1/3', None, lambda v: v < F(1, 3), None,
     '删掉只评论气氛的技能台词，把它要交代的事交给对方的话或你的追问；不要加你和世界的台词去稀释'),
    ('single', '单句', '30%–50%', lambda v: v >= F(3, 10), lambda v: v <= F(1, 2),
     '截短已有台词或删掉只评论气氛的那条，不要加台词凑数',
     '给几条单句接上半句理由或一个具体的东西，不要加新台词'),
    ('imperative', '祈使开头', '不超过 10%', None, lambda v: v <= F(1, 10), None,
     '把指令改成判断或观察；真要下指令，交给一个想坑你的声音'),
    ('connective', '连词或语气词', '至少 20%', lambda v: v >= F(1, 5), None,
     '在已有台词里用因为、不过、所以、如果把两句接起来，或带上吧、呢、啊；不要加新台词', None),
)
FLAG_GATES = (
    # 键, 名称, 适用于叙事稿（否则只查危机回复）, 怎么改
    ('bracket_ending', '方括号行', True, '删掉整行方括号；场景停在下一个动作或世界的最后一句话上'),
    ('crisis_leak', '提到技能或规则', False, '危机回复只写给这个人，删掉提到技能、规则、声音、风格的句子'),
    ('crisis_ui_leak', '界面行', False, '危机回复不写任务、道具、抬头这类界面行'),
)

CABINET_HEAD = re.compile(r'^>\s*#+.*思维阁')
SKILL_LINE = re.compile(r'^\*\*([^*]+)\*\*\s*(?:[（(][^）)]*[）)])?\s*(【[^】]*】)?\s*(?:—\s*(.*))?$')
YOU_LINE = re.compile(r'^>\s*\*\*你\*\*\s*—\s*(.*)$')
WORLD_LINE = re.compile(r'^(\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_|[^\s*>\[#|`\-_].{0,20}?)\s+—\s+(.*)$')
UI_LINE = re.compile(r'^(?:>\s*)?(新任务|(?:隐藏)?任务完成|获得道具|失去道具|解锁思维)[:：]|^Day\s?\d+\s|^[+-]\s?\d\s?\S{2,6}[:：]')
SKIP_LINE = re.compile(r'^(-{3,}|\*{3,}|#|\||```|[-*+]\s|>)')
QUOTE = re.compile(r'[“"「]')


def plain(t):
    """去掉强调符：*强调*，以及 prettier 改写出的 _强调_（snake_case 里的下划线保留）。"""
    return re.sub(r'(?<![A-Za-z0-9])_|_(?![A-Za-z0-9])', '', t.replace('*', '')).strip()


def classify(line):
    if BRACKET.match(line):
        return {'kind': 'bracket', 'speaker': '', 'tag': '', 'text': line}
    m = UI_LINE.match(line)
    if m:
        sub = '新任务' if m[1] == '新任务' else '任务完成' if m[1] and '任务完成' in m[1] else '界面行'
        return {'kind': 'ui', 'speaker': sub, 'tag': '', 'text': line}
    m = YOU_LINE.match(line)
    if m:
        return {'kind': 'you', 'speaker': '你', 'tag': '', 'text': m[1]}
    m = SKILL_LINE.match(line)
    if m and re.sub(r'[（(].*', '', m[1]) in SKILLS:
        return {'kind': 'skill', 'speaker': re.sub(r'[（(].*', '', m[1]), 'tag': m[2] or '', 'text': m[3] or ''}
    m = WORLD_LINE.match(line)
    if m:
        return {'kind': 'world', 'speaker': m[1].strip(), 'tag': '', 'text': m[2]}
    if SKIP_LINE.match(line):
        return {'kind': 'skip'}
    return None


def parse(text):
    """场景里的发言，按出现顺序；思维阁块不算。标签行之后不空行的续行并进同一条，空行结束一条。"""
    recs, cur, in_cabinet = [], None, False
    for line in (l.strip() for l in text.split('\n')):
        if in_cabinet:
            if not line or line.startswith('>'):
                continue
            in_cabinet = False
        if CABINET_HEAD.match(line):
            in_cabinet, cur = True, None
            continue
        if not line:
            if cur is not None and cur['text']:
                cur = None  # 标签单独一行时，正文在下一段
            continue
        rec = classify(line)
        if rec is None and cur is not None:
            cur['text'] += line
            continue
        if rec is None:
            rec = {'kind': 'narration', 'speaker': '', 'tag': '', 'text': line}
        if rec['kind'] == 'skip':
            cur = None
            continue
        recs.append(rec)
        cur = rec if rec['kind'] in ('skill', 'you', 'world', 'narration') else None
    return recs


def cabinet_part(t, label):
    m = re.search(rf'\*\*{label}\*\*[:：]\s*(.+?)(?=\n>?\s*\n(?!>)|\n> \*\*|\n---|\Z)', t, re.S)
    return re.sub(r'^>\s?', '', m[1], flags=re.M).strip() if m else ''


def opening(t, cap=18):
    t = plain(t)
    m = re.match(r'.*?[。！？!?…]+', t, re.S)
    s = (m[0] if m else t).strip()
    return s if len(s) <= cap else s[:cap] + '…'


def last_line(recs):
    """返回 (类型, 那一条)。带标签的句子没有引语时算旁白（style.md「叙述旁白」），斜体物件说「我」时算它开口。"""
    for r in reversed(recs):
        k, label = r['kind'], r['speaker']
        if k == 'ui':
            return label, r
        if k == 'bracket':
            return '方括号行', r
        if k == 'you':
            return '你的台词', r
        if k == 'skill':
            return '技能台词', r
        if k == 'world':
            spoken = label.startswith('**') or QUOTE.search(r['text']) or (label[0] in '*_' and '我' in r['text'])
            return ('世界或人物的一句话' if spoken else '旁白动作'), r
        if k == 'narration':
            return '旁白动作', r
    return '', None


def read_draft(name, text):
    recs = parse(text)
    return {'name': name, 'text': text, 'recs': recs,
            'skill_recs': [r for r in recs if r['kind'] == 'skill'],
            'question': cabinet_part(text, '问题'), 'answer': cabinet_part(text, '解答')}


def gates(r):
    """[(名称, 实测, 门槛, 状态, 怎么改)]，状态是 通过 / 未通过 / 不判。"""
    narrative = is_narrative(r)
    rows = []
    if narrative:
        for key, name, rule, low, high, fix_low, fix_high in TEXTURE_GATES:
            h, n = r[key]
            if n < MIN_SAMPLE:
                rows.append((name, f'{h}/{n}', rule, '不判', f'样本太少，不判（分母不到 {MIN_SAMPLE} 条）'))
                continue
            v = F(h, n)
            fix = fix_low if low and not low(v) else fix_high if high and not high(v) else ''
            rows.append((name, f'{round(100 * h / n)}%（{h}/{n}）', rule, '未通过' if fix else '通过', fix))
    for key, name, for_narrative, fix in FLAG_GATES:
        if for_narrative == narrative:
            rows.append((name, '有' if r[key] else '无', '不能有', '未通过' if r[key] else '通过', fix if r[key] else ''))
    return rows


def check_draft(d):
    t, recs, skill_recs = d['text'], d['recs'], d['skill_recs']
    ans = d['answer']
    last = [s for s in re.split(r'(?<=[。！？!?])', ans) if s.strip()]
    texts = [plain(x['text']) for x in skill_recs]
    skill = len(skill_recs)
    you = sum(x['kind'] == 'you' for x in recs)
    world = sum(x['kind'] == 'world' for x in recs)
    narrative = skill + you + world > 0
    count = lambda f: [sum(bool(f(x)) for x in texts), len(texts)]
    seen = collections.Counter(x['speaker'] for x in skill_recs)
    r = {
        'file': d['name'],
        'cabinet': '思维阁' in t,
        'bureau_answer': bool(ans and BUREAU.search(ans)),
        'todo_ending': bool(last and TODO.search(last[-1])),
        'stock_props': [k for k, p in PROPS.items() if re.search(p, t)],
        'crisis_leak': (not narrative) and bool(LEAK.search(t)),
        'task_lines': len(TASK.findall(t)),
        'bracket_ending': bool(BRACKET.search(t)),
        'crisis_ui_leak': (not narrative) and bool(UI.search(t)),
        'skill': skill, 'you': you, 'world': world,
        'skill_share': [skill, skill + you + world],
        'single': count(lambda x: len(sents(x)) == 1),
        'imperative': count(IMPERATIVE.search),
        'connective': count(lambda x: PARTICLE.search(x) or CONJUNCTION.search(x)),
        'appearances': dict(sorted(seen.items(), key=lambda kv: (-kv[1], SKILLS.index(kv[0])))),
        'failures': [x['speaker'] for x in skill_recs if '失败' in x['tag']],
        'ending': last_line(recs)[0] if narrative else '',
        'question_open': opening(d['question']) if d['question'] else '',
        'answer_open': opening(d['answer']) if d['answer'] else '',
    }
    r['failed'] = [g[0] for g in gates(r) if g[3] == '未通过']
    return r


def check(path):
    return check_draft(read_draft(path, Path(path).read_text()))


def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)


def pad(s, w):
    return s + ' ' * max(0, w - width(s))


def display(name):
    return '标准输入' if name == '-' else name


def excerpt(t, cap=24):
    t = plain(t)
    return t if len(t) <= cap else t[:cap] + '…'


def is_narrative(r):
    return r['skill'] + r['you'] + r['world'] > 0


def report(d, r):
    out = [f'== {display(r["file"])}']
    if is_narrative(r):
        out.append(f'叙事稿：发言 {r["skill_share"][1]} 条（技能 {r["skill"]}、你 {r["you"]}、世界 {r["world"]}）')
    else:
        out.append('危机回复（没有叙事台词）：质地门槛不跑，只查有没有漏出写作框架')
    out.append('门槛')
    for name, got, rule, status, fix in gates(r):
        line = f'  {pad(name, 16)}{pad(got, 14)}门槛 {pad(rule, 12)}'
        if status == '未通过':
            line += f'未通过：{fix}'
            if name == '祈使开头':
                hits = [excerpt(x['text'], 14) for x in d['skill_recs'] if IMPERATIVE.search(plain(x['text']))]
                line += '（命中：' + '、'.join(f'「{h}」' for h in hits) + '）'
            if name == '提到技能或规则':
                line += '（命中：' + '、'.join(sorted(set(LEAK.findall(d['text'])))) + '）'
        else:
            line += fix if status == '不判' else status
        out.append(line)
    if is_narrative(r):
        kind, text = ending_view(d)
        out.append('只报不判')
        out.append('  出场：' + '、'.join(f'{k} {v}' for k, v in r['appearances'].items()))
        out.append(f'  失败：{len(r["failures"])} 条' + (f'（{"、".join(r["failures"])}）' if r['failures'] else ''))
        out.append(f'  最后一行：{kind}「{text}」')
        if r['question_open'] or r['answer_open']:
            out.append(f'  思维阁：问题开口「{r["question_open"]}」，解答开口「{r["answer_open"]}」')
        else:
            out.append('  思维阁：没有')
        out.append(f'  任务行 {r["task_lines"]} 条；机构腔解答：{"是" if r["bureau_answer"] else "否"}；'
                   f'解答派活收尾：{"是" if r["todo_ending"] else "否"}；常见道具：{"、".join(r["stock_props"]) or "无"}')
    out.append(f'结论：{len(r["failed"])} 项未通过' if r['failed'] else '结论：全部通过')
    return '\n'.join(out)


SKILL_NAME = re.compile('|'.join(SKILLS))


def grams(texts, shortest=4):
    """台词里所有不跨标点、不含技能名的连续片段。"""
    out = set()
    for t in texts:
        for seg in re.split(r'\W+', SKILL_NAME.sub(' ', t)):
            for i in range(len(seg)):
                for j in range(i + shortest, len(seg) + 1):
                    out.add(seg[i:j])
    return out


def repeated_phrases(named_texts, shortest=4):
    """[(短语, [篇名])]：在至少一半篇目（且不少于 2 篇）的技能台词里出现的连续片段。命中篇目相同的子串只留最长的。"""
    hits = collections.defaultdict(set)
    for i, (_, texts) in enumerate(named_texts):
        for g in grams(texts, shortest):
            hits[g].add(i)
    need = max(2, math.ceil(len(named_texts) / 2))
    keep = {g: s for g, s in hits.items() if len(s) >= need}
    rows = [(g, s) for g, s in keep.items() if not any(g != h and g in h and s == keep[h] for h in keep)]
    rows.sort(key=lambda x: (-len(x[1]), -len(x[0]), x[0]))
    return [(g, [named_texts[i][0] for i in sorted(s)]) for g, s in rows]


def short_names(names):
    """文件名不重复时用文件名，否则用去掉公共父目录后的相对路径（run1/migrate.md、run2/migrate.md）。"""
    base = [Path(n).name for n in names]
    if len(set(base)) == len(base):
        return base
    files = [Path(n).resolve() for n in names if n != '-']
    root = Path(os.path.commonpath([f.parent for f in files]))
    return [n if n == '-' else str(Path(n).resolve().relative_to(root)) for n in names]


def across(drafts):
    pairs = [(name, d, check_draft(d)) for name, d in zip(short_names([d['name'] for d in drafts]), drafts)]
    story = [(name, d, r) for name, d, r in pairs if is_narrative(r)]
    seen = collections.Counter(s for _, _, r in story for s in r['appearances'])
    pooled = [plain(x['text']) for _, d, _ in story for x in d['skill_recs']]
    utter = sum(r['skill_share'][1] for _, _, r in story)
    pct = lambda f: round(100 * sum(bool(f(x)) for x in pooled) / len(pooled), 1) if pooled else 0.0
    return {
        'drafts': len(pairs),
        'stories': [name for name, _, _ in story],
        'crisis': [name for name, _, r in pairs if not is_narrative(r)],
        'appearances': sorted(((s, seen[s]) for s in SKILLS if seen[s]), key=lambda kv: (-kv[1], SKILLS.index(kv[0]))),
        'missing': [s for s in SKILLS if not seen[s]],
        'failures': [(name, r['failures']) for name, _, r in story],
        'cabinet': [(name, r['question_open'], r['answer_open']) for name, _, r in story],
        'endings': [(name, *ending_view(d)) for name, d, _ in story],
        'phrases': repeated_phrases([(name, [plain(x['text']) for x in d['skill_recs']]) for name, d, _ in story]),
        'pooled': {
            '技能台词': len(pooled),
            '技能占比': round(100 * len(pooled) / utter, 1) if utter else 0.0,
            '单句': pct(lambda x: len(sents(x)) == 1),
            '祈使开头': pct(IMPERATIVE.search),
            '语气词': pct(PARTICLE.search),
            '连词': pct(CONJUNCTION.search),
            '连词或语气词': pct(lambda x: PARTICLE.search(x) or CONJUNCTION.search(x)),
        },
    }


def ending_view(d):
    kind, rec = last_line(d['recs'])
    label = f'（{rec["speaker"]}）' if rec and rec['kind'] == 'world' else ''
    return kind + label, excerpt(rec['text']) if rec else ''


def print_across(s):
    n = len(s['stories'])
    w = max([width(x) for x in s['stories']] + [8]) + 2
    out = [f'跨篇汇总：{s["drafts"]} 篇，叙事稿 {n} 篇' +
           (f'；危机回复不计入分母：{"、".join(s["crisis"])}' if s['crisis'] else '')]
    out.append(f'\n技能出场（出场篇数/{n}）')
    out.append('  ' + '  '.join(f'{k} {v}/{n}' for k, v in s['appearances']))
    out.append(f'  没出场（{len(s["missing"])} 个）：' + ('、'.join(s['missing']) or '无'))
    out.append('\n失败（【失败】条数与技能）')
    for name, fails in s['failures']:
        out.append(f'  {pad(name, w)}{len(fails)}  {"、".join(fails)}')
    tally = collections.Counter(len(f) for _, f in s['failures'])
    out.append('  合计：' + '，'.join(f'{k} 条的 {v} 篇' for k, v in sorted(tally.items())))
    qw = max([width(q) for _, q, _ in s['cabinet']] + [4]) + 2
    out.append('\n思维阁开口（第一句）')
    out.append(f'  {pad("篇目", w)}{pad("问题", qw)}解答')
    for name, q, a in s['cabinet']:
        out.append(f'  {pad(name, w)}' + (f'{pad(q, qw)}{a}' if q or a else '（没有思维阁）'))
    out.append('\n最后一行')
    for name, kind, text in s['endings']:
        out.append(f'  {pad(name, w)}{kind}「{text}」')
    tally = collections.Counter(re.sub(r'（.*', '', k) for _, k, _ in s['endings'])
    out.append('  合计：' + '，'.join(f'{k} {v}/{n}' for k, v in tally.most_common()))
    need = max(2, math.ceil(n / 2))
    out.append(f'\n重复短语（技能台词里连续 4 字以上，至少 {need}/{n} 篇）')
    for g, where in s['phrases'][:20]:
        out.append(f'  {pad(g, 16)}{len(where)}/{n}  {" ".join(where)}')
    if len(s['phrases']) > 20:
        out.append(f'  另有 {len(s["phrases"]) - 20} 条')
    if not s['phrases']:
        out.append('  无')
    p = s['pooled']
    out.append(f'\n合计质地（叙事稿全部技能台词 {p["技能台词"]} 条，口径同 style_eval.py texture 的「本批」）')
    out.append('  ' + '  '.join(f'{k} {v}%' for k, v in p.items() if k != '技能台词'))
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description='成稿检查：质地门槛、界面层与危机回复；--across 做跨篇汇总')
    ap.add_argument('paths', nargs='+', help='成稿文件；写 - 时从标准输入读一篇')
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--json', action='store_true', help='每篇一行 JSON')
    mode.add_argument('--across', action='store_true', help='打印跨篇汇总')
    a = ap.parse_args(argv)
    drafts = []
    for p in a.paths:
        if p == '-':
            drafts.append(read_draft('-', sys.stdin.read()))
        elif not Path(p).is_file():
            ap.error(f'找不到文件：{p}')
        else:
            drafts.append(read_draft(p, Path(p).read_text()))
    if a.across:
        print(print_across(across(drafts)))
        return 0
    failed = False
    for i, d in enumerate(drafts):
        r = check_draft(d)
        failed |= bool(r['failed'])
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            print(('\n' if i else '') + report(d, r))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
