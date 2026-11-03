#!/usr/bin/env python3
"""给成稿做机械检查（只用标准库）。用法：draft_check.py draft.md ...

每篇输出一行 JSON：
  cabinet       有没有思维阁
  bureau_answer 思维阁解答是不是机构腔开口（通告、通知、委员会……）
  todo_ending   解答最后一句是不是在给你派活（请、记得、尽快……）
  stock_props   命中的常见道具（凉咖啡、悬在回车上的手指……）
  crisis_leak   危机回复里有没有提技能、规则、声音
  task_lines    新任务、任务完成行的条数
  bracket_ending 有没有整行方括号（[雨刷还在摆] 这类语料里没有的结尾）
  crisis_ui_leak 危机回复里有没有界面行（任务、道具、抬头、思维、属性行）
  skill / you / world  技能、你、其他人物和物件的台词条数
"""
import json, re, sys
from pathlib import Path

SKILLS = set(("逻辑思维 博学多闻 能说会道 故弄玄虚 标新立异 见微知著 平心定气 内陆帝国 通情达理 争强好胜 同舟共济 循循善诱 "
              "钢筋铁骨 坚忍不拔 强身健体 食髓知味 天人感应 疑神疑鬼 眼明手巧 五感发达 反应速度 鬼祟玲珑 能工巧匠 从容自若").split())
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


def lines_of(t):
    return [l for l in t.split('\n') if l.strip()]


def cabinet_answer(t):
    m = re.search(r'\*\*解答\*\*[:：]\s*(.+?)(?=\n>?\s*\n(?!>)|\n> \*\*|\n---|\Z)', t, re.S)
    return re.sub(r'^>\s?', '', m[1], flags=re.M).strip() if m else ''


def check(path):
    t = Path(path).read_text()
    ans = cabinet_answer(t)
    last = [s for s in re.split(r'(?<=[。！？!?])', ans) if s.strip()]
    skill = you = world = 0
    for l in lines_of(t):
        m = re.match(r'^\*\*([^*]+)\*\*', l)
        if m and m[1] in SKILLS:
            skill += 1
        elif l.startswith('> **你**'):
            you += 1
        elif re.match(r'^[^*>\[#|`\-].{0,20} — ', l):
            world += 1
    narrative = skill + you + world > 0
    return {
        'file': path,
        'cabinet': '思维阁' in t,
        'bureau_answer': bool(ans and BUREAU.search(ans)),
        'todo_ending': bool(last and TODO.search(last[-1])),
        'stock_props': [k for k, p in PROPS.items() if re.search(p, t)],
        'crisis_leak': (not narrative) and bool(LEAK.search(t)),
        'task_lines': len(TASK.findall(t)),
        'bracket_ending': bool(BRACKET.search(t)),
        'crisis_ui_leak': (not narrative) and bool(UI.search(t)),
        'skill': skill, 'you': you, 'world': world,
    }


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(check(p), ensure_ascii=False))
