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
    groups = "".join(f'<g data-step="{f}"><rect id="r{i}" width="5" height="5" /></g>' for i, f in enumerate(frames))
    return ('<figure class="steps"><span class="marginnote">图 1　题</span>'
            f'<div class="scroll-x"><svg viewBox="0 0 10 10" width="200" role="img" aria-label="图">{groups}<circle r="1" /></svg></div>'
            f'<ol class="step-captions">{"".join(f"<li>说明 {k + 1}。</li>" for k in range(caps))}</ol></figure>')


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
        # 网络字体的样式表由构建注入，不算作者写的外链
        self.assertEqual(html.count('<link data-tr="font" rel="stylesheet" href="https://cdn.jsdelivr.net/'), 5)

    def test_author_external_stylesheet_is_error(self):
        rc, _, out = run(PAGE.replace("<!--TR:CSS-->", '<link rel="stylesheet" href="https://example.org/a.css"><!--TR:CSS-->')
                         .replace("BODY", "<p>正文。</p>"))
        self.assertEqual(rc, 1)
        self.assertIn("外链脚本或样式", out)

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

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_glued_math_runs_can_wrap(self):
        # 相邻的不换行片段之间要留断行机会，否则 Firefox 内核里一串「公式、公式、」会撑宽页面
        rc, html, out = run(PAGE.replace("BODY", "<p>有 $a$、$b$。（$c$），再看「$d$」。</p>"))
        self.assertEqual(rc, 0, out)
        self.assertEqual(html.count("、</span><wbr>"), 1)
        self.assertEqual(html.count("。</span><wbr>"), 1)
        self.assertNotIn("）</span><wbr>", html)  # 后面紧跟逗号，不能在这里断
        self.assertIn("看<wbr><span", html)

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
    def test_tagged_equation_keeps_tag_out_of_math(self):
        rc, html, out = run(PAGE.replace("BODY", "<p>甲</p>\n$$a = b \\tag{2.4}$$\n$$c = d$$"))
        self.assertEqual(rc, 0, out)
        self.assertIn("0 个 WARN", out)
        self.assertRegex(html, r'<span class="math-display tagged"><math.*?</math><span class="eq-tag">\(2\.4\)</span></span>')
        self.assertNotIn("tml-tag", html.split("<body", 1)[1])
        self.assertIn('<span class="math-display"><math', html)

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_script_labels_render_alike_across_engines(self):
        # Firefox 内核会把「文字 + 箭头 + 文字」的上下标当成可伸缩运算符；构建要写死缩小一级、箭头不伸缩
        rc, html, out = run(PAGE.replace("BODY", (
            "<p>甲</p>\n$$\\underbrace{x}_{\\text{the}\\to\\text{cat}} + \\hat{y} + a \\xrightarrow{f} b$$")))
        self.assertEqual(rc, 0, out)
        self.assertIn('</munder><mrow style="math-depth:add(1);font-size:math;"><mtext>the</mtext>', html)
        self.assertIn('<mo stretchy="false">→</mo>', html)
        self.assertIn('<mo stretchy="true" lspace="0" rspace="0">→</mo>', html)  # \xrightarrow 仍然伸缩
        self.assertEqual(html.count("math-depth:add(1)"), 1)

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_wide_display_math_warns(self):
        terms = " + ".join(f"x_{{{i}}}" for i in range(14))  # 约 29em：不带编号放得下，带编号放不下
        rc, _, out = run(PAGE.replace("BODY", f"<p>甲</p>\n$$y = {terms}$$"))
        self.assertIn("0 个 WARN", out)
        rc, _, out = run(PAGE.replace("BODY", f"<p>甲</p>\n$$y = {terms} \\tag{{1}}$$"))
        self.assertEqual(rc, 0, out)
        self.assertIn("扣掉编号后只有 28em", out)
        rc, _, out = run(PAGE.replace("BODY", "<p>甲</p>\n$$\\begin{align} a &= b \\tag{1} \\\\ c &= d \\tag{2} \\end{align}$$"))
        self.assertIn("没能把编号移出来", out)

    @unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
    def test_specimen_builds_clean(self):
        rc, html, out = run((ROOT / "assets" / "specimen.html").read_text(encoding="utf-8"))
        self.assertEqual(rc, 0, out)
        self.assertIn("0 个 WARN", out)
        self.assertIn('<span class="math-display">', html)
        self.assertNotIn("$$", html.split("<body", 1)[1].split("<script", 1)[0])
        self.assertEqual(build.leftover_dollars(html), [])
        self.assertIn("图 2  页边图 0", out)
        self.assertIn("边注 2  旁注 5  脚注 2  块级公式 3  行内公式 76  分步图 1  帧 3", out)
        self.assertEqual(html.count('<input type="checkbox"'), 7)
        self.assertNotIn('data-step="', html)

    def test_steps_expand_to_small_multiples(self):
        rc, first, out = run(PAGE.replace("BODY", steps_figure()))
        self.assertEqual(rc, 0, out)
        self.assertIn("展开分步图 1 幅", out)
        self.assertIn("分步图 1  帧 3", out)
        body = first.split("<body", 1)[1]
        self.assertNotIn("data-step", body)
        self.assertNotIn("step-captions", body)
        self.assertNotIn("scroll-x", body)
        self.assertNotIn("<script>", body)
        self.assertIn('<ol class="step-frames" style="--step-w: 150px">', body)
        frames = body.split('<ol class="step-frames"', 1)[1].split("</ol>", 1)[0].split("<li>")[1:]
        self.assertEqual(len(frames), 3)
        # 每一步只留这一步显示的帧；不带 data-step 的元素每幅都在；id 加后缀互不冲突
        self.assertEqual([f.count("<rect") for f in frames], [1, 3, 2])
        self.assertTrue(all(f.count("<circle") == 1 for f in frames))
        self.assertIn('id="r0-s1"', frames[0])
        self.assertIn('id="r0-s3"', frames[2])
        self.assertIn('aria-label="图（第 2 步，共 3 步）"', frames[1])
        self.assertIn("说明 3。", frames[2])
        rc, second, out = run(first)
        self.assertEqual(rc, 0, out)
        self.assertEqual(first, second)

    def test_steps_errors(self):
        cases = [
            (steps_figure(frames=("1", "2", "4"), caps=4), "缺第 3 步"),
            (steps_figure(caps=2), "有 3 步，说明却是 2 条"),
            (steps_figure(frames=()), "里没有帧"),
            (steps_figure(frames=("1", "3-2", "3")), "写法不对"),
            (steps_figure().replace(' class="step-captions"', ""), "缺 <ol class=\"step-captions\">"),
            ('<figure><svg viewBox="0 0 1 1" width="1" role="img" aria-label="图"><g data-step="1"></g></svg></figure>', "没有展开成小图"),
        ]
        for body, message in cases:
            rc, _, out = run(PAGE.replace("BODY", body))
            self.assertEqual(rc, 1, out)
            self.assertIn(message, out)


if __name__ == "__main__":
    unittest.main()
