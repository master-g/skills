#!/usr/bin/env python3
"""figprobe.py 页面.html [-o 输出目录] [--min-slack 2]

检查构建好的读本里每一幅 Mermaid 图：节点里的标签文字有没有越出节点框。页面要先用 build.py 构建。
每幅图打印一行：页内序号、类型、显示宽度、最小余量、图注；最小余量低于 --min-slack（CSS px）的图标出最紧的节点和标签。
全部达标退出码 0；有图不达标，或有图不是 pele 画的（认不出、没法量）为 1；找不到 Chrome 或探针没跑出结果 2。
页面里没有 Mermaid 图时报 0 幅，退出码 0。
同时在 1280px 宽度下截出明暗两种主题的整页 PNG（<名字>-light.png / <名字>-dark.png），不给 -o 就放进新建的临时目录。

余量是标签文字的包围盒到它所在节点各形状的合并包围盒四条边的最小距离，负数就是越界。两边都用 getBoundingClientRect 量，
是缩放之后读者实际看到的像素。只在亮色主题下量：暗色主题只换颜色，不改字体和字重。
这个检查是为 pele 的内置字宽而设的：它按 -apple-system 排拉丁字母偏窄，类图的成员行曾经越出框外。

不截 390px：无头 Chrome 的窗口最窄 500px，手机宽度的看法见 SKILL.md。
"""
import argparse
import html
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

WIDTH = 1280
CHROME_NAMES = ("google-chrome", "chromium", "chromium-browser", "chrome")
CHROME_MAC = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_TIMEOUT_MS = 20000

PROBE = """<script>addEventListener("load", () => {
  const height = document.documentElement.scrollHeight;
  const figures = [...document.querySelectorAll("div.mermaid-figure")].map((div, i) => {
    const svg = div.querySelector(":scope > svg.pele");
    if (!svg) return { n: i + 1, caption: div.querySelector(":scope > svg")?.getAttribute("aria-label") || "",
                       type: "?", width: 0, slack: null, node: "", label: "", unknown: true };
    const type = [...svg.classList].find((c) => c.startsWith("pele-")) || "";
    let worst = null;
    for (const g of svg.querySelectorAll("g.pele-node")) {
      const shapes = [...g.querySelectorAll("rect, path, polygon, circle, ellipse")].map((s) => s.getBoundingClientRect());
      if (!shapes.length) continue;
      const L = Math.min(...shapes.map((r) => r.left)), R = Math.max(...shapes.map((r) => r.right));
      const T = Math.min(...shapes.map((r) => r.top)), B = Math.max(...shapes.map((r) => r.bottom));
      for (const t of g.querySelectorAll("text")) {
        const r = t.getBoundingClientRect();
        if (!r.width) continue;
        const slack = Math.min(r.left - L, R - r.right, r.top - T, B - r.bottom);
        if (!worst || slack < worst.slack) worst = { slack, node: g.dataset.id || "", label: t.textContent.trim() };
      }
    }
    return { n: i + 1, caption: svg.getAttribute("aria-label") || "", type: type.slice(5),
             width: svg.getBoundingClientRect().width, ...(worst || { slack: null, node: "", label: "" }) };
  });
  const pre = document.createElement("pre");
  pre.id = "figprobe";
  pre.hidden = true;
  pre.textContent = JSON.stringify({ height, figures });
  document.body.append(pre);
});</script>"""


def find_chrome():
    for name in CHROME_NAMES:
        path = shutil.which(name)
        if path:
            return path
    return CHROME_MAC if Path(CHROME_MAC).is_file() else None


def probe_copy(page, out_dir, theme):
    """在输出目录里写一份设好主题、带探针的副本；<base> 让副本里的相对路径仍指向原页面所在目录。

    各章平时是 content-visibility: auto，没进视口的章按 10000px 占位，量出的页高不是真的；
    副本里让各章都排版，页高和截图就是读者从头翻到尾看到的样子。"""
    text = page.read_text(encoding="utf-8")
    head = (f'<base href="{page.parent.as_uri()}/">'
            "<style>article.chapter { content-visibility: visible !important }</style>"
            f"<script>document.documentElement.dataset.theme = {json.dumps(theme)}</script>")
    text, n = re.subn(r"</head\s*>", lambda m: head + m.group(0), text, count=1, flags=re.I)
    copy = out_dir / f"{page.stem}-{theme}.probe.html"
    copy.write_text(text + ("" if n else head) + PROBE, encoding="utf-8")
    return copy


def chrome(exe, profile, height, *args):
    # 读本从 jsDelivr 拉网络字体，无头 Chrome 不读 HTTP(S)_PROXY，字体请求会拖住 load。指向一个不通的代理，
    # 请求立刻失败，全页停在系统字体上：插图本来就用系统字体（--font-figure），余量不变；而放开网络时 shell.js
    # 会在 load 之后换上网络字体，正文换字后页高跟着变，截图就和量出的页高对不上。整次运行实测约 2.6 秒，放开网络是 5 到 7 秒。
    cmd = [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
           "--proxy-server=127.0.0.1:9", f"--user-data-dir={profile}", f"--timeout={CHROME_TIMEOUT_MS}",
           f"--window-size={WIDTH},{height}", *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=CHROME_TIMEOUT_MS / 1000 + 30)


def png_height(path):
    with open(path, "rb") as f:
        return struct.unpack(">I", f.read(24)[20:24])[0]


def row(fig, min_slack):
    caption = fig["caption"] if len(fig["caption"]) <= 30 else fig["caption"][:30] + "…"
    head = f"{fig['n']:>3}  {fig['type']:<10} {fig['width']:>6.0f}px"
    if fig.get("unknown"):
        return f"{head}  {'—':>7}  {caption}  ← 认不出：没有 svg.pele，可能是别的编译器画的，未测"
    if fig["slack"] is None:
        why = "图没有显示出来" if fig["width"] == 0 else "没有带文字的节点"
        return f"{head}  {'—':>7}  {caption}  （{why}，未测）"
    line = f"{head}  {fig['slack']:>7.1f}  {caption}"
    if fig["slack"] < min_slack:
        line += f"  ← {'越界' if fig['slack'] < 0 else '贴边'}：节点 {fig['node']}「{fig['label']}」"
    return line


class ProbeError(Exception):
    pass


def probe(exe, page, out_dir):
    """量出各图的余量，截出明暗两张整页图，返回 (探针结果, PNG 路径列表)。"""
    copies = {theme: probe_copy(page, out_dir, theme) for theme in ("light", "dark")}
    shots = []
    # 每次运行用一个新的空 profile：不给 --user-data-dir 时，本机 Chrome 每次启动要多花约 4 秒
    with tempfile.TemporaryDirectory(prefix="figprobe-profile-") as profile:
        try:
            dump = chrome(exe, profile, 900, "--dump-dom", copies["light"].as_uri())
            m = re.search(r'<pre id="figprobe"[^>]*>(.*?)</pre>', dump.stdout, re.S)
            if not m:
                raise ProbeError(f"探针没有跑出结果（Chrome 退出码 {dump.returncode}）。探针页：{copies['light']}")
            result = json.loads(html.unescape(m.group(1)))
            for theme, copy in copies.items():
                png = out_dir / f"{page.stem}-{theme}.png"
                shot = chrome(exe, profile, result["height"], f"--screenshot={png}", copy.as_uri())
                if shot.returncode != 0 or not png.is_file():
                    raise ProbeError(f"截图失败（{theme}）：" + (shot.stderr.strip().splitlines() or ["未知错误"])[-1])
                shots.append(png)
        except subprocess.TimeoutExpired:
            raise ProbeError(f"Chrome 超时没有退出。探针页：{copies['light']}")
    for copy in copies.values():
        copy.unlink()
    return result, shots


def main(argv):
    ap = argparse.ArgumentParser(usage=__doc__.splitlines()[0])
    ap.add_argument("page")
    ap.add_argument("-o", dest="out")
    ap.add_argument("--min-slack", type=float, default=2.0)
    args = ap.parse_args(argv)

    page = Path(args.page).resolve()
    if not page.is_file():
        print(f"没有这个文件：{page}")
        return 2
    exe = find_chrome()
    if not exe:
        print(f"没有找到 Chrome：PATH 里没有 {' / '.join(CHROME_NAMES)}，也没有 {CHROME_MAC}")
        return 2
    out_dir = Path(args.out).resolve() if args.out else Path(tempfile.mkdtemp(prefix="figprobe-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        result, shots = probe(exe, page, out_dir)
    except ProbeError as e:
        print(e)
        return 2
    for png in shots:
        got = png_height(png)
        print(png if got == result["height"] else f"{png}  （页面高 {result['height']}px，截图只有 {got}px）")

    figures = result["figures"]
    if figures:
        print(f"{'#':>3}  {'类型':<8} {'宽度':>6}  {'最小余量':>4}  图注")
    for fig in figures:
        print(row(fig, args.min_slack))
    bad = [f for f in figures if f["slack"] is not None and f["slack"] < args.min_slack]
    unknown = [f for f in figures if f.get("unknown")]
    if bad or unknown:
        parts = [f"{len(bad)} 幅有标签越出或贴着节点框（最小余量 < {args.min_slack:g}px）"] if bad else []
        parts += [f"{len(unknown)} 幅认不出、没有量"] if unknown else []
        print(f"未通过：{len(figures)} 幅 Mermaid 图里 " + "，".join(parts))
        return 1
    print(f"通过：{len(figures)} 幅 Mermaid 图，标签都在节点框内（最小余量 ≥ {args.min_slack:g}px）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
