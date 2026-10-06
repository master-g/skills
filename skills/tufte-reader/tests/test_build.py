"""python3 -m unittest discover -s skills/tufte-reader/tests"""
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402

PAGE = """<!doctype html><html lang="zh-CN"><head><title>测试 · Test</title><!--TR:CSS--></head><body>
<header class="titlepage"><h1>测试</h1><nav class="toc"></nav></header>
<article class="chapter" id="one"><h2><span class="chapter-number">1</span>第一章</h2>
<section>BODY</section></article>
<article class="chapter" id="two"><h2><span class="chapter-number">2</span>第二章</h2>
<section><p>正文。</p></section></article>
<!--TR:JS--></body></html>"""


PNG_1PX = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def run(html, files=None):
    d = Path(tempfile.mkdtemp())
    for name, data in (files or {}).items():
        (d / name).parent.mkdir(parents=True, exist_ok=True)
        (d / name).write_bytes(data)
    page = d / "p.html"
    page.write_text(html, encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = build.main([str(page)])
    return rc, page.read_text(encoding="utf-8"), out.getvalue()


def steps_figure(frames=("1-", "2", "2-3"), caps=3):
    groups = "".join(f'<g data-step="{f}"><rect width="5" height="5" /></g>' for f in frames)
    return ('<figure class="steps"><span class="marginnote">图 1　题</span>'
            f'<svg viewBox="0 0 10 10" width="10" role="img" aria-label="图">{groups}</svg>'
            f'<ol class="step-captions">{"<li>说明。</li>" * caps}</ol></figure>')


class BuildTest(unittest.TestCase):
    def test_notes_footnotes_toc_nav(self):
        rc, html, out = run(PAGE.replace("BODY", (
            '<p>甲<span class="sidenote">边注</span>乙<span class="marginnote">旁注</span>'
            '丙<span class="footnote">脚注一</span>丁<span class="footnote">脚注二</span></p>')))
        self.assertEqual(rc, 0, out)
        self.assertIn('<label for="sn-1" class="margin-toggle sidenote-number"></label>', html)
        self.assertIn('<input type="checkbox" id="mn-1" class="margin-toggle"/>', html)
        self.assertIn('href="#fn-one-1">*</a>', html)
        self.assertIn('href="#fn-one-2">†</a>', html)
        self.assertIn('<nav class="toc" id="toc"', html)
        self.assertIn('<a href="#two">第二章</a>', html)

    def test_rebuild_is_stable(self):
        _, first, _ = run(PAGE.replace("BODY", '<p>甲<span class="sidenote">注</span><span class="footnote">脚</span></p>'))
        rc, second, out = run(first)
        self.assertEqual(rc, 0, out)
        self.assertEqual(first, second)

    def test_note_outside_paragraph_is_error(self):
        rc, _, out = run(PAGE.replace("BODY", '<span class="sidenote">悬空</span><p>正文。</p>'))
        self.assertEqual(rc, 1)
        self.assertIn("边注不在", out)

    def test_local_image_inlined_remote_rejected(self):
        import base64
        img = '<figure><span class="marginnote">图 1　题</span><img src="figures/a.png" alt="a" /></figure>'
        rc, html, out = run(PAGE.replace("BODY", img), {"figures/a.png": base64.b64decode(PNG_1PX)})
        self.assertEqual(rc, 0, out)
        self.assertIn('src="data:image/png;base64,', html)
        rc, _, out = run(PAGE.replace("BODY", '<figure><img src="https://example.org/a.png" alt="a" /></figure>'))
        self.assertEqual(rc, 1)
        self.assertIn("外网地址", out)

    def test_deep_heading_is_error(self):
        rc, _, out = run(PAGE.replace("BODY", "<h4>太深</h4><p>正文。</p>"))
        self.assertEqual(rc, 1)
        self.assertIn("h4", out)

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_math_entities_decoded(self):
        rc, html, out = run(PAGE.replace("BODY", "<p>其中 $K&lt;D$，且 $n&gt;n'$。</p>"))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("temml-error", html)

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_inline_math_across_lines(self):
        rc, html, out = run(PAGE.replace("BODY", (
            "<p>同一行的公式 $a_k = b$ 正常。跨行的公式 $d_k = d_v =\n  2$ 也要编译。"
            "乘法 $0.16 \\times (0, 1) + 0.16\n  \\times (1, 0)$ 也一样。</p>")))
        self.assertEqual(rc, 0, out)
        self.assertIn("行内 3 个", out)
        self.assertEqual(build.leftover_dollars(html), [])

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_math_does_not_pair_across_tags(self):
        rc, html, out = run(PAGE.replace("BODY", "<p>开头 $a</p>\n<p>b$ 结尾，另有 $x$。</p>"))
        self.assertEqual(rc, 0, out)
        self.assertIn("行内 1 个", out)
        self.assertIn("$a</p>", html)

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_math_glued_to_fullwidth_punctuation(self):
        rc, first, out = run(PAGE.replace("BODY", "<p>最后乘 $V$：输出（$n$）结束，$x$ 不动。</p>"))
        self.assertEqual(rc, 0, out)
        self.assertEqual(first.count('<span class="math-nobr">'), 2)
        self.assertIn("</math>：</span>", first)
        self.assertIn('<span class="math-nobr">（<math', first)
        _, second, _ = run(first)
        self.assertEqual(first, second)

    def test_dollar_amounts_are_not_math(self):
        rc, html, out = run(PAGE.replace("BODY", "<p>早餐 $5，午餐 $8，合计 $13。写成 &#36;x&#36; 也不算公式。</p>"))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("<math", html)

    def test_leftover_dollar_pair_is_error(self):
        rc, _, out = run(PAGE.replace("BODY", "<p>这里的 $a 乘以 b$ 含中文，不会被编译。</p>"))
        self.assertEqual(rc, 1)
        self.assertIn("没有编译成公式", out)
        self.assertIn("$a 乘以 b$", out)

    def test_notes_with_wrapped_open_tag(self):
        rc, html, out = run(PAGE.replace("BODY", (
            '<p>甲<span\n  class="sidenote"\n  >边注</span\n>乙<span\n  class="footnote"\n  >脚注</span\n  >丙</p>')))
        self.assertEqual(rc, 0, out)
        self.assertIn('<label for="sn-1" class="margin-toggle sidenote-number"></label>', html)
        self.assertIn('<li id="fn-one-1"><span class="fn-mark">*</span>脚注 <a', html)

    def test_unexpanded_note_is_error(self):
        rc, _, out = run(PAGE.replace("BODY", (
            '<p>甲<span class="sidenote wide">边注</span>乙<span class="footnote" lang="en">note</span></p>')))
        self.assertEqual(rc, 1)
        self.assertIn("没有展开开关", out)
        self.assertIn("没有归位到章末", out)

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_specimen_builds_clean(self):
        rc, html, out = run((ROOT / "assets" / "specimen.html").read_text(encoding="utf-8"))
        self.assertEqual(rc, 0, out)
        self.assertIn("0 个 WARN", out)
        self.assertIn('<span class="math-display">', html)
        self.assertNotIn("$$", html.split("<body", 1)[1].split("<script", 1)[0])
        self.assertEqual(build.leftover_dollars(html), [])
        self.assertIn("图 3  页边图 0", out)
        self.assertIn("边注 2  旁注 6  脚注 2  块级公式 3  行内公式 83  分步图 1  帧 3", out)
        self.assertEqual(html.count('<input type="checkbox"'), 8)
        self.assertIn('<script data-tr="steps">', html)
        self.assertIn('<style data-tr="fig">', html)

    def test_steps_figure(self):
        rc, first, out = run(PAGE.replace("BODY", steps_figure()))
        self.assertEqual(rc, 0, out)
        self.assertIn("分步图 1  帧 3", out)
        self.assertEqual(first.count('<script data-tr="steps">'), 1)
        self.assertEqual(first.count('<style data-tr="fig">'), 1)
        # 没有脚本和打印时显示最后一步：只有第 3 步可见的帧带标记
        self.assertIn('<g data-step="1-" data-step-last>', first)
        self.assertIn('<g data-step="2"><', first)
        self.assertIn('<g data-step="2-3" data-step-last>', first)
        rc, second, out = run(first)
        self.assertEqual(rc, 0, out)
        self.assertEqual(first, second)
        # 改掉帧之后重新构建，过期的标记要撤掉
        rc, third, out = run(second.replace('data-step="2-3" data-step-last', 'data-step="2"').replace(
            "</svg>", '<g data-step="3"><circle r="1" /></g></svg>'))
        self.assertEqual(rc, 0, out)
        self.assertEqual(third.count(" data-step-last>"), 2)
        self.assertNotIn('data-step="2" data-step-last', third)

    def test_page_without_steps_gets_no_extra_assets(self):
        code = '<pre><code class="language-html">&lt;figure class="steps"&gt;&lt;div class="controls"&gt;</code></pre>'
        rc, html, out = run(PAGE.replace("BODY", "<p>正文。</p>" + code))
        self.assertEqual(rc, 0, out)
        self.assertNotIn('data-tr="steps"', html)
        self.assertNotIn('data-tr="fig"', html)
        self.assertIn("分步图 0  帧 0", out)
        # 去掉分步图后重新构建，脚本和样式一并撤掉
        _, built, _ = run(PAGE.replace("BODY", steps_figure()))
        start = built.index('<figure class="steps">')
        rc, html, out = run(built[:start] + "<p>正文。</p>" + built[built.index("</figure>") + 9:])
        self.assertEqual(rc, 0, out)
        self.assertNotIn('data-tr="steps"', html)
        self.assertNotIn('data-tr="fig"', html)

    def test_steps_errors(self):
        cases = [
            (steps_figure(frames=("1", "2", "4"), caps=4), "缺第 3 步"),
            (steps_figure(caps=2), "有 3 步，说明却是 2 条"),
            (steps_figure(frames=()), "里没有帧"),
            (steps_figure(frames=("1", "3-2", "3")), "写法不对"),
            (steps_figure().replace(' class="step-captions"', ""), "缺 <ol class=\"step-captions\">"),
        ]
        for body, message in cases:
            rc, _, out = run(PAGE.replace("BODY", body))
            self.assertEqual(rc, 1, out)
            self.assertIn(message, out)

    def test_author_script(self):
        fig = ('<figure><svg viewBox="0 0 10 10" width="10" role="img" aria-label="图"><rect width="5" height="5" /></svg>'
               '<div class="controls" hidden><input type="range" /><output>1</output></div><script>SCRIPT</script></figure>'
               '<pre><code class="language-js">fetch("https://example.org")</code></pre>')
        ok = 'document.createElementNS("http://www.w3.org/2000/svg", "rect");'
        rc, html, out = run(PAGE.replace("BODY", fig.replace("SCRIPT", ok)))
        self.assertEqual(rc, 0, out)
        self.assertIn(ok, html)
        self.assertIn('<style data-tr="fig">', html)
        self.assertNotIn('data-tr="steps"', html)
        for bad in ('fetch("data.json")', "new XMLHttpRequest()", 'import("./m.js")', 'var u = "https://example.org/x.js";'):
            rc, _, out = run(PAGE.replace("BODY", fig.replace("SCRIPT", bad)))
            self.assertEqual(rc, 1, bad)
            self.assertIn("作者脚本里出现", out)


if __name__ == "__main__":
    unittest.main()
