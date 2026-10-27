import hashlib
import json
import os
import re
import runpy
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
BUILD = SKILL / "scripts" / "build.py"
FIXTURES = Path(__file__).parent / "fixtures"
CSS = SKILL / "assets" / "show-me.css"

RECIPES = runpy.run_path(str(BUILD))["RECIPES"]
FIND_CHROME = runpy.run_path(str(BUILD))["find_chrome"]
RENDERER = bool(FIND_CHROME() and shutil.which("node"))
SHELL = SKILL / "assets" / "shell.html"


def chrome_pids(tmpdir):
    """命令行里带着 tmpdir 的进程：Chrome 的 --user-data-dir 在 TMPDIR 下。"""
    return subprocess.run(["pgrep", "-f", str(tmpdir)], capture_output=True, text=True).stdout.split()


def png_size(path):
    data = Path(path).read_bytes()
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def run_build(page, *args):
    return subprocess.run(
        [sys.executable, str(BUILD), str(page), "--no-render", *args],
        text=True,
        capture_output=True,
        check=False,
    )


class BuildCliTests(unittest.TestCase):
    def copy_fixture(self, name="minimal-shell.html"):
        tmp = tempfile.TemporaryDirectory()
        page = Path(tmp.name) / "page.html"
        page.write_text((FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8")
        self.addCleanup(tmp.cleanup)
        return page

    def test_build_inlines_owned_css_once(self):
        page = self.copy_fixture()

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        html = page.read_text(encoding="utf-8")
        self.assertEqual(html.count('data-show-me="css"'), 1)
        self.assertIn("--color-background", html)
        self.assertIn('[data-recipe="status-report"]', html)

    def test_build_is_idempotent(self):
        page = self.copy_fixture()
        first = run_build(page)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = hashlib.sha256(page.read_bytes()).digest()

        second = run_build(page)

        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(hashlib.sha256(page.read_bytes()).digest(), before)

    def test_build_refreshes_stale_owned_css(self):
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        html = page.read_text(encoding="utf-8")
        html = re.sub(
            r'(<style data-show-me="css">).*?(</style>)',
            r"\1/* stale-owned-css */\2",
            html,
            count=1,
            flags=re.S,
        )
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        refreshed = page.read_text(encoding="utf-8")
        self.assertNotIn("stale-owned-css", refreshed)
        self.assertIn("--color-background", refreshed)
        self.assertEqual(refreshed.count('data-show-me="css"'), 1)

    def test_static_page_does_not_inline_basecoat_js(self):
        page = self.copy_fixture()

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('data-show-me="js"', page.read_text(encoding="utf-8"))

    def test_tabs_inline_basecoat_js(self):
        page = self.copy_fixture("component-states.html")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('data-show-me="js"', page.read_text(encoding="utf-8"))

    def test_chart_page_inlines_chart_runtime(self):
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8")
        html = html.replace("</main>", '<section><figure class="fig" data-chart="F1"><div class="fig-box"><svg id="x" viewBox="0 0 4 4" role="img" aria-labelledby="x-t x-d"><title id="x-t">t</title><desc id="x-d">d</desc></svg></div></figure></section></main>')
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        built = page.read_text(encoding="utf-8")
        self.assertIn('data-show-me="charts"', built)
        self.assertIn("window.showMeChart", built)

    FIGURE = '<section><figure class="fig" data-chart="F1"><div class="fig-box"><svg id="x" viewBox="0 0 4 4" role="img" aria-labelledby="x-t x-d"><title id="x-t">t</title><desc id="x-d">d</desc></svg></div></figure></section>'

    def insert(self, page, snippet, before="</main>"):
        html = page.read_text(encoding="utf-8")
        page.write_text(html.replace(before, snippet + before, 1), encoding="utf-8")

    def test_rebuild_adds_chart_runtime_for_new_chart(self):
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        self.assertNotIn('data-show-me="charts"', page.read_text(encoding="utf-8"))
        self.insert(page, self.FIGURE)

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(page.read_text(encoding="utf-8").count('data-show-me="charts"'), 1)

    def test_rebuild_adds_basecoat_for_new_tabs(self):
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        self.insert(page, '<section><div class="tabs"></div></section>')

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(page.read_text(encoding="utf-8").count('data-show-me="js"'), 1)

    def test_rebuild_adds_new_highlight_language(self):
        page = self.copy_fixture()
        self.insert(page, '<section><pre><code class="language-python">x = 1</code></pre></section>')
        self.assertEqual(run_build(page).returncode, 0)
        self.insert(page, '<section><pre><code class="language-rust">let x = 1;</code></pre></section>')

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        built = page.read_text(encoding="utf-8")
        self.assertIn('__SHJ_LANGS["rs"]', built)
        self.assertIn('__SHJ_LANGS["py"]', built)
        self.assertEqual(built.count('data-show-me="hl"'), 1)

    def test_kotlin_code_is_highlighted(self):
        """kotlin / kts 归一到自写的 kt.js（上游没有 Kotlin），不再报「没有对应的语法规则」。"""
        page = self.copy_fixture()
        self.insert(page, '<section><pre><code class="language-kotlin">val x = listOf(1)</code></pre></section>')

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("language-kotlin 没有对应的语法规则", result.stdout)
        built = page.read_text(encoding="utf-8")
        self.assertIn('__SHJ_LANGS["kt"]', built)
        self.assertIn('__SHJ_LANGS["kotlin"]=window.__SHJ_LANGS["kt"]', built)

    def test_rebuild_drops_runtime_no_longer_needed(self):
        page = self.copy_fixture()
        self.insert(page, self.FIGURE)
        self.assertEqual(run_build(page).returncode, 0)
        html = page.read_text(encoding="utf-8")
        page.write_text(re.sub(r"<section><figure.*?</figure></section>", "", html, count=1, flags=re.S), encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(page.read_text(encoding="utf-8").count('data-show-me="charts"'), 0)

    def test_rebuild_after_edit_is_idempotent(self):
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        self.insert(page, self.FIGURE)
        self.assertEqual(run_build(page).returncode, 0)
        before = hashlib.sha256(page.read_bytes()).digest()

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(hashlib.sha256(page.read_bytes()).digest(), before)

    def test_rebuild_replaces_copied_shell_scripts(self):
        # 骨架改为构建注入之前的页面：骨架以普通 <script> 复制在哨兵块之后，页面脚本再往后
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        built = re.sub(r'<script data-show-me="shell">.*?</script>', "", page.read_text(encoding="utf-8"), flags=re.S)
        shell_js = (SKILL / "assets" / "shell.js").read_text(encoding="utf-8")
        legacy = built.replace("<!--SHOW-ME:JS:END-->",
                               f"<!--SHOW-ME:JS:END-->\n    <script>\n{shell_js}</script>\n"
                               "    <script>window.__pageScript = 1;</script>", 1)
        page.write_text(legacy, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        html = page.read_text(encoding="utf-8")
        self.assertEqual(html.count('data-show-me="shell"'), 1)
        self.assertEqual(html.count("定尺卡（share-card）"), 1)
        self.assertLess(html.index('data-show-me="shell"'), html.index("window.__pageScript"))
        before = hashlib.sha256(page.read_bytes()).digest()
        self.assertEqual(run_build(page).returncode, 0)
        self.assertEqual(hashlib.sha256(page.read_bytes()).digest(), before)

    def test_chart_runtime_precedes_page_scripts(self):
        page = self.copy_fixture()
        self.insert(page, self.FIGURE)
        self.insert(page, "<script>window.__pageScript = 1;</script>", before="</body>")
        self.assertEqual(run_build(page).returncode, 0)
        self.insert(page, self.FIGURE.replace('id="x', 'id="y').replace("x-t x-d", "y-t y-d").replace('"x-', '"y-'))

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        built = page.read_text(encoding="utf-8")
        self.assertLess(built.index('data-show-me="charts"'), built.index("window.__pageScript"))

    def test_check_only_flags_chart_without_runtime(self):
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        self.insert(page, self.FIGURE)

        result = run_build(page, "--check-only")

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("图表运行时", result.stdout)

    def chart_figure(self, chart):
        # 同页多张图的 id 各带前缀，否则会撞上重复 id 检查
        return self.FIGURE.replace('data-chart="F1"', f'data-chart="{chart}"').replace('"x', f'"{chart}').replace(" x-", f" {chart}-")

    def test_legacy_license_notice_is_kept_verbatim(self):
        """此前交付的页面带着许可声明：重新构建不再增删它，也不再发许可 WARN。"""
        page = self.copy_fixture()
        for chart in ("L1", "F3", "G22"):
            self.insert(page, self.chart_figure(chart))
        notice = "<!--SHOW-ME:LICENSE:BEGIN\n  本页图表 L1 改写自上游。\nSHOW-ME:LICENSE:END-->"
        page.write_text(page.read_text(encoding="utf-8").replace("</head>", notice + "\n</head>", 1), encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("PolyForm", result.stdout)
        built = page.read_text(encoding="utf-8")
        self.assertEqual(built.count(notice), 1)
        self.assertEqual(built.count("SHOW-ME:LICENSE:BEGIN"), 1)
        before = hashlib.sha256(page.read_bytes()).digest()
        self.assertEqual(run_build(page).returncode, 0)
        self.assertEqual(hashlib.sha256(page.read_bytes()).digest(), before)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_snap_renders_both_themes_and_exports_markdown(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        page = Path(tmp.name) / "page.html"
        html = SHELL.read_text(encoding="utf-8").replace("PAGE TITLE", "快照测试").replace("choose-a-recipe", "status-report")
        html = re.sub(r'<main id="doc">.*?</main>',
                      '<main id="doc"><section><h1>快照测试</h1><p>正文一段。</p><h2>第二节</h2><p>内容</p>'
                      '<div class="item"><section><h4>条目</h4><p>说明</p></section></div>'
                      '<h3>泳道</h3><article class="card"><header><h3>工单</h3></header>'
                      '<section><h4>卡内小节</h4><p>细节</p></section></article></section></main>',
                      html, count=1, flags=re.S)
        page.write_text(html, encoding="utf-8")
        out = Path(tmp.name) / "snap"

        result = run_build(page, "--snap", str(out))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, width in (("light-390", 390), ("dark-390", 390), ("light-500", 500), ("dark-500", 500),
                         ("light-1280", 1280), ("dark-1280", 1280)):
            png = out / f"{name}-01.png"
            self.assertTrue(png.exists(), name)
            self.assertEqual(png_size(png)[0], width, name)
        self.assertNotEqual((out / "light-1280-01.png").read_bytes(), (out / "dark-1280-01.png").read_bytes())
        self.assertIn("light-1280-01.png  含：第二节", result.stdout)
        md = (out / "export.md").read_text(encoding="utf-8")
        self.assertIn("# 快照测试", md)
        self.assertIn("## 第二节", md)
        # 组件里的标题按所在节排级：h2 下的 item h4 → ###；h3 泳道下的卡片 h3/h4 → ####/#####
        self.assertIn("\n### 条目\n", md)
        self.assertIn("\n#### 工单\n", md)
        self.assertIn("\n##### 卡内小节\n", md)
        self.assertNotIn("__snap", md)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_markdown_export_keeps_figure_desc(self):
        """图的 <desc> 是数据摘要：在图的位置导出成一段（单位行之后、来源行之前）。宽窄两版只出正在显示的那版，隐藏标签页里的图照样出，和上一段相同的不重复出。"""
        page = self.copy_fixture()
        figs = """<section><figure class="fig" data-chart="F1"><div class="fig-box">
          <div class="fig-head"><span class="fig-title">五月客流最高</span></div>
          <p class="fig-sub">单位：千人 · 2026 Q2</p>
          <svg id="d1" viewBox="0 0 400 120" role="img" aria-labelledby="d1-t d1-d"><title id="d1-t">月度客流</title>
          <desc id="d1-d">四月 120 千人，五月 135 千人，六月 98 千人。</desc></svg>
          <p class="fig-src">票务系统 · 2026 Q2</p></div>
          <figcaption>五月是全年峰值。</figcaption></figure>
          <figure class="fig"><div class="fig-box">
          <svg class="diagram-wide" viewBox="0 0 400 120" role="img"><title>流程</title><desc>宽版：甲到乙到丙。</desc></svg>
          <svg class="diagram-narrow" viewBox="0 0 200 300" role="img"><title>流程</title><desc>窄版：甲到乙到丙。</desc></svg>
          </div></figure>
          <figure class="fig"><div class="fig-box"><p class="fig-sub">单位：次 · 9 月</p>
          <svg viewBox="0 0 400 120" role="img"><title>重复</title><desc>单位：次 · 9 月</desc></svg></div></figure>
          <div class="tabs" id="tb"><nav role="tablist">
          <button type="button" role="tab" id="t1" aria-controls="p1" aria-selected="true" tabindex="0">甲</button>
          <button type="button" role="tab" id="t2" aria-controls="p2" aria-selected="false" tabindex="-1">乙</button></nav>
          <div role="tabpanel" id="p1" aria-labelledby="t1" tabindex="-1"><p>甲面板。</p></div>
          <div role="tabpanel" id="p2" aria-labelledby="t2" tabindex="-1" hidden><figure class="fig"><div class="fig-box">
          <svg viewBox="0 0 400 120" role="img"><title>乙</title><desc>乙面板的图：七月 88 千人。</desc></svg></div></figure></div>
          </div></section>"""
        page.write_text(page.read_text(encoding="utf-8").replace("</main>", figs + "</main>"), encoding="utf-8")
        md = {}
        for width in ("1280", "390"):
            out = page.parent / f"snap-{width}"
            result = run_build(page, "--snap", str(out), "--snap-theme", "light", "--snap-width", width)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            md[width] = (out / "export.md").read_text(encoding="utf-8")
        self.assertIn("单位：千人 · 2026 Q2\n\n四月 120 千人，五月 135 千人，六月 98 千人。\n\n票务系统 · 2026 Q2", md["1280"])
        self.assertNotIn("月度客流", md["1280"])
        self.assertIn("宽版：甲到乙到丙。", md["1280"])
        self.assertNotIn("窄版", md["1280"])
        self.assertIn("窄版：甲到乙到丙。", md["390"])
        self.assertNotIn("宽版", md["390"])
        self.assertIn("乙面板的图：七月 88 千人。", md["1280"])
        self.assertEqual(md["1280"].count("单位：次 · 9 月"), 1)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_snap_narrows_to_one_theme_and_width(self):
        page = self.copy_fixture()
        out = page.parent / "snap"
        result = run_build(page, "--snap", str(out), "--snap-theme", "dark", "--snap-width", "1280")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sorted(p.name for p in out.glob("*.png")), ["dark-1280-01.png"])
        self.assertTrue((out / "export.md").exists())

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_pdf_prints_a4_beside_the_page(self):
        page = self.copy_fixture()
        result = run_build(page, "--pdf")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("已导出", result.stdout)
        pdf = page.with_suffix(".pdf").read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF"))
        box = re.search(rb"/MediaBox \[([^\]]*)\]", pdf)
        self.assertIsNotNone(box)
        self.assertRegex(box.group(1).decode(), r"^0 0 59[45]\.\d+ 84[12]\.\d+$")  # A4，不是 Letter 的 612 x 792

    @unittest.skipUnless(RENDERER and shutil.which("pdftotext"), "需要本机 Chrome/Chromium、node 和 pdftotext")
    def test_pdf_draws_charts_below_the_fold(self):
        """数据图滚入视口才画：--pdf 打印前要把首屏以外的图也画出来，不然 PDF 里是空框。"""
        def chart(cid, below):
            return ('<section>' + ('<div style="height: 3000px"></div>' if below else '')
                    + '<figure class="fig" data-chart="F1"><div class="fig-box">'
                    f'<svg id="{cid}" viewBox="0 0 400 320" role="img" aria-labelledby="{cid}-t {cid}-d">'
                    f'<title id="{cid}-t">t</title><desc id="{cid}-d">d</desc></svg></div></figure></section>')
        script = ('<script>["top", "fold"].forEach(function (id) { showMeChart.reveal(document.getElementById(id), (s) =>'
                  ' showMeChart.txt(s, { x: 20, y: 40, "font-size": 14 }, id === "top" ? "TOPLABEL" : "FOLDLABEL")); });</script>')
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8")
        html = html.replace("</main>", chart("top", False) + chart("fold", True) + "</main>").replace(
            "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script)
        page.write_text(html, encoding="utf-8")
        result = run_build(page, "--pdf")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = subprocess.run(["pdftotext", str(page.with_suffix(".pdf")), "-"],
                              capture_output=True, text=True, check=True).stdout
        self.assertIn("TOPLABEL", text)
        self.assertIn("FOLDLABEL", text)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_warns_on_phone_overflow_only(self):
        """390 按手机模拟：420px 宽的块在 500 及以上放得下，只在 390 溢出，报 WARN 不报 ERROR。"""
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "</main>", '<section><div style="width: 420px">定宽的块</div></section></main>')
        page.write_text(html, encoding="utf-8")
        result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("WARN   390px（手机）视口横向溢出", result.stdout)
        self.assertNotIn("ERROR", result.stdout)

    @unittest.skipIf(shutil.which("node", path="/usr/bin:/bin"), "/usr/bin 里有 node，造不出没有 node 的环境")
    def test_render_check_reports_not_run_without_node(self):
        page = self.copy_fixture()
        result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True,
                                check=False, env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home())})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("渲染检查未运行：找不到 Chrome/Chromium 或 node 22+", result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_runner_returns_long_output_whole(self):
        """运行器的结果经管道交回，macOS 上写管道是异步的：超过 64 KB 也要完整。"""
        run_jobs = runpy.run_path(str(BUILD))["run_jobs"]
        results, err = run_jobs([{"url": (FIXTURES / "minimal-shell.html").as_uri(), "eval": "'x'.repeat(200000)"}])
        self.assertIsNone(err)
        self.assertEqual(len(results[0]["value"]), 200000)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_shot_keeps_card_at_full_size(self):
        """--shot 按卡的尺寸、两倍像素截图；卡没有被 fit() 缩小（缩小时 build 报「卡片被缩放」）。"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        page = Path(tmp.name) / "card.html"
        html = SHELL.read_text(encoding="utf-8").replace("PAGE TITLE", "卡片测试").replace("choose-a-recipe", "share-card")
        html = re.sub(r'<main id="doc">.*?</main>',
                      '<main id="doc"><section><div class="sheet-stage"><article class="sheet">'
                      '<div class="sheet-mast"><strong>周报</strong><span>W35</span></div>'
                      '<div class="sheet-body"><h1>结论</h1><p>一句话说明。</p></div>'
                      '<div class="sheet-foot"><span>来源</span><span>2026-09-06</span></div>'
                      '</article></div></section></main>',
                      html, count=1, flags=re.S)
        page.write_text(html, encoding="utf-8")

        result = run_build(page, "--shot")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("--shot 未完成", result.stdout)
        self.assertIn("已截图", result.stdout)
        self.assertEqual(png_size(page.with_name("card.png")), (1200, 2000))

    def test_gallery_pages_build_and_scripts_parse(self):
        gallery = SKILL / "assets" / "gallery"
        pages = sorted(gallery.glob("*.html"))
        self.assertEqual([p.name for p in pages], ["basics.html", "big.html", "editorial.html", "glance.html"])
        node = shutil.which("node")
        for src in pages:
            with self.subTest(page=src.name):
                tmp = tempfile.TemporaryDirectory()
                self.addCleanup(tmp.cleanup)
                page = Path(tmp.name) / src.name
                page.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                result = run_build(page)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("ERROR", result.stdout)
                warns = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
                self.assertEqual(warns, [])
                built = page.read_text(encoding="utf-8")
                self.assertIn('data-show-me="charts"', built)
                self.assertNotIn("SHOW-ME:LICENSE", built)
                self.assertEqual(built.count("data-chart="), len(re.findall(r"// ════ [A-Z]\d+ · ", built)))
                if node:
                    script = re.findall(r"<script>(.*?)</script>", built, re.S)[-1]  # 页尾图型脚本（prettier 可能重排缩进）
                    js = Path(tmp.name) / "page.js"
                    js.write_text(script, encoding="utf-8")
                    check = subprocess.run([node, "--check", str(js)], text=True, capture_output=True, check=False)
                    self.assertEqual(check.returncode, 0, check.stderr)

    def test_gallery_overview_page_has_every_chart(self):
        """scripts/gallery.py 拼出的总览页：59 张图各有唯一 id，构建只剩「超过 400 KB」一条 WARN，拼接后的脚本能解析。"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "gallery.py"), "--out", tmp.name, "--no-render"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("ERROR", result.stdout)
        warns = [line for line in result.stdout.splitlines() if line.startswith("WARN")]
        self.assertEqual(len(warns), 1, warns)
        self.assertIn("超过 400 KB", warns[0])
        built = (Path(tmp.name) / "all-charts.html").read_text(encoding="utf-8")
        ids = re.findall(r'<figure id="fig-([A-Z]\d+)"', built)
        total = sum(p.read_text(encoding="utf-8").count("data-chart=")
                    for p in (SKILL / "assets" / "gallery").glob("*.html"))
        self.assertEqual(len(ids), total)
        self.assertEqual(len(set(ids)), total)
        node = shutil.which("node")
        if node:
            js = Path(tmp.name) / "page.js"
            js.write_text(re.findall(r"<script>(.*?)</script>", built, re.S)[-1], encoding="utf-8")
            check = subprocess.run([node, "--check", str(js)], text=True, capture_output=True, check=False)
            self.assertEqual(check.returncode, 0, check.stderr)

    @unittest.skipUnless(shutil.which("node"), "需要 node")
    def test_cdp_proxy_args_follow_proxy_env(self):
        """Chrome 不读代理环境变量：有代理时传 --proxy-server，HTTPS 优先，NO_PROXY 转绕行列表，NO_PROXY=* 不走代理。"""
        cases = [{}, {"https_proxy": "http://127.0.0.1:7890/"},
                 {"HTTP_PROXY": "http://a.test:1", "HTTPS_PROXY": "http://b.test:2"},
                 {"ALL_PROXY": "socks5://127.0.0.1:7891", "NO_PROXY": "localhost, .corp.test"},
                 {"HTTPS_PROXY": "http://b.test:2", "no_proxy": "*"}]
        script = ("import(process.argv[1]).then(m => console.log(JSON.stringify("
                  "JSON.parse(process.argv[2]).map(e => m.proxyArgs(e)))))")
        out = subprocess.run(["node", "-e", script, (SKILL / "scripts" / "cdp.mjs").as_uri(), json.dumps(cases)],
                             capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(out), [
            [], ["--proxy-server=http://127.0.0.1:7890"], ["--proxy-server=http://b.test:2"],
            ["--proxy-server=socks5://127.0.0.1:7891", "--proxy-bypass-list=localhost;*.corp.test"], []])

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_cdp_signal_closes_chrome_and_removes_profile(self):
        """launch() 接 SIGINT / SIGTERM：结束 Chrome、删掉配置目录，再按 130 / 143 退出。"""
        script = ("import(process.argv[1]).then(async (m) => { await m.launch(process.argv[2], 'sigtest-');"
                  " console.log('ready'); setInterval(() => {}, 1000); })")
        for sig, code in ((signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(sig=sig.name), tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
                proc = subprocess.Popen(["node", "-e", script, (SKILL / "scripts" / "cdp.mjs").as_uri(), FIND_CHROME()],
                                        stdout=subprocess.PIPE, text=True, env={**os.environ, "TMPDIR": td})
                try:
                    self.assertEqual(proc.stdout.readline().strip(), "ready")
                    proc.send_signal(sig)
                    self.assertEqual(proc.wait(timeout=30), code)
                    self.assertEqual([p.name for p in Path(td).iterdir() if p.name.startswith("sigtest-")], [])
                    self.assertEqual(chrome_pids(td), [], "Chrome 进程还在")
                finally:
                    proc.kill()
                    proc.stdout.close()
                    subprocess.run(["pkill", "-KILL", "-f", td])

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_interrupted_build_leaves_no_chrome_profile(self):
        """构建中途被 Ctrl-C：build.py 先对运行器发 SIGTERM，运行器结束 Chrome、删掉配置目录后才退出。"""
        page = self.copy_fixture()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            def profiles():
                return [p.name for p in Path(td).iterdir() if p.name.startswith("show-me-cdp-")]
            proc = subprocess.Popen([sys.executable, str(BUILD), str(page), "--no-render", "--snap", str(page.parent / "snap")],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    env={**os.environ, "TMPDIR": td})
            try:
                for _ in range(200):  # 等运行器建好配置目录，说明 Chrome 已经起来
                    if profiles():
                        break
                    time.sleep(0.05)
                time.sleep(0.5)
                self.assertIsNone(proc.poll(), "构建在打断之前就结束了")
                proc.send_signal(signal.SIGINT)
                proc.communicate(timeout=30)
                self.assertEqual(proc.returncode, -signal.SIGINT)
                self.assertEqual(profiles(), [])
                self.assertEqual(chrome_pids(td), [], "Chrome 进程还在")
            finally:
                proc.kill()
                subprocess.run(["pkill", "-KILL", "-f", td])

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_flags_chart_text_below_font_floor(self):
        """图内字号下限 9（viewBox 单位）：图滚入视野才画，探针要先强制画出来再量。"""
        # 图放在首屏之外：reveal 不会自己画它
        chart = """<section><div style="height: 3000px"></div><figure class="fig" data-chart="F1"><div class="fig-box">
          <svg id="tiny" viewBox="0 0 400 320" role="img" aria-labelledby="tiny-t tiny-d"><title id="tiny-t">t</title>
          <desc id="tiny-d">d</desc></svg></div></figure></section>"""
        script = """<script>showMeChart.reveal(document.getElementById("tiny"), (s) =>
          showMeChart.txt(s, { x: 20, y: 40, "font-size": SIZE }, "label"));</script>"""
        for size, flagged in (("8", True), ("9", False)):
            with self.subTest(size=size):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                html = html.replace("</main>", chart + "</main>").replace(
                    "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script.replace("SIZE", size))
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual("字号低于下限：F1（#tiny） 最小 8 < 下限 9" in result.stdout, flagged, result.stdout)
                self.assertEqual(result.returncode, 1 if flagged else 0, result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_warns_on_text_outside_the_frame(self):
        """SVG 外的部分会被裁掉：文字越出图框报 WARN，构建不失败。"""
        chart = """<section><figure class="fig" data-chart="F1"><div class="fig-box">
          <svg id="edge" viewBox="0 0 400 120" role="img" aria-labelledby="edge-t edge-d"><title id="edge-t">t</title>
          <desc id="edge-d">d</desc></svg></div></figure></section>"""
        script = """<script>showMeChart.reveal(document.getElementById("edge"), (s) =>
          showMeChart.txt(s, { x: X, y: 60, "font-size": 10 }, "越出图框的长标签"));</script>"""
        for x, flagged in (("360", True), ("20", False)):
            with self.subTest(x=x):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                html = html.replace("</main>", chart + "</main>").replace(
                    "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script.replace("X", x))
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual("文字越出图框，SVG 外的部分会被裁掉：F1（#edge）「越出图框的长标签」" in result.stdout,
                                 flagged, result.stdout)
                self.assertEqual(result.returncode, 0, result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_flags_shrunk_stat_num(self):
        """页面 <style> 写 .band p 会连 .stat-num 一起压小（2026-10 实例：12.8px 的大数、6.4px 的单位）。"""
        band = """<section><div class="metric-band"><div><p class="stat-num">720<small>p</small></p>
          <p>ABR 自动档上限</p></div></div></section>"""
        for style, flagged in ((".metric-band p { font-size: 0.8rem; }", False),
                               (".band p { font-size: 0.8rem; }", True)):
            with self.subTest(style=style):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                markup = band if not flagged else band.replace('class="metric-band"', 'class="band"')
                html = html.replace("</main>", markup + "</main>").replace(
                    "</head>", f"<style>{style}</style></head>")
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual("正文字号过小：.stat-num「720p」" in result.stdout, flagged, result.stdout)
                self.assertEqual(result.returncode, 1 if flagged else 0, result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_flags_low_contrast_text(self):
        """来源行与图内刻度字在亮色主题下要 4.5:1；ink-45 只有 2.8–3.1:1（2026-10 实例：进房基线报告的来源行与刻度）。"""
        markup = """<section><p class="src">来源 · 演示数据</p><figure class="fig" data-chart="F1"><div class="fig-box">
          <svg id="dim" viewBox="0 0 400 120" role="img" aria-labelledby="dim-t dim-d"><title id="dim-t">t</title>
          <desc id="dim-d">d</desc></svg></div></figure></section>"""
        script = """<script>showMeChart.reveal(document.getElementById("dim"), (s) =>
          showMeChart.txt(s, showMeChart.tick({ x: 20, y: 40EXTRA }), "刻度 10"));</script>"""
        for style, extra, flagged in (("", "", False),
                                      (".src { color: var(--ink-45); }", ', fill: "var(--ink-45)"', True)):
            with self.subTest(flagged=flagged):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                html = html.replace("</main>", markup + "</main>").replace(
                    "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script.replace("EXTRA", extra)).replace(
                    "</head>", f"<style>{style}</style></head>")
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                for part in ("文字对比度不足", "p.src「来源 · 演示数据」", "F1（#dim）「刻度 10」"):
                    self.assertEqual(part in result.stdout, flagged, result.stdout)
                self.assertEqual(result.returncode, 1 if flagged else 0, result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_measures_only_the_shown_diagram_variant(self):
        """宽窄两版图：500px 只量窄版、1024/1280 只量宽版，被媒体查询隐藏的那版不报。"""
        for label, size, flagged in (("ok", None, ()), ("narrow", '13"', ("500px",)),
                                     ("wide", '12"', ("1024px", "1280px"))):
            with self.subTest(variant=label):
                page = self.copy_fixture("diagram-variants.html")
                if size:
                    html = page.read_text(encoding="utf-8")
                    page.write_text(html.replace('font-size="' + size, 'font-size="5"'), encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                for w in ("500px", "1024px", "1280px"):
                    self.assertEqual(f"{w} 下示意图字号渲染后低于 8px：{'窄版' if label == 'narrow' else '宽版'}"
                                     in result.stdout, w in flagged, result.stdout)
                self.assertEqual(result.returncode, 1 if flagged else 0, result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_warns_when_a_chart_is_scaled_up(self):
        """半宽卡的 400 宽 viewBox 单独占整栏会放大一倍多（2026-10 实例：F5 刻度行 2.3 倍，刻度间距 12px）。"""
        fig = """<figure class="fig" data-chart="F5"><div class="fig-box"><svg id="ID" viewBox="0 0 400 200" role="img"
          aria-labelledby="ID-t"><title id="ID-t">t</title></svg></div></figure>"""
        for layout, flagged in (("lone", True), ("pair", False)):
            with self.subTest(layout=layout):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                body = fig.replace("ID", "solo") if layout == "lone" else (
                    '<div class="charts">' + fig.replace("ID", "left") + fig.replace("ID", "right") + "</div>")
                # 夹具没有骨架的 .layout 版心包裹，内容会铺满视口；套上它，倍率才与真实页面（60rem 版心）一致
                html = html.replace('<main id="doc">', '<div class="layout"><main id="doc">').replace(
                    "</main>", f"<section>{body}</section></main></div>")
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                # 反例的两张图 id 是 left / right，只查 #solo 会让误报漏过去，所以先查有没有任何倍率 WARN
                self.assertEqual("显示倍率" in result.stdout, flagged, result.stdout)
                if flagged:
                    self.assertIn("WARN   1280px 下图的显示倍率超出 0.8–1.5：F5（#solo）", result.stdout)
                self.assertEqual(result.returncode, 0, result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_names_content_wider_than_its_box(self):
        """盒子没越界、盒子里不断行的长串越界时，也要点名元素（2026-10 实例：.src 里的长源码路径，报错时只有文档宽度）。"""
        long_path = "/".join(["sdk/src/google/java/libx/android/billing/google"] * 4) + "/GPBillingWrapper.kt"
        page = self.copy_fixture()
        self.insert(page, f'<section><p class="src">{long_path}</p></section>')

        result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertRegex(result.stdout, r"500px 视口横向溢出：文档宽 \d+px；越界元素：p\.src\(内容比盒子宽 \d+px\)")

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_render_check_warns_on_wide_chart_without_narrow_variant(self):
        """通栏 800 宽的数据图在 500px 下 9 号字只剩约 5px：没画窄版报 WARN，画了窄版不报。"""
        wide = """<svg id="ID" CLS viewBox="0 0 800 200" role="img" aria-labelledby="ID-t"><title id="ID-t">t</title></svg>"""
        script = """<script>["IDS"].forEach((id) => showMeChart.reveal(document.getElementById(id), (s) =>
          showMeChart.txt(s, showMeChart.tick({ x: 20, y: 40 }), "label")));</script>"""
        variants = {
            "wide-only": (wide.replace("ID", "solo").replace("CLS", ""), '"solo"'),
            "with-narrow": (wide.replace("ID", "w").replace("CLS", 'class="diagram-wide"')
                            + wide.replace("ID", "n").replace("CLS", 'class="diagram-narrow"').replace("0 0 800 200", "0 0 340 200"),
                            '"w", "n"'),
        }
        for label, (svgs, ids) in variants.items():
            with self.subTest(variant=label):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8").replace(
                    "</main>", f'<section><figure class="fig wide" data-chart="L11"><div class="fig-box">{svgs}</div></figure></section></main>'
                ).replace("<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script.replace('"IDS"', ids))
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertEqual("500px 下数据图字号渲染后低于 8px：L11（#solo）" in result.stdout,
                                 label == "wide-only", result.stdout)
                self.assertNotIn("数据图字号渲染后低于 8px：L11（#n）", result.stdout)

    def test_duplicate_svg_ids_fail(self):
        """宽窄两版共用 marker id 时，窄版的 url(#…) 会指到隐藏的宽版里。"""
        page = self.copy_fixture("diagram-variants.html")
        html = page.read_text(encoding="utf-8")
        page.write_text(html.replace("flow-n-arrow", "flow-arrow"), encoding="utf-8")
        result = run_build(page)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("SVG 里有重复 id：flow-arrow", result.stdout)

    def test_gallery_loops_are_registered_for_pause(self):
        """循环必须登记进 keep：reveal 靠它在图滚出视口时停表，漏登记的会一直逼出重绘。"""
        for src in sorted((SKILL / "assets" / "gallery").glob("*.html")):
            with self.subTest(page=src.name):
                text = src.read_text(encoding="utf-8")
                loose = [
                    text[max(0, m.start() - 40) : m.start()]
                    for m in re.finditer(r"\bsetInterval\(", text)
                    if "keep(" not in text[max(0, m.start() - 40) : m.start()]
                ]
                # 只认 setInterval：循环 rAF 也走 keep，但一次性的 rAF（入场前一帧对齐）不必
                self.assertEqual(loose, [], f"{src.name}: setInterval 未登记进 keep()")

    def test_check_only_does_not_mutate(self):
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        before = page.read_bytes()

        result = run_build(page, "--check-only")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(page.read_bytes(), before)

    def test_missing_recipe_fails(self):
        page = self.copy_fixture()
        page.write_text(
            page.read_text(encoding="utf-8").replace(' data-recipe="status-report"', ""),
            encoding="utf-8",
        )

        result = run_build(page)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("data-recipe", result.stdout + result.stderr)

    def test_check_only_accepts_pre_recipe_historical_page(self):
        page = self.copy_fixture()
        self.assertEqual(run_build(page).returncode, 0)
        page.write_text(
            page.read_text(encoding="utf-8").replace(' data-recipe="status-report"', ""),
            encoding="utf-8",
        )

        result = run_build(page, "--check-only")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("历史页面", result.stdout + result.stderr)

    def test_unknown_recipe_fails(self):
        page = self.copy_fixture()
        page.write_text(
            page.read_text(encoding="utf-8").replace("status-report", "unknown-recipe"),
            encoding="utf-8",
        )

        result = run_build(page)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown-recipe", result.stdout + result.stderr)

    def test_all_recipes_are_accepted(self):
        source = (FIXTURES / "minimal-shell.html").read_text(encoding="utf-8")
        for recipe in RECIPES:
            with self.subTest(recipe=recipe):
                with tempfile.TemporaryDirectory() as tmp:
                    page = Path(tmp) / "page.html"
                    page.write_text(source.replace("status-report", recipe), encoding="utf-8")
                    result = run_build(page)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_style_option_has_migration_error(self):
        page = self.copy_fixture()

        result = run_build(page, "--style", "nova")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--style 已移除", result.stdout + result.stderr)

    def test_generated_inner_html_is_rejected(self):
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "</body>",
            '<script>const value = input.value; output.innerHTML = value;</script></body>',
        )
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("innerHTML", result.stdout + result.stderr)

    def test_inner_html_bypasses_are_rejected_and_literals_allowed(self):
        """+= 与 insertAdjacentHTML 也会把动态值写成 HTML；字面量与比较运算不算。"""
        cases = (
            ("output.innerHTML += value;", True),
            ('output.insertAdjacentHTML("beforeend", value);', True),
            ('output.insertAdjacentHTML("beforeend", "<br>");', False),
            ('output.innerHTML = "<br>";', False),
            ('output.innerHTML = "";', False),
            ('output.innerHTML = "<b>" + value;', True),
            ("output.innerHTML = `<b>${value}</b>`;", True),
            ('if (output.innerHTML == "") output.textContent = value;', False),
        )
        for js, rejected in cases:
            with self.subTest(js=js):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8").replace("</body>", f"<script>{js}</script></body>")
                page.write_text(html, encoding="utf-8")

                result = run_build(page)

                self.assertEqual("innerHTML" in result.stdout, rejected, result.stdout)
                self.assertEqual(result.returncode != 0, rejected, result.stdout)

    def test_hidden_native_control_requires_accessible_replacement(self):
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "</section>", '<input type="checkbox" hidden /></section>', 1
        )
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("隐藏原生控件", result.stdout + result.stderr)

    def test_clickable_non_control_requires_keyboard_semantics(self):
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "</section>", '<div onclick="activate()">打开</div></section>', 1
        )
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("非语义元素", result.stdout + result.stderr)

    def test_latex_compiles_to_mathml_and_stays_idempotent(self):
        import shutil
        if not shutil.which("node"):
            self.skipTest("需要 node")
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "<h1>", "<p>价格 $5 和 $8 不是公式；$E = mc^2$ 是。</p>\n$$\\sum_{k=0}^{n} 2^k$$\n<h1>", 1)
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = page.read_text(encoding="utf-8")
        self.assertEqual(out.count("<math"), 2)
        self.assertIn("价格 $5 和 $8", out)
        self.assertIn('display="block"', out)
        self.assertEqual(out.count('data-show-me="math"'), 1)
        again = run_build(page)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(page.read_text(encoding="utf-8"), out)

    def test_uncompiled_latex_is_an_error_in_check_only(self):
        page = self.copy_fixture()
        page.write_text(page.read_text(encoding="utf-8").replace("<h1>", "<p>$x^2$</p><h1>", 1), encoding="utf-8")
        result = run_build(page, "--check-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("未编译", result.stdout + result.stderr)

    def test_repeated_eyebrows_warn(self):
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "<h1>", '<p class="eyebrow">周报</p><h2>周报</h2><p class="eyebrow">状态</p><h1>', 1
        )
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("眉标口吃", result.stdout + result.stderr)


    def test_repeated_ink_cards_warn(self):
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "<h1>",
            '<article class="card" data-variant="ink"><section><p>1</p></section></article>'
            '<article class="card" data-variant="ink"><section><p>2</p></section></article><h1>',
            1,
        )
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("反色暗卡", result.stdout + result.stderr)

    def test_grid_without_track_template_warns(self):
        page = self.copy_fixture()
        style = (
            "<style>.ok { display: grid; grid-template-columns: 1fr; }"
            " @media (min-width: 40rem) { .bare { display: grid; } }"
            " .noted { display: grid; /* grid-template-columns later */ }</style></head>"
        )
        page.write_text(page.read_text(encoding="utf-8").replace("</head>", style, 1), encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("`.bare` 是 grid", result.stdout)
        self.assertIn("`.noted` 是 grid", result.stdout)
        self.assertNotIn("`.ok` 是 grid", result.stdout)

    def test_long_inline_data_does_not_stall_checks(self):
        page = self.copy_fixture()
        blob = "A" * 400_000  # 约等于一张内联截图；旧的规则扫描在这里要跑几分钟
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "</section>", f'<p><img alt="示意" src="data:image/png;base64,{blob}"></p></section>', 1
            ),
            encoding="utf-8",
        )

        started = time.monotonic()
        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertLess(time.monotonic() - started, 20)


class VisualContractTests(unittest.TestCase):
    def test_css_covers_every_recipe(self):
        css = CSS.read_text(encoding="utf-8")
        for recipe in RECIPES:
            with self.subTest(recipe=recipe):
                self.assertIn(f'[data-recipe="{recipe}"]', css)

    def test_css_avoids_broad_transitions(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertNotRegex(css, r"transition(?:-property)?\s*:\s*all\b")

    def test_spacing_scale_is_complete(self):
        css = CSS.read_text(encoding="utf-8")
        for step in range(1, 8):
            with self.subTest(step=step):
                self.assertRegex(css, rf"--space-{step}:\s*[\d.]+rem")

    def test_card_padding_lives_on_the_card(self):
        """三段可选，所以内边距不能只挂在 header/section/footer 上：
        挂在三段上时，卡里直接写 <p> 会四边贴边，而且不报错、只难看。"""
        css = CSS.read_text(encoding="utf-8")
        block = re.search(r"\n\.card \{(.*?)\n\}", css, re.S)
        self.assertIsNotNone(block, ".card 规则块找不到了")
        self.assertRegex(block.group(1), r"padding:\s*[\d.]+rem")
        self.assertNotRegex(
            css, r"\.card > header,\n\.card > section,\n\.card > footer \{\n  padding:"
        )

    def test_recipe_matrix_lists_every_recipe(self):
        html = (FIXTURES / "recipe-matrix.html").read_text(encoding="utf-8")
        for recipe in RECIPES:
            with self.subTest(recipe=recipe):
                self.assertIn(f'data-recipe="{recipe}"', html)

    def test_alert_content_has_an_explicit_grid_column(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertRegex(css, r"\.alert\s*>\s*section\s*\{[^}]*grid-column:\s*2")
        self.assertRegex(css, r"\.alert\s*>\s*:is\(h2, h3, h4\)\s*\{[^}]*grid-column:\s*2")

    def test_print_resets_owned_theme_tokens(self):
        css = CSS.read_text(encoding="utf-8")
        print_css = css.split("@media print", 1)[1]
        self.assertRegex(print_css, r":root,\s*html\.dark,\s*\.dark\s*\{")
        for token in ("--background", "--foreground", "--card", "--muted", "--border"):
            with self.subTest(token=token):
                self.assertRegex(print_css, rf"{token}:\s*#[0-9a-f]+")

    def test_literal_colors_live_only_in_primitive_layer(self):
        css = CSS.read_text(encoding="utf-8")
        body = re.sub(r"@media print\b[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
        literal = re.findall(r"#[0-9a-fA-F]{3,8}\b", body)
        # 原语：ink / paper / hero / 7 个 tone / ink-fixed，加深色主题的 ink / paper
        self.assertLessEqual(len(literal), 13, literal)
        for token in ("--chart-1", "--chart-hero", "--color-card", "--syn-keyword"):
            with self.subTest(token=token):
                self.assertRegex(css, rf"{token}:\s*(?:var|color-mix)\(")

    def test_layout_docs_define_every_visual_contract(self):
        layouts = (SKILL / "references" / "layouts.md").read_text(encoding="utf-8")
        self.assertEqual(layouts.count("**视觉契约**"), len(RECIPES))
        for recipe in RECIPES:
            with self.subTest(recipe=recipe):
                self.assertIn(f"`{recipe}`", layouts)


if __name__ == "__main__":
    unittest.main()
