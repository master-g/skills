#!/usr/bin/env python3
"""把一篇 Markdown 成稿渲染成终端彩色输出（只用标准库）。用法：render_tui.py <成稿.md|-> [--width N] [--light] [--no-color]

技能名按属性上色，检定标记暗灰，续行悬挂缩进，思维阁是反白标题条加页签。
正文用终端默认色。颜色按深色终端调；浅色终端加 --light 换一套压暗的同色相颜色。设了 NO_COLOR 或加 --no-color 时只排版不上色。
"""
import argparse, os, re, sys, unicodedata
from pathlib import Path

# 属性分组与 references/html-output.md「技能属性」一致，颜色与 assets/templates/narrative.html 一致（test_render_tui.py 会比对）。
ATTR = {
    'int': '逻辑思维 博学多闻 能说会道 故弄玄虚 标新立异 见微知著',
    'psy': '平心定气 内陆帝国 通情达理 争强好胜 同舟共济 循循善诱',
    'fys': '钢筋铁骨 坚忍不拔 强身健体 食髓知味 天人感应 疑神疑鬼',
    'mot': '眼明手巧 五感发达 反应速度 鬼祟玲珑 能工巧匠 从容自若',
    'reptile': '古老的爬虫脑 边缘系统',
}
SKILL = {name: a for a, names in ATTR.items() for name in names.split()}
HEX = {
    'int': '5dbfcd', 'psy': '9a86e0', 'fys': 'db5f84', 'mot': 'd9b84a', 'reptile': 'c2705a',
    'you': 'a9b4c0', 'ck': '86867f', 'gold': 'b08d4f', 'bar': 'e4e4de', 'bar-ink': '121212',
}
# 浅色终端用：同色相压暗到在米白底 #f5f5f0 上对比度不低于 4.5，标题条改成深底浅字。
LIGHT = {
    'int': '297984', 'psy': '7559d5', 'fys': 'cc2e5d', 'mot': '836b1b', 'reptile': 'aa563f',
    'you': '5f7082', 'ck': '6f6f69', 'gold': '846a3b', 'bar': '1c1c1c', 'bar-ink': 'f0f0ea',
}
LEGEND = (('int', '智力'), ('psy', '精神'), ('fys', '体格'), ('mot', '身手'))
HANG = 3
NO_LINE_START = set('，。！？；：、）】》」』”’…—·,.!?;:)')


def rgb(key, table=HEX):
    return ';'.join(str(int(table[key][i:i + 2], 16)) for i in (0, 2, 4))


def fg(key):
    return '38;2;' + rgb(key)


BOLD, ITALIC, DIM = '1', '3', fg('ck')
BAR = f'1;{fg("bar-ink")};48;2;{rgb("bar")}'


def width(text):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)


def spans(text, base=''):
    """把 *强调* 拆成 [(片段, 样式)]。"""
    return [(part, ';'.join(x for x in (base, ITALIC if i % 2 else '') if x))
            for i, part in enumerate(re.split(r'\*([^*]+)\*', text)) if part]


def wrap(segs, cols, hang=0):
    """按显示宽度折行，续行缩进 hang 格；标点不落在行首。返回 [[(片段, 样式)]]。"""
    lines, cur, used = [], [], 0
    for text, style in segs:
        buf = ''
        for ch in text:
            w = width(ch)
            if used + w > cols and ch not in NO_LINE_START:
                if buf:
                    cur.append((buf, style))
                lines.append(cur)
                cur, buf, used = [(' ' * hang, '')] if hang else [], '', hang
                if ch == ' ':
                    continue
            buf += ch
            used += w
        if buf:
            cur.append((buf, style))
    lines.append(cur)
    return lines


def speech(name, name_style, tag, text, cols):
    head = [(name, name_style)] + ([(tag, DIM)] if tag else [])
    return wrap(head + [(' — ', DIM)] + spans(text), cols, HANG)


def table(rows, cols):
    cells = [[c.strip() for c in r.strip('|').split('|')] for r in rows if not re.match(r'^\|[\s:|-]+\|$', r)]
    widths = [max(width(r[k]) for r in cells if k < len(r)) + 3 for k in range(len(cells[0]))]
    out = []
    for n, row in enumerate(cells):
        out.append([(c + ' ' * (widths[k] - width(c)), DIM if n == 0 else '') for k, c in enumerate(row)])
        if n == 0:
            out.append([('─' * min(sum(widths), cols), DIM)])
    return out


def card(title, body_lines, cols):
    inner = cols - 4
    rows = [[('获得道具  ', DIM), (title, fg('gold'))]]
    for line in body_lines:
        rows += wrap(spans(line), inner - 2)
    out = [[('┌' + '─' * (cols - 2) + '┐', DIM)]]
    for row in rows:
        pad = max(0, inner - sum(width(t) for t, _ in row))
        out.append([('│ ', DIM)] + row + [(' ' * pad + ' │', DIM)])
    return out + [[('└' + '─' * (cols - 2) + '┘', DIM)]]


def blocks(md, cols):
    """Markdown 成稿 → 段落列表，每段是 [[(片段, 样式)]]。行的写法见 references/format.md。"""
    lines, i = md.split('\n'), 0
    while i < len(lines):
        ln = lines[i].strip()
        i += 1
        if not ln or ln == '>':
            continue
        if m := re.match(r'^>\s*#+\s*💭?\s*思维阁[:：]\s*「(.+)」', ln):
            yield [[('思 维 阁', DIM)], [(' ' * max(0, cols - width(m[1]) - 2) + m[1] + '  ', BAR)]]
        elif m := re.match(r'^>\s*\*\*(问题|解答)\*\*[:：]\s*(.+)', ln):
            tabs = [(f' {t} ', BAR if t == m[1] else DIM) for t in ('问题', '解答')]
            tabs.insert(1, (' / ', DIM))
            yield [[(' ' * ((cols - 15) // 2), '')] + tabs]
            yield wrap(spans(m[2]), cols)
        elif ln.startswith('|'):
            rows = [ln]
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip())
                i += 1
            yield table(rows, cols)
        elif ln == '---':
            yield [[(' ' * ((cols - 9) // 2) + '─── ✦ ───', fg('gold'))]]
        elif re.match(r'^Day\s?\d+\s', ln):
            yield [[(ln, DIM)]]
        elif m := re.match(r'^(新任务|任务完成)[:：]\s*(.+)', ln):
            yield [[(m[1] + '  ', DIM), (m[2], fg('gold'))]]
        elif m := re.match(r'^获得道具[:：]\s*(.+)', ln):
            body = []
            while i < len(lines) and lines[i].strip():
                body.append(lines[i].strip())
                i += 1
            yield card(m[1], body, cols)
        elif m := re.match(r'^\*\*(.+?)\*\*\s*([(（][^)）]+[)）])?\s*(【[^】]+】)?\s*—\s*(.+)', ln):
            color = fg(SKILL[m[1]]) if m[1] in SKILL else ''
            yield speech(m[1] + (m[2] or ''), ';'.join(x for x in (BOLD, color) if x), m[3], m[4], cols)
        elif m := re.match(r'^>\s*\*\*你\*\*\s*—\s*(.+)', ln):
            yield speech('你', f'{BOLD};{fg("you")}', None, m[1], cols)
        elif m := re.match(r'^([*_])([^*_]+)\1\s*—\s*(.+)', ln):
            yield speech(m[2], f'{BOLD};{ITALIC}', None, m[3], cols)
        elif m := re.match(r'^([^\s—*>|#]{1,12})\s+—\s*(.+)', ln):
            yield speech(m[1], BOLD, None, m[2], cols)
        else:
            yield wrap(spans(re.sub(r'^>\s*', '', ln)), cols)


def paint(line, color):
    return ''.join(f'\x1b[{style}m{text}\x1b[0m' if color and style else text for text, style in line).rstrip()


def render(md, cols=72, color=True, light=False):
    out = []
    for block in blocks(md, cols):
        out += [paint(line, color) for line in block] + ['']
    legend = [('技能名按属性着色  ', DIM)] + [(label + '  ', f'{BOLD};{fg(a)}') for a, label in LEGEND]
    text = '\n'.join(out + [paint([('─' * cols, DIM)], color), paint(legend, color)])
    if light:
        swap = {rgb(k): rgb(k, LIGHT) for k in HEX}
        text = re.sub(r'(?<=[34]8;2;)\d+;\d+;\d+', lambda m: swap[m[0]], text)
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description='把 Markdown 成稿渲染成终端彩色输出')
    ap.add_argument('draft', help='成稿路径；写 - 从标准输入读')
    ap.add_argument('--width', type=int, default=72, help='正文宽度，按终端格数算，默认 72')
    ap.add_argument('--light', action='store_true', help='浅色终端用的颜色')
    ap.add_argument('--no-color', action='store_true', help='只排版，不输出颜色')
    a = ap.parse_args(argv)
    md = sys.stdin.read() if a.draft == '-' else Path(a.draft).read_text()
    print(render(md, a.width, not (a.no_color or os.environ.get('NO_COLOR')), a.light))


if __name__ == '__main__':
    main()
