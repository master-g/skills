#!/usr/bin/env python3
"""figpreview.py 图.svg [-o 输出目录] [--width 1280] [--browser chromium|firefox|webkit]

单独预览一幅插图：把它放进一页只有这幅图的读本里构建，再截出明暗两种主题的 PNG，不用构建整本书。
输入是一段 <svg>…</svg>，或者一整个 <figure>…</figure>（分步图要给 figure）；写 - 从标准输入读。
图里的公式、分类色、分步图都按正式构建处理，截图就是它在页面上的样子。

截图用 Playwright 的命令行（pipx install playwright && playwright install chromium）。没装时只生成预览页，
打印它的路径，自己用浏览器打开看。--width 390 看手机宽度；带公式的图另用 --browser firefox 看一遍。

不用 rsvg-convert：它不画 <foreignObject>，带公式的图是空的；CSS 变量也取不到，分类色只能画成回退色。
"""
import contextlib
import io
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

SHELL = build.ASSETS / "shell.html"
HEIGHT = 900


def preview_page(fragment, out_dir, name):
    """生成并构建预览页，返回 (页面路径, 构建输出)。"""
    if not fragment.lstrip().startswith("<figure"):
        fragment = f"<figure>{fragment}</figure>"
    shell = SHELL.read_text(encoding="utf-8")
    head = shell[: shell.index("<body")].replace("中文标题 · 原文标题", f"图预览 · {name}")
    page = out_dir / f"{name}.preview.html"
    page.write_text(f'{head}<body>\n<article class="chapter" id="preview"><section>\n{fragment}\n</section></article>\n'
                    f"{build.JS_SLOT}\n</body></html>", encoding="utf-8")
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        build.main([str(page)])
    return page, log.getvalue()


def main(argv):
    args, opts, it = [], {"-o": None, "--width": "1280", "--browser": "chromium"}, iter(argv)
    for a in it:
        if a in opts:
            opts[a] = next(it, None)
        else:
            args.append(a)
    if len(args) != 1 or None in (opts["--width"], opts["--browser"]):
        print(__doc__)
        return 2
    src = args[0]
    fragment = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    name = "figure" if src == "-" else Path(src).stem
    out_dir = Path(opts["-o"] or ("." if src == "-" else Path(src).parent)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    page, log = preview_page(fragment, out_dir, name)
    # 只有一幅图的页面没有章标题和目录，相关的检查不适用；其余的 WARN / ERROR 照常给出
    for line in log.splitlines():
        if line.startswith(("WARN", "ERROR")) and "<h2>" not in line:
            print(line)

    cli = shutil.which("playwright")
    if not cli:
        print(f"没有找到 playwright 命令，未截图。预览页：{page}")
        return 0
    failed = False
    for theme in ("light", "dark"):
        png = out_dir / f"{name}.{theme}.png"
        cmd = [cli, "screenshot", "--browser", opts["--browser"], "--color-scheme", theme, "--full-page",
               "--viewport-size", f"{opts['--width']},{HEIGHT}", page.as_uri(), str(png)]
        run = subprocess.run(cmd, capture_output=True, text=True)
        if run.returncode != 0 and opts["--browser"] == "chromium":
            # Playwright 自带的 Chromium 没下载或版本对不上时，改用本机的 Chrome
            run = subprocess.run(cmd[:2] + ["--channel", "chrome"] + cmd[2:], capture_output=True, text=True)
        if run.returncode != 0:
            failed = True
            print(f"截图失败（{theme}）：" + (run.stderr.strip().splitlines() or ["未知错误"])[-1])
        else:
            print(png)
    if failed:
        print(f"预览页：{page}")
    else:
        page.unlink()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
