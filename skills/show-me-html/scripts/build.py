#!/usr/bin/env python3
"""show-me-html 的合成与自检工具。

用法：
    python3 build.py page.html                # 内联资产 + 自检
    python3 build.py page.html --check-only   # 只跑自检，不改文件
    python3 build.py page.html --open         # 自检通过后用系统默认浏览器打开
    python3 build.py page.html --pdf          # 自检通过后出一份 A4 PDF

做四件事，然后自检：
  1. 把 show-me-html 自有 CSS 内联到 <!--SHOW-ME:CSS--> 处。
  2. 把用到的 lucide 图标从 sprite 里抽出来，替换 data-lucide="name"。
  3. 页面用到需要 JS 的组件时，把保留的 basecoat JS 内联到 <!--SHOW-ME:JS--> 处。
  4. 按页面实际出现的 language-* 内联语法高亮：只带上用到的语言。
  5. 注入骨架行为脚本 assets/shell.js（主题切换、目录、Markdown 导出等）。每次构建重算，旧页面重建也拿到最新骨架。

对已合成的文件重复运行是安全的：占位符已消失时只跑自检。
"""

import argparse
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

ASSETS = Path(__file__).resolve().parent.parent / "assets"
VENDOR = ASSETS / "vendor"
CSS_PATH = ASSETS / "show-me.css"
RECIPES = (
    "approach-compare", "visual-directions", "code-review", "pr-writeup",
    "code-understanding", "design-system-ref", "component-variants",
    "animation-proto", "interaction-proto", "status-report", "incident-report",
    "implementation-plan", "slide-deck", "flowchart", "svg-illustrations",
    "feature-explainer", "concept-explainer", "triage-board", "config-editor",
    "text-tuner", "share-card",
)

CSS_SLOT = "<!--SHOW-ME:CSS-->"
JS_SLOT = "<!--SHOW-ME:JS-->"
JS_BEGIN = "<!--SHOW-ME:JS:BEGIN-->"
JS_END = "<!--SHOW-ME:JS:END-->"
JS_BLOCK_RE = re.compile(re.escape(JS_BEGIN) + r".*?" + re.escape(JS_END), re.S)
CSS_MARK = 'data-show-me="css"'
JS_MARK = 'data-show-me="js"'
HL_MARK = 'data-show-me="hl"'
CHART_MARK = 'data-show-me="charts"'
CHART_JS = ASSETS / "charts.js"
MATH_MARK = 'data-show-me="math"'
SHELL_MARK = 'data-show-me="shell"'
SHELL_JS = ASSETS / "shell.js"
# 骨架脚本改为构建注入之前，页面带着从 shell.html 复制来的普通 <script>；按各版本骨架块的段首注释认出来，重建时删掉
LEGACY_SHELL_RE = re.compile(r"[ \t]*<script>\s*/\* ── (?:定尺卡|滑块填充|代码工具条|主题三态切换).*?</script>[ \t]*\n?", re.S)
MATH_SCRIPT = Path(__file__).resolve().parent / "math.mjs"
# 作者写 LaTeX：行内 \( … \) 或 $ … $（pandoc 规则），块级 \[ … \] 或 $$ … $$。
MATH_DELIM_RE = re.compile(r"\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|(?:^|[^\\$])\$(?=\S)[^$\n]*?\S\$(?!\d)")
CODE_ISLAND_RE = re.compile(r"<(pre|code|script|style)\b[\s\S]*?</\1\s*>", re.I)

# 需要 basecoat JS 才能工作的组件。命中任一即内联 JS。
JS_COMPONENTS = (
    "dropdown-menu", "popover", "select", "combobox", "command",
    "sidebar", "drawer", "tabs", "toaster", "chart",
)

# 页面自己写死的颜色。show-me-html 自有 CSS 不算。
SYSTEM_STYLE_RE = re.compile(r'<style data-show-me="(?:css|palette|math)"[^>]*>.*?</style>', re.S)
SYSTEM_CSS_RE = re.compile(r'<style data-show-me="css"[^>]*>.*?</style>', re.S)
SYSTEM_SCRIPT_RE = re.compile(r'<script data-show-me="(?:js|hl|charts|shell)"[^>]*>.*?</script>', re.S)
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
    "kotlin": "kt", "kts": "kt",
}
# diff 由页面自己的 .d-add / .d-del 着色，text/plain 是结构视图（调用树、文件树）—— 都不碰
HL_SKIP = {"diff", "text", "plain", "plaintext", "txt"}


# ── 原生控件 ────────────────────────────────────────────────────────────
# 和 <section> 那条闸是同一种失败模式：没命中选择器，不报错，只是难看。
# show-me.css 同时覆盖裸 range、`.field` 和 `.input` 包裹。这道闸防止有人误删或改窄
# 裸控件规则，导致自定义壳里的滑块退回系统外观。
NATIVE_CONTROLS = {
    "range": (r'<input[^>]+type="range"', r"input\[type=.range.\]::-webkit-slider-runnable-track"),
}


def check_native_controls(html, warns):
    for name, (uses, styled) in NATIVE_CONTROLS.items():
        if re.search(uses, html, re.I) and not re.search(styled, html):
            warns.append(
                f"页面用了原生 {name} 控件，但 show-me.css 没有裸 `input[type={name}]` 样式："
                "自定义壳里的控件会落回系统外观；恢复 owned CSS 的裸控件规则。")


def check_accessible_authored_controls(html, errors):
    """拦截两种窄而可证的鼠标专用控件；复杂委托交互仍由人工门禁负责。"""
    markup = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", "", html, flags=re.I | re.S)
    for tag in re.findall(r"<input\b[^>]*>", markup, flags=re.I):
        input_type = re.search(r'\btype=["\']([^"\']+)', tag, flags=re.I)
        if input_type and input_type.group(1).lower() == "hidden":
            continue
        hidden = re.search(r"\shidden(?:\s|=|/?>)", tag, flags=re.I) or re.search(
            r'\bstyle=["\'][^"\']*(?:display\s*:\s*none|visibility\s*:\s*hidden)',
            tag,
            flags=re.I,
        )
        if hidden and "data-accessible-replacement" not in tag:
            errors.append(
                "隐藏原生控件没有可访问替代：保留原生控件可聚焦，或在完成等价键盘/ARIA 控件后"
                "加 data-accessible-replacement 记录该契约"
            )
            break

    for match in re.finditer(
        r"<(div|span|li|section|article|svg|g|path)\b([^>]*)>", markup, flags=re.I
    ):
        attrs = match.group(2)
        if not re.search(r"\bonclick\s*=", attrs, flags=re.I):
            continue
        role = re.search(r'\brole=["\'](button|link)["\']', attrs, flags=re.I)
        focusable = re.search(r'\btabindex=["\']?0["\']?', attrs, flags=re.I)
        keyboard = re.search(r"\bonkey(?:down|up|press)\s*=", attrs, flags=re.I)
        if not (role and focusable and keyboard):
            errors.append(
                f"非语义元素 <{match.group(1)}> 只有点击路径：改用 button/a，或同时提供"
                " role、tabindex=0 与键盘处理"
            )
            break


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
    "IBM Plex Sans", "Newsreader",
    # 数学（本机装了哪支用哪支；一支都没有时落到 math 通用族再到衬线）
    "Latin Modern Math", "STIX Two Math", "Cambria Math", "Noto Sans Math",
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
SVG_ID_RE = re.compile(r'\sid="([^"]+)"')


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

    # 同一张图画宽窄两版时最容易撞 id：url(#arrow) 会指向排在前面、可能正被隐藏的那一版
    ids = [i for m in SVG_BLOCK_RE.finditer(html) for i in SVG_ID_RE.findall(m.group(0))]
    dup = list(dict.fromkeys(i for i in ids if ids.count(i) > 1))
    if dup:
        errors.append(f"SVG 里有重复 id：{'、'.join(dup[:5])}。marker 引用会指错图、读屏会读错标题；"
                      "每张图（含宽窄两版）的 id 用各自的前缀（references/diagrams.md「窄屏另画一版」）")


# ── <main> 直接子元素 ────────────────────────────────────────────────────
# 骨架的间距节奏全部挂在 `main > section > * + *` 上（56/40/20/12 四级）。
# 内容不包 section 时这四条规则一条都不命中，整页间距塌成零 —— 而且只有人眼看得出来。
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img",
             "input", "link", "meta", "param", "source", "track", "wbr"}


class MainChildren(HTMLParser):
    """收集 <main> 的直接子元素标签名（按出现顺序，可重复）。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth: int | None = None  # None 还没进 main，0 表示已经出来了
        self.children: list[str] = []

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
        if self.depth is None or self.depth <= 0 or tag in VOID_TAGS:
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
# 选择器只从文本开头或 { } 之后起算：不锚定时，每个起点都会把一长段无花括号的文本
# （内联 base64 图片、长正文）扫到底再失败，耗时随长度平方增长，1.6 MB 的页面会卡死。
RULE_BLOCK_RE = re.compile(r"(?:^|(?<=[{}]))([^{}]+)\{([^{}]*)\}")
AUTHORED_STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)


def check_grid_tracks(html, warns):
    seen = set()
    for css in AUTHORED_STYLE_RE.findall(SYSTEM_STYLE_RE.sub("", html)):
        for m in RULE_BLOCK_RE.finditer(css):
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

def read_css():
    if not CSS_PATH.exists():
        sys.exit(f"ERROR  找不到自有样式：{CSS_PATH}")
    return CSS_PATH.read_text(encoding="utf-8")


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


CJK_RE = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")
BLOCK_MATH_RE = re.compile(r"\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)")


def single_dollar_spans(text):
    """与 math.mjs 同一套扫描：pandoc 规则，另加「内容含中文（\\text{} 之外）不算公式」。
    被拒的候选只跳过它的开 $，这样「$8 不是公式；$E = mc^2$」里后一段仍能命中。"""
    i, n = 0, len(text)
    while i < n:
        i = text.find("$", i)
        if i < 0:
            return
        if (i and text[i - 1] in "\\$") or i + 1 >= n or text[i + 1].isspace() or text[i + 1] == "$":
            i += 1
            continue
        j = text.find("$", i + 1)
        while j > 0 and (text[j - 1].isspace() or text[j - 1] == "\\"):
            j = text.find("$", j + 1)
        if j < 0:
            return
        inner = text[i + 1 : j]
        ok = "\n" not in inner and not (j + 1 < n and text[j + 1].isdigit()) \
            and not CJK_RE.search(re.sub(r"\\text\{[^}]*\}", "", inner))
        if ok:
            yield i, j + 1
            i = j + 1
        else:
            i += 1


def has_math_source(html):
    """页面正文里还有没编译的 LaTeX 定界符（代码、脚本、样式内部不算）。"""
    text = CODE_ISLAND_RE.sub("", html)
    return bool(BLOCK_MATH_RE.search(text)) or any(True for _ in single_dollar_spans(text))


def compile_math(page, errors, warns):
    """作者写 LaTeX，这里用 vendor 的 Temml 编译成 MathML 内联。返回是否改写了文件。

    需要 node：Temml 是 JS 库，没有 Python 等价物。找不到 node 时这是 ERROR ——
    留着 $…$ 的页面公式不会显示，不能算合成完成。
    """
    import shutil, subprocess
    html = page.read_text(encoding="utf-8")
    if not has_math_source(html):
        return False
    node = shutil.which("node")
    if not node:
        errors.append("页面里有 LaTeX 公式（$…$ / \\(…\\)），但找不到 node 来编译成 MathML；"
                      "装 Node.js 后重跑，或手写 <math> 标签")
        return False
    out = subprocess.run([node, str(MATH_SCRIPT), str(page)], capture_output=True, text=True)
    if out.returncode != 0:
        errors.append("公式编译失败：" + (out.stderr.strip().splitlines() or ["未知错误"])[-1])
        return False
    for line in out.stdout.splitlines():
        if line.startswith("WARN"):
            warns.append(line[4:].strip())
    return True


def runtime_scripts(html, warns):
    """按页面当前内容算出应当内联的运行时脚本。每次构建都重算：加了就补，删了就去。
    返回 (拼好的 <script> 串, 语言名集合)。判断时先剥掉已内联的系统脚本，免得脚本自身的文本误命中。"""
    authored = SYSTEM_SCRIPT_RE.sub("", html)
    slot = ""
    if needs_basecoat(authored):
        slot += f'<script {JS_MARK}>{(VENDOR / "basecoat.min.js").read_text(encoding="utf-8")}</script>'
    if re.search(r'\bdata-chart=', authored):
        # 图表运行时：页面用 data-chart 标记图型时内联，图型代码本身由页面自带
        slot += f'<script {CHART_MARK}>{CHART_JS.read_text(encoding="utf-8")}</script>'
    hl, langs = inline_highlight(authored, warns)
    if hl:
        # 同步执行，位置在代码块之后 —— 首绘时已着色，不会闪一下再变色
        slot += f'<script {HL_MARK}>{hl}</script>'
    # 骨架放最后：原先它就紧跟在这些运行时脚本之后，页面脚本与它的相对顺序因此不变
    slot += f'<script {SHELL_MARK}>{SHELL_JS.read_text(encoding="utf-8")}</script>'
    return slot, langs


def needs_basecoat(html):
    return any(re.search(rf'class="[^"]*\b{c}\b', html) for c in JS_COMPONENTS)


def build(html, errors):
    changed = False

    css_tag = f'<style {CSS_MARK}>{read_css()}</style>'
    if CSS_SLOT in html:
        html = html.replace(CSS_SLOT, css_tag, 1)
        changed = True
    elif CSS_MARK in html:
        refreshed, count = re.subn(
            r'<style\b(?=[^>]*\bdata-show-me=["\']css["\'])[^>]*>.*?</style>',
            lambda _match: css_tag,
            html,
            count=1,
            flags=re.I | re.S,
        )
        if count != 1:
            errors.append("已内联的 show-me-html CSS 标记无法定位")
        elif refreshed != html:
            html = refreshed
            changed = True
    else:
        errors.append(f"缺少 {CSS_SLOT} 占位符，也没有已内联的 show-me-html CSS")

    html, used = inline_icons(html, errors)
    if used:
        changed = True

    warns = []
    legacy = LEGACY_SHELL_RE.search(html)
    slot, langs = runtime_scripts(html, warns)
    block = f"{JS_BEGIN}{slot}{JS_END}"
    if JS_SLOT in html:
        new = html.replace(JS_SLOT, block, 1)
    elif JS_BEGIN in html:
        new = JS_BLOCK_RE.sub(lambda _m: block, html, count=1)
    else:
        # 本改动之前合成的旧页面：没有哨兵。拿掉散落的系统脚本，在原位置（没有就在 </main> 后第一个 <script> 前）放回哨兵块
        first = SYSTEM_SCRIPT_RE.search(html) or legacy
        if first:
            anchor = first.start()
        else:
            main_end = html.find("</main>")
            nxt = html.find("<script", main_end) if main_end >= 0 else -1
            anchor = nxt if nxt >= 0 else html.rfind("</body>")
        if anchor < 0:
            errors.append("找不到内联运行时脚本的位置（没有 <!--SHOW-ME:JS--> 占位符，也没有 </body>）")
            return html, changed, used, langs, warns
        head = html[:anchor]
        tail = SYSTEM_SCRIPT_RE.sub("", html[anchor:])
        new = head + block + tail
    new = LEGACY_SHELL_RE.sub("", new)
    if new != html:
        html = new
        changed = True

    return html, changed, used, langs, warns


# ── 自检 ────────────────────────────────────────────────────────────────

def writes_dynamic_html(script):
    """innerHTML / outerHTML 赋值（含 +=，不含 == 比较）或 insertAdjacentHTML 的 HTML 参数，
    只要不是一整个字符串字面量就算动态写入：拼接、模板字符串、变量都可能带进未转义的内容。"""
    literal = re.compile(r"""\s*(["'])[^"'\\]*\1\s*""")
    for m in re.finditer(r"\.(?:innerHTML|outerHTML)\s*\+?=(?!=)([^;\n]*)", script):
        if not literal.fullmatch(m.group(1)):
            return True
    for m in re.finditer(r"\.insertAdjacentHTML\(\s*[^,()]+,([^;\n]*)\)", script):
        if not literal.fullmatch(m.group(1)):
            return True
    return False


def check(html, path, allow_legacy_recipe=False):
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
        errors.append("页面里没有内联的 show-me-html CSS")

    body = re.search(r"<body\b([^>]*)>", stripped, re.I)
    recipe = re.search(r'\bdata-recipe="([a-z0-9-]+)"', body.group(1)) if body else None
    if not recipe:
        message = "<body> 缺少 data-recipe，无法选择版式指纹"
        if allow_legacy_recipe:
            warns.append(f"历史页面：{message}；仅复检现有契约，不要求回填")
        else:
            errors.append(message)
    elif recipe.group(1) not in RECIPES:
        errors.append(
            f"不支持的 data-recipe=\"{recipe.group(1)}\"；"
            f"可选值：{', '.join(RECIPES)}"
        )

    for m in re.finditer(r'data-lucide="([a-z0-9-]+)"', html):
        errors.append(f"data-lucide=\"{m.group(1)}\" 未被替换成内联 SVG")

    authored_markup = SYSTEM_SCRIPT_RE.sub("", stripped)
    if re.search(r'\bdata-chart=', authored_markup) and CHART_MARK not in html:
        errors.append("页面有 data-chart 但没有内联图表运行时：跑一遍不带 --check-only 的 build")
    if needs_basecoat(authored_markup) and JS_MARK not in html:
        errors.append("页面用了需要 JS 的组件（tabs / dropdown-menu 等）但没有内联 basecoat JS：跑一遍不带 --check-only 的 build")
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

    authored = SYSTEM_SCRIPT_RE.sub("", stripped)
    for script in re.findall(r"<script\b[^>]*>(.*?)</script>", authored, re.S | re.I):
        if writes_dynamic_html(script):
            errors.append(
                "页面脚本把动态值写进 innerHTML/outerHTML/insertAdjacentHTML："
                "改用 textContent、DOM 构造或经过严格转义的可信片段"
            )
            break
    check_accessible_authored_controls(stripped, errors)

    # 一级标题只能有一个：多 h1 会同时搞坏目录语义与 Markdown 导出的 title 拼接规则
    h1s = re.findall(r"<h1\b", stripped)
    if len(h1s) > 1:
        errors.append(f"页面有 {len(h1s)} 个 <h1>：一级标题只能有一个，小节用 h2/h3。")

    # 眉标口吃：眉标文字与紧随其后的标题重复。数量本身不是问题——报告节律里每节一个编号眉标是正当用法
    stutters = []
    for m in re.finditer(r'<[a-z][^>]*\bclass=["\'][^"\']*\beyebrow\b[^"\']*["\'][^>]*>(.*?)</[a-z0-9]+>', stripped, flags=re.I | re.S):
        eyebrow = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        nxt = re.search(r"<h[1-3]\b[^>]*>(.*?)</h[1-3]>", stripped[m.end():], flags=re.I | re.S)
        if not eyebrow or not nxt:
            continue
        heading = re.sub(r"<[^>]+>", "", nxt.group(1)).strip()
        norm = lambda t: re.sub(r"[\s·:：,，。.\-–—]+", "", t).lower()
        a, b = norm(eyebrow), norm(heading)
        if a and b and (a in b or b in a):
            stutters.append(eyebrow)
    if stutters:
        warns.append(
            f"眉标口吃 {len(stutters)} 处（{'、'.join(stutters[:3])}）：眉标只保留标题没有的范围、状态或来源；重复标题时删掉"
        )

    ink_cards = len(re.findall(r'<[a-z][^>]*\bdata-variant=["\']ink["\']', stripped, flags=re.I))
    if ink_cards > 1:
        warns.append(
            f"页面有 {ink_cards} 块反色暗卡：反色与 hero 共用强调预算，一页只留一块给决定性的数字或结论"
        )

    if has_math_source(stripped):
        errors.append("正文里还有未编译的 LaTeX 定界符（$…$ / $$…$$ / \\(…\\)）：跑一遍不带 --check-only 的 build，"
                      "或检查定界符是否成对")

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

    own = SYSTEM_STYLE_RE.sub("", stripped)
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
    authored = SYSTEM_STYLE_RE.sub("", SYSTEM_SCRIPT_RE.sub("", stripped))
    check_svgs(authored, warns, errors)
    check_grid_tracks(stripped, warns)

    size = len(html.encode("utf-8"))
    # 这些页面主要走 IM / 邮件附件转发，分级预警让作者在发送前知情。
    if size > 3_000_000:
        warns.append(f"页面 {size/1e6:.1f} MB，过大：检查是否内联了大图/长代码")
    elif size > 1_000_000:
        warns.append(f"页面 {size/1e6:.1f} MB，超过 1 MB：IM/邮件转发可能被压缩或拒收")
    elif size > 400_000:
        warns.append(f"页面 {size/1e3:.0f} KB，超过 400 KB：检查是否有可裁的内联内容")
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
  // 盒子都没越界、越界的是盒子装不下的内容（长路径、长标识符等不断行的长串）时，上一段找不到元素：
  // 顺着 overflow 为 visible 且内容比盒子宽的子元素往下走，报最深的那一个
  if (de.scrollWidth > de.clientWidth + 1 && !over.length) {
    var deepest = function(el){
      for (var i = 0; i < el.children.length; i++) {
        var c = el.children[i];
        if (getComputedStyle(c).overflowX === 'visible' && c.scrollWidth > c.clientWidth + 1) return deepest(c);
      }
      return el;
    };
    var culprit = deepest(document.body);
    if (culprit !== document.body)
      over.push(culprit.tagName.toLowerCase() + (culprit.id ? '#' + culprit.id : '') +
        (typeof culprit.className === 'string' && culprit.className.trim()
          ? '.' + culprit.className.trim().split(/\\s+/).slice(0,2).join('.') : '') +
        '(内容比盒子宽 ' + (culprit.scrollWidth - culprit.clientWidth) + 'px)');
  }
  document.querySelectorAll('.sheet').forEach(function(s){
    if (s.scrollHeight > s.clientHeight + 1 || s.scrollWidth > s.clientWidth + 1)
      over.push('定尺卡溢出：内容 ' + s.scrollHeight + 'px > 卡高 ' + s.clientHeight + 'px，换更少的内容或另一张卡，不缩字号');
  });
  var sw = de.scrollWidth, cw = de.clientWidth;
  // 字号下限（charts.md「文字」，viewBox 单位，半宽与通栏都是 9）：图只在滚入视野时才画，先强制全画，等入场定时器跑完再量
  document.querySelectorAll('figure[data-chart] svg').forEach(function(s){ if (s._replay) s._replay(); });
  setTimeout(function(){
    var small = [];
    document.querySelectorAll('figure[data-chart]').forEach(function(f){
      var floor = 9, min = Infinity;
      f.querySelectorAll('svg text, svg tspan').forEach(function(t){
        if (t.textContent.trim()) min = Math.min(min, parseFloat(getComputedStyle(t).fontSize));
      });
      if (min < floor) {
        var svg = f.querySelector('svg[id]');
        small.push(f.dataset.chart + (svg ? '（#' + svg.id + '）' : '') + ' 最小 ' + min + ' < 下限 ' + floor);
      }
    });
    // 正文文字字号下限（不含图内 SVG 与公式）：页面 <style> 用宽选择器压掉骨架字号时，构建要看得见。
    // 只量自己直接带文字的可见元素；收起的 <details> 内容尺寸为 0，自动跳过
    var text = [], doc = document.getElementById('doc') || document.body;
    var name = function(el){
      return el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim()
        ? '.' + el.className.trim().split(/\\s+/).slice(0,2).join('.') : '');
    };
    var shown = function(el){ var r = el.getBoundingClientRect(); return r.width >= 2 && r.height >= 2; };
    doc.querySelectorAll('*').forEach(function(el){
      if (el.closest('svg, math')) return;
      var own = false;
      for (var n = el.firstChild; n; n = n.nextSibling)
        if (n.nodeType === 3 && n.textContent.trim()) { own = true; break; }
      if (!own || !shown(el)) return;
      var fs = parseFloat(getComputedStyle(el).fontSize);
      if (fs < 10) text.push(name(el) + ' ' + fs + 'px「' + el.textContent.trim().slice(0, 12) + '」 < 10px');
    });
    // 大数契约（components.md「大数」）：.stat-num 最小 1.75rem。更小说明被页面样式覆盖了
    doc.querySelectorAll('.stat-num').forEach(function(el){
      if (!shown(el)) return;
      var fs = parseFloat(getComputedStyle(el).fontSize);
      if (fs < 27.5) text.push('.stat-num「' + el.textContent.trim().slice(0, 12) + '」' + fs + 'px < 1.75rem');
    });
    // 宽窄两版的示意图（diagrams.md「窄屏另画一版」）：量当前显示那一版渲染后的字号，
    // 被媒体查询隐藏的那一版没有盒子，跳过。和上面的 viewBox 单位不同，这里随视口变，每档都报
    var diag = [];
    document.querySelectorAll('.diagram-wide, .diagram-narrow').forEach(function(v){
      (v.tagName.toLowerCase() === 'svg' ? [v] : Array.from(v.querySelectorAll('svg'))).forEach(function(s){
        if (!s.getClientRects().length || !shown(s)) return;
        var min = Infinity;
        s.querySelectorAll('text, tspan').forEach(function(t){
          var m = t.getScreenCTM();
          if (!m || !t.textContent.trim()) return;
          min = Math.min(min, parseFloat(getComputedStyle(t).fontSize) * Math.hypot(m.a, m.b));
        });
        if (min < 8) diag.push((v.classList.contains('diagram-wide') ? '宽版' : '窄版')
          + (s.id ? '#' + s.id : '') + ' 最小 ' + min.toFixed(1) + 'px');
      });
    });
    // 没画窄版的数据图（charts.md「五件套外壳」）：通栏 800 宽的图在 500px 下约缩到 0.6 倍，9 号字只剩 5px 多。
    // 判据同上（渲染后 < 8px），但只报 WARN：存量页面的通栏图普遍如此，由作者决定是否补窄版
    var chartsmall = [];
    document.querySelectorAll('figure[data-chart] svg').forEach(function(s){
      if (s.closest('.diagram-wide, .diagram-narrow') || !s.getClientRects().length || !shown(s)) return;
      var min = Infinity;
      s.querySelectorAll('text, tspan').forEach(function(t){
        var m = t.getScreenCTM();
        if (!m || !t.textContent.trim()) return;
        min = Math.min(min, parseFloat(getComputedStyle(t).fontSize) * Math.hypot(m.a, m.b));
      });
      if (min < 8) chartsmall.push(s.closest('figure').dataset.chart + (s.id ? '（#' + s.id + '）' : '')
        + ' 最小 ' + min.toFixed(1) + 'px');
    });
    // 文字对比度（visual-system.md「对比度」）：render_check 把页面固定在亮色主题下量，亮色是明度阶与主角色最差的一侧。
    // 颜色先经 canvas 解析成 sRGB（color-mix、oklab 也读得出），再按 WCAG 2.x 算；正文要 4.5:1，24px 以上或 18.66px 以上的粗体要 3:1
    var cv = document.createElement('canvas'); cv.width = cv.height = 1;
    var cx = cv.getContext('2d', {willReadFrequently: true});
    var rgba = function(c){ cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); return cx.getImageData(0, 0, 1, 1).data; };
    var lum = function(a){
      var f = function(v){ v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
      return 0.2126 * f(a[0]) + 0.7152 * f(a[1]) + 0.0722 * f(a[2]);
    };
    var ratio = function(a, b){ var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
    var need = function(px, weight){ return px >= 24 || (px >= 18.66 && weight >= 700) ? 3 : 4.5; };
    // 盒子的底色：往上找第一个不透明的背景
    var boxBg = function(el){
      for (var p = el; p && p.nodeType === 1; p = p.parentElement) {
        var v = rgba(getComputedStyle(p).backgroundColor);
        if (v[3] > 200) return v;
      }
      return rgba(getComputedStyle(document.body).backgroundColor);
    };
    // SVG 文字的底色：文字中心往下第一个有填充的图形，没有就是图所在的卡面
    var SHAPE = {rect: 1, circle: 1, ellipse: 1, path: 1, polygon: 1};
    var svgBg = function(t){
      var r = t.getBoundingClientRect(), stack = document.elementsFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      for (var i = 0; i < stack.length; i++) {
        var e = stack[i], tag = e.tagName.toLowerCase();
        if (e === t || e.closest('text')) continue;
        if (e.namespaceURI !== 'http://www.w3.org/2000/svg' || tag === 'svg') break;
        if (!SHAPE[tag]) continue;
        var cs = getComputedStyle(e), v = rgba(cs.fill);
        if (cs.fill !== 'none' && v[3] > 128 && parseFloat(cs.fillOpacity) * parseFloat(cs.opacity) > 0.5) return v;
      }
      return boxBg(t.closest('svg'));
    };
    var dim = [], dimSeen = {};
    var dimNote = function(where, cr, s){
      var k = where + cr.toFixed(2);
      if (dimSeen[k]) { dimSeen[k].n++; return; }
      dimSeen[k] = {s: where + '「' + s.split('|').join('/').slice(0, 10) + '」' + cr.toFixed(2) + ':1', n: 1};
      dim.push(dimSeen[k]);
    };
    doc.querySelectorAll('*').forEach(function(el){
      if (el.closest('svg, math, pre, [aria-hidden="true"]') || el.matches(':disabled')) return;
      var own = false;
      for (var n = el.firstChild; n; n = n.nextSibling)
        if (n.nodeType === 3 && n.textContent.trim()) { own = true; break; }
      if (!own || !shown(el)) return;
      var cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
      var cr = ratio(rgba(cs.color), boxBg(el));
      if (cr < need(parseFloat(cs.fontSize), parseInt(cs.fontWeight, 10))) dimNote(name(el), cr, el.textContent.trim());
    });
    doc.querySelectorAll('svg').forEach(function(s){
      var texts = [].filter.call(s.querySelectorAll('text'), function(t){ return t.textContent.trim(); });
      if (!texts.length || !s.getClientRects().length || s.closest('[aria-hidden="true"]')) return;
      // 命中测试只认视口里的点，先把图滚进视口；页面有 scroll-behavior: smooth，不写 instant 就不会立刻到位
      s.scrollIntoView({block: 'center', behavior: 'instant'});
      var fig = s.closest('figure[data-chart]'), where = (fig ? fig.dataset.chart : 'svg') + (s.id ? '（#' + s.id + '）' : '');
      texts.forEach(function(t){
        var cs = getComputedStyle(t), m = t.getScreenCTM(), r = t.getBoundingClientRect();
        if (!m || r.width < 1 || cs.fill === 'none' || parseFloat(cs.opacity) === 0 || t.closest('[aria-hidden="true"]')) return;
        var cr = ratio(rgba(cs.fill), svgBg(t));
        if (cr < need(parseFloat(cs.fontSize) * Math.hypot(m.a, m.b), parseInt(cs.fontWeight, 10))) dimNote(where, cr, t.textContent.trim());
      });
    });
    // 图的显示倍率（charts.md「五件套外壳」）：字号下限按 viewBox 单位核对，前提是图大致按 1:1 显示。
    // 半宽卡的 400 宽 viewBox 单独放进整栏会放大一倍多，刻度和珠子变疏、字比同页别的图大一圈；缩到 0.8 倍以下字就小于下限
    var scaled = [];
    document.querySelectorAll('figure[data-chart] svg[viewBox]').forEach(function(s){
      var vb = s.viewBox.baseVal, w = s.getBoundingClientRect().width;
      if (!vb || !vb.width || !w) return;
      var k = w / vb.width;
      if (k > 1.5 || k < 0.8)
        scaled.push(s.closest('figure').dataset.chart + (s.id ? '（#' + s.id + '）' : '') + ' viewBox 宽 ' + vb.width + '，显示 ' + Math.round(w) + 'px，' + k.toFixed(2) + ' 倍');
    });
    // 文字越出图框（charts.md「交付前自检」第 3 条）：SVG 外面的部分被裁掉，读者看到半截字。
    // 判据同 gallery.py 的探针：只比水平文字，外接框超出 SVG 的盒子 1px 以上就算
    var clipped = [];
    doc.querySelectorAll('svg').forEach(function(s){
      if (!s.getClientRects().length || !shown(s) || getComputedStyle(s).overflow === 'visible') return;
      var sr = s.getBoundingClientRect(), fig = s.closest('figure[data-chart]');
      var where = (fig ? fig.dataset.chart : 'svg') + (s.id ? '（#' + s.id + '）' : '');
      s.querySelectorAll('text').forEach(function(t){
        var cs = getComputedStyle(t), m = t.getScreenCTM(), r = t.getBoundingClientRect();
        if (!t.textContent.trim() || !m || Math.abs(m.b) > 1e-3 || Math.abs(m.c) > 1e-3 || r.width < 1
            || cs.display === 'none' || parseFloat(cs.opacity) === 0) return;
        if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1)
          clipped.push(where + '「' + t.textContent.trim().split('|').join('/').split('；').join(';').slice(0, 12) + '」');
      });
    });
    document.title = 'PROBE|' + sw + '|' + cw + '|' + over.slice(0, 4).join('  ') + '|' + small.join('；')
      + '|' + text.slice(0, 4).join('；') + (text.length > 4 ? ' 等 ' + text.length + ' 处' : '')
      + '|' + diag.join('；')
      + '|' + dim.slice(0, 6).map(function(d){ return d.s + (d.n > 1 ? ' ×' + d.n : ''); }).join('；')
      + (dim.length > 6 ? ' 等 ' + dim.length + ' 组' : '')
      + '|' + scaled.join('；')
      + '|' + clipped.slice(0, 20).join('；')
      + '|' + chartsmall.join('；');
  }, 1500);
});</script>
"""

# ── 定尺卡截图（--shot）────────────────────────────────────────────
SHOT_CSS = """
<style>
  .page-chrome, .toc { display: none !important; }
  body { background: transparent !important; }
  .layout, main { max-width: none !important; padding: 0 !important; margin: 0 !important; }
  .sheet-stage { justify-content: flex-start !important; overflow: visible !important; }
  .sheet { box-shadow: none !important; }
  main > section { margin: 0 !important; }
</style>
"""


def sheet_size(html):
    """页面可在自己的 <style> 里改 --sheet-w / --sheet-h；读不到就用配方默认 600×1000。"""
    def pick(name, default):
        found = re.findall(rf"{name}\s*:\s*(\d+)px", html)
        return int(found[-1]) if found else default
    return pick("--sheet-w", 600), pick("--sheet-h", 1000)


def print_pdf(page):
    """按页面的打印样式出 PDF（show-me.css 定为 A4），放在页面旁边、同名 .pdf。返回 (路径, 错误信息)。
    数据图先全部画出、reduced motion 下画末帧，再打印（render.mjs 的 pdf 任务）。"""
    out = page.with_suffix(".pdf")
    results, err = run_jobs([{"url": page.resolve().as_uri(), "reduced": True, "pdf": str(out)}])
    if results is None:
        return None, err or "找不到 Chrome/Chromium 或 Node 22+"
    if results[0].get("error"):
        return None, results[0]["error"]
    return out, None


def shoot_sheets(page, theme="light", scale=2):
    """把每张 .sheet 渲染成 PNG：按卡的尺寸开视口，隐藏 chrome 与桌面，两倍像素。
    返回 (输出文件列表, 错误信息)。"""
    import tempfile
    html = page.read_text(encoding="utf-8")
    # 只数 class 里独立的 sheet 一词：sheet-stage / sheet-body 不算
    n = len(re.findall(r'class=["\'](?:[^"\']*\s)?sheet(?:\s[^"\']*)?["\']', html))
    if not n:
        return [], "页面里没有 .sheet"
    w, h = sheet_size(html)
    # shell.js 的 fit() 视口比卡窄时把卡等比缩小；截图视口就是卡宽，读出缩放说明隐藏 chrome 的样式没在 fit() 之前生效
    scaled = "[].map.call(document.querySelectorAll('.sheet'), function(s){ return s.style.transform; }).join(' ').trim()"
    jobs = []
    with tempfile.TemporaryDirectory() as td:
        for i in range(n):
            hide = "".join(
                f".sheet-stage:nth-of-type({j + 1}){{display:none!important}}" for j in range(n) if j != i
            )
            # 样式放进 <head>：fit() 在页面脚本执行时就量版心，追加在文末的样式那时还没生效
            themed = html.replace(
                "<head>",
                f'<head><script>try{{localStorage.setItem("show-me-theme","{theme}")}}catch(e){{}}</script>'
                + SHOT_CSS + f"<style>{hide}</style>", 1,
            )
            probe = Path(td) / f"shot-{i}.html"
            probe.write_text(themed, encoding="utf-8")
            suffix = f"-{i + 1}" if n > 1 else ""
            out = page.with_name(f"{page.stem}{suffix}{'-dark' if theme == 'dark' else ''}.png")
            jobs.append({"url": probe.as_uri(), "width": w, "height": h, "dpr": scale, "mobile": False,
                         "eval": scaled, "shot": str(out)})
        results, err = run_jobs(jobs)
    if results is None:
        return [], err or "找不到 Chrome/Chromium 或 node 22+"
    outs = []
    for job, r in zip(jobs, results):
        if r.get("error"):
            return outs, f"截图失败：{r['error']}"
        if r.get("value"):
            return outs, f"截图失败：卡片被缩放（{r['value']}），截出来不是原尺寸"
        outs.append(Path(job["shot"]))
    return outs, None


# ── 整页快照（--snap）──────────────────────────────────────────────
# 眼睛关的替身：agent 没有交互浏览器，但能读图。每个主题 × 宽度按视口高度切片截图（长图读进来会被降采样），
# 每片写明含哪几节，小修后只重读受影响的那几片；外加页面自带导出器的 Markdown。
SNAP_EVAL = """(function(){
  var heads = [].map.call(document.querySelectorAll('#doc h2'), function(h){
    return [Math.round(h.getBoundingClientRect().top + scrollY), h.textContent.replace(/\\s+/g, ' ').trim()];
  });
  return {md: window.showMeMarkdown ? window.showMeMarkdown() : null, heads: heads};
})()"""
SNAP_SLICE = {390: 1600, 500: 1600}  # 每片高度：读图时不被明显降采样（2026-10 实测 1280×1500、500×1600 读得清）；其余宽度 1500


def snap_page(page, out_dir, widths=(390, 500, 1280), themes=("light", "dark")):
    """返回 (输出列表 [(路径, 说明)], 提示信息列表, 错误信息或 None)。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    md_from = ("light" if "light" in themes else themes[0], max(widths))
    jobs = [{"url": page.resolve().as_uri(), "width": w, "theme": t, "reduced": True, "eval": SNAP_EVAL,
             "slices": {"prefix": str(out_dir / f"{t}-{w}"), "height": SNAP_SLICE.get(w, 1500)}}
            for t in themes for w in widths]
    results, err = run_jobs(jobs)
    if results is None:
        return [], [], err or "找不到 Chrome/Chromium 或 node 22+"
    outs, notes = [], []
    for job, r in zip(jobs, results):
        if r.get("error"):
            return outs, notes, f"{job['theme']} {job['width']}px：{r['error']}"
        heads = r["value"]["heads"]
        for s in r["slices"]:
            names = [h for top, h in heads if s["top"] <= top < s["top"] + s["height"]]
            about = "含：" + "、".join(names) if names else ("（页首）" if s["top"] == 0 else "（接上一片）")
            outs.append((Path(s["path"]), about))
        if (job["theme"], job["width"]) == md_from:
            md = out_dir / "export.md"
            md.write_text(r["value"]["md"] or "", encoding="utf-8")
            outs.append((md, ""))
            if r["value"]["md"] is None:
                notes.append("页面没有 window.showMeMarkdown：导出器缺失，export.md 为空")
    return outs, notes, None


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


RENDER_SCRIPT = Path(__file__).resolve().parent / "render.mjs"


def run_jobs(jobs):
    """在一个无头 Chrome 实例里依次跑完 jobs（scripts/render.mjs，走 CDP），返回 (结果列表, 错误信息)。
    任务与结果的字段见 render.mjs 文件头。找不到 Chrome 或 node、或 node 早于 22（没有内置 WebSocket）时
    返回 (None, None)：调用方按「这道关没跑」处理。"""
    import contextlib, json, os, shutil, signal, subprocess, tempfile
    chrome, node = find_chrome(), shutil.which("node")
    if not chrome or not node:
        return None, None
    with tempfile.TemporaryDirectory() as td:
        spec = Path(td) / "jobs.json"
        spec.write_text(json.dumps({"chrome": chrome, "jobs": jobs}, ensure_ascii=False), encoding="utf-8")
        # 运行器单独一个进程组：超时或被中断时连同它启动的 Chrome 一起结束，不留孤儿进程
        proc = subprocess.Popen([node, str(RENDER_SCRIPT), str(spec)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, encoding="utf-8", start_new_session=True)

        def stop():
            # 先对整组发 SIGTERM：运行器（cdp.mjs）收到后结束 Chrome、删掉配置目录再退出；最多等 5 秒，再 SIGKILL 剩下的。
            # 进程组可能已经全部退出（ProcessLookupError）；macOS 上组长被回收后再 killpg 还可能报 PermissionError。
            # 两种都忽略，否则会盖掉原来的 KeyboardInterrupt，或让超时路径崩掉
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGTERM)
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGKILL)

        try:
            out, err = proc.communicate(timeout=90 * len(jobs) + 30)
        except subprocess.TimeoutExpired:
            stop()
            proc.communicate()
            return None, "Chrome 运行器超时"
        except BaseException:  # Ctrl-C 等：单独的进程组收不到终端发来的信号，要自己结束它
            stop()
            raise
    if proc.returncode == 3:
        return None, None
    if proc.returncode:
        return None, (err.strip().splitlines() or [f"运行器退出码 {proc.returncode}"])[-1]
    try:
        return json.loads(out), None
    except ValueError:
        return None, f"运行器的输出不是完整的 JSON（{len(out)} 字节）"


# 390 用 CDP 的手机模拟（--window-size 最窄只到 500px，模拟不受这个限制），只查横向溢出、报 WARN；
# 字号、对比度、倍率这些检查只在 500 / 1024 / 1280 跑。
def render_check(page, widths=(500, 1024, 1280)):
    """返回 (issues, notes, measured, ran)。issues 是 ERROR，notes 是 WARN；
    ran=False 表示没有 Chrome、node 或 node 早于 22，这道关没跑。"""
    import html as htmllib, tempfile

    html = page.read_text(encoding="utf-8")
    issues, notes, measured = [], [], []
    clipped = []  # 越框文字跨宽度去重：数据图的 viewBox 不随视口变，同一处在每个宽度都会报
    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "probe.html"
        # 固定亮色主题：对比度在亮色下最差；其余几何检查与主题无关，固定下来结果也不随本机外观变
        probe.write_text(html.replace(
            "<head>", '<head><script>document.documentElement.dataset.theme="light";'
            'try{localStorage.setItem("show-me-theme","light")}catch(e){}</script>', 1) + PROBE,
            encoding="utf-8")
        # 一个 Chrome 依次跑完所有宽度（scripts/render.mjs）。PROBE 把结果写进 <title>；包回 --dump-dom 的样子，
        # 下面的正则与 unescape 原样沿用。读标题元素的文本而不是 document.title：后者会合并连续空格。
        # reduced motion 下量末帧，与 gallery.py 的探针、--snap 一致：逐帧布局的图（如 G11 力导向图）
        # 在无头 Chrome 里不一定跑完，量到的是节点还在原点的中间状态
        title = "(document.querySelector('head > title') || {}).textContent || ''"
        results, err = run_jobs([{"url": probe.as_uri(), "width": w, "reduced": True, "eval": title}
                                 for w in (390, *widths)])
        if results is None:  # err 为空：没有 Chrome、node 或 node 早于 22，这道关没跑；err 非空：运行器出错，记 ERROR
            return ([f"渲染检查跑不起来：{err}"] if err else []), [], [], False
        wrap = lambda r: "<title>" + htmllib.escape(r.get("value") or "", quote=False) + "</title>"
        why = lambda r: r.get("error") or "；".join(r.get("errors", [])[:2]) or "页面没写回结果"
        # 390（手机）只看横向溢出，报 WARN：字号类检查在 500px 已经量过窄版
        phone = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|", wrap(results[0]), re.S)
        if not phone:
            notes.append(f"390px（手机）：探针没返回结果（{why(results[0])}），这一档没查")
        elif int(phone.group(1)) > int(phone.group(2)) + 1:
            who = htmllib.unescape(phone.group(3).strip())
            notes.append(f"390px（手机）视口横向溢出：文档宽 {phone.group(1)}px" + (f"；越界元素：{who}" if who else "")
                         + "。手机上要横向拖动整页，把越界元素收窄或放进局部滚动容器（visual-system.md「响应式与打印」）")
        for w, r in zip(widths, results[1:]):
            out = wrap(r)
            m = re.search(r"<title>PROBE\|(\d+)\|(\d+)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(?P<contrast>.*?)\|(?P<scaled>.*?)\|(?P<clipped>.*?)\|(?P<chartsmall>.*?)</title>", out, re.S)
            if not m:
                issues.append(f"{w}px：探针没返回结果（{why(r)}）")
                continue
            try:
                sw, cw = (int(value) for value in m.group(1, 2))
            except ValueError:
                issues.append(f"{w}px：探针返回了无效宽度")
                continue
            who = m.group(3).strip()
            measured.append(cw)
            if sw > cw + 1:
                issues.append(f"{cw}px 视口横向溢出：文档宽 {sw}px"
                              + (f"；越界元素：{who}" if who else ""))
            elif "定尺卡溢出" in who and w == max(widths):
                issues.append(who)
            small = htmllib.unescape(m.group(4).strip())  # --dump-dom 把 <title> 里的 < 转义了
            if small and w == max(widths):  # viewBox 单位与视口宽度无关，报一次
                issues.append(f"图内字号低于下限：{small}。装不下改 <title> hover 出，不缩字号硬塞（charts.md「文字」）")
            text = htmllib.unescape(m.group(5).strip())
            if text and w == max(widths):
                issues.append(f"正文字号过小：{text}。多半是页面 <style> 的宽选择器（如 .xxx p）压掉了骨架字号，"
                              "改窄选择器或换骨架组件（components.md「大数」「指标带」）")
            diag = htmllib.unescape(m.group(6).strip())
            if diag:
                issues.append(f"{cw}px 下示意图字号渲染后低于 8px：{diag}。宽版缩得太小就画窄版，"
                              "窄版控制 viewBox 宽度（diagrams.md「窄屏另画一版」）")
            contrast = htmllib.unescape(m.group("contrast").strip())
            if contrast and w == max(widths):
                issues.append(f"文字对比度不足（亮色主题；正文要 4.5:1，大字要 3:1）：{contrast}。次要文字用 --color-muted-foreground，"
                              "主角色写字用 --chart-hero-text，纯装饰的字加 aria-hidden=\"true\"（visual-system.md「对比度」）")
            scaled = htmllib.unescape(m.group("scaled").strip())
            if scaled and w == max(widths):
                notes.append(f"{cw}px 下图的显示倍率超出 0.8–1.5：{scaled}。单张图独占整栏时写成 .fig.wide 配 800 宽 viewBox，"
                             "按单位计数的图（刻度、珠子、点阵）把单位细一档，保持标记间距（charts.md「五件套外壳」）")
            chartsmall = htmllib.unescape(m.group("chartsmall").strip())
            if chartsmall:
                notes.append(f"{cw}px 下数据图字号渲染后低于 8px：{chartsmall}。手机上读不清：按 diagrams.md「窄屏另画一版」"
                             "补一版窄图（.diagram-narrow，viewBox 宽 320–360），宽窄两版各自 reveal（charts.md「五件套外壳」）")
            for c in htmllib.unescape(m.group("clipped").strip()).split("；"):
                if c and c not in clipped:
                    clipped.append(c)
    if clipped:
        notes.append(f"文字越出图框，SVG 外的部分会被裁掉：{'；'.join(clipped[:6])}"
                     + (f" 等 {len(clipped)} 处" if len(clipped) > 6 else "")
                     + "。把字挪进 viewBox 或缩短；确实放不下再加宽 viewBox，不缩字号（charts.md「交付前自检」第 3 条）")
    return issues, notes, measured, True


def main():
    if any(arg == "--style" or arg.startswith("--style=") for arg in sys.argv[1:]):
        print("ERROR  --style 已移除；show-me-html 现在只有一套自有视觉系统。", file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description="内联资产并自检 show-me-html 页面")
    ap.add_argument("page", type=Path)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--no-render", action="store_true", help="跳过无头浏览器的溢出检查")
    ap.add_argument(
        "--open",
        action="store_true",
        help="自检通过后用系统默认浏览器打开（macOS: open / Windows: os.startfile / Linux·WSL: wslview→xdg-open）",
    )
    ap.add_argument(
        "--shot",
        nargs="?",
        const="light",
        choices=("light", "dark", "both"),
        help="share-card 配方：自检通过后把每张 .sheet 截成 PNG（两倍像素，放在页面旁边）。默认浅色，可选 dark / both",
    )
    ap.add_argument("--pdf", action="store_true",
                    help="自检通过后按打印样式出一份 A4 PDF，放在页面旁边（同名 .pdf）")
    ap.add_argument(
        "--snap",
        nargs="?",
        const="",
        metavar="DIR",
        help="自检通过后按 light/dark × 390/500/1280px 切片截图（每片约一屏多高，输出时写明每片含哪几节），并导出 Markdown 到 export.md；不给 DIR 时写到新建的临时目录。供眼睛关读图用",
    )
    ap.add_argument("--snap-theme", choices=("light", "dark", "both"), default="both",
                    help="--snap 拍哪个主题，默认 both；小修只拍受影响的主题")
    ap.add_argument("--snap-width", default="390,500,1280", metavar="W[,W…]",
                    help="--snap 拍哪些视口宽度（px），逗号分隔，默认 390,500,1280；小于 500 按手机模拟")
    args = ap.parse_args()
    try:
        snap_widths = tuple(int(x) for x in args.snap_width.split(",") if x.strip())
    except ValueError:
        snap_widths = ()
    if not snap_widths or any(not 320 <= w <= 2560 for w in snap_widths):
        ap.error("--snap-width 要写 320–2560 之间的整数，逗号分隔，例如 390,1280")

    if not args.page.exists():
        sys.exit(f"ERROR  找不到文件：{args.page}")
    html = args.page.read_text(encoding="utf-8")

    build_errors, build_warns = [], []
    if not args.check_only:
        if compile_math(args.page, build_errors, build_warns):
            html = args.page.read_text(encoding="utf-8")
        html, changed, used, langs, warns_from_build = build(html, build_errors)
        build_warns += warns_from_build
        if changed:
            args.page.write_text(html, encoding="utf-8")
            print(f"已合成  {args.page}  图标={len(used)} 个"
                  f"{'  语法=' + ','.join(sorted(langs)) if langs else ''}"
                  f"  体积={len(html.encode('utf-8'))/1024:.0f} KB")

    errors, warns = check(html, args.page, allow_legacy_recipe=args.check_only)
    errors = build_errors + errors
    warns = build_warns + warns

    rendered, measured = False, []
    if not args.no_render and not errors:
        render_issues, render_notes, measured, rendered = render_check(args.page)
        errors += render_issues
        warns += render_notes

    for w in warns:
        print(f"WARN   {w}")
    for e in errors:
        print(f"ERROR  {e}")

    if errors:
        print(f"\n自检未通过：{len(errors)} 个错误。")
        return 1

    print(f"自检通过{f'（{len(warns)} 个警告需逐条判断）' if warns else ''}。")
    if rendered:
        print(f"渲染检查：{' / '.join(f'{w}px' for w in measured)} 无横向溢出；390px 手机视口另查，溢出只报 WARN。")
    elif not args.no_render:
        print("渲染检查未运行：找不到 Chrome/Chromium 或 node 22+。横向溢出没有被验证过，"
              "自己在浏览器里拉一遍窄屏，不要报「已验证」。")

    if args.snap is not None:
        import tempfile
        out_dir = Path(args.snap) if args.snap else Path(tempfile.mkdtemp(prefix=f"show-me-snap-{args.page.stem}-"))
        themes = ("light", "dark") if args.snap_theme == "both" else (args.snap_theme,)
        outs, notes, err = snap_page(args.page, out_dir, snap_widths, themes)
        for path, about in outs:
            print(f"已快照  {path}" + (f"  {about}" if about else ""))
        for n in notes:
            print(f"注意    {n}")
        if err:
            print(f"--snap 未完成：{err}")

    if args.shot:
        for theme in (("light", "dark") if args.shot == "both" else (args.shot,)):
            outs, err = shoot_sheets(args.page, theme)
            for o in outs:
                print(f"已截图  {o}")
            if err:
                print(f"--shot 未完成：{err}")

    if args.pdf:
        out, err = print_pdf(args.page)
        print(f"已导出  {out}" if out else f"--pdf 未完成：{err}")

    if args.open:  # 走到这里自检已通过：有 ERROR 时上面已经 return 1
        if not open_page(args.page.resolve()):
            print("--open 未执行：找不到可用的打开命令（macOS 需要 open，"
                  "Linux/WSL 需要 wslview 或 xdg-open，Windows 用 os.startfile）。")
        else:
            print(f"已在默认浏览器打开 {args.page}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
