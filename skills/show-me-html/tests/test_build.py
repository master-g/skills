import hashlib
import re
import runpy
import shutil
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
SHELL = SKILL / "assets" / "shell.html"


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
        return self.FIGURE.replace('data-chart="F1"', f'data-chart="{chart}"')

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

    @unittest.skipUnless(FIND_CHROME(), "需要本机 Chrome/Chromium")
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
        for name, width in (("light-500", 500), ("dark-500", 500), ("light-1280", 1280), ("dark-1280", 1280)):
            png = out / f"{name}.png"
            self.assertTrue(png.exists(), name)
            self.assertEqual(png_size(png)[0], width, name)
        self.assertNotEqual((out / "light-1280.png").read_bytes(), (out / "dark-1280.png").read_bytes())
        md = (out / "export.md").read_text(encoding="utf-8")
        self.assertIn("# 快照测试", md)
        self.assertIn("## 第二节", md)
        # 组件里的标题按所在节排级：h2 下的 item h4 → ###；h3 泳道下的卡片 h3/h4 → ####/#####
        self.assertIn("\n### 条目\n", md)
        self.assertIn("\n#### 工单\n", md)
        self.assertIn("\n##### 卡内小节\n", md)
        self.assertNotIn("__snap", md)

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

    @unittest.skipUnless(runpy.run_path(str(BUILD))["find_chrome"](), "需要本机 Chrome/Chromium")
    def test_render_check_flags_chart_text_below_font_floor(self):
        """半宽卡图内字号下限 6.5：图滚入视野才画，探针要先强制画出来再量。"""
        # 图放在首屏之外：reveal 不会自己画它
        chart = """<section><div style="height: 3000px"></div><figure class="fig" data-chart="F1"><div class="fig-box">
          <svg id="tiny" viewBox="0 0 400 320" role="img" aria-labelledby="tiny-t tiny-d"><title id="tiny-t">t</title>
          <desc id="tiny-d">d</desc></svg></div></figure></section>"""
        script = """<script>showMeChart.reveal(document.getElementById("tiny"), (s) =>
          showMeChart.txt(s, { x: 20, y: 40, "font-size": SIZE }, "label"));</script>"""
        for size, flagged in (("5", True), ("6.5", False)):
            with self.subTest(size=size):
                page = self.copy_fixture()
                html = page.read_text(encoding="utf-8")
                html = html.replace("</main>", chart + "</main>").replace(
                    "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script.replace("SIZE", size))
                page.write_text(html, encoding="utf-8")
                result = subprocess.run([sys.executable, str(BUILD), str(page)], text=True, capture_output=True, check=False)
                self.assertEqual("字号低于下限：F1（#tiny） 最小 5 < 半宽下限 6.5" in result.stdout, flagged, result.stdout)
                self.assertEqual(result.returncode, 1 if flagged else 0, result.stdout)

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
