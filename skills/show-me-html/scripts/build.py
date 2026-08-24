#!/usr/bin/env python3
"""show-me-html 的合成与自检工具。

用法：
    python3 build.py page.html                # 内联资产 + 自检
    python3 build.py page.html --style nova   # 换一套 basecoat 风格包
    python3 build.py page.html --check-only   # 只跑自检，不改文件

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

    for m in re.finditer(r'<(link|script|img|iframe|source|video|audio|use)\b[^>]*'
                         r'(?:src|href|xlink:href)="(https?:)?//[^"]+"', stripped, re.I):
        errors.append(f"外部资源引用：{m.group(0)[:90]}…（页面必须离线可开）")
    for m in re.finditer(r'url\(\s*["\']?(?:https?:)?//', stripped):
        errors.append("CSS 里有外部 url() 引用")
    if re.search(r"@import\s+url\(\s*[\"']?(?:https?:)?//", stripped):
        errors.append("CSS 里有外部 @import")
    if re.search(r"@font-face", stripped) and "base64" not in stripped:
        warns.append("有 @font-face 但没看到 base64 字体，可能会去联网取字体")

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

    # 高亮脚本发的是 class，页面没给对应规则的话代码块只会变成一色黑
    if HL_MARK in html and ".shj-syn-" not in html:
        warns.append("页面内联了语法高亮，但没有 .shj-syn-* 的配色规则："
                     "从 assets/shell.html 重新起手，或把那段 CSS 补进来")

    own = VENDOR_STYLE_RE.sub("", stripped)
    hard = [m.group(1) for m in HARDCODED_COLOR_RE.finditer(own)]
    if hard:
        shown = "、".join(dict.fromkeys(hard))[:80]
        warns.append(f"页面自己写死了 {len(hard)} 处颜色（{shown}）："
                     "深色主题下不会跟着变，改用 var(--color-*) / var(--tone-*) / var(--chart-*)")

    size = len(html.encode("utf-8"))
    if size > 3_000_000:
        warns.append(f"页面 {size/1e6:.1f} MB，偏大")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
