#!/usr/bin/env python3
"""draft_check.py 的夹具测试。用法：python3 test_draft_check.py"""
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

from draft_check import MIN_SAMPLE, SKILLS, across, check, check_draft, read_draft

HERE = Path(__file__).resolve().parent
STYLE_EVAL = HERE.parent / 'evals' / 'style_eval.py'

SCENE = """**逻辑思维**【成功】 — 他在拖时间。

> **你** — 我先去把锁等待查清楚。

新任务:查清锁等待

值班同事 — “查吧。”他没抬头。
"""
BRACKET = SCENE + "\n[雨刷还在摆]\n[你没有下车]\n"
CRISIS_OK = "你说这周一直站在阳台上想这件事，我听到了。你现在安全吗？\n"
CRISIS_UI = CRISIS_OK + "\n新任务:给信任的人打电话\n"

# 10 条技能台词：单句 4（40%）、祈使开头 1（10%）、连词或语气词 2（20%），配 21 条你和世界，占比 10/31
PASSING = [
    '他在拖时间。',
    '他不知道。所以他连你看没看见都不知道。',
    '这两个字是说给你听的。',
    '如果周一投影仪上也是这一行呢……',
    '他累了。今晚一个表情都没有。',
    '对，抢在他发第三条之前。',
    '收尾这个词多好听。好像真有个头似的。',
    '你一个字都没写。哪来的尾？',
    '他没被说服。他只是换了一样东西来要。',
    '先别回。他在等你开口。',
]


def scene(texts, others=21):
    parts = [f'**{SKILLS[i % len(SKILLS)]}**【成功】 — {t}' for i, t in enumerate(texts)]
    parts += ['> **你** — “然后呢？”' if i % 2 else '周总 — “你再想想。”' for i in range(others)]
    return '\n\n'.join(parts) + '\n'


def run(text):
    return check_draft(read_draft('-', text))


def cli(*args, stdin=''):
    p = subprocess.run([sys.executable, str(HERE / 'draft_check.py'), *args], input=stdin, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def texture_numbers(texts):
    """用 style_eval.py texture 算同一组台词的「本批」数字；语料换成一个最小的假文件（第 340 行之前不解析）。"""
    with tempfile.TemporaryDirectory() as tmp:
        dev, imit = Path(tmp, 'dev.txt'), Path(tmp, 'imit.json')
        dev.write_text('\n' * 345 + '逻辑思维 — 这是一条够长的语料台词。\n')
        imit.write_text(json.dumps([{'voice': '逻辑思维', 'text': t} for t in texts], ensure_ascii=False))
        out = subprocess.run([sys.executable, str(STYLE_EVAL), 'texture', str(dev), str(imit)],
                             capture_output=True, text=True, check=True).stdout
    return {k: float(v.split('本批 ')[1]) for k, v in (line.split('\t', 1) for line in out.splitlines())}


def test_ui_fields():
    r = run(SCENE)
    assert r['task_lines'] == 1 and not r['bracket_ending'] and not r['crisis_ui_leak'], r
    r = run(BRACKET)
    assert r['bracket_ending'] and '方括号行' in r['failed'], r
    r = run(CRISIS_OK)
    assert r['task_lines'] == 0 and not r['crisis_ui_leak'] and not r['crisis_leak'] and not r['failed'], r
    r = run(CRISIS_UI)
    assert r['crisis_ui_leak'] and r['task_lines'] == 1 and r['failed'] == ['界面行'], r
    assert run('> 任务完成：查清锁等待\n')['task_lines'] == 1


def test_speakers():
    text = '\n\n'.join([
        '**内陆帝国** — 那张票有点烫手……',
        '**五感发达**（视觉）【成功】 — 有烟味。',
        '**逻辑思维**【中等:失败】',
        '有三种可能。',
        '*自动灯器* — 绿灯。运行正常。',
        '_砂糖橘_ — 翠苑好啊。',
        '**古老的爬虫脑** — 嘘……',
        '房东 — “涨五百。”',
        '> **你** — “五百？”',
        '楼道的声控灯灭了。',
    ])
    r = run(text)
    assert (r['skill'], r['you'], r['world']) == (3, 1, 4), r
    assert r['appearances'] == {'逻辑思维': 1, '内陆帝国': 1, '五感发达': 1}, r
    assert r['failures'] == ['逻辑思维'] and r['single'] == [3, 3], r


def test_gates():
    r = run(scene(PASSING))
    assert [r[k] for k in ('skill_share', 'single', 'imperative', 'connective')] == [[10, 31], [4, 10], [1, 10], [2, 10]], r
    assert r['failed'] == [], r
    few = PASSING[:]
    few[0], few[2], few[5] = '他在拖时间。他知道。', '这两个字。是说给你听的。', '对。抢在他发第三条之前。'
    assert run(scene(few))['failed'] == ['单句']
    code, out = cli('-', stdin=scene(few))
    assert code == 1 and '未通过：截短已有台词或删掉只评论气氛的那条，不要加台词凑数' in out, out
    many = PASSING[:]
    many[1], many[4] = '他不知道，所以也不急。', '他累了，今晚一个表情都没有。'
    code, out = cli('-', stdin=scene(many))
    assert code == 1 and '60%（6/10）' in out and '不要加新台词' in out and '凑数' not in out, out
    assert run(scene(PASSING, others=20))['failed'] == ['技能占比']
    bossy = PASSING[:]
    bossy[8] = '别信他。他只是换了一样东西来要。'
    code, out = cli('-', stdin=scene(bossy))
    assert code == 1 and '20%（2/10）' in out and '「别信他。' in out and '「先别回。' in out, out
    flat = PASSING[:]
    flat[1] = '他不知道。他连你看没看见都不知道。'
    assert run(scene(flat))['failed'] == ['连词或语气词']


def test_small_sample():
    texts = ['他在拖时间。他知道。', '别回。等着。'] + ['他累了。他没说。'] * (MIN_SAMPLE - 3)
    r = run(scene(texts))
    assert r['single'] == [0, MIN_SAMPLE - 1] and r['failed'] == [], r
    code, out = cli('-', stdin=scene(texts))
    assert code == 0 and out.count('样本太少') == 3 and '结论：全部通过' in out, out


def test_texture_parity():
    # 没有一条同时含连词和语气词，所以「连词或语气词」等于 texture 的语气词% 加连词%
    texts = [t for t in PASSING if '如果' not in t] + ['你三十一了？把话说出来。', '*别*发了。', '等等...还有呢',
                                                      '是的!给我。', '去吧。', '可是_你的_钥匙。']
    r = run(scene(texts, others=40))
    ref = texture_numbers([t.replace('*', '').replace('_', '') for t in texts])
    for key, metric in (('single', '单句%'), ('imperative', '指令起句%')):
        h, n = r[key]
        assert round(100 * h / n, 1) == ref[metric], (key, r[key], ref)
    h, n = r['connective']
    assert abs(100 * h / n - ref['语气词%'] - ref['连词%']) < 0.15, (r['connective'], ref)
    spec = importlib.util.spec_from_file_location('style_eval', STYLE_EVAL)
    style_eval = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(style_eval)
    assert SKILLS == style_eval.SKILLS


def test_endings():
    cases = {
        '> **你** — 查。\n\n新任务:查清锁等待\n\n任务完成：查清锁等待\n': '任务完成',
        '> **你** — “周一给你看。”\n': '你的台词',
        '老鲁 — “看得见。”\n\n电话挂了。\n': '旁白动作',
        '电话挂了。\n\n老鲁 — “看得见。”\n': '世界或人物的一句话',
        '*PPT 第一页* — 灰字没了。\n': '旁白动作',
        '*储物柜手环* — 我一直在这儿。\n': '世界或人物的一句话',
        '> **你** — 好。\n\n新任务:去一次健身房\n': '新任务',
    }
    for text, kind in cases.items():
        assert run(text)['ending'] == kind, (text, run(text)['ending'])
    with_cabinet = ('妈妈 — “行。”\n\n电话挂了。\n\n---\n\n> ### 💭 思维阁:「牛肉干走私犯」\n>\n> **问题**: 当然，它只是一袋牛肉干。'
                    '可它是被人塞进来的。\n>\n> **解答**: 它哪边也不站。牛肉干没有立场。\n')
    r = run(with_cabinet)
    assert r['ending'] == '旁白动作' and r['question_open'] == '当然，它只是一袋牛肉干。' and r['answer_open'] == '它哪边也不站。', r


def test_json_and_files():
    old = ('cabinet bureau_answer todo_ending stock_props crisis_leak task_lines bracket_ending crisis_ui_leak skill you world '
           'skill_share single imperative connective appearances failures ending question_open answer_open failed').split()
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp, 'a.md'), Path(tmp, 'b.md')
        a.write_text(scene(PASSING))
        b.write_text(CRISIS_OK)
        assert check(str(a))['failed'] == []
        code, out = cli('--json', str(a), str(b))
        rows = [json.loads(line) for line in out.splitlines()]
        assert code == 0 and len(rows) == 2 and all(set(old) <= set(x) for x in rows), out
        code, out = cli(str(a), str(Path(tmp, 'missing.md')))
        assert code == 2 and '找不到文件' in out, out


def test_across():
    drafts = [
        read_draft('a.md', scene(['你可以不在今天定。', '内陆帝国又来了。'], others=4)),
        read_draft('b.md', scene(['你可以不在今天。', '内陆帝国又来了。'], others=4)),
        read_draft('c.md', scene(['你可以不搬。', '只有这一篇有这句话。'], others=4)),
        read_draft('d.md', CRISIS_OK),
    ]
    s = across(drafts)
    assert s['stories'] == ['a.md', 'b.md', 'c.md'] and s['crisis'] == ['d.md'], s
    assert s['phrases'] == [('你可以不', ['a.md', 'b.md', 'c.md']), ('你可以不在今天', ['a.md', 'b.md'])], s['phrases']
    assert s['appearances'] == [('逻辑思维', 3), ('博学多闻', 3)] and len(s['missing']) == 22, s
    assert s['failures'] == [('a.md', []), ('b.md', []), ('c.md', [])], s
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for d in drafts:
            Path(tmp, d['name']).write_text(d['text'])
            paths.append(str(Path(tmp, d['name'])))
        code, out = cli('--across', *paths)
    assert code == 0 and '危机回复不计入分母：d.md' in out and '逻辑思维 3/3' in out, out
    assert '你可以不' in out and '3/3  a.md b.md c.md' in out, out
    same = across([read_draft('runs/r1/a.md', scene(['你可以不在今天定。'], others=2)),
                   read_draft('runs/r2/a.md', scene(['你可以不在今天。'], others=2)),
                   read_draft('runs/r2/b.md', scene(['只有这一篇有这句话。'], others=2))])
    assert same['stories'] == ['r1/a.md', 'r2/a.md', 'r2/b.md'], same['stories']
    assert same['phrases'] == [('你可以不在今天', ['r1/a.md', 'r2/a.md'])], same['phrases']


def main():
    for name, f in list(globals().items()):
        if name.startswith('test_'):
            f()
    print('test_draft_check: ok')


if __name__ == '__main__':
    main()
