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
        self.assertIn("边注 2  旁注 4  脚注 2  块级公式 3  行内公式 70", out)
        self.assertEqual(html.count('<input type="checkbox"'), 6)


if __name__ == "__main__":
    unittest.main()
