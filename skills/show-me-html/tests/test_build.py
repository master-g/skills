import base64
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
    def test_markdown_export_names_inlined_images_without_data(self):
        """内联后的图片导出成 ![说明](文件名)：文件名取 data-img-name，带空格时用尖括号包住；
        没有文件名的 data: 图片写 image。export.md 里不出现 data: 地址。"""
        page = self.copy_fixture()
        png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aG1cAAAAASUVORK5CYII="
        imgs = f"""<section><h2>截图</h2>
          <figure class="fig"><img alt="登录页报错" data-img-name="login-error.png" src="{png}" />
          <figcaption>提交后弹出 500。</figcaption></figure>
          <p>行内图 <img alt="旧版图标" src="{png}" /> 已替换。</p>
          <img alt="设置页" data-img-name="Screenshot 2026-11-17 at 10.00.png" src="{png}" />
          </section>"""
        page.write_text(page.read_text(encoding="utf-8").replace("</main>", imgs + "</main>"), encoding="utf-8")

        md = (self.snap_one(page) / "export.md").read_text(encoding="utf-8")

        self.assertIn("![登录页报错](login-error.png)\n\n提交后弹出 500。", md)
        self.assertIn("行内图 ![旧版图标](image) 已替换。", md)
        self.assertIn("![设置页](<Screenshot 2026-11-17 at 10.00.png>)", md)
        self.assertNotIn("data:", md)

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

    @unittest.skipUnless(shutil.which("node"), "需要 node")
    def test_mermaid_compiles_to_wide_and_narrow_svg_and_stays_idempotent(self):
        """横向流程图编译成宽窄两版，时序图只出一版；源码留在页面里，重复构建结果不变。"""
        page = self.copy_fixture("mermaid-flow.html")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = page.read_text(encoding="utf-8")
        self.assertEqual(out.count('<div class="mermaid-figure">'), 2)
        self.assertEqual(out.count('<pre class="mermaid">'), 2)
        self.assertEqual(out.count('class="diagram-wide pele pele-flowchart"'), 1)
        self.assertEqual(out.count('class="diagram-narrow pele pele-flowchart"'), 1)
        self.assertEqual(out.count('class="pele pele-sequence"'), 1)
        svgs = re.findall(r"<svg\b[^>]*\bpele\b[^>]*>", out)
        self.assertEqual(len(svgs), 3)
        for tag in svgs:
            self.assertIn('role="img"', tag)
            self.assertIn("aria-labelledby=", tag)
            self.assertRegex(tag, r'style="max-width:\d+px;')
            self.assertNotRegex(tag, r'\swidth="')
        self.assertIn('class="pele-node pele-shape-rect focus"', out)
        self.assertNotIn("SVG 图缺少", result.stdout)
        self.assertNotIn("斜线", result.stdout)
        again = run_build(page)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(page.read_text(encoding="utf-8"), out)

    @unittest.skipUnless(shutil.which("node"), "需要 node")
    def test_mermaid_syntax_error_names_the_source_line(self):
        page = self.copy_fixture("mermaid-flow.html")
        page.write_text(page.read_text(encoding="utf-8").replace("  D --> A\n", "  D --> [[\n", 1), encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Mermaid 图第 1 幅编译失败，源码第 7 行", result.stdout)
        self.assertIn("有 1 幅 Mermaid 图没有编译成 SVG", result.stdout)
        self.assertEqual(page.read_text(encoding="utf-8").count('<div class="mermaid-figure">'), 1)

    def test_uncompiled_mermaid_is_an_error_in_check_only(self):
        page = self.copy_fixture("mermaid-flow.html")
        result = run_build(page, "--check-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("有 2 幅 Mermaid 图没有编译成 SVG", result.stdout)

    @unittest.skipUnless(shutil.which("node"), "需要 node")
    def test_mermaid_without_acc_title_warns(self):
        page = self.copy_fixture("mermaid-flow.html")
        html = re.sub(r"  acc(Title|Descr): [^\n]*\n", "", page.read_text(encoding="utf-8"), count=2)
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("Mermaid 图没写 accTitle / accDescr"), 2, result.stdout)

    @unittest.skipUnless(shutil.which("node"), "需要 node")
    def test_mermaid_overwide_chart_warns(self):
        """横向图排出来超过 960px：放进图框字会偏小，构建点名这一幅并给出 Mermaid 的改法。"""
        page = self.copy_fixture("mermaid-flow.html")
        html = page.read_text(encoding="utf-8").replace(
            "  I -.-> D\n", "  I -.-> D\n  H --> J[通知全体干系人和值班] --> K[更新对外发布说明文档]\n", 1)
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"WARN   Mermaid 图第 1 幅排出来宽 \d{4}px，放进图框要缩到 0\.\d\d 倍")
        self.assertIn("把主流向改成 TD", result.stdout)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_mermaid_page_passes_render_check_and_exports_source(self):
        """宽窄两版都过渲染检查；「复制为 Markdown」带出 accDescr 和 mermaid 代码块，各一次。"""
        page = self.copy_fixture("mermaid-flow.html")
        snap = page.parent / "snap"

        result = subprocess.run([sys.executable, str(BUILD), str(page), "--snap", str(snap),
                                 "--snap-theme", "light", "--snap-width", "1280"],
                                text=True, capture_output=True, check=False)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("WARN   ", result.stdout)
        md = (snap / "export.md").read_text(encoding="utf-8")
        self.assertEqual(md.count("```mermaid\nflowchart LR\n"), 1, md)
        self.assertEqual(md.count("```mermaid\nsequenceDiagram\n"), 1, md)
        self.assertEqual(md.count("任何一步不过都回到修复。"), 2, md)  # 一次是 desc 导出的段落，一次在源码的 accDescr 行
        self.assertIn("错误率 < 1%?", md)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_mermaid_nodes_become_buttons_in_both_variants(self):
        """interactions.md「可点击的 Mermaid 节点」的脚本：有详情的节点变成按钮，点一个，宽窄两版同时标成选中，详情栏换内容。"""
        page = self.copy_fixture("mermaid-flow.html")
        script = """<aside id="node-detail" aria-live="polite" data-md-skip></aside>
<script>
const DETAIL = { A: { title: "提交 PR", body: "作者侧先验证。" }, F: { title: "灰度 5%", body: "观察 30 分钟。" } };
const nodes = document.querySelectorAll(".pele-node[data-id]");
const pick = (id) => {
  nodes.forEach((n) => n.hasAttribute("role") && n.setAttribute("aria-pressed", String(n.dataset.id === id)));
  const detail = document.getElementById("node-detail");
  const title = document.createElement("h3");
  const body = document.createElement("p");
  title.textContent = DETAIL[id].title;
  body.textContent = DETAIL[id].body;
  detail.replaceChildren(title, body);
};
nodes.forEach((g) => {
  const value = DETAIL[g.dataset.id];
  if (!value) return;
  g.closest("svg").setAttribute("role", "group");
  g.setAttribute("role", "button");
  g.setAttribute("tabindex", "0");
  g.setAttribute("aria-label", value.title);
  g.setAttribute("aria-pressed", "false");
  g.addEventListener("click", () => pick(g.dataset.id));
  g.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      pick(g.dataset.id);
    }
  });
});
</script>
"""
        page.write_text(page.read_text(encoding="utf-8").replace("<!--SHOW-ME:JS-->", script + "<!--SHOW-ME:JS-->"), encoding="utf-8")
        result = run_build(page)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        run_jobs = runpy.run_path(str(BUILD))["run_jobs"]
        probe = """(function(){
          var q = function(s){ return document.querySelectorAll(s).length; };
          var before = [q('.pele-node[role="button"]'), q('svg.pele[role="group"]'), q('svg.pele[role="img"]')];
          document.querySelector('.diagram-wide .pele-node[data-id="F"]').dispatchEvent(new MouseEvent('click', {bubbles: true}));
          var shown = getComputedStyle(document.querySelector('.diagram-wide .pele-node[data-id="F"] > :first-child'));
          return JSON.stringify({before: before, pressed: q('.pele-node[aria-pressed="true"]'),
            ids: Array.from(document.querySelectorAll('.pele-node[aria-pressed="true"]')).map(function(n){ return n.dataset.id; }).join(''),
            detail: document.getElementById('node-detail').textContent, cursor: shown.cursor, width: shown.strokeWidth});
        })()"""
        results, err = run_jobs([{"url": page.as_uri(), "width": 1280, "eval": probe}])
        self.assertIsNotNone(results, err)
        got = json.loads(results[0]["value"])
        self.assertEqual(got["before"], [4, 2, 1])  # A、F 各在宽窄两版里；时序图没有可点节点，保持 role="img"
        self.assertEqual((got["pressed"], got["ids"]), (2, "FF"))
        self.assertEqual(got["detail"], "灰度 5%观察 30 分钟。")
        self.assertEqual((got["cursor"], got["width"]), ("pointer", "2.5px"))

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

    # ── 本地图片：构建时内联成 data URI，未内联的本地资源引用报 ERROR ──

    PNG = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + b"\x00" * 17

    def image_page(self, img, files=()):
        """在临时目录里写页面和图片文件；img 是插进第一节的标记，files 是 (相对路径, 字节) 对。"""
        page = self.copy_fixture()
        for name, data in files:
            target = page.parent / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        self.insert(page, img, before="</section>")
        return page

    def inlined(self, page):
        """成品里每张 <img> 的 (data-img-name, MIME, 解码后的字节)。"""
        html = page.read_text(encoding="utf-8")
        found = []
        for tag in re.findall(r"<img\b[^>]*>", html):
            name = re.search(r'\sdata-img-name="([^"]*)"', tag)
            src = re.search(r'\ssrc="data:([^;,]+);base64,([^"]*)"', tag)
            if src:
                found.append((name and name.group(1), src.group(1), base64.b64decode(src.group(2))))
        return found

    def test_relative_image_is_inlined_with_its_file_name_only(self):
        page = self.image_page('<img src="shots/a.png" alt="截图">', [("shots/a.png", self.PNG)])

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.inlined(page), [("a.png", "image/png", self.PNG)])
        html = page.read_text(encoding="utf-8")
        self.assertNotIn("shots/", html)
        self.assertNotIn(str(page.parent), html)

    def test_absolute_file_url_and_home_paths_are_inlined(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        shot = Path(elsewhere.name) / "my shot.png"
        shot.write_bytes(self.PNG)
        cases = (str(shot), shot.as_uri(), "~/my%20shot.png")
        for src in cases:
            with self.subTest(src=src):
                page = self.image_page(f'<img src="{src}" alt="截图">')

                result = subprocess.run([sys.executable, str(BUILD), str(page), "--no-render"], text=True,
                                        capture_output=True, env={**os.environ, "HOME": elsewhere.name})

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.inlined(page), [("my shot.png", "image/png", self.PNG)])
                self.assertNotIn(elsewhere.name, page.read_text(encoding="utf-8"))

    def image_errors(self, page, *args):
        result = run_build(page, *args)
        self.assertEqual(result.returncode, 1, result.stdout)
        return [line for line in result.stdout.splitlines() if line.startswith("ERROR  ")]

    def test_missing_image_names_the_path_and_the_folder_it_was_read_from(self):
        page = self.image_page('<img src="shots/gone.png" alt="截图">')

        errors = self.image_errors(page)

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("shots/gone.png", errors[0])
        self.assertIn(str(page.parent), errors[0])

    def test_unsupported_extension_lists_the_supported_formats(self):
        page = self.image_page('<img src="a.bmp" alt="截图">', [("a.bmp", b"BM" + b"\x00" * 40)])

        errors = self.image_errors(page)

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("a.bmp", errors[0])
        for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"):
            self.assertIn(ext, errors[0])

    SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4"><rect width="4" height="4"/></svg>'
    FORMATS = (
        ("a.png", "image/png", PNG),
        ("a.jpg", "image/jpeg", b"\xff\xd8\xff\xe0" + b"\x00" * 16),
        ("a.jpeg", "image/jpeg", b"\xff\xd8\xff\xdb" + b"\x00" * 16),
        ("a.gif", "image/gif", b"GIF89a" + b"\x00" * 16),
        ("b.gif", "image/gif", b"GIF87a" + b"\x00" * 16),
        ("a.webp", "image/webp", b"RIFF\x10\x00\x00\x00WEBPVP8 " + b"\x00" * 8),
        ("a.avif", "image/avif", b"\x00\x00\x00\x1cftypavif" + b"\x00" * 16),
        ("a.svg", "image/svg+xml", SVG),
        ("b.svg", "image/svg+xml", b'\xef\xbb\xbf<?xml version="1.0"?>\n<!-- made by hand -->\n'
                                   b'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "x.dtd">\n' + SVG),
    )

    def test_each_supported_format_passes_its_content_check(self):
        for name, mime, data in self.FORMATS:
            with self.subTest(name=name):
                page = self.image_page(f'<img src="{name}" alt="图">', [(name, data)])

                result = run_build(page)

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.inlined(page), [(name, mime, data)])

    def test_content_that_is_not_the_claimed_format_fails(self):
        cases = (("a.png", b"\xff\xd8\xff\xe0" + b"\x00" * 16), ("a.jpg", self.PNG), ("a.gif", b"GIF90a"),
                 ("a.webp", b"RIFF\x10\x00\x00\x00WAVEfmt "), ("a.avif", b"\x00\x00\x00\x1cftypmp42"),
                 ("a.svg", b"<html><svg></svg></html>"), ("b.png", b"not an image at all"))
        for name, data in cases:
            with self.subTest(name=name):
                page = self.image_page(f'<img src="{name}" alt="图">', [(name, data)])

                errors = self.image_errors(page)

                self.assertEqual(len(errors), 1, errors)
                self.assertIn(name, errors[0])
                self.assertIn("内容不是", errors[0])

    def test_image_over_the_size_limit_reports_its_size_and_the_limit(self):
        big = self.PNG + b"\x00" * (6 * 1024 * 1024)
        page = self.image_page('<img src="big.png" alt="大图">', [("big.png", big)])

        errors = self.image_errors(page)

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("big.png", errors[0])
        self.assertIn("6.0 MB", errors[0])
        self.assertIn("上限 5 MB", errors[0])

    def test_directory_named_like_an_image_fails(self):
        page = self.image_page('<img src="shots.png" alt="图">')
        (page.parent / "shots.png").mkdir()

        errors = self.image_errors(page)

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("shots.png", errors[0])
        self.assertIn("不是文件", errors[0])

    def test_images_in_secret_folders_are_not_inlined(self):
        for folder in (".git", ".ssh", ".aws", ".azure", ".gnupg", ".kube", ".docker", ".password-store"):
            with self.subTest(folder=folder):
                page = self.image_page(f'<img src="{folder}/a.png" alt="图">', [(f"{folder}/a.png", self.PNG)])

                errors = self.image_errors(page)

                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"{folder}/a.png", errors[0])
                self.assertIn("密钥", errors[0])
                self.assertNotIn("data:image/png", page.read_text(encoding="utf-8"))

    def test_symlink_into_a_secret_folder_is_not_inlined(self):
        page = self.image_page('<img src="innocent.png" alt="图">', [(".ssh/id.png", self.PNG)])
        (page.parent / "innocent.png").symlink_to(page.parent / ".ssh" / "id.png")

        errors = self.image_errors(page)

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("innocent.png", errors[0])
        self.assertIn("密钥", errors[0])

    def test_svg_that_looks_like_it_holds_a_secret_is_not_inlined(self):
        tokens = ("-----BEGIN OPENSSH PRIVATE KEY-----", "AKIA" + "ABCDEFGHIJKLMNOP", "ghp_" + "a" * 36,
                  "sk-ant-api03-abc", "https://user:hunter2@example.com/", 'api_key="abcdefghijklmnop"')
        for token in tokens:
            with self.subTest(token=token):
                svg = self.SVG.replace(b"</svg>", f"<text>{token}</text></svg>".encode())
                page = self.image_page('<img src="a.svg" alt="图">', [("a.svg", svg)])

                errors = self.image_errors(page)

                self.assertEqual(len(errors), 1, errors)
                self.assertIn("a.svg", errors[0])
                self.assertIn("令牌", errors[0])

    def test_rebuilding_a_page_with_inlined_images_is_byte_identical(self):
        page = self.image_page('<figure>\n  <img\n    src="a.png"\n    alt="截图"\n  />\n  <figcaption>图注</figcaption>\n</figure>',
                               [("a.png", self.PNG)])
        self.assertEqual(run_build(page).returncode, 0)
        before = page.read_bytes()
        (page.parent / "a.png").unlink()  # 内联后原文件不再需要

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(page.read_bytes(), before)
        self.assertEqual(self.inlined(page), [("a.png", "image/png", self.PNG)])

    def test_existing_data_uri_images_are_kept_verbatim(self):
        img = ('<img alt="手工内联" data-img-name="old.png" src="data:image/png;base64,'
               + base64.b64encode(self.PNG).decode() + '"><img alt="" src="data:image/svg+xml,%3Csvg%3E%3C/svg%3E">')
        page = self.image_page(img)

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(img, page.read_text(encoding="utf-8"))

    def test_pointing_src_back_at_a_file_replaces_the_image(self):
        page = self.image_page('<img src="a.png" alt="图">', [("a.png", self.PNG), ("b.gif", b"GIF89a" + b"\x00" * 16)])
        self.assertEqual(run_build(page).returncode, 0)
        html = page.read_text(encoding="utf-8")
        page.write_text(re.sub(r'src="data:[^"]*"', 'src="b.gif"', html), encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.inlined(page), [("b.gif", "image/gif", b"GIF89a" + b"\x00" * 16)])
        self.assertEqual(page.read_text(encoding="utf-8").count("data-img-name"), 1)

    def test_image_without_alt_fails_and_empty_alt_passes(self):
        data = "data:image/png;base64," + base64.b64encode(self.PNG).decode()
        page = self.image_page(f'<img src="{data}" alt=""><img src="a.png">', [("a.png", self.PNG)])

        errors = self.image_errors(page)

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("alt", errors[0])
        self.assertIn("a.png", errors[0])
        self.assertEqual(len(self.image_errors(page, "--check-only")), 1)
        page.write_text(page.read_text(encoding="utf-8").replace('data-img-name="a.png"', 'data-img-name="a.png" alt="图"'),
                        encoding="utf-8")
        self.assertEqual(run_build(page).returncode, 0)

    def test_check_only_flags_local_images_that_are_not_inlined(self):
        page = self.image_page('<img src="a.png" alt="图"><img src="gone.png" alt="图">', [("a.png", self.PNG)])
        self.assertEqual(run_build(page).returncode, 1)  # gone.png 找不到；a.png 照常内联
        page.write_text(page.read_text(encoding="utf-8").replace('src="gone.png"', 'src="later.png"'), encoding="utf-8")

        errors = self.image_errors(page, "--check-only")

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("later.png", errors[0])
        self.assertIn("没有内联", errors[0])

    def test_other_local_resource_references_fail_and_point_at_img_src(self):
        png = "data:image/png;base64," + base64.b64encode(self.PNG).decode()
        cases = (
            f'<img src="{png}" alt="图" srcset="{png} 1x, a@2x.png 2x">',
            '<picture><source srcset="a.webp" type="image/webp"><img src="https://example.com/a.png" alt="图"></picture>',
            '<video src="clip.mp4"></video>',
            '<audio controls><source src="~/a.mp3"></audio>',
            '<svg viewBox="0 0 4 4" role="img" aria-label="图"><image href="a.png" width="4" height="4"/></svg>',
            '<svg viewBox="0 0 4 4" role="img" aria-label="图"><image xlink:href="file:///tmp/a.png"/></svg>',
            '<style>.hero { background: url("bg.png") }</style>',
            '<div style="background-image: url(/tmp/bg.png)">x</div>',
        )
        for snippet in cases:
            with self.subTest(snippet=snippet):
                page = self.image_page(snippet)

                errors = [e for e in self.image_errors(page) if "外部资源" not in e]

                self.assertEqual(len(errors), 1, errors)
                self.assertIn("<img src>", errors[0])

    def test_fragment_and_data_references_are_not_local_resources(self):
        png = "data:image/png;base64," + base64.b64encode(self.PNG).decode()
        snippet = (
            '<svg viewBox="0 0 4 4" role="img" aria-label="图"><defs><linearGradient id="g"><stop offset="0"/>'
            '</linearGradient><clipPath id="c"><rect width="4" height="4"/></clipPath></defs>'
            "<rect width=\"4\" height=\"4\" fill=\"url(#g)\" clip-path=\"url( '#c' )\"/>"
            f'<image href="{png}" width="4" height="4"/><use href="#c"/></svg>'
            f'<style>.hero {{ background: url("{png}") }} .mask {{ mask: url(#c) }}</style>'
            f'<img src="{png}" alt="图" srcset="{png} 1x, {png} 2x">'
            "<p>CSS 写法示例：<code>background: url(bg.png)</code></p>"
        )
        page = self.image_page(snippet)

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_remote_images_still_fail_as_external_resources(self):
        for src in ("https://example.com/a.png", "//example.com/a.png"):
            with self.subTest(src=src):
                page = self.image_page(f'<img src="{src}" alt="图">')

                errors = self.image_errors(page)

                self.assertEqual(len(errors), 1, errors)
                self.assertIn("外部资源引用", errors[0])
                self.assertNotIn("data-img-name", page.read_text(encoding="utf-8"))

    def test_page_with_a_large_image_checks_fast_without_false_alarms(self):
        """图片数据不算页面自己的样式和脚本：未编码的 SVG data URI 里写到颜色和 innerHTML 也不报。"""
        near_limit = self.PNG + os.urandom(5 * 1024 * 1024 - 64 * 1024)
        svg = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'><script>el.innerHTML = x + y</script>"
               "<rect style='fill: #ff0000' width='4' height='4'/></svg>")
        page = self.image_page(f'<figure><img src="shot.png" alt="截图"></figure><p><img src="{svg}" alt="示意"></p>',
                               [("shot.png", near_limit)])

        started = time.monotonic()
        first = run_build(page)
        second = run_build(page)
        elapsed = time.monotonic() - started

        for result in (first, second):
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("写死了", result.stdout)
            self.assertNotIn("innerHTML", result.stdout)
            self.assertNotIn("SVG 图缺少", result.stdout)
        self.assertLess(elapsed, 20)
        self.assertEqual(self.inlined(page)[0][2], near_limit)

    # ── 回复能力：读者在页面上作答，再把决定和评论汇总成一段 Markdown ──

    def test_reply_page_inlines_reply_runtime_once(self):
        page = self.copy_fixture("reply-decisions.html")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        built = page.read_text(encoding="utf-8")
        self.assertEqual(built.count('data-show-me="reply"'), 1)
        self.assertIn("window.showMeReply", built)
        before = hashlib.sha256(page.read_bytes()).digest()
        self.assertEqual(run_build(page).returncode, 0)
        self.assertEqual(hashlib.sha256(page.read_bytes()).digest(), before)

    def test_page_without_reply_flag_has_no_reply_runtime(self):
        page = self.copy_fixture()

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        built = page.read_text(encoding="utf-8")
        self.assertNotIn('data-show-me="reply"', built)
        self.assertNotIn("showMeReply", built)

    def test_rebuild_drops_reply_runtime_when_flag_is_removed(self):
        page = self.copy_fixture("reply-decisions.html")
        html = page.read_text(encoding="utf-8")
        page.write_text(re.sub(r"<fieldset.*?</fieldset>", "", html, flags=re.S), encoding="utf-8")
        self.assertEqual(run_build(page).returncode, 0)
        page.write_text(page.read_text(encoding="utf-8").replace(" data-reply>", ">", 1), encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        built = page.read_text(encoding="utf-8")
        self.assertNotIn('data-show-me="reply"', built)
        self.assertNotIn("showMeReply", built)

    def snap_one(self, page):
        """--snap 只拍一个主题、一个宽度；返回输出目录。"""
        out = page.parent / "snap"
        result = run_build(page, "--snap", str(out), "--snap-theme", "light", "--snap-width", "1280")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("--snap 未完成", result.stdout)
        return out

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_snap_writes_reply_md_only_for_reply_pages(self):
        out = self.snap_one(self.copy_fixture("reply-decisions.html"))
        self.assertEqual((out / "reply.md").read_text(encoding="utf-8"),
                         "# 回复：任务队列选型\n\n## 决定\n\n"
                         "- 采用哪个队列方案？：未作答（建议是 方案乙）\n"
                         "- 哪些前提要在上线前满足？：未作答（建议是 压测报告、回滚演练）\n")

        plain = self.snap_one(self.copy_fixture())
        self.assertTrue((plain / "export.md").exists())
        self.assertFalse((plain / "reply.md").exists())

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_reply_md_reports_adopted_and_changed_decisions(self):
        """标记里预选的状态就是读者的选择：预选建议项是采纳，预选别的项是改选；多选列出全部选中项。"""
        cases = (
            ('<input type="radio" data-suggested />', '<input type="radio" data-suggested checked />',
             "- 采用哪个队列方案？：方案乙（采纳建议）\n"),
            ('<input type="radio" /> 方案丙', '<input type="radio" checked /> 方案丙',
             "- 采用哪个队列方案？：方案丙（改选，建议是 方案乙）\n"),
            ('<input type="checkbox" /> 灰度一周', '<input type="checkbox" checked /> 灰度一周',
             "- 哪些前提要在上线前满足？：灰度一周（改选，建议是 压测报告、回滚演练；加选 灰度一周；未选 压测报告、回滚演练）\n"),
            ('<input type="checkbox" data-suggested />', '<input type="checkbox" data-suggested checked />',
             "- 哪些前提要在上线前满足？：压测报告、回滚演练（采纳建议）\n"),
        )
        for old, new, line in cases:
            with self.subTest(line=line):
                page = self.copy_fixture("reply-decisions.html")
                html = page.read_text(encoding="utf-8")
                self.assertIn(old, html)
                page.write_text(html.replace(old, new), encoding="utf-8")

                reply = (self.snap_one(page) / "reply.md").read_text(encoding="utf-8")

                self.assertIn(line, reply)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_reply_md_lists_every_checked_option_of_a_multi_choice(self):
        page = self.copy_fixture("reply-decisions.html")
        html = page.read_text(encoding="utf-8").replace('<input type="checkbox" />', '<input type="checkbox" checked />')
        page.write_text(html.replace('<input type="checkbox" data-suggested />', '<input type="checkbox" data-suggested checked />', 1),
                        encoding="utf-8")

        reply = (self.snap_one(page) / "reply.md").read_text(encoding="utf-8")

        self.assertIn("- 哪些前提要在上线前满足？：压测报告、灰度一周（改选，建议是 压测报告、回滚演练；加选 灰度一周；未选 回滚演练）\n", reply)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_reply_md_restores_initial_state_with_section_comments(self):
        """初始状态数据与保存的状态同形：决定按选项名、评论按节标题；评论带节标题、逐行引用原文。"""
        state = {"decisions": {"queue": ["方案甲"]},
                 "comments": {"方案对比": "方案乙的运维成本没算进去。\n\n谁来值班？", "上线前提": "  "}}
        page = self.copy_fixture("reply-decisions.html")
        self.insert(page, '<script type="application/json" data-reply-state>'
                    + json.dumps(state, ensure_ascii=False) + "</script>\n", before="<!--SHOW-ME:JS-->")

        reply = (self.snap_one(page) / "reply.md").read_text(encoding="utf-8")

        self.assertIn("- 采用哪个队列方案？：方案甲（改选，建议是 方案乙）\n", reply)
        self.assertTrue(reply.endswith(
            "\n## 评论\n\n- 「方案对比」\n  > 方案乙的运维成本没算进去。\n  >\n  > 谁来值班？\n"), reply)
        self.assertNotIn("上线前提", reply)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_same_titled_sections_keep_their_comments_apart(self):
        """同名的节从第二个起带序号：回复里的节标题就是状态的键，照抄回复写初始状态，评论回到原来那一节。"""
        state = {"comments": {"方案对比": "第一节的意见", "方案对比（2）": "第二节的意见"}}
        page = self.copy_fixture("reply-decisions.html")
        page.write_text(page.read_text(encoding="utf-8").replace("<h2>上线前提</h2>", "<h2>方案对比</h2>"), encoding="utf-8")
        self.insert(page, '<script type="application/json" data-reply-state>'
                    + json.dumps(state, ensure_ascii=False) + "</script>\n", before="<!--SHOW-ME:JS-->")

        reply = (self.snap_one(page) / "reply.md").read_text(encoding="utf-8")

        self.assertTrue(reply.endswith(
            "\n## 评论\n\n- 「方案对比」\n  > 第一节的意见\n- 「方案对比（2）」\n  > 第二节的意见\n"), reply)

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_markdown_export_lists_decision_options_without_reader_answers(self):
        """「复制为 Markdown」导出的是页面内容：决定块出问题和选项、标出建议项；读者的选择、评论入口和回复控件都不进导出。"""
        state = {"comments": {"方案对比": "读者原文不该进导出"}}
        page = self.copy_fixture("reply-decisions.html")
        html = page.read_text(encoding="utf-8").replace('<input type="radio" /> 方案丙', '<input type="radio" checked /> 方案丙')
        page.write_text(html, encoding="utf-8")
        self.insert(page, '<script type="application/json" data-reply-state>'
                    + json.dumps(state, ensure_ascii=False) + "</script>\n", before="<!--SHOW-ME:JS-->")

        md = (self.snap_one(page) / "export.md").read_text(encoding="utf-8")

        self.assertIn("## 方案对比\n\n三个方案的代价。\n\n**采用哪个队列方案？**（单选）\n\n"
                      "- 方案甲 — 沿用现有 cron\n- 方案乙（建议） — 引入 Redis 队列\n- 方案丙\n", md)
        self.assertIn("**哪些前提要在上线前满足？**（多选）\n\n- 压测报告（建议）\n- 灰度一周\n- 回滚演练（建议）\n", md)
        for leaked in ("读者原文", "评论", "清空作答", "复制回复", "已选", "[x]"):
            self.assertNotIn(leaked, md)

    def test_reader_text_in_initial_state_is_not_checked_as_page_code(self):
        """初始状态数据是不执行的读者原文：评论里写到脚本或颜色，不算页面自己的脚本和写死颜色。"""
        state = {"comments": {"方案对比": "示例里的 el.innerHTML = x 要改掉；标题色 color: #ff0000 太刺眼"}}
        page = self.copy_fixture("reply-decisions.html")
        self.insert(page, '<script type="application/json" data-reply-state>'
                    + json.dumps(state, ensure_ascii=False) + "</script>\n", before="<!--SHOW-ME:JS-->")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("innerHTML", result.stdout)
        self.assertNotIn("写死了", result.stdout)

    def test_decision_block_without_reply_flag_fails(self):
        page = self.copy_fixture("reply-decisions.html")
        page.write_text(page.read_text(encoding="utf-8").replace(" data-reply>", ">", 1), encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("ERROR  页面有 2 个决定块，但 <body> 没有 data-reply", result.stdout)

    def test_check_only_flags_decision_blocks_after_flag_is_removed(self):
        """已构建的页面带着回复运行时的源码，运行时里写到的开关不能被当成页面的开关。"""
        page = self.copy_fixture("reply-decisions.html")
        self.assertEqual(run_build(page).returncode, 0)
        page.write_text(page.read_text(encoding="utf-8").replace(" data-reply>", ">", 1), encoding="utf-8")

        result = run_build(page, "--check-only")

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("ERROR  页面有 2 个决定块，但 <body> 没有 data-reply", result.stdout)

    def test_malformed_decision_blocks_fail_and_name_the_block(self):
        extra = '<label><input type="checkbox" /> 其他</label>'
        cases = (
            ('<fieldset class="decision" data-decision="queue">', '<fieldset class="decision">', 1,
             "决定块「采用哪个队列方案？」缺少 data-decision 标识"),
            ('<fieldset class="decision" data-decision="queue">', '<fieldset data-decision="queue">', 1,
             '决定块 queue 的 <fieldset> 缺少 class="decision"'),
            ('data-decision="queue"', 'data-decision="gates"', 1,
             "决定块标识 gates 重复：「采用哪个队列方案？」「哪些前提要在上线前满足？」"),
            ('<label><input type="radio" /> 方案丙</label>', "", 1, "决定块 queue 有 2 个选项"),
            ('<input type="radio" />', "", -1, "决定块 queue 有 1 个选项：要 2 到 6 个"),
            ("上线前满足？</legend>", "上线前满足？</legend>" + extra * 4, 1, "决定块 gates 有 7 个选项：要 2 到 6 个"),
            ('<input type="radio" data-suggested />', '<input type="radio" />', 1,
             "单选决定块 queue 的建议项有 0 个：要恰好 1 个"),
            ('<input type="radio" />', '<input type="radio" data-suggested />', 1,
             "单选决定块 queue 的建议项有 2 个：要恰好 1 个"),
            # 选项名不含 <small> 说明：带说明的「方案甲」与不带说明的「方案甲」同名
            ("方案丙</label>", "方案甲</label>", 1, "决定块 queue 的选项名「方案甲」重复"),
        )
        for old, new, count, message in cases:
            with self.subTest(message=message):
                page = self.copy_fixture("reply-decisions.html")
                html = page.read_text(encoding="utf-8")
                self.assertIn(old, html)
                page.write_text(html.replace(old, new, count), encoding="utf-8")

                result = run_build(page)

                if "有 2 个选项" in message:  # 2 个选项是合法的下限
                    self.assertEqual(result.returncode, 0, result.stdout)
                    self.assertNotIn(message, result.stdout)
                    continue
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(f"ERROR  {message}", result.stdout)


class VisualContractTests(unittest.TestCase):
    def test_css_covers_every_recipe(self):
        css = CSS.read_text(encoding="utf-8")
        for recipe in RECIPES:
            with self.subTest(recipe=recipe):
                self.assertIn(f'[data-recipe="{recipe}"]', css)

    def test_css_avoids_broad_transitions(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertNotRegex(css, r"transition(?:-property)?\s*:\s*all\b")

    def test_every_button_variant_has_its_own_hover(self):
        """基础 .btn:hover 把底色换成主色；变体不自带 hover 时，会拿着自己的文字色落在主色底上。"""
        css = CSS.read_text(encoding="utf-8")
        variants = set(re.findall(r'^\.btn\[data-variant="([\w-]+)"\] \{', css, flags=re.M))
        self.assertGreaterEqual(variants, {"secondary", "outline", "ghost", "link", "destructive"})
        for name in sorted(variants):
            self.assertRegex(css, rf'\.btn\[data-variant="{name}"\]:hover:not\(:disabled\)', name)

    def test_images_fit_the_column_and_stay_whole_in_print(self):
        """截图按原尺寸会撑破版心、在窄屏横滚；打印时跨页会被切成两半。"""
        css = CSS.read_text(encoding="utf-8")
        self.assertRegex(css, r"(?m)^img \{[^}]*max-width:\s*100%[^}]*height:\s*auto")
        print_css = "".join(re.findall(r"@media print \{(.*?)\n\}", css, re.S))
        self.assertRegex(print_css, r"img[^{]*\{[^}]*break-inside:\s*avoid")

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
