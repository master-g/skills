"""figlib —— 读本插图的图元库。只用标准库，由作者自己的脚本 import，产出内联 <svg> 字符串。

    import sys; sys.path.insert(0, "<skill-path>/scripts")
    from figlib import *

    b = [box(20, 20, None, 28, "编码器"), line(96, 34, 140, 34, arrow=True), mathtext(170, 34, r"h_{T-1}")]
    FIGS["enc"] = svg(220, 68, "".join(b), "编码器输出最后一步的隐藏状态")

章节源码里写 <!--FIG:enc-->，拼页面时用 embed(源码, FIGS) 填回，再交给 build.py。用法与约定见
references/markup.md 的「图元库」。

约定：
- 每个图元返回一段 SVG 字符串，坐标是 viewBox 里的用户单位；svg() 把它们包成一幅图。
- 颜色：color=None 用 currentColor，跟随明暗主题；color=1…4 用 tufte.css 的分类色 --fig-1 … --fig-4。
  深浅一律用 fill（0–1 的不透明度）表示，所以同一种分类色可以有任意多档深浅。
- 箭头、斜线填充的 <defs> 由 svg() 按需加上；图内所有 id 由 svg() 加上每幅图不同的前缀，作者不用管。
- 公式用 mathtext()：它输出 <foreignObject> 里的 $…$，由 build.py 编译成 MathML。<text> 里不能写公式。
"""
import re
import unicodedata
from html import escape

__all__ = ["FIGS", "SANS", "MONO", "tw", "fit", "paint", "svg", "embed", "text", "mathtext", "rect", "circ", "line",
           "poly", "elbow", "box", "boxes", "panel", "cells", "heat", "g", "rle", "steps"]

FIGS = {}
SANS = '-apple-system, "PingFang SC", "Noto Sans CJK SC", sans-serif'
MONO = "ui-monospace, SFMono-Regular, Menlo, monospace"

# 分类色的回退值，取 tufte.css 亮色主题的 --fig-1 … --fig-4。页面里有变量时用变量；
# 单独打开一幅 SVG（或 rsvg-convert）取不到变量，画成回退色
FALLBACK = {1: "#1f5fa8", 2: "#d55e00", 3: "#2e9d4e", 4: "#882255"}


def paint(color=None):
    """color → 可以写进 fill / stroke 的值。"""
    return "currentColor" if color is None else f"var(--fig-{color}, {FALLBACK[color]})"


# ── 文字宽度 ────────────────────────────────────────────────────────────
# 构建时量不了真实宽度，按字符类别粗算。系数用 Chrome 里 SANS、MONO 两套字体的实测宽度校准过（macOS），
# 32 条中英文标签里 30 条的误差在 ±8% 以内，偏差大的是两三个字符的短标签。只用来决定方块多宽，不用来精确对齐。
NARROW, WIDE = set("iIjl.,:;'|!()[]{}· "), set("mwMW@%—")
SEMI = set("ftr-/\"*")


def tw(s, size=13, mono=False):
    """估算一段文字排出来的宽度（SVG 用户单位）。mono=True 按等宽字体算。"""
    w = 0
    for c in s:
        if unicodedata.east_asian_width(c) in "WF":
            w += 1
        elif mono:
            w += 0.602
        elif c in NARROW:
            w += 0.3
        elif c in SEMI:
            w += 0.38
        elif c in WIDE:
            w += 0.9
        elif c.isupper():
            w += 0.68
        elif c.isdigit():
            w += 0.56
        else:
            w += 0.55
    return w * size


def fit(s, size=12, pad=8, mono=False):
    """装得下这段文字的方块宽度：估算宽度加两侧留白。"""
    return round(tw(s, size, mono) + 2 * pad)


# ── 画布 ────────────────────────────────────────────────────────────────
def _marker(color):
    return ('<marker id="arr{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{p}"/></marker>'
            ).format(k=color or "", p=paint(color))


DEFS = {f"arr{k or ''}": _marker(k) for k in (None, *FALLBACK)}
DEFS["hatch"] = ('<pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                 '<line x1="0" y1="0" x2="0" y2="5" stroke="currentColor" stroke-width="1.6"/></pattern>')
_ID_RE = re.compile(r'\bid="([^"]+)"')
_count = [0]


def _canvas(w, h, body, label, width):
    used = "".join(d for k, d in DEFS.items() if f"url(#{k})" in body)
    body = (f"<defs>{used}</defs>" if used else "") + body
    _count[0] += 1
    for i in sorted(set(_ID_RE.findall(body)), key=len, reverse=True):
        body = re.sub(rf'(\bid="|url\(#|href="#){re.escape(i)}(?=["\)])', rf"\g<1>f{_count[0]}-{i}", body)
    return (f'<svg viewBox="0 0 {w} {h}" width="{width or min(600, round(w * 1.15))}" role="img" '
            f'aria-label="{escape(label)}" font-family=\'{SANS}\' font-size="13">{body}</svg>')


def svg(w, h, body, label, width=None):
    """把图元拼成的 body 包成一幅图。w、h 是 viewBox 的大小；width 是页面上的显示宽度（px），
    默认是 w 的 1.15 倍、不超过 600（正文栏在 1280 宽的窗口里是 616）。label 写图说了什么，给读屏用。"""
    return _canvas(w, h, body, label, width)


def embed(html, figs=FIGS):
    """把源码里的 <!--FIG:name--> 换成 figs[name]；有没画的图时报出名字。"""
    missing = [m for m in re.findall(r"<!--FIG:([\w-]+)-->", html) if m not in figs]
    if missing:
        raise KeyError(f"缺图：{'、'.join(missing)}")
    return re.sub(r"<!--FIG:([\w-]+)-->", lambda m: figs[m.group(1)], html)


# ── 基本图元 ────────────────────────────────────────────────────────────
def _stroke(sw, dash, op, color):
    return (f'stroke="{paint(color)}" stroke-width="{sw}"' + (' stroke-dasharray="3 3"' if dash else "")
            + (f' stroke-opacity="{op}"' if op != 1 else ""))


def text(x, y, s, anchor="start", size=13, font=None, op=1, weight=None, color=None):
    """一行文字，y 是基线。anchor：start / middle / end。s 按纯文本处理，不能写标签和公式。"""
    extra = (f" font-family='{font}'" if font else "") + (f' fill-opacity="{op}"' if op != 1 else "") \
        + (f' font-weight="{weight}"' if weight else "")
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" fill="{paint(color)}"{extra}>'
            f"{escape(str(s), quote=False)}</text>")


def mathtext(x, y, tex, anchor="middle", size=13, color=None):
    """一个公式，tex 是不带 $ 的 LaTeX。y 是公式的垂直中心（不是基线），anchor 决定 x 是左端、中点还是右端。
    公式多宽构建时不知道，这里给一个足够宽的框，由 tufte.css 的 .fig-math 按 anchor 对齐。"""
    w = max(80, 0.75 * size * len(tex))
    left = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
    style = f"font-size:{size}px" + (f";color:{paint(color)}" if color else "")
    return (f'<foreignObject x="{left:.1f}" y="{y - 1.5 * size:.1f}" width="{w:.1f}" height="{3 * size}" overflow="visible">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" class="fig-math fig-math-{anchor}" style="{style}">'
            f"${escape(tex, quote=False)}$</div></foreignObject>")


def rect(x, y, w, h, fill=0, dash=False, sw=1, rx=3, color=None, hatch=False):
    """矩形。fill 是填充的不透明度；hatch=True 再叠一层斜线（表示「被缓存」「被屏蔽」这类状态）。"""
    at = f'x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"'
    lines = f'<rect {at} fill="url(#hatch)" fill-opacity="0.55"/>' if hatch else ""
    return f'<rect {at} fill="{paint(color)}" fill-opacity="{fill}" {_stroke(sw, dash, 1, color)}/>{lines}'


def circ(x, y, r=17, fill=0.06, sw=1, color=None):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{paint(color)}" fill-opacity="{fill}" {_stroke(sw, False, 1, color)}/>'


def _arrow(arrow, color):
    return f' marker-end="url(#arr{color or ""})"' if arrow else ""


def line(x1, y1, x2, y2, sw=1, dash=False, op=1, arrow=False, color=None):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {_stroke(sw, dash, op, color)}'
            f"{_arrow(arrow, color)}/>")


def poly(points, sw=1, dash=False, op=1, arrow=False, color=None):
    """折线，points 是 [(x, y), …]。arrow=True 在末端加箭头。"""
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{pts}" fill="none" {_stroke(sw, dash, op, color)}{_arrow(arrow, color)}/>'


def elbow(x1, y1, x2, y2, via="hv", at=None, **kw):
    """直角拐弯的连线。via="hv" 先横后竖，"vh" 先竖后横；"hvh"、"vhv" 中间拐两次，
    at 是中间那一段所在的 x（hvh）或 y（vhv），默认取两端的中点。其余参数同 poly。"""
    if via == "hv":
        mid = [(x2, y1)]
    elif via == "vh":
        mid = [(x1, y2)]
    elif via == "hvh":
        m = (x1 + x2) / 2 if at is None else at
        mid = [(m, y1), (m, y2)]
    elif via == "vhv":
        m = (y1 + y2) / 2 if at is None else at
        mid = [(x1, m), (x2, m)]
    else:
        raise ValueError(f'via="{via}"：写 hv、vh、hvh 或 vhv')
    return poly([(x1, y1), *mid, (x2, y2)], **kw)


# ── 组合图元 ────────────────────────────────────────────────────────────
def box(x, y, w, h, s, fill=0.06, size=12, font=None, dash=False, color=None, hatch=False):
    """带一行文字的方块，文字居中。w=None 时按文字宽度自适应（fit()），这时 x 仍是左边界。"""
    if w is None:
        w = fit(s, size, mono=font == MONO)
    return rect(x, y, w, h, fill, dash=dash, color=color, hatch=hatch) \
        + text(x + w / 2, y + h / 2 + size * 0.36, s, "middle", size, font)


def boxes(items, x, y, h=26, pad=7, gap=4, size=13, font=MONO, fill=0.06):
    """一行紧挨着的方块（token 序列）。返回 (svg, 各方块中心 x 的列表, 末端 x)。"""
    out, cx = [], []
    for s in items:
        w = fit(s, size, pad, font == MONO)
        out.append(box(x, y, w, h, s, fill, size, font))
        cx.append(x + w / 2)
        x += w + gap
    return "".join(out), cx, x - gap


def panel(x, y, w, h, fill=0.05, rx=8, color=None):
    """分组用的底板：圆角、无边框的浅色块，画在这一组图元的下面。"""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{paint(color)}" fill-opacity="{fill}"/>'


def cells(x, y, nr, nc, cw, ch=None, fill=0.03, color=None, label=None, size=11, font=MONO, sw=0.6, rx=0, gap=0):
    """nr 行 nc 列的网格。fill、color、label 可以是固定值，也可以是 (i, j) 的函数；
    函数返回 None 时：fill 不画这一格，label 不写字。"""
    ch = ch or cw
    pick = lambda v, i, j: v(i, j) if callable(v) else v
    out = []
    for i in range(nr):
        for j in range(nc):
            f = pick(fill, i, j)
            if f is None:
                continue
            cx, cy = x + j * (cw + gap), y + i * (ch + gap)
            out.append(rect(cx, cy, cw, ch, f, sw=sw, rx=rx, color=pick(color, i, j)))
            s = pick(label, i, j)
            if s is not None:
                out.append(text(cx + cw / 2, cy + ch / 2 + size * 0.36, s, "middle", size, font))
    return "".join(out)


def heat(M, x, y, cell=34, rows=None, cols=None, fmt="{:.2f}", size=11, maxv=None):
    """矩阵热图：不透明度表示数值大小，None 的格子画一道斜线（被掩码）。rows、cols 是行、列的标签。"""
    out = []
    mv = maxv or max(v for r in M for v in r if v is not None) or 1
    for i, r in enumerate(M):
        for j, v in enumerate(r):
            cx, cy = x + j * cell, y + i * cell
            if v is None:
                out.append(rect(cx, cy, cell, cell, 0, rx=0, sw=0.6))
                out.append(line(cx + 6, cy + cell - 6, cx + cell - 6, cy + 6, 0.8, op=0.45))
            else:
                out.append(rect(cx, cy, cell, cell, round(0.04 + 0.6 * v / mv, 3), rx=0, sw=0.6))
                if fmt:
                    out.append(text(cx + cell / 2, cy + cell / 2 + 4, fmt.format(v), "middle", size, MONO))
    for i, s in enumerate(rows or []):
        out.append(text(x - 8, y + i * cell + cell / 2 + 4, s, "end", 12, MONO))
    for j, s in enumerate(cols or []):
        out.append(text(x + j * cell + cell / 2, y - 8, s, "middle", 12, MONO))
    return "".join(out)


# ── 分步图（markup.md 的「分步图」）─────────────────────────────────────
def g(step, content):
    """只在某几步出现的一组图元。step 的写法同 data-step："3"、"3-5"、"3-"、"1,4-6"。"""
    return f'<g data-step="{step}">{content}</g>' if content else ""


def rle(per_step):
    """per_step[k-1] 是第 k 步这一部分的 SVG；相邻几步相同的合并成一个 data-step="a-b" 的组。"""
    out, i, n = [], 0, len(per_step)
    while i < n:
        j = i
        while j + 1 < n and per_step[j + 1] == per_step[i]:
            j += 1
        out.append(g(f"{i + 1}" if i == j else f"{i + 1}-{j + 1}", per_step[i]))
        i = j + 1
    return "".join(out)


def steps(w, h, body, label, captions, width=None):
    """分步图：返回 <svg> 加 <ol class="step-captions">，放进 <figure class="steps"> 里。
    captions 的第 k 条是第 k 步的说明，可以写行内公式。"""
    return (f'<div class="scroll-x">{_canvas(w, h, body, label, width)}</div><ol class="step-captions">'
            + "".join(f"<li>{c}</li>" for c in captions) + "</ol>")
