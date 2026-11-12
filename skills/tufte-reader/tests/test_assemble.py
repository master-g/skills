import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSEMBLE = ROOT / "scripts" / "assemble.py"
SHELL = (ROOT / "assets" / "shell.html").read_text(encoding="utf-8").replace("中文标题 · 原文标题", "测试 · Test")
HEAD = SHELL[: SHELL.index("</header>") + len("</header>")] + "\n"
TAIL = SHELL[SHELL.index("<!--TR:JS-->") :]


def chapter(cid, number, body="<p>正文。</p>"):
    return (f'<article class="chapter" id="{cid}"><h2><span class="chapter-number">{number}</span>第 {number} 章</h2>'
            f"<section>{body}</section></article>\n")


def figure(key):
    return f'<figure><span class="marginnote">图　题。</span><!--FIG:{key}--></figure>'


ARROW = 'from figlib import *\nFIGS["{key}"] = svg(200, 60, line(10, 30, 150, 30, arrow=True), "箭头")\n'


def assemble(files, *args):
    d = Path(tempfile.mkdtemp())
    src = d / "src"
    src.mkdir()
    for name, text in {"head.html": HEAD, "tail.html": TAIL, **files}.items():
        (src / name).write_text(text, encoding="utf-8")
    page = d / "book.html"
    out = subprocess.run([sys.executable, str(ASSEMBLE), str(src), "-o", str(page), *args], capture_output=True, text=True)
    return out.returncode, page, out.stdout + out.stderr


class AssembleTest(unittest.TestCase):
    def test_chapters_in_order_with_figures_filled(self):
        rc, page, out = assemble({
            "ch01.html": chapter("one", 1, "<p>正文。</p>" + figure("one-a")),
            "ch02.html": chapter("two", 2),
            "figs.py": ARROW.format(key="one-a"),
        })
        self.assertEqual(rc, 0, out)
        html = page.read_text(encoding="utf-8")
        self.assertLess(html.index('id="one"'), html.index('id="two"'))
        self.assertNotIn("<!--FIG:", html)
        self.assertIn('aria-label="箭头"', html)

    def test_appendix_follows_chapters_and_references_come_last(self):
        rc, page, out = assemble({
            "ch01.html": chapter("one", 1),
            "ch02.html": chapter("two", 2),
            "apx.html": chapter("extra", "附录"),
            "refs.html": '<section class="references" id="references"><h2>参考文献</h2><ol><li id="ref-a">A.</li></ol></section>\n',
        })
        self.assertEqual(rc, 0, out)
        html = page.read_text(encoding="utf-8")
        order = [html.index(mark) for mark in ('<article class="chapter" id="two"', '<article class="chapter" id="extra"',
                                                '<section class="references"', '<script data-tr="js">')]
        self.assertEqual(order, sorted(order))

    def test_missing_figure_fails_before_writing_the_page(self):
        rc, page, out = assemble({"ch01.html": chapter("one", 1, figure("nope"))})
        self.assertEqual(rc, 1)
        self.assertIn("缺图：nope", out)
        self.assertFalse(page.exists())

    def test_only_builds_one_chapter_beside_the_page(self):
        rc, page, out = assemble({"ch01.html": chapter("one", 1), "ch02.html": chapter("two", 2)}, "--only", "ch02")
        self.assertEqual(rc, 0, out)
        self.assertFalse(page.exists())
        trial = page.with_name("book.ch02.check.html").read_text(encoding="utf-8")
        self.assertIn('<article class="chapter" id="two"', trial)
        self.assertNotIn('<article class="chapter" id="one"', trial)

    def test_per_chapter_figure_scripts_do_not_collide(self):
        rc, page, out = assemble({
            "ch01.html": chapter("one", 1, figure("one-a")),
            "ch02.html": chapter("two", 2, figure("two-a")),
            "ch01.figs.py": ARROW.format(key="one-a"),
            "ch02.figs.py": ARROW.format(key="two-a"),
        })
        self.assertEqual(rc, 0, out)
        self.assertNotIn("重复的 id", out)
        self.assertEqual(page.read_text(encoding="utf-8").count('aria-label="箭头"'), 2)

    def test_unknown_flag_fails_before_writing_the_page(self):
        rc, page, out = assemble({"ch01.html": chapter("one", 1)}, "--only=ch01")
        self.assertEqual(rc, 2)
        self.assertIn("不认识的参数：--only=ch01", out)
        self.assertFalse(page.exists())


if __name__ == "__main__":
    unittest.main()
