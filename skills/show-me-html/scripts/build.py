#!/usr/bin/env python3
"""show-me-html 的合成与自检工具。

用法：
    python3 build.py page.html                # 内联资产 + 自检
    python3 build.py page.html --style nova   # 换一套 basecoat 风格包
    python3 build.py page.html --check-only   # 只跑自检，不改文件
    python3 build.py page.html --open         # 自检通过后用系统默认浏览器打开

做四件事，然后自检：
  1. 把 basecoat CSS 内联到 <!--SHOW-ME:CSS--> 处。
  2. 把用到的 lucide 图标从 sprite 里抽出来，替换 data-lucide="name"。
  3. 页面用到需要 JS 的组件时，把 basecoat JS 内联到 <!--SHOW-ME:JS--> 处。
  4. 按页面实际出现的 language-* 内联语法高亮：只带上用到的那几种语言。

对已合成的文件重复运行是安全的：占位符已消失时只跑自检。
"""

import argparse
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

VENDOR = Path(__file__).resolve().parent.parent / "assets" / "vendor"
STYLES = ("vega", "nova", "maia", "lyra", "mira", "luma", "sera", "rhea")

CSS_SLOT = "<!--SHOW-ME:CSS-->"
JS_SLOT = "<!--SHOW-ME:JS-->"
CSS_MARK = 'data-show-me="css"'
JS_MARK = 'data-show-me="js"'
HL_MARK = 'data-show-me="hl"'

# 需要 basecoat JS 才能工作的组件。命中任一即内联 JS。
JS_COMPONENTS = (
    "dropdown-menu", "popover", "select", "combobox", "command",
    "sidebar", "drawer", "tabs", "toaster", "chart",
)

# 页面自己写死的颜色。骨架的调色板块与 vendor CSS 不算。
VENDOR_STYLE_RE = re.compile(r'<style data-show-me="(?:css|palette)"[^>]*>.*?</style>', re.S)
# 只剥 vendor 的 basecoat CSS：palette 块里住着 --font-serif，剥掉字体闸就瞎了
VENDOR_CSS_RE = re.compile(r'<style data-show-me="css"[^>]*>.*?</style>', re.S)
HARDCODED_COLOR_RE = re.compile(
    r'(?::|=")\s*(#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|oklch\()'
)

ICON_RE = re.compile(
    r'<(?P<tag>i|span)(?P<pre>[^>]*?)\sdata-lucide="(?P<name>[a-z0-9-]+)"(?P<post>[^>]*?)>\s*</(?P=tag)>'
)
SYMBOL_RE = re.compile(r'<symbol id="([a-z0-9-]+)"[^>]*>(.*?)</symbol>', re.S)

# ── 语法高亮（@speed-highlight/core，CC0）──────────────────────────────────
# 只发 class（shj-syn-*），颜色由骨架的 --syn-* token 给，两套主题各一组。
HL_DIR = VENDOR / "shj"
CODE_LANG_RE = re.compile(r'<code[^>]*\bclass="[^"]*\blanguage-([\w+-]+)')
# 页面里写的语言名 -> vendor/shj/languages 里的文件名
HL_ALIASES = {
    "rust": "rs", "golang": "go", "python": "py", "javascript": "js", "typescript": "ts",
    "jsx": "js", "tsx": "ts", "shell": "bash", "sh": "bash", "zsh": "bash", "console": "bash",
    "yml": "yaml", "markdown": "md", "dockerfile": "docker", "htm": "html", "jsonc": "json",
}
# diff 由页面自己的 .d-add / .d-del 着色，text/plain 是结构视图（调用树、文件树）—— 都不碰
HL_SKIP = {"diff", "text", "plain", "plaintext", "txt"}


# ── 原生控件 ────────────────────────────────────────────────────────────
# 和 <section> 那条闸是同一种失败模式：**没命中选择器，不报错，只是难看。**
# basecoat 只给 `.field > input[type=range]` 和 `.input[type=range]` 上样式，页面自造一个
# 壳把滑块包进去就两个都不命中，滑块退回操作系统外观（macOS 上是一条亮蓝色粗轨道）。
# 骨架已经连裸 `input[type=range]` 一起兜住了，这道闸是防着有人把那段删掉或改窄。
NATIVE_CONTROLS = {
    "range": (r'<input[^>]+type="range"', r"input\[type=.range.\]::-webkit-slider-runnable-track"),
}


def check_native_controls(html, warns):
    own = VENDOR_CSS_RE.sub("", html)
    for name, (uses, styled) in NATIVE_CONTROLS.items():
        if re.search(uses, html, re.I) and not re.search(styled, own):
            warns.append(
                f"页面用了原生 {name} 控件，但没有任何裸 `input[type={name}]` 的样式规则："
                "basecoat 只管 .field / .input 两种包裹，别的壳一律落回系统外观。"
                "从 assets/shell.html 重新起手，或把那段滑块样式补回来")


# ── 在默认浏览器里打开（--open）────────────────────────────────────
def open_page(path):
    """用系统默认浏览器打开生成好的页面。返回 True 表示已发起。"""
    import shutil
    import subprocess

    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
        return True
    import os

    if os.name == "nt":
        # os.startfile 是 Windows 的 ShellExecute，走的就是「默认浏览器/默认关联程序」
        startfile = getattr(os, "startfile", None)
        if startfile:
            startfile(str(path))
            return True
        return False
    # Linux / BSD / WSL：xdg-open 是桌面标准；WSL 下优先 wslview（wslu），
    # 它会把路径翻译成 Windows 侧 UNC 路径再用宿主默认浏览器打开
    for cmd in ("wslview", "xdg-open"):
        exe = shutil.which(cmd)
        if exe:
            subprocess.run([exe, str(path)], check=False)
            return True
    return False


# ── 字体栈 ──────────────────────────────────────────────────────────────
# 字体是这样一类东西：写错的表现不是崩，是变丑，而变丑没有退出码。家族名少一个词
# （"Source Han Serif SC" 少了 " VF"）浏览器不报错，安静地落到栈里下一个系统字体，
# 中文从此一直是 Songti SC —— 直到有人觉得「怎么这么细」。所以把「栈里每个家族名
# 都必须有出处」变成一道闸。
#
# 出处有两种：在下面这张已知名单里，或者页面自己有对应的 @font-face。
# 名单只收真实存在的家族名；拿不准的新字体请连 @font-face 一起加。
KNOWN_FAMILIES = {
    # 拉丁 / 系统
    "Segoe UI", "Helvetica Neue", "Times New Roman", "Iowan Old Style",
    "SF Mono", "SFMono-Regular", "Liberation Mono", "JetBrains Mono",
    "JetBrains Maple Mono", "Cascadia Code", "Fira Code", "IBM Plex Mono",
    # 中文
    "PingFang SC", "PingFang TC", "Hiragino Sans GB", "Microsoft YaHei",
    "Songti SC", "STSong", "STHeiti", "SimSun", "SimHei",
    "Source Han Serif SC VF", "Source Han Serif SC",
    "Source Han Sans SC VF", "Source Han Sans SC",
    "Noto Serif CJK SC", "Noto Serif SC", "Noto Sans CJK SC", "Noto Sans SC",
    "LXGW WenKai", "Sarasa Gothic SC", "Sarasa Mono SC",
    # 日文 / 韩文
    "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", "Apple SD Gothic Neo",
}
FONT_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}
# 通用族。字体栈必须以其中之一收尾，否则最后一步匹配失败时落到浏览器默认字体
GENERIC_FAMILIES = {"serif", "sans-serif", "monospace", "cursive", "fantasy",
                    "system-ui", "ui-serif", "ui-sans-serif", "ui-monospace",
                    "ui-rounded", "math", "emoji", "fangsong"}
GF_FAMILY_RE = re.compile(r"family=([^:&]+)")
FONT_TOKEN_RE = re.compile(r"--font-[a-z-]+\s*:([^;]+);")
FACE_FAMILY_RE = re.compile(r"@font-face\s*\{[^}]*?font-family:\s*[\"\']([^\"\']+)", re.S)


def check_font_stacks(html, warns, errors):
    html = VENDOR_CSS_RE.sub("", html)
    declared = set(FACE_FAMILY_RE.findall(html))

    # 网络字体：取不到时必须还有得可落。这是「自包含」这条规矩为字体开的口子的代价。
    webfonts = set()
    for href in re.findall(r'href="https?://fonts\.googleapis\.com/[^"]+"', html):
        for fam in GF_FAMILY_RE.findall(href.replace("&amp;", "&")):
            webfonts.add(fam.replace("+", " "))

    stacks = {}
    for m in re.finditer(r"(--font-[a-z-]+)\s*:([^;]+);", html):
        raw = re.sub(r"/\*.*?\*/", " ", m.group(2), flags=re.S)
        stacks[m.group(1)] = [x.strip().strip("\"'") for x in raw.split(",") if x.strip()]

    for token, families in stacks.items():
        if families[-1] not in GENERIC_FAMILIES:
            errors.append(
                f"{token} 没有以通用族收尾（现在是 `{families[-1]}`）："
                "栈里每一个都没匹配上时会落到浏览器默认字体，中文尤其难看。"
                "结尾补 serif / sans-serif / monospace")
        for i, fam in enumerate(families):
            if fam in webfonts and not any(f not in webfonts for f in families[i + 1:]):
                errors.append(
                    f"{token} 里的网络字体 `{fam}` 后面没有任何本地兜底："
                    "Google Fonts 取不到时（离线、被墙、请求失败）这个位置就空了。"
                    "网络字体后面必须跟系统字体，再以通用族收尾")

    seen = set()
    for m in FONT_TOKEN_RE.finditer(html):
        for family in re.findall(r"[\"\']([^\"\']+)[\"\']", m.group(1)):
            if family in KNOWN_FAMILIES or family in declared or family in seen:
                continue
            seen.add(family)
            warns.append(
                f"字体栈里的 \"{family}\" 既不在已知家族名单里，页面也没有对应的 "
                "@font-face：写错一个字母的表现是静默回退到下一个字体，不会报错。"
                "确认名字无误就把它加进 build.py 的 KNOWN_FAMILIES")
    # local() 引用的家族名同样是「写错就静默失效」，一并核一遍
    for family in re.findall(r"local\(\s*[\"\']([^\"\']+)[\"\']\s*\)", html):
        if family not in KNOWN_FAMILIES and family not in seen:
            seen.add(family)
            warns.append(
                f"@font-face 的 local(\"{family}\") 不在已知家族名单里："
                "这个名字要是错的，这条 src 就是死的，而页面看起来一切正常")


# ── SVG 图 ─────────────────────────────────────────────────────────────
# references/diagrams.md 里能机械判定的两条：斜线直连（规则 1）与无障碍契约。
# lucide 图标不查：那是 24×24 的装饰性 path，斜线、无 <title> 都是它的正常形态。
# 几何级规则（遮罩重叠、6–10px 间隙）要解析坐标，留在眼睛关，脚本不查。
SVG_BLOCK_RE = re.compile(r"<svg\b([^>]*)>(.*?)</svg>", re.S | re.I)
LINE_TAG_RE = re.compile(r"<line\b[^>]*?/?>", re.I)
LINE_ATTR_RE = re.compile(r'\b(x[12]|y[12])="(-?[\d.]+)"')


def check_svgs(html, warns, errors):
    for m in SVG_BLOCK_RE.finditer(html):
        attrs, body = m.group(1), m.group(2)
        if "lucide" in attrs or 'aria-hidden="true"' in attrs:
            continue
        missing = []
        if 'role="img"' not in attrs:
            missing.append('role="img"')
        if "aria-labelledby" not in attrs:
            missing.append("aria-labelledby")
        if not re.search(r"<title[\s>]", body):
            missing.append("<title>")
        if not re.search(r"<desc[\s>]", body):
            missing.append("<desc>")
        if missing:
            snippet = re.sub(r"\s+", " ", m.group(0)[:80]).strip()
            warns.append(f"SVG 图缺少 {'、'.join(missing)}（{snippet}…）：读屏器拿不到这张图的内容。"
                         "契约见 references/diagrams.md「无障碍 SVG 契约」；"
                         "纯装饰图写 aria-hidden=\"true\"")
        diagonals = []
        for line in LINE_TAG_RE.findall(body):
            nums = dict(LINE_ATTR_RE.findall(line))
            if len(nums) < 4:
                continue
            try:
                x1, y1, x2, y2 = (float(nums[k]) for k in ("x1", "y1", "x2", "y2"))
            except ValueError:
                continue
            if x1 != x2 and y1 != y2:
                diagonals.append(f"({x1:g},{y1:g})→({x2:g},{y2:g})")
        if diagonals:
            shown = "、".join(diagonals[:3]) + (f" 等 {len(diagonals)} 处" if len(diagonals) > 3 else "")
            errors.append(f"SVG 里有斜线直连：{shown}。不共轴的节点之间必须走圆角直角肘形线"
                          "（references/diagrams.md 规则 1 有 path 公式），斜线没有例外")


# ── <main> 直接子元素 ────────────────────────────────────────────────────
# 骨架的间距节奏全部挂在 `main > section > * + *` 上（56/40/20/12 四级）。
# 内容不包 section 时这四条规则一条都不命中，整页间距塌成零 —— 而且只有人眼看得出来。
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img",
             "input", "link", "meta", "param", "source", "track", "wbr"}


class MainChildren(HTMLParser):
    """收集 <main> 的直接子元素标签名（按出现顺序，可重复）。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = None          # None 还没进 main，负数表示已经出来了
        self.children = []

    def _inside(self):
        return self.depth is not None and self.depth > 0

    def handle_starttag(self, tag, attrs):
        if self.depth is None:
            if tag == "main":
                self.depth = 1
            return
        if not self._inside():
            return
        if self.depth == 1:
            self.children.append(tag)
        if tag not in VOID_TAGS:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        if self._inside() and self.depth == 1:
            self.children.append(tag)

    def handle_endtag(self, tag):
        if not self._inside() or tag in VOID_TAGS:
            return
        self.depth -= 1


def main_children(html):
    p = MainChildren()
    p.feed(html)
    return p.children


# ── 自造 grid 容器 ──────────────────────────────────────────────────
# 隐式轨道溢出（anti-patterns.md #3）：`display: grid` 不写
# `grid-template-columns` 时，隐式 auto 轨道按内容 max-content 计宽，
# 窄屏时文档宽超出视口（实测 500px 视口被撑到 596px）。
# 渲染关只能抓到溢出症状，这条指根因。
RULE_BLOCK_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def check_grid_tracks(html, warns):
    own = VENDOR_STYLE_RE.sub("", html)
    seen = set()
    for m in RULE_BLOCK_RE.finditer(own):
        # 先剥 CSS 注释再判断：注释里提到 grid-template-columns 字样不能算写了模板
        body = re.sub(r"/\*.*?\*/", " ", m.group(2))
        if not re.search(r"display\s*:\s*grid", body):
            continue
        if re.search(r"grid-template-columns|grid-template-areas", body):
            continue
        sel = re.sub(r"\s+", " ", m.group(1)).strip()[:60]
        if sel in seen:
            continue
        seen.add(sel)
        warns.append(
            f"`{sel}` 是 grid 但没写 grid-template-columns：隐式 auto 轨道按内容"
            " max-content 计宽，窄屏会横向溢出。单列写 1fr，多列抄 layouts.md 里"
            "带 minmax(min(100%,…),…) 的写法（anti-patterns.md #3）")


def fail(msg):
    print(f"ERROR  {msg}")
    return 1


# ── 合成 ────────────────────────────────────────────────────────────────

def read_css(style):
    path = VENDOR / "basecoat.min.css" if style == "vega" else VENDOR / "styles" / f"{style}.min.css"
    if not path.exists():
        sys.exit(f"ERROR  找不到风格包 {style}：{path}")
    return path.read_text(encoding="utf-8")


def inline_icons(html, errors):
    sprite = (VENDOR / "lucide-sprite.svg").read_text(encoding="utf-8")
    symbols = dict(SYMBOL_RE.findall(sprite))
    used = set()

    def sub(m):
        name = m.group("name")
        used.add(name)
        body = symbols.get(name)
        if body is None:
            errors.append(f"未知的 lucide 图标名 `{name}`（sprite 里没有这个 symbol）")
            return m.group(0)
        attrs = (m.group("pre") + " " + m.group("post")).strip()
        cls = re.search(r'class="([^"]*)"', attrs)
        classes = f"lucide lucide-{name}" + (f" {cls.group(1)}" if cls else "")
        keep = re.sub(r'\sclass="[^"]*"', "", " " + attrs).strip()
        labelled = "aria-label=" in keep
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" class="{classes}" width="1em" height="1em"'
            f' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
            f' stroke-linecap="round" stroke-linejoin="round"'
            f'{"" if labelled else " aria-hidden=\"true\""}'
            f'{" " + keep if keep else ""}>{body.strip()}</svg>'
        )

    return ICON_RE.sub(sub, html), used


def inline_highlight(html, warns):
    """按页面实际用到的 language-* 拼出高亮脚本。返回 (js, 语言名集合)。

    每种语言是一份独立的规则表（几百字节到 3 KB），带上谁由页面决定；
    core.js 是共用的分词器（1.7 KB）。全部语言加起来也才 30 KB，但没必要。
    """
    if not HL_DIR.exists():
        return "", set()

    wanted = {}  # 文件名 -> 页面上写的语言名（可能多个别名指向同一个文件）
    for name in sorted(set(CODE_LANG_RE.findall(html))):
        if name in HL_SKIP:
            continue
        stem = HL_ALIASES.get(name, name)
        if not (HL_DIR / "languages" / f"{stem}.js").exists():
            warns.append(f"language-{name} 没有对应的语法规则，该代码块不着色"
                         f"（可用语言见 assets/vendor/shj/languages/）")
            continue
        wanted.setdefault(stem, set()).add(name)
    if not wanted:
        return "", set()

    # 语言之间会互相引用（go 的注释里嵌 todo，md 里嵌 bash/html/js），跟着 sub 递归带上
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
            warns.append(f"语法规则 {stem}.js 的格式不认识，跳过")
            continue
        # 包一层 IIFE：语言文件内部的临时变量不外泄到全局
        parts.append(f'window.__SHJ_LANGS["{stem}"]=(function(){{{src[:m.start()]}'
                     f"return {m.group(1)};}})();")
        for alias in sorted(wanted.get(stem, set()) - {stem}):
            parts.append(f'window.__SHJ_LANGS["{alias}"]=window.__SHJ_LANGS["{stem}"];')
    parts.append((HL_DIR / "core.js").read_text(encoding="utf-8"))
    return "".join(parts), {n for names in wanted.values() for n in names}


def build(html, style, errors):
    changed = False

    if CSS_SLOT in html:
        html = html.replace(CSS_SLOT, f'<style {CSS_MARK}>{read_css(style)}</style>', 1)
        changed = True
    elif CSS_MARK in html:
        if style != "vega":
            print(f"注意   页面已内联过 CSS，--style {style} 未生效。"
                  "换风格要从 assets/shell.html 重新起手。")
    else:
        errors.append(f"缺少 {CSS_SLOT} 占位符，也没有已内联的 basecoat CSS")

    html, used = inline_icons(html, errors)
    if used:
        changed = True

    langs, warns = set(), []
    if JS_SLOT in html:
        slot = ""
        needs_js = any(re.search(rf'class="[^"]*\b{c}\b', html) for c in JS_COMPONENTS)
        if needs_js:
            js = (VENDOR / "basecoat.min.js").read_text(encoding="utf-8")
            slot += f'<script {JS_MARK}>{js}</script>'
        hl, langs = inline_highlight(html, warns)
        if hl:
            # 同步执行，位置在代码块之后 —— 首绘时已着色，不会闪一下再变色
            slot += f'<script {HL_MARK}>{hl}</script>'
        html = html.replace(JS_SLOT, slot, 1)
        changed = True
    elif HL_MARK not in html and "</body>" in html:
        # 占位符已经用掉的旧页面：仍然可以补上高亮，这样升级 skill 后不必重做整页
        hl, langs = inline_highlight(html, warns)
        if hl:
            html = html.replace("</body>", f"    <script {HL_MARK}>{hl}</script>\n  </body>", 1)
            changed = True

    return html, changed, used, langs, warns


# ── 自检 ────────────────────────────────────────────────────────────────

def check(html, path):
    errors, warns = [], []
    stripped = re.sub(r"<!--.*?-->", "", html, flags=re.S)

    # 页面必须离线可开。唯一例外是 Google Fonts —— 它取不到时会静默回退到系统字体栈，
    # 页面照常可读（骨架把它写成异步加载，首屏也不会被卡住）。别的外部资源没有这个性质。
    for m in re.finditer(r'<(link|script|img|iframe|source|video|audio|use)\b[^>]*'
                         r'(?:src|href|xlink:href)="(https?:)?//([^"/]+)[^"]*"', stripped, re.I):
        if m.group(3).lower() in FONT_HOSTS:
            continue
        errors.append(f"外部资源引用：{m.group(0)[:90]}…（页面必须离线可开）")
    for m in re.finditer(r'url\(\s*["\']?(?:https?:)?//', stripped):
        errors.append("CSS 里有外部 url() 引用")
    if re.search(r"@import\s+url\(\s*[\"']?(?:https?:)?//", stripped):
        errors.append("CSS 里有外部 @import")
    # 只用 local() 的 @font-face 永远不会联网（配平面就是这么写的），别误报
    for face in re.findall(r"@font-face\s*\{[^}]*\}", stripped, re.S):
        srcs = re.findall(r"url\(\s*[\"']?([^)\"']+)", face)
        if srcs and not all(u.startswith("data:") for u in srcs):
            warns.append("有 @font-face 的 src 不是 data: URI，页面可能会去联网取字体："
                         f"{srcs[0][:60]}")
            break

    for slot in (CSS_SLOT, JS_SLOT):
        if slot in html:
            errors.append(f"占位符 {slot} 未被替换")
    if CSS_MARK not in html:
        errors.append("页面里没有内联的 basecoat CSS")

    for m in re.finditer(r'data-lucide="([a-z0-9-]+)"', html):
        errors.append(f"data-lucide=\"{m.group(1)}\" 未被替换成内联 SVG")

    if "data-copy-md" not in html:
        errors.append("缺少「复制为 Markdown」按钮（data-copy-md）")
    if "data-theme-set" not in html:
        errors.append("缺少 light/dark/system 主题切换（data-theme-set）")
    if 'id="doc"' not in html and "data-md-root" not in html:
        errors.append("找不到 Markdown 导出根节点（#doc 或 [data-md-root]）")

    if not re.search(r'<meta[^>]+charset', html, re.I):
        errors.append("缺少 <meta charset>")
    if not re.search(r'<meta[^>]+name="viewport"', html, re.I):
        errors.append("缺少 viewport meta")
    if not re.search(r"<html[^>]+lang=", html, re.I):
        errors.append("<html> 缺少 lang 属性")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    if not title or not title.group(1).strip():
        errors.append("缺少 <title>")
    elif title.group(1).strip().upper() in ("PAGE TITLE", "UNTITLED", "DOCUMENT"):
        errors.append(f"<title> 还是骨架里的占位文本：{title.group(1).strip()}")

    for pat, label in ((r"\{\{[^}]{1,60}\}\}", "{{…}} 模板占位符"),
                       (r"Lorem ipsum", "Lorem ipsum 填充文本"),
                       (r"TODO:", "TODO 标记")):
        hits = re.findall(pat, stripped)
        if hits:
            errors.append(f"残留{label}：{hits[0][:60]}")
    gaps = re.findall(r"\[DATA NEEDED[^\]]*\]", stripped)
    for g in gaps:
        warns.append(f"缺口标记仍在页面上（须向用户点名）：{g}")

    if re.search(r"<main[^>]*>\s*(<!--.*?-->)?\s*</main>", html, re.S):
        errors.append("<main> 是空的")
    else:
        stray = [t for t in main_children(html) if t != "section"]
        if stray:
            shown = "、".join(dict.fromkeys(stray))[:60]
            errors.append(
                f"<main> 里有 {len(stray)} 个不是 <section> 的直接子元素（{shown}）："
                "骨架的间距节奏写在 `main > section > * + *` 上，不包 section 的内容"
                "拿不到任何块间距，整页会挤成一团。每个大节包一个 <section id=\"…\">。")

    # 一级标题只能有一个：多 h1 会同时搞坏目录语义与 Markdown 导出的 title 拼接规则
    h1s = re.findall(r"<h1\b", stripped)
    if len(h1s) > 1:
        errors.append(f"页面有 {len(h1s)} 个 <h1>：一级标题只能有一个，小节用 h2/h3。")

    # 行内 MathML 里的堆叠分数会把正文行高撑坏；MathML Core 不支持 bevelled，行内改写线性形式
    for m in re.finditer(r"<(p|li)\b[^>]*>(.*?)</\1>", html, re.S):
        if "<mfrac" in m.group(2):
            warns.append("正文里的行内 <math> 用了 <mfrac>，会撑坏行高："
                         "行内公式写成 `2P₀ / Δ` 的线性形式，<mfrac> 只用在 display=\"block\" 里")
            break

    # 高亮脚本发的是 class，页面没给对应规则的话代码块只会变成一色黑
    if HL_MARK in html and ".shj-syn-" not in html:
        warns.append("页面内联了语法高亮，但没有 .shj-syn-* 的配色规则："
                     "从 assets/shell.html 重新起手，或把那段 CSS 补进来")

    own = VENDOR_STYLE_RE.sub("", stripped)
    # @media print 块里的字面色是合法的：打印重置的目的就是无视主题强制白纸深字，
    # 用 var() 会循环引用。剥掉 print 块再查。
    own = re.sub(
        r"@media print\b[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", own
    )
    hard = [m.group(1) for m in HARDCODED_COLOR_RE.finditer(own)]
    if hard:
        shown = "、".join(dict.fromkeys(hard))[:80]
        warns.append(f"页面自己写死了 {len(hard)} 处颜色（{shown}）："
                     "深色主题下不会跟着变，改用 var(--color-*) / var(--tone-*) / var(--chart-*)")

    check_font_stacks(html, warns, errors)
    check_native_controls(html, warns)
    check_svgs(stripped, warns, errors)
    check_grid_tracks(stripped, warns)

    size = len(html.encode("utf-8"))
    # 体积预算：basecoat 全量内联就 ~218KB，单文件成品的常态是 250–290KB。
    # 这些页面主要走 IM / 邮件附件转发，分级预警让作者在发送前知情。
    if size > 3_000_000:
        warns.append(f"页面 {size/1e6:.1f} MB，过大：检查是否内联了大图/长代码")
    elif size > 1_000_000:
        warns.append(f"页面 {size/1e6:.1f} MB，超过 1 MB：IM/邮件转发可能被压缩或拒收")
    elif size > 400_000:
        warns.append(f"页面 {size/1e3:.0f} KB，超过 400 KB（常态 250–290 KB）："
                     "检查是否有可裁的内联内容")
    return errors, warns


# ── 渲染检查（有 Chrome 才跑）─────────────────────────────────────────────

PROBE = """
<script>addEventListener('load', function(){
  var de = document.documentElement, over = [];
  var scrolls = function(el){
    for (var p = el.parentElement; p && p !== de; p = p.parentElement) {
      var o = getComputedStyle(p).overflowX;
      if (o === 'auto' || o === 'scroll' || o === 'hidden') return true;
    }
    return false;
  };
  if (de.scrollWidth > de.clientWidth + 1) {
    document.querySelectorAll('body *').forEach(function(el){
      var r = el.getBoundingClientRect();
      if (r.width && r.right > de.clientWidth + 1 && !scrolls(el)) {
        over.push(el.tagName.toLowerCase() +
          (el.id ? '#' + el.id : '') +
          (typeof el.className === 'string' && el.className.trim()
            ? '.' + el.className.trim().split(/\\s+/).slice(0,2).join('.') : '') +
          '(右缘 ' + Math.round(r.right) + 'px)');
      }
    });
  }
  document.title = 'PROBE|' + de.scrollWidth + '|' + de.clientWidth + '|' + over.slice(0, 4).join('  ');
});</script>
"""

CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


def find_chrome():
    import shutil
    for p in CHROME_PATHS:
        if Path(p).exists():
            return p
    for n in ("google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(n)
        if p:
            return p
    return None


# 无头 Chrome 把窗口宽度钳在 500px，比这更窄的视口测不到 —— 390px 只能人眼验。
def render_check(page, widths=(500, 1280)):
    """返回 (issues, measured, ran)。ran=False 表示没有浏览器，这道关没跑。"""
    import subprocess, tempfile
    chrome = find_chrome()
    if not chrome:
        return [], [], False

    html = page.read_text(encoding="utf-8")
    issues, measured = [], []
    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "probe.html"
        probe.write_text(html + PROBE, encoding="utf-8")
        for w in widths:
            try:
                out = subprocess.run(
                    [chrome, "--headless", "--disable-gpu", "--no-sandbox",
                     "--virtual-time-budget=4000", f"--window-size={w},900",
                     "--dump-dom", probe.as_uri()],
                    capture_output=True, text=True, timeout=90).stdout
            except Exception as e:
                return [f"渲染检查跑不起来：{e}"], [], False
            m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)</title>", out, re.S)
            if not m:
                issues.append(f"{w}px：探针没返回结果（页面 JS 可能报错，去控制台看）")
                continue
            sw, cw, who = int(m.group(1)), int(m.group(2)), m.group(3).strip()
            measured.append(cw)
            if sw > cw + 1:
                issues.append(f"{cw}px 视口横向溢出：文档宽 {sw}px"
                              + (f"；越界元素：{who}" if who else ""))
    return issues, measured, True


def main():
    ap = argparse.ArgumentParser(description="内联资产并自检 show-me-html 页面")
    ap.add_argument("page", type=Path)
    ap.add_argument("--style", default="vega", choices=STYLES)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--no-render", action="store_true", help="跳过无头浏览器的溢出检查")
    ap.add_argument(
        "--open",
        action="store_true",
        help="自检通过后用系统默认浏览器打开（macOS: open / Windows: os.startfile / Linux·WSL: wslview→xdg-open）",
    )
    args = ap.parse_args()

    if not args.page.exists():
        sys.exit(f"ERROR  找不到文件：{args.page}")
    html = args.page.read_text(encoding="utf-8")

    build_errors, build_warns = [], []
    if not args.check_only:
        html, changed, used, langs, build_warns = build(html, args.style, build_errors)
        if changed:
            args.page.write_text(html, encoding="utf-8")
            print(f"已合成  {args.page}  风格={args.style}  图标={len(used)} 个"
                  f"{'  语法=' + ','.join(sorted(langs)) if langs else ''}"
                  f"  体积={len(html.encode('utf-8'))/1024:.0f} KB")

    errors, warns = check(html, args.page)
    errors = build_errors + errors
    warns = build_warns + warns

    rendered, measured = False, []
    if not args.no_render and not errors:
        render_issues, measured, rendered = render_check(args.page)
        errors += render_issues

    for w in warns:
        print(f"WARN   {w}")
    for e in errors:
        print(f"ERROR  {e}")

    if errors:
        print(f"\n自检未通过：{len(errors)} 个错误。")
        return 1

    print(f"自检通过{f'（{len(warns)} 个警告需逐条判断）' if warns else ''}。")
    if rendered:
        print(f"渲染检查：{' / '.join(f'{w}px' for w in measured)} 无横向溢出。"
              "（无头 Chrome 最窄只到 500px，更窄的屏幕仍需人眼过一遍。）")
    elif not args.no_render:
        print("渲染检查未运行：找不到 Chrome/Chromium。横向溢出没有被验证过，"
              "自己在浏览器里拉一遍窄屏，不要报「已验证」。")

    if args.open:
        if errors:
            print("--open 未执行：自检有错误，先修再开。")
        elif not open_page(args.page.resolve()):
            print("--open 未执行：找不到可用的打开命令（macOS 需要 open，"
                  "Linux/WSL 需要 wslview 或 xdg-open，Windows 用 os.startfile）。")
        else:
            print(f"已在默认浏览器打开 {args.page}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
