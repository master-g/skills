#!/usr/bin/env python3
"""render_tui.py 的测试。用法：python3 test_render_tui.py"""
import re
from pathlib import Path

from draft_check import SKILLS
from render_tui import ATTR, HEX, LIGHT, SKILL, fg, render, rgb, width

ROOT = Path(__file__).resolve().parent.parent
DRAFT = '''*门铃* — 响了两声，接着是敲门，敲得很客气。

> **你** — “那续签的话，还按原来的？”

房东 — “续肯定是续。”他把文件袋换到左手。“就是房租得动一动，涨五百。”

**五感发达**(视觉)【成功】 — 文件袋里那几页纸是新打印的，第一页抬头写着：房屋租赁合同，*新的*。

**从容自若**【失败】 — 你想让脸上什么都不写，嘴角却先往下撇了一下，又被你硬拉回来。拉得太快，他看见了，还冲你点点头。

**循循善诱** — 他松了二十块，这就是他的底了。

_冰柜_ — 压缩机嗡了一声。

新任务:打听附近的租金

| 项目 | 现在 |
| --- | --- |
| 月租 | 三千五 |

获得道具:房屋租赁合同
这是一份新打印的合同，纸还是温的，订书钉打歪了。第三页的租金栏空着，空得很整齐。

---

> ### 💭 思维阁:「门框上的第三层胶」
>
> **问题**: 按照通常的租赁习惯，续租时的涨幅大致跟着附近同户型的成交价走。
>
> **解答**: 停！答案是：不算。
'''


def plain(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def test_skill_names_take_their_attribute_color():
    out = render(DRAFT)
    assert f'\x1b[1;{fg("mot")}m五感发达(视觉)\x1b[0m' in out
    assert f'\x1b[1;{fg("mot")}m从容自若\x1b[0m' in out
    assert f'\x1b[1;{fg("psy")}m循循善诱\x1b[0m' in out
    assert f'\x1b[{fg("ck")}m【成功】\x1b[0m' in out and f'\x1b[{fg("ck")}m【失败】\x1b[0m' in out
    assert f'\x1b[1;{fg("you")}m你\x1b[0m' in out
    assert '\x1b[1m房东\x1b[0m' in out and '\x1b[1;3m门铃\x1b[0m' in out and '\x1b[1;3m冰柜\x1b[0m' in out
    assert '\x1b[3m新的\x1b[0m' in out


def test_layout():
    for cols in (40, 72):
        lines = plain(render(DRAFT, cols)).split('\n')
        assert max(width(l) for l in lines) <= cols + 2, cols
        i = next(k for k, l in enumerate(lines) if l.startswith('从容自若【失败】 — '))
        assert lines[i + 1].startswith('   ') and not lines[i + 1].startswith('    '), lines[i + 1]
    text = plain(render(DRAFT))
    assert '新任务  打听附近的租金' in text and '获得道具  房屋租赁合同' in text
    assert '门框上的第三层胶' in text and '💭' not in text and ' 问题  /  解答 ' in text
    assert '月租' in text and '|' not in text and '**' not in text
    box = [l for l in text.split('\n') if l and l[0] in '┌│└']
    assert len(box) >= 4 and len({width(l) for l in box}) == 1, box


def test_no_color_keeps_the_text():
    out = render(DRAFT, color=False)
    strip = lambda text: [line.rstrip() for line in text.split('\n')]
    assert '\x1b' not in out and strip(out) == strip(plain(render(DRAFT)))


def contrast(a, b):
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_light_palette_reads_on_a_light_ground():
    out = render(DRAFT, light=True)
    assert f'\x1b[1;38;2;{rgb("mot", LIGHT)}m从容自若\x1b[0m' in out
    assert plain(out) == plain(render(DRAFT))
    assert not any(f'8;2;{rgb(k)}' in out for k in HEX)
    assert sorted(LIGHT) == sorted(HEX)
    for key, value in LIGHT.items():
        ground = LIGHT['bar'] if key == 'bar-ink' else 'f5f5f0'
        assert key == 'bar' or contrast(value, ground) >= 4.5, key


def test_table_matches_docs_and_template():
    assert sorted(n for n in SKILL if SKILL[n] != 'reptile') == sorted(SKILLS)
    doc = (ROOT / 'references/html-output.md').read_text()
    for attr, names in ATTR.items():
        if attr != 'reptile':
            assert re.search(rf'`{attr}`\s*\|\s*{"、".join(names.split())}\s*\|', doc), attr
    css = (ROOT / 'assets/templates/narrative.html').read_text()
    for key, value in HEX.items():
        assert re.search(rf'--{key}:\s*#{value};', css), key


def main():
    for name, f in list(globals().items()):
        if name.startswith('test_'):
            f()
    print('test_render_tui: ok')


if __name__ == '__main__':
    main()
