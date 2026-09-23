#!/usr/bin/env python3
"""把四个 gallery 页拼成一张总览页 all-charts.html，供人和 agent 评估全部图型。

  python3 scripts/gallery.py [--out DIR] [--shots] [--no-render]

总览页按家族分节（基础型 → 编辑型 → 快读型 → 交互大图），页首是编号索引；
每张 figure 的 id 是 fig-编号：all-charts.html#fig-L5 直达，?only=L5,F1 只看这几张（?only=* 全部单列）。
--shots 再用无头 Chrome 给每张图在 light / dark 下各截一张 PNG，并写 index.md：
编号、标题、单位行、图注、截图路径与探针结果（空图、控制台报错、字号下限）。
agent 没有交互浏览器，读 index.md 与 PNG 完成眼检；hover / 钉住等交互仍要真实浏览器。
"""
import argparse
import datetime
import html as htmllib
import json
import re
import runpy
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
GALLERY = SKILL / "assets" / "gallery"
BUILD = SKILL / "scripts" / "build.py"
# 家族顺序同 references/charts.md 的家族表
FAMILIES = (
    ("basics", "基础型 · Basics"),
    ("editorial", "编辑型 · Editorial"),
    ("glance", "快读型 · Glance"),
    ("big", "交互大图 · Big"),
)
# 字号下限（viewBox 单位），见 charts.md「文字」：半宽卡 6.5、通栏 5.5
MIN_FONT = {"half": 6.5, "wide": 5.5}
# 单看模式的截图宽度：通栏按版心宽，半宽卡按双栏里的一格；无头 Chrome 窗口最窄 500px
SHOT_W = {"wide": 1000, "half": 500}
PAD = 12

ONLY_CSS = f"""
    <style>
      /* 单看模式（?only=编号）：只留选中的图，去掉工具条、目录与节标题，截图与细看用 */
      html[data-only] .page-chrome,
      html[data-only] .toc,
      html[data-only] #intro,
      html[data-only] main > section:not([data-on]),
      html[data-only] main > section > :not(.charts),
      html[data-only] figure[data-chart]:not([data-on]) {{
        display: none !important;
      }}
      html[data-only] .layout {{
        max-width: none;
        padding: {PAD}px;
      }}
      html[data-only] main,
      html[data-only] main > section,
      html[data-only] .charts {{
        margin: 0;
        padding: 0;
      }}
      html[data-only] .charts {{
        display: block;
      }}
      html[data-only] .charts > .fig + .fig {{
        margin-top: {PAD}px;
      }}
    </style>
"""
ONLY_JS = """
    <script>
      /* ?only=L5,F1 只看这几张；?only=* 全部单列 */
      (function () {
        var q = new URLSearchParams(location.search).get("only");
        if (!q) return;
        document.documentElement.dataset.only = q;
        var figs = document.querySelectorAll("figure[data-chart]");
        figs.forEach(function (f) {
          if (q === "*" || q.split(",").indexOf(f.dataset.chart) >= 0) {
            f.dataset.on = "";
            f.closest("section").dataset.on = "";
          }
        });
      })();
    </script>
"""


def section_parts(src):
    """(引言 lede 文本, figures HTML, 图表脚本) —— gallery 页的结构见任一页的 #intro / #charts / 页尾脚本。"""
    lede = re.search(r'<p class="lede">(.*?)</p>', src, re.S).group(1).strip()
    figs = re.search(r'<section id="charts">.*?<div class="charts">(.*)</div>\s*</section>', src, re.S).group(1)
    script = re.findall(r"<script>(.*?)</script>", src, re.S)[-1]
    return lede, figs, script


def git_label():
    def git(*a):
        r = subprocess.run(["git", "-C", str(SKILL), *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    sha = git("rev-parse", "--short", "HEAD")
    if not sha:
        return "不在 git 仓库里"
    dirty = git("status", "--porcelain", "--", "assets")
    return sha + ("（assets 有未提交改动）" if dirty else "")


def compose():
    """返回 (页面 HTML, [(家族 key, [编号…])…])。"""
    template = (GALLERY / "basics.html").read_text(encoding="utf-8")
    sections, scripts, index, total = [], [], [], 0
    for key, name in FAMILIES:
        lede, figs, script = section_parts((GALLERY / f"{key}.html").read_text(encoding="utf-8"))
        # id 带 fig- 前缀：#F10 这类锚点会被 build.py 的写死颜色检查当成色值
        figs = re.sub(r'<figure class="([^"]*)" data-chart="([A-Z]\d+)"', r'<figure id="fig-\2" class="\1" data-chart="\2"', figs)
        ids = re.findall(r'<figure id="fig-([A-Z]\d+)"', figs)
        if len(ids) != figs.count("<figure"):
            raise SystemExit(f"{key}.html：有 figure 不是 `<figure class=… data-chart=…>` 的写法，没法加 id")
        total += len(ids)
        index.append((key, name, ids))
        scripts.append(f"      /* ── {key}.html ── */\n      {script.strip()}")
        sections.append(
            f'        <section id="{key}">\n          <h2>{name} · {len(ids)} 张</h2>\n'
            f"          <p>{lede}</p>\n          <div class=\"charts\">{figs}</div>\n        </section>"
        )
    links = "\n".join(
        f'          <p><strong>{name}</strong>　' + " ".join(f'<a href="#fig-{i}">{i}</a>' for i in ids) + "</p>"
        for _, name, ids in index
    )
    when = datetime.date.today().isoformat()
    intro = f"""        <section id="intro">
          <p class="eyebrow">show-me-html · 评估用总览</p>
          <h1>图型总览 · {total} 张</h1>
          <p class="lede">
            四个 gallery 页拼成的一页，按家族排列；版本 <code>{git_label()}</code>，生成于 {when}。
          </p>
          <p>
            编号直达：<code>all-charts.html#fig-L5</code>；只看几张：<code>?only=L5,F1</code>。主题在右上角切换，
            动态图型滚入才播放、卡片右上角可重播。代码在 <code>assets/gallery/</code> 对应页的
            <code>// ════ 编号 ════</code> 块，这一页由 <code>scripts/gallery.py</code> 生成，不要手改。
          </p>
{links}
        </section>"""
    main = '<main id="doc">\n' + intro + "\n" + "\n".join(sections) + "\n      </main>"
    page = re.sub(r'<main id="doc">.*?</main>', lambda _: main, template, count=1, flags=re.S)
    page = re.sub(r"<title>.*?</title>", "<title>图型总览 · 评估</title>", page, count=1)
    page = page.replace('<span class="chrome-title">图型参考 · 基础型 · Basics</span>',
                        '<span class="chrome-title">图型总览 · 评估</span>')
    last = page.rfind("<script>")
    page = page[:last] + "<script>\n" + "\n".join(scripts) + "\n    </script>" + page[page.index("</script>", last) + 9:]
    page = page.replace("<!--SHOW-ME:CSS-->", "<!--SHOW-ME:CSS-->" + ONLY_CSS, 1)
    page = page.replace("<!--SHOW-ME:JS-->", ONLY_JS + "    <!--SHOW-ME:JS-->", 1)
    return page, index


# ── 截图（--shots）──────────────────────────────────────────────────
# 探针与截图用两份文件：探针插进页面的 <pre> 不能出现在截图里。
ERR_CAPTURE = (
    "<script>window.__errs=[];addEventListener('error',function(e){__errs.push(String(e.message))});"
    "var __ce=console.error;console.error=function(){__errs.push([].join.call(arguments,' '));__ce.apply(console,arguments)};</script>"
)
PROBE = """
<script>addEventListener('load', function(){
  var W = %s, PAD = %d;
  var figs = [].slice.call(document.querySelectorAll('figure[data-chart]'));
  figs.forEach(function(f){
    var wide = f.classList.contains('wide');
    f.style.width = (W[wide ? 'wide' : 'half'] - 2 * PAD) + 'px';
    var s = f.querySelector('svg');
    if (s && s._replay) s._replay();
  });
  setTimeout(function(){
    var q = function(f, sel){ var n = f.querySelector(sel); return n ? n.textContent.replace(/\\s+/g, ' ').trim() : ''; };
    var out = figs.map(function(f){
      var svgs = [].slice.call(f.querySelectorAll('svg'));
      var marks = 0, fonts = [];
      svgs.forEach(function(s){
        marks += s.querySelectorAll('*:not(title):not(desc)').length;
        s.querySelectorAll('text').forEach(function(t){
          if (t.textContent.trim()) fonts.push(parseFloat(getComputedStyle(t).fontSize));
        });
      });
      return {id: f.dataset.chart, wide: f.classList.contains('wide'), h: Math.ceil(f.getBoundingClientRect().height),
        name: q(f, '.fig-id'), title: q(f, '.fig-title'), sub: q(f, '.fig-sub'), cap: q(f, 'figcaption'),
        svgs: svgs.length, marks: marks, minFont: fonts.length ? Math.min.apply(null, fonts) : null};
    });
    var p = document.createElement('pre'); p.id = '__probe';
    p.textContent = JSON.stringify({figs: out, errs: window.__errs});
    document.body.appendChild(p);
  }, 3000);
});</script>
"""


def chrome_run(chrome, *args):
    """偶发卡住（多半在等字体请求）就重试一次。别加 --user-data-dir：新配置没有字体缓存，virtual time 会一直等网络。"""
    for _ in range(2):
        try:
            return subprocess.run(
                [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-prefers-reduced-motion", *args],
                capture_output=True, text=True, timeout=45,
            )
        except subprocess.TimeoutExpired:
            pass
    return subprocess.CompletedProcess(args, 1, "", "超时")


def shots(page, out, index):
    chrome = runpy.run_path(str(BUILD))["find_chrome"]()
    if not chrome:
        raise SystemExit("--shots 需要本机 Chrome/Chromium")
    html = page.read_text(encoding="utf-8")
    work = out / "shots"
    work.mkdir(exist_ok=True)
    themed = {}
    for theme in ("light", "dark"):
        themed[theme] = work / f"{theme}.html"
        themed[theme].write_text(html.replace(
            "<head>", f'<head><script>try{{localStorage.setItem("show-me-theme","{theme}")}}catch(e){{}}</script>', 1),
            encoding="utf-8")
    probe = work / "probe.html"
    probe.write_text(html.replace("<head>", "<head>" + ERR_CAPTURE, 1) + PROBE % (json.dumps(SHOT_W), PAD), encoding="utf-8")
    dom = chrome_run(chrome, "--virtual-time-budget=8000", "--window-size=1000,900", "--dump-dom",
                     probe.as_uri() + "?only=*").stdout
    m = re.search(r'<pre id="__probe">(.*?)</pre>', dom, re.S)
    if not m:
        raise SystemExit("探针没返回结果（页面 JS 可能报错）：用浏览器打开 all-charts.html 看控制台")
    data = json.loads(htmllib.unescape(m.group(1)))
    figs = {f["id"]: f for f in data["figs"]}

    def shoot(job):
        fid, theme = job
        f = figs[fid]
        png = work / f"{fid}-{theme}.png"
        w = SHOT_W["wide" if f["wide"] else "half"]
        chrome_run(chrome, "--force-device-scale-factor=2", "--virtual-time-budget=4000",
                   f"--window-size={w},{f['h'] + 2 * PAD}", f"--screenshot={png}",
                   themed[theme].as_uri() + f"?only={fid}")
        return png if png.exists() else None

    jobs = [(fid, t) for fid in figs for t in ("light", "dark")]
    with ThreadPoolExecutor(max_workers=4) as pool:
        made = dict(zip(jobs, pool.map(shoot, jobs)))

    problems = [f"控制台报错：{e}" for e in data["errs"]]
    lines = []
    for key, name, ids in index:
        lines += [f"## {name}", ""]
        for fid in ids:
            f = figs[fid]
            size = "wide" if f["wide"] else "half"
            notes = []
            if f["svgs"] and f["marks"] == 0:
                notes.append("空图")
            if f["minFont"] is not None and f["minFont"] < MIN_FONT[size]:
                notes.append(f"最小字号 {f['minFont']:g} 低于{'通栏' if f['wide'] else '半宽'}下限 {MIN_FONT[size]:g}")
            missing = [t for t in ("light", "dark") if not made[(fid, t)]]
            if missing:
                notes.append("截图失败：" + "、".join(missing))
            problems += [f"{fid}：{n}" for n in notes]
            lines += [
                f"### {f['name'] or fid} — {f['title']}",
                "",
                f"- 单位行：{f['sub'] or '（无）'}",
                f"- 图注：{f['cap'] or '（无）'}",
                f"- 幅面：{'通栏' if f['wide'] else '半宽'} · 来源：`assets/gallery/{key}.html`",
                f"- 探针：图元 {f['marks']} 个 · 最小字号 {f['minFont'] if f['minFont'] is not None else '—'}"
                + (f" · **{'；'.join(notes)}**" if notes else ""),
                f"- 截图：[light]({fid}-light.png) · [dark]({fid}-dark.png)",
                "",
            ]
    head = [
        "# 图型总览 · 截图索引",
        "",
        f"页面 `{page}`，版本 {git_label()}，{datetime.date.today().isoformat()}。",
        f"每张图 light / dark 各一张，两倍像素，reduced-motion 下截（动态图型是末帧）。"
        f"通栏按 {SHOT_W['wide']}px、半宽按 {SHOT_W['half']}px 窗口截。hover、钉住、拖拽等交互不在截图里，要真实浏览器验。",
        "",
        "## 探针发现的问题",
        "",
        *([f"- {p}" for p in problems] or ["- 无"]),
        "",
    ]
    md = work / "index.md"
    md.write_text("\n".join(head + lines), encoding="utf-8")
    for tmp in (*themed.values(), probe):
        tmp.unlink()
    return md, sum(1 for v in made.values() if v), len(jobs), problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, help="输出目录；不给时新建临时目录")
    ap.add_argument("--shots", action="store_true", help="每张图 light/dark 各截一张 PNG，并写 index.md")
    ap.add_argument("--no-render", action="store_true", help="构建时跳过 build.py 的溢出检查")
    args = ap.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix="show-me-gallery-"))
    out.mkdir(parents=True, exist_ok=True)
    page = out / "all-charts.html"
    html, index = compose()
    page.write_text(html, encoding="utf-8")
    built = subprocess.run([sys.executable, str(BUILD), str(page), *(["--no-render"] if args.no_render else [])],
                           capture_output=True, text=True)
    print(built.stdout.strip())
    if built.returncode:
        print(built.stderr.strip(), file=sys.stderr)
        return built.returncode
    print(f"总览页  {page}（{sum(len(ids) for *_, ids in index)} 张）")
    if args.shots:
        md, ok, n, problems = shots(page, out, index)
        print(f"截图    {ok}/{n} 张 → {md.parent}")
        print(f"索引    {md}")
        print(f"问题    {len(problems)} 条" + ("，见 index.md 开头" if problems else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
