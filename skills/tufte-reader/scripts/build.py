#!/usr/bin/env python3
"""build.py 页面.html [--open] [--check-only]

把作者写的读本源码就地合成为单文件成品，再做检查。可重复运行：成品再跑一遍会刷新内联的
CSS/JS、重建目录，已展开的边注和已归位的脚注不会重复处理。

合成：
  1. LaTeX → MathML（node + vendor 的 Temml）；公式与紧邻的全角标点之间禁止断行
  2. <span class="sidenote|marginnote"> 补全 label + checkbox
  3. 每章的 <span class="footnote"> 挪到章末 section.footnotes，原位留编号
  4. 填 <nav class="toc">
  5. 本地图片转 data URI
  6. 分步图（figure.steps）展开成并排的小图，每一步一幅，成品里没有脚本和控件
  7. 内联 tufte.css、骨架脚本，以及页面用到的代码高亮语言；注入网络字体的 <link>
     （jsDelivr，离线时回退系统字体）

ERROR 必须修；WARN 需要判断。
"""
import base64
import mimetypes
import re
import shutil
import subprocess
import sys
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
VENDOR = ASSETS / "vendor"
HL_DIR = VENDOR / "shj"
MATH_SCRIPT = ROOT / "scripts" / "math.mjs"

CSS_SLOT, JS_SLOT = "<!--TR:CSS-->", "<!--TR:JS-->"
CSS_TAG_RE = re.compile(r'<style data-tr="css">.*?</style>|<link data-tr="font"[^>]*>', re.S)
# 网络字体：西文 STIX Two Text、中文 Noto Serif SC，都是按 unicode-range 分片的样式表，不阻塞首绘；
# 离线或加载失败时回退 tufte.css 里的系统字体。粗体加载 600，与 tufte.css 的 --weight-bold 一致
FONT_CSS = [f"https://cdn.jsdelivr.net/npm/@fontsource/{name}@5.3.0/{w}.css"
            for name, weights in (("stix-two-text", ("400", "400-italic", "600")), ("noto-serif-sc", ("400", "600")))
            for w in weights]
FONT_LINKS = "".join(
    f'<link data-tr="font" rel="stylesheet" href="{u}" media="print" onload="this.media=\'all\'">' for u in FONT_CSS)
JS_TAG_RE = re.compile(r'<script data-tr="(?:js|hl)">.*?</script>', re.S)

SIZE_WARN = 5 * 1024 * 1024
CJK = r"\u3400-\u4dbf\u4e00-\u9fff"
CODE_ISLAND_RE = re.compile(r"<(pre|code|script|style|math|svg)\b.*?</\1\s*>", re.S | re.I)

CODE_LANG_RE = re.compile(r'<code[^>]*\bclass="[^"]*\blanguage-([\w+-]+)')
HL_ALIASES = {
    "rust": "rs", "golang": "go", "python": "py", "javascript": "js", "typescript": "ts",
    "jsx": "js", "tsx": "ts", "shell": "bash", "sh": "bash", "zsh": "bash", "console": "bash",
    "yml": "yaml", "markdown": "md", "dockerfile": "docker", "htm": "html", "jsonc": "json",
}
HL_SKIP = {"text", "plain", "plaintext", "txt"}


# ── 公式 ────────────────────────────────────────────────────────────────
BLOCK_MATH_RE = re.compile(r"\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)")
CJK_RE = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")


def single_dollar_spans(text, allow_cjk=False):
    """与 math.mjs 同一套扫描规则：公式内部可以换行，不能跨越标签。
    allow_cjk 只给构建后的残留检查用：含中文的 $…$ 不会被编译，但要报出来。"""
    i, n = 0, len(text)
    while i < n:
        i = text.find("$", i)
        if i < 0:
            return
        if (i and text[i - 1] in "\\$") or i + 1 >= n or text[i + 1].isspace() or text[i + 1] == "$":
            i += 1
            continue
        j = text.find("$", i + 1)
        while j > 0 and text[j - 1] in " \t\n\\":
            j = text.find("$", j + 1)
        if j < 0:
            return
        inner = text[i + 1 : j]
        ok = "<" not in inner and not (j + 1 < n and text[j + 1].isdigit()) \
            and (allow_cjk or not CJK_RE.search(re.sub(r"\\text\{[^}]*\}", "", inner)))
        if ok:
            yield i, j + 1
            i = j + 1
        else:
            i += 1


# <svg> 里只有 <foreignObject> 的内容是 HTML，公式写在那里（图元库的 mathtext）
FOREIGN_RE = re.compile(r"<foreignObject\b[^>]*>(.*?)</foreignObject\s*>", re.S | re.I)


def has_math_source(html):
    text = CODE_ISLAND_RE.sub(lambda m: " ".join(FOREIGN_RE.findall(m.group(0))) if m.group(1).lower() == "svg" else "", html)
    return bool(BLOCK_MATH_RE.search(text)) or any(True for _ in single_dollar_spans(text))


ANNOTATION_RE = re.compile(r"<annotation\b.*?</annotation\s*>", re.S)  # 编译产物里留着的 LaTeX 源


def leftover_dollars(html):
    """成品正文里仍然成对的 $：没被编译的公式。逐个文本片段扫描，不跨标签。
    插图也查：<svg> 的 <text> 里写了 $…$ 不会被编译，会原样显示出来。"""
    found = []
    islands = CODE_ISLAND_RE.sub(lambda m: m.group(0) if m.group(1).lower() == "svg" else "<i>", html)
    for piece in re.split(r"<[^>]+>", ANNOTATION_RE.sub("", islands)):
        for a, b in single_dollar_spans(piece, allow_cjk=True):
            found.append(" ".join(piece[max(0, a - 12) : b + 12].split()))
    return found


def compile_math(page, errors, warns):
    if not has_math_source(page.read_text(encoding="utf-8")):
        return
    node = shutil.which("node")
    if not node:
        errors.append("页面里有 LaTeX 公式，但找不到 node 来编译成 MathML；装 Node.js 后重跑")
        return
    out = subprocess.run([node, str(MATH_SCRIPT), str(page)], capture_output=True, text=True)
    if out.returncode != 0:
        errors.append("公式编译失败：" + (out.stderr.strip().splitlines() or ["未知错误"])[-1])
        return
    for line in out.stdout.splitlines():
        if line.startswith("ERROR"):
            errors.append(line[5:].strip())
        elif line.startswith("WARN"):
            warns.append(line[4:].strip())
        else:
            print(line)


# 浏览器把行内 <math> 当成一个整块，块的前后总能断行，于是「$V$：」的冒号会落到下一行行首
# （Chrome 实测，U+2060 也拦不住）。把公式连同紧邻的全角标点包进不换行的 span。
# 长公式（math-inline-long）不包：窄屏下它占满一行，再粘一个标点会撑出版心。
OPENERS, CLOSERS = "（「『《〈【", "，。；：？！、）」』》〉】"
MATH_PUNCT_RE = re.compile(
    r'(<span class="math-nobr">|<span class="math-inline-long">)?'
    r"([（「『《〈【]?)(<math\b(?![^>]*\bdisplay=)[^>]*>.*?</math>)([，。；：？！、）」』》〉】]?)", re.S)


def glue_math_punctuation(html):
    def repl(m):
        if m.group(1) or not (m.group(2) or m.group(4)):
            return m.group(0)
        # Firefox 内核在相邻的两个不换行片段之间不给断行机会，「$a$、$b$、$c$」会连成一条撑宽页面；
        # 在标点允许断行的一侧补 <wbr>。紧挨着另一个标点时不补，免得标点落到行首或行尾
        s, before, after = m.string, m.start(), m.end()
        pre = "<wbr>" if m.group(2) and before and s[before - 1] not in OPENERS + "<>" else ""
        post = "<wbr>" if m.group(4) and after < len(s) and s[after] not in CLOSERS else ""
        return f'{pre}<span class="math-nobr">{m.group(2)}{m.group(3)}{m.group(4)}</span>{post}'

    return MATH_PUNCT_RE.sub(repl, html)


# ── 平衡扫描：取出一个元素的完整外层 HTML ──────────────────────────────
def element_end(html, start, tag):
    """start 指向 <tag 的 '<'，返回对应闭合标签之后的位置。"""
    pat = re.compile(rf"<(/?){tag}\b[^>]*>", re.I)
    depth = 0
    for m in pat.finditer(html, start):
        if m.group(0).endswith("/>"):
            continue  # 自闭合（SVG 里的 <g … />），不改变嵌套深度
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return m.end()
    raise ValueError(f"<{tag}> 没有闭合")


# ── 边注 ────────────────────────────────────────────────────────────────
# 开标签里允许换行：格式化工具会把 <span class="…"> 折成几行
NOTE_OPEN_RE = re.compile(r'<span\s+class="(sidenote|marginnote)"\s*>')
TOGGLE_TAIL_RE = re.compile(r'class="margin-toggle"\s*/?>\s*$')


def expand_notes(html):
    used = set(re.findall(r'\bid="((?:sn|mn)-\d+)"', html))
    counter = {"sn": 0, "mn": 0}

    def next_id(prefix):
        while True:
            counter[prefix] += 1
            cand = f"{prefix}-{counter[prefix]}"
            if cand not in used:
                used.add(cand)
                return cand

    out, pos, added = [], 0, 0
    for m in NOTE_OPEN_RE.finditer(html):
        if TOGGLE_TAIL_RE.search(html[max(0, m.start() - 80) : m.start()]):
            continue  # 已展开
        kind = m.group(1)
        prefix = "sn" if kind == "sidenote" else "mn"
        nid = next_id(prefix)
        label = (
            f'<label for="{nid}" class="margin-toggle sidenote-number"></label>'
            if kind == "sidenote"
            else f'<label for="{nid}" class="margin-toggle">&#8853;</label>'
        )
        out.append(html[pos : m.start()])
        out.append(f'{label}<input type="checkbox" id="{nid}" class="margin-toggle"/>')
        pos = m.start()
        added += 1
    out.append(html[pos:])
    return "".join(out), added


# ── 章、脚注、目录 ────────────────────────────────────────────
CHAPTER_RE = re.compile(r'<article\b[^>]*\bclass="[^"]*\bchapter\b[^"]*"[^>]*>', re.I)
FOOTNOTE_OPEN_RE = re.compile(r'<span\s+class="footnote"\s*>')
CHAPTER_NUMBER_RE = re.compile(r'<span\s+class="chapter-number"\s*>(.*?)</span\s*>', re.S)
# 章末脚注用符号，与边注的数字编号区分开；超出后退回数字
FN_MARKS = ["*", "†", "‡", "§", "‖", "¶"]


def chapters(html):
    """[(start, end, id, number_html, title_html)]"""
    found = []
    for m in CHAPTER_RE.finditer(html):
        end = element_end(html, m.start(), "article")
        body = html[m.start() : end]
        cid = re.search(r'\bid="([^"]+)"', m.group(0))
        h2 = re.search(r"<h2\b[^>]*>(.*?)</h2>", body, re.S)
        num, title = "", ""
        if h2:
            inner = h2.group(1)
            nm = CHAPTER_NUMBER_RE.search(inner)
            num = nm.group(1).strip() if nm else ""
            title = CHAPTER_NUMBER_RE.sub("", inner).strip()
        found.append((m.start(), end, cid.group(1) if cid else None, num, title))
    return found


def place_footnotes(html, errors):
    total = 0
    for start, end, cid, _, _ in reversed(chapters(html)):
        body = html[start:end]
        if not FOOTNOTE_OPEN_RE.search(body):
            continue
        if not cid:
            errors.append("含脚注的 <article class=\"chapter\"> 缺 id，脚注无法编号")
            continue
        existing = len(re.findall(rf'<li id="fn-{re.escape(cid)}-\d+"', body))
        items, out, pos, n = [], [], 0, existing
        for m in FOOTNOTE_OPEN_RE.finditer(body):
            if m.start() < pos:
                continue  # 嵌套在上一个脚注里
            fend = element_end(body, m.start(), "span")
            n += 1
            mark = FN_MARKS[n - 1] if n <= len(FN_MARKS) else str(n)
            content = re.sub(r"</span\s*>$", "", body[m.end() : fend]).strip()
            out.append(body[pos : m.start()])
            out.append(f'<a class="fn-ref" id="fnref-{cid}-{n}" href="#fn-{cid}-{n}">{mark}</a>')
            items.append(
                f'<li id="fn-{cid}-{n}"><span class="fn-mark">{mark}</span>{content} '
                f'<a class="fn-back" href="#fnref-{cid}-{n}" aria-label="回到正文">↩</a></li>'
            )
            pos = fend
        out.append(body[pos:])
        body = "".join(out)
        total += len(items)
        block = "\n".join(items)
        if '<section class="footnotes">' in body:
            body = re.sub(r'(<section class="footnotes">.*?)(</ol>)', lambda mm: mm.group(1) + block + "\n" + mm.group(2), body, count=1, flags=re.S)
        else:
            sec = f'<section class="footnotes"><ol>\n{block}\n</ol></section>\n'
            at = body.rfind("</article>")
            body = body[:at] + sec + body[at:]
        html = html[:start] + body + html[end:]
    return html, total


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def build_toc(html, errors):
    chs = chapters(html)
    if not chs:
        return html
    for _, _, cid, _, title in chs:
        if not cid:
            errors.append(f"章「{strip_tags(title)[:20]}」缺 id，目录无法链接")
        if not title:
            errors.append(f"章 {cid} 没有 <h2> 标题")
    if any(not c[2] for c in chs):
        return html

    has_toc = '<nav class="toc"' in html
    if has_toc:
        items = []
        for _, _, cid, num, title in chapters(html):
            items.append(f'<li><span class="toc-number">{num or "·"}</span><a href="#{cid}">{strip_tags(title)}</a></li>')
        ref = re.search(r'<section class="references" id="([^"]+)"', html)
        if ref:
            items.append(f'<li><span class="toc-number">·</span><a href="#{ref.group(1)}">参考文献</a></li>')
        toc = '<nav class="toc" id="toc" aria-label="目录"><h2>目录</h2><ol>\n' + "\n".join(items) + "\n</ol></nav>"
        s = html.index('<nav class="toc"')
        html = html[:s] + toc + html[element_end(html, s, "nav"):]
    return html


# ── 宽代码块 ────────────────────────────────────────────────────────
# 正文栏宽随窗口变，1280 宽的窗口里是 616px，里面的代码块约 76 列（0.9rem 的 Menlo，两侧各留 1rem）；按 black / PEP 8 排的 79 列代码放不下，
# 35/56 个块要横向滚动（annotated-transformer 实测）。超宽的块改成 fullwidth，占正文栏加页边。
CODE_COLS = 76
PRE_RE = re.compile(r'<pre(\s[^>]*)?>(\s*<code\b[^>]*>)(.*?)</code>', re.S)


def widen_code(html):
    """超宽的代码块加 fullwidth。超过一半的块都超宽时全部加宽，页面上代码宽度保持一致。"""
    import html as htmllib

    def cols(m):
        text = htmllib.unescape(re.sub(r"<[^>]+>", "", m.group(3)))
        return max((len(l.expandtabs(4)) for l in text.split("\n")), default=0)

    blocks = list(PRE_RE.finditer(html))
    wide_all = sum(cols(m) > CODE_COLS for m in blocks) * 2 > len(blocks)
    count = 0

    def repl(m):
        nonlocal count
        attrs = m.group(1) or ""
        if "fullwidth" in attrs or (not wide_all and cols(m) <= CODE_COLS):
            return m.group(0)
        count += 1
        if 'class="' in attrs:
            attrs = attrs.replace('class="', 'class="fullwidth ', 1)
        else:
            attrs += ' class="fullwidth"'
        return f"<pre{attrs}>{m.group(2)}{m.group(3)}</code>"

    return PRE_RE.sub(repl, html), count


# ── 图片内联 ────────────────────────────────────────────────────────────
IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', re.I)


def inline_images(html, base, errors):
    count = 0

    def repl(m):
        nonlocal count
        src = m.group(2)
        if src.startswith("data:"):
            return m.group(0)
        if re.match(r"https?://", src):
            errors.append(f"图片引用外网地址，离线打不开：{src[:80]}；先下载到本地再引用")
            return m.group(0)
        path = (base / src).resolve()
        if not path.is_file():
            errors.append(f"图片不存在：{src}")
            return m.group(0)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        count += 1
        return m.group(1) + f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode() + m.group(3)

    return IMG_RE.sub(repl, html), count


# ── 分步图：构建时展开成并排的小图 ────────────────────────────────────────
# 作者写一幅 <svg>，里面带 data-step 的元素是帧，<ol class="step-captions"> 的第 k 项是第 k 步的说明；
# 构建把每一步各画一幅小图，连同说明排进 <ol class="step-frames">。成品里没有脚本和控件。
STEPS_FIGURE_RE = re.compile(r'<figure\b[^>]*\bclass="[^"]*(?<![\w-])steps(?![\w-])[^"]*"[^>]*>', re.I)
STEP_TAG_RE = re.compile(r'<([A-Za-z][\w:-]*)\b[^<>]*?\sdata-step="([^"]*)"[^<>]*?(/?)>')
STEP_PART_RE = re.compile(r"\s*(\d+)\s*(?:(-)\s*(\d*))?\s*$")


def step_ranges(spec):
    """data-step 的值 → [(起, 止)]，止为 None 表示到最后一步；写法不对返回 None。"3"、"3-5"、"3-"、"1,4-6"。"""
    out = []
    for part in spec.split(","):
        m = STEP_PART_RE.match(part)
        if not m:
            return None
        a = int(m.group(1))
        b = a if not m.group(2) else int(m.group(3)) if m.group(3) else None
        if a < 1 or (b is not None and b < a):
            return None
        out.append((a, b))
    return out


def list_items(inner):
    """<ol> 内部的直接子 <li> 的内容；嵌套列表里的 <li> 不算。"""
    items, depth, start = [], 0, None
    for m in re.finditer(r"<(/?)(li|ol|ul)\b[^>]*>", inner, re.I):
        closing, tag = m.group(1), m.group(2).lower()
        if tag == "li":
            if not closing and depth == 0:
                start = m.end()
            elif closing and depth == 0 and start is not None:
                items.append(inner[start : m.start()].strip())
                start = None
        else:
            depth += -1 if closing else 1
    return items


def step_frame(svg, k, n):
    """第 k 步的那幅图：去掉这一步不显示的帧，去掉 data-step；图内的 id 加后缀，各幅小图互不冲突。"""
    out, pos = [], 0
    for m in STEP_TAG_RE.finditer(svg):
        if m.start() < pos:
            continue  # 在一个已经去掉的帧里面
        out.append(svg[pos : m.start()])
        if any(a <= k <= (b or n) for a, b in step_ranges(m.group(2))):
            out.append(re.sub(r'\sdata-step(?:-last)?(?:="[^"]*")?', "", m.group(0)))
            pos = m.end()
        else:
            pos = m.end() if m.group(3) else element_end(svg, m.start(), m.group(1))
    out.append(svg[pos:])
    frame = "".join(out)
    for i in sorted(set(re.findall(r'\bid="([^"]+)"', frame)), key=len, reverse=True):
        frame = re.sub(rf'(\bid="|url\(#|href="#){re.escape(i)}(?=["\)])', rf"\g<1>{i}-s{k}", frame)
    return re.sub(r'(<svg\b[^>]*\baria-label="[^"]*)"', rf'\g<1>（第 {k} 步，共 {n} 步）"', frame, count=1)


def expand_steps(html, errors, warns):
    islands = [m.span() for m in CODE_ISLAND_RE.finditer(html) if m.group(1).lower() != "svg"]
    figures = [m for m in STEPS_FIGURE_RE.finditer(html) if not any(a <= m.start() < b for a, b in islands)]
    count = 0
    for no, fm in reversed(list(enumerate(figures, 1))):
        where = f"第 {no} 幅分步图"
        end = element_end(html, fm.start(), "figure")
        body = html[fm.start() : end]
        if '<ol class="step-frames"' in body:
            continue  # 已展开
        cap = re.search(r'<ol\b[^>]*\bclass="[^"]*\bstep-captions\b[^"]*"[^>]*>', body)
        if not cap:
            errors.append(f"{where}缺 <ol class=\"step-captions\">：每一步的说明写成其中的一个 <li>")
            continue
        cap_end = element_end(body, cap.start(), "ol")
        caps = list_items(body[cap.end() : cap_end - len("</ol>")])
        stage = re.search(r"<svg\b", body)
        if not stage or stage.start() > cap.start():
            errors.append(f"{where}里没有 <svg>：帧写在说明列表之前的一幅 <svg> 里")
            continue
        s0, s1 = stage.start(), element_end(body, stage.start(), "svg")
        svg = body[s0:s1]
        specs = [m.group(2) for m in STEP_TAG_RE.finditer(svg)]
        bad = [x for x in specs if step_ranges(x) is None]
        if not specs:
            errors.append(f"{where}里没有帧：给 <svg> 里每一步要显示的元素加 data-step")
            continue
        if bad:
            errors.append(f"{where}的 data-step=\"{bad[0]}\" 写法不对：写 3、3-5、3-（从第 3 步到最后一步）或 1,4-6")
            continue
        n = max(max(a, b or a) for x in specs for a, b in step_ranges(x))
        covered = {k for x in specs for a, b in step_ranges(x) for k in range(a, (b or n) + 1)}
        missing = [str(k) for k in range(1, n + 1) if k not in covered]
        if missing:
            errors.append(f"{where}的帧编号不连续：共 {n} 步，缺第 {'、'.join(missing[:8])} 步")
            continue
        if len(caps) != n:
            errors.append(f"{where}有 {n} 步，说明却是 {len(caps)} 条：两者要一样多")
            continue
        if n == 1:
            warns.append(f"{where}只有 1 步，用普通的 <figure> 就够了")
        width = re.search(r'<svg\b[^>]*?\swidth="(\d+(?:\.\d+)?)"', svg)
        col = f' style="--step-w: {round(float(width.group(1)) * 0.75)}px"' if width else ""
        items = "\n".join(f"<li>{step_frame(svg, k, n)}{caps[k - 1]}</li>" for k in range(1, n + 1))
        frames = f'<ol class="step-frames"{col}>\n{items}\n</ol>'
        between = re.sub(r"<div\b[^>]*>\s*</div>", "", body[:s0] + body[s1 : cap.start()])  # 包着 <svg> 的空壳
        html = html[: fm.start()] + between + frames + body[cap_end:] + html[end:]
        count += 1
    return html, count


# ── 代码高亮与资源内联 ──────────────────────────────────────────────────
def highlight_script(html, warns):
    wanted = {}
    for name in sorted(set(CODE_LANG_RE.findall(html))):
        if name in HL_SKIP:
            continue
        stem = HL_ALIASES.get(name, name)
        if not (HL_DIR / "languages" / f"{stem}.js").exists():
            warns.append(f"language-{name} 没有对应的语法规则，该代码块不着色")
            continue
        wanted.setdefault(stem, set()).add(name)
    if not wanted:
        return ""
    stems, queue = set(wanted), list(wanted)
    while queue:
        src = (HL_DIR / "languages" / f"{queue.pop()}.js").read_text(encoding="utf-8")
        for dep in re.findall(r'sub:"(\w+)"', src):
            if dep not in stems and (HL_DIR / "languages" / f"{dep}.js").exists():
                stems.add(dep)
                queue.append(dep)
    parts = ["window.__SHJ_LANGS={};"]
    for stem in sorted(stems):
        src = (HL_DIR / "languages" / f"{stem}.js").read_text(encoding="utf-8").strip()
        m = re.search(r"export\s*\{\s*(\w+)\s+as\s+default\s*\}\s*;?\s*$", src)
        if not m:
            continue
        parts.append(f'window.__SHJ_LANGS["{stem}"]=(function(){{{src[:m.start()]}return {m.group(1)};}})();')
        for alias in sorted(wanted.get(stem, set()) - {stem}):
            parts.append(f'window.__SHJ_LANGS["{alias}"]=window.__SHJ_LANGS["{stem}"];')
    parts.append((HL_DIR / "core.js").read_text(encoding="utf-8"))
    return "".join(parts)


def inline_assets(html, warns, errors):
    css = FONT_LINKS + f'<style data-tr="css">{(ASSETS / "tufte.css").read_text(encoding="utf-8")}</style>'
    if CSS_SLOT in html:
        html = html.replace(CSS_SLOT, css, 1)
    elif CSS_TAG_RE.search(html):
        first = CSS_TAG_RE.search(html).start()
        html = CSS_TAG_RE.sub("", html)
        html = html[:first] + css + html[first:]
    else:
        errors.append(f"找不到 {CSS_SLOT} 占位符或已内联的样式；页面应从 assets/shell.html 开始")

    authored = JS_TAG_RE.sub("", html)
    hl = highlight_script(authored, warns)
    js = (f'<script data-tr="hl">{hl}</script>' if hl else "") + \
        f'<script data-tr="js">{(ASSETS / "shell.js").read_text(encoding="utf-8")}</script>'
    if JS_SLOT in html:
        html = html.replace(JS_SLOT, js, 1)
    elif JS_TAG_RE.search(html):
        first = JS_TAG_RE.search(html).start()
        html = JS_TAG_RE.sub("", html)
        html = html[:first] + js + html[first:]
    else:
        errors.append(f"找不到 {JS_SLOT} 占位符或已内联的脚本")
    return html


# ── 检查 ────────────────────────────────────────────────────────────────
NOTE_HOSTS = {"p", "figure", "li", "dd", "blockquote", "td", "figcaption"}
BLOCK_BREAKERS = {"section", "article", "header", "footer", "div", "nav", "body", "main"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.classes, self.ids, self.hrefs = [], [], [], []
        self.stats = {"章": 0, "小节(h3)": 0, "图": 0, "页边图": 0, "表": 0, "代码块": 0, "边注": 0, "旁注": 0, "脚注": 0, "块级公式": 0, "行内公式": 0, "图内公式": 0, "分步图": 0, "帧": 0}
        self.errors, self.text = [], []
        self.deep_heading = []
        self.external = []
        self.after_toggle = False  # 上一个标签是不是边注开关的 checkbox
        self.raw_notes = self.raw_footnotes = self.raw_steps = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and (a.get("href") or "").startswith("#"):
            self.hrefs.append(a["href"][1:])
        if tag in ("h4", "h5", "h6"):
            self.deep_heading.append(tag)
        if tag in ("script", "link") and "data-tr" not in a and re.match(r"https?://", a.get("src") or a.get("href") or ""):
            self.external.append(a.get("src") or a.get("href"))
        if tag == "article" and "chapter" in cls:
            self.stats["章"] += 1
        if tag == "h3":
            self.stats["小节(h3)"] += 1
        if tag == "figure":
            self.stats["图"] += 1
            self.stats["分步图"] += "steps" in cls
        if tag == "li" and self.classes and "step-frames" in self.classes[-1]:
            self.stats["帧"] += 1
        if "data-step" in a:
            self.raw_steps += 1
        if tag == "table":
            self.stats["表"] += 1
        if tag == "pre":
            self.stats["代码块"] += 1
        if tag == "li" and (a.get("id") or "").startswith("fn-"):
            self.stats["脚注"] += 1
        if tag == "math":
            self.stats["图内公式" if "svg" in self.stack else "块级公式" if a.get("display") == "block" else "行内公式"] += 1
        if tag == "span" and "footnote" in cls:
            self.raw_footnotes += 1
        if tag == "span" and ("sidenote" in cls or "marginnote" in cls):
            self.stats["边注" if "sidenote" in cls else "旁注"] += 1
            self.raw_notes += not self.after_toggle
            host = next((t for t in reversed(self.stack) if t in NOTE_HOSTS | BLOCK_BREAKERS), None)
            if host not in NOTE_HOSTS:
                self.errors.append(f"{'边注' if 'sidenote' in cls else '旁注'}不在 <p>/<figure>/<li> 里（直接挂在 <{host}> 下），页边定位会错位")
        if tag == "img" and any("marginnote" in c for c in self.classes) and "figure" not in self.stack:
            self.stats["页边图"] += 1
        self.after_toggle = tag == "input" and "margin-toggle" in cls
        if tag not in VOID:
            self.stack.append(tag)
            self.classes.append(cls)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                self.classes.pop()
                if self.stack.pop() == tag:
                    break

    def handle_data(self, data):
        if data.strip():
            self.after_toggle = False
        if not any(t in ("script", "style", "pre", "code", "math") for t in self.stack):
            self.text.append(data)


def check(html, errors, warns):
    c = Checker()
    c.feed(html)
    errors.extend(c.errors)

    dup = sorted({i for i in c.ids if c.ids.count(i) > 1})
    if dup:
        errors.append("重复的 id：" + "、".join(dup[:8]))
    ids = set(c.ids)
    broken = sorted({h for h in c.hrefs if h and h not in ids})
    if broken:
        errors.append("页内链接指向不存在的 id：" + "、".join(broken[:8]))
    if c.deep_heading:
        errors.append(f"出现 {'/'.join(sorted(set(c.deep_heading)))}：读本只用 h2（章）与 h3（节），更深一级用 <span class=\"newthought\"> 起段")
    for u in c.external:
        errors.append(f"外链脚本或样式，离线打不开：{u[:80]}")
    if c.raw_footnotes:
        errors.append(f"有 {c.raw_footnotes} 处 <span class=\"footnote\"> 没有归位到章末：要么不在 <article class=\"chapter\"> 里，"
                      "要么开标签不是 <span class=\"footnote\"> 这个写法（不要加别的属性或 class）")
    if c.raw_steps:
        errors.append(f"有 {c.raw_steps} 处 data-step 没有展开成小图：它要写在 <figure class=\"steps\"> 的 <svg> 里；"
                      "同时修掉上面关于分步图的 ERROR")
    if c.raw_notes:
        errors.append(f"有 {c.raw_notes} 处边注/旁注没有展开开关，窄屏下点不开：开标签只写 <span class=\"sidenote\"> 或 "
                      "<span class=\"marginnote\">，不要加别的属性或 class")
    if re.search(r"<p\b[^>]*>(?:(?!</p>).)*?<(div|figure|pre|table|ol|ul|section|blockquote|details)\b", html, re.S):
        errors.append("<p> 里嵌了块级元素：浏览器会提前闭合 <p>，边注与版心随之错位；把块级元素移到段落之外")
    if not re.search(r"<title>[^<]+</title>", html) or "中文标题 · 原文标题" in html:
        errors.append("<title> 还是骨架占位，换成「中文标题 · 原文标题」（原创撰写写「书名 · 副标题」）")
    if BLOCK_MATH_RE.search(CODE_ISLAND_RE.sub("", html)):
        errors.append("仍有未编译的块级公式定界符（$$、\\[、\\(）")
    left = leftover_dollars(html)
    if left:
        errors.append(f"正文里有 {len(left)} 处成对的 $ 没有编译成公式（" + "；".join(f"…{x[:60]}…" for x in left[:5])
                      + "）：公式里的中文写进 \\text{}；确实要显示美元符号就写 &#36;；插图里的公式不能写在 <text> 里，"
                      "放进 <foreignObject>（图元库的 mathtext）")
    # 两种残留：解析失败整段变红字 span；未知宏在 MathML 里变红色 mtext
    bad = re.findall(r'<span class="temml-error"[^>]*>(.*?)</span>', html, re.S) + \
        re.findall(r'<mtext style="color:#b22222;">(.*?)</mtext>', html, re.S)
    if bad:
        errors.append("公式编译出错残留 " + str(len(bad)) + " 处（" + "；".join(" ".join(b.split())[:40] for b in bad[:3])
                      + "）：把出错的整个 <span class=\"temml-error\"> 或 <math> 换回改正后的 $…$ 再构建")

    text = "\n".join(c.text)  # 只查同一文本节点内部；跨元素拼接会把单元格、标签边界误报为相邻
    gaps = re.findall(rf"[{CJK}][A-Za-z0-9]|[A-Za-z0-9][{CJK}]", text)
    if gaps:
        sample = "、".join(dict.fromkeys(gaps))
        warns.append(f"中西文之间缺空格 {len(gaps)} 处（{sample[:40]}）")
    half = re.findall(rf"[{CJK}][,;:?!]|[,;:?!][{CJK}]|[{CJK}]\([^)]*\)", text)
    if half:
        warns.append(f"中文语境里用了半角标点 {len(half)} 处（{'、'.join(dict.fromkeys(half))[:40]}）")
    straight = re.findall(rf'"[^"\n]*[{CJK}][^"\n]*"', text)
    if straight:
        warns.append(f"中文引文用了直引号 {len(straight)} 处，改用「」")
    fixed = fixed_colors(html)
    if fixed:
        warns.append(f"插图里有 {len(fixed)} 处写死的颜色（{'、'.join(dict.fromkeys(fixed))[:40]}），不跟随明暗主题："
                     "改用 currentColor，数据分成几类时用 var(--fig-1) … var(--fig-4)")
    return c.stats


# ── 插图颜色 ────────────────────────────────────────────────────────────
# 写死的颜色不跟随明暗主题。允许的写法：currentColor、none、var(--…)（可以带回退值）、url(#…)
SVG_RE = re.compile(r"<svg\b.*?</svg\s*>", re.S | re.I)
PAINT_RE = re.compile(r'(?<![\w-])(?:fill|stroke|stop-color|flood-color|color)\s*(?:=\s*"([^"]*)"|:\s*([^;"]+))', re.I)
PAINT_OK_RE = re.compile(r"\s*(?:none|currentcolor|inherit|transparent|context-(?:fill|stroke)|(?:var|url)\(.*\))\s*$", re.I | re.S)


def fixed_colors(html):
    found = []
    for svg in SVG_RE.findall(html):
        for tag in re.findall(r"<[^>]+>", svg):
            found += [v.strip() for m in PAINT_RE.finditer(tag) for v in [m.group(1) or m.group(2) or ""]
                      if not PAINT_OK_RE.match(v)]
    return found


# ── 打开 ────────────────────────────────────────────────────────────────
def open_page(path):
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
        return True
    import os
    if os.name == "nt" and hasattr(os, "startfile"):
        os.startfile(str(path))
        return True
    for cmd in ("wslview", "xdg-open"):
        exe = shutil.which(cmd)
        if exe:
            subprocess.run([exe, str(path)], check=False)
            return True
    return False


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    if len(args) != 1:
        print(__doc__)
        return 2
    page = Path(args[0]).resolve()
    if not page.is_file():
        print(f"ERROR 文件不存在：{page}")
        return 2
    errors, warns = [], []

    if "--check-only" not in flags:
        compile_math(page, errors, warns)
        html = glue_math_punctuation(page.read_text(encoding="utf-8"))
        html, notes = expand_notes(html)
        html, fns = place_footnotes(html, errors)
        html = build_toc(html, errors)
        html, imgs = inline_images(html, page.parent, errors)
        html, wide = widen_code(html)
        html, steps = expand_steps(html, errors, warns)
        html = inline_assets(html, warns, errors)
        page.write_text(html, encoding="utf-8")
        print(f"合成    新展开边注/旁注 {notes} 条，新归位脚注 {fns} 条，内联图片 {imgs} 张，加宽代码块 {wide} 个，展开分步图 {steps} 幅")

    html = page.read_text(encoding="utf-8")
    stats = check(html, errors, warns)
    print("统计    " + "  ".join(f"{k} {v}" for k, v in stats.items()))
    size = page.stat().st_size
    if size > SIZE_WARN:
        warns.append(f"页面 {size / 1024 / 1024:.1f} MB：检查是否有可压缩的大图")

    for w in warns:
        print("WARN  ", w)
    for e in errors:
        print("ERROR ", e)
    print(f"{'失败' if errors else '通过'}：{len(errors)} 个 ERROR，{len(warns)} 个 WARN  →  {page}")
    if errors:
        return 1
    if "--open" in flags and not open_page(page):
        print("未能打开浏览器，请手动打开上面的路径")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
