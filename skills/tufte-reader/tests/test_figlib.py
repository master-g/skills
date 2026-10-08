"""python3 -m unittest discover -s skills/tufte-reader/tests"""
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import figlib as f  # noqa: E402


class FiglibTest(unittest.TestCase):
    def test_ids_unique_across_figures(self):
        body = f.line(0, 0, 10, 0, arrow=True) + f.line(0, 5, 10, 5, arrow=True, color=2) + f.rect(0, 0, 5, 5, hatch=True)
        a, b = f.svg(20, 20, body, "甲"), f.svg(20, 20, body, "乙")
        ids_a, ids_b = re.findall(r'\bid="([^"]+)"', a), re.findall(r'\bid="([^"]+)"', b)
        self.assertEqual(len(ids_a), 3)  # 黑箭头、2 号色箭头、斜线；没用到的不带
        self.assertFalse(set(ids_a) & set(ids_b))
        for i in ids_a:
            self.assertIn(f"url(#{i})", a)
        self.assertEqual(len(re.findall(r"url\(#([^)]+)\)", a)), 3)

    def test_no_defs_when_unused(self):
        self.assertNotIn("<defs>", f.svg(20, 20, f.rect(0, 0, 5, 5), "甲"))

    def test_colors_follow_theme(self):
        out = f.rect(0, 0, 5, 5, 0.3, color=3) + f.circ(0, 0) + f.text(0, 0, "a", color=1)
        self.assertIn('fill="var(--fig-3, #2e9d4e)"', out)
        self.assertIn('fill="currentColor"', out)
        # 回退色与 tufte.css 亮色主题的 token 一致
        css = (Path(f.__file__).parent.parent / "assets" / "tufte.css").read_text(encoding="utf-8")
        for k, v in f.FALLBACK.items():
            self.assertIn(f"--fig-{k}: {v};", css)

    def test_text_is_escaped(self):
        self.assertIn(">a &lt; b &amp; c</text>", f.text(0, 0, "a < b & c"))

    def test_text_width(self):
        self.assertEqual(f.tw("编码器", 10), 30)
        self.assertAlmostEqual(f.tw("abc", 10, mono=True), 18.06)
        self.assertLess(f.tw("illicit"), f.tw("mammoth"))
        # 自适应宽度的方块装得下文字
        w = float(re.search(r'width="([\d.]+)"', f.box(0, 0, None, 20, "Language Model")).group(1))
        self.assertGreater(w, f.tw("Language Model", 12))

    def test_elbow(self):
        self.assertIn('points="0.0,0.0 10.0,0.0 10.0,20.0"', f.elbow(0, 0, 10, 20))
        self.assertIn('points="0.0,0.0 0.0,20.0 10.0,20.0"', f.elbow(0, 0, 10, 20, "vh"))
        self.assertIn('points="0.0,0.0 4.0,0.0 4.0,20.0 10.0,20.0"', f.elbow(0, 0, 10, 20, "hvh", at=4))
        self.assertIn('points="0.0,0.0 0.0,10.0 10.0,10.0 10.0,20.0"', f.elbow(0, 0, 10, 20, "vhv"))
        with self.assertRaises(ValueError):
            f.elbow(0, 0, 1, 1, "x")

    def test_cells(self):
        out = f.cells(0, 0, 2, 2, 10, fill=lambda i, j: None if i == j else 0.5,
                      color=lambda i, j: j + 1, label=lambda i, j: f"{i}{j}")
        self.assertEqual(out.count("<rect"), 2)
        self.assertIn(">01</text>", out)
        self.assertIn("var(--fig-2", out)

    def test_mathtext(self):
        out = f.mathtext(100, 50, r"a < b", anchor="end")
        self.assertIn('class="fig-math fig-math-end"', out)
        self.assertIn("$a &lt; b$", out)
        x, w = (float(re.search(rf'\b{k}="([\d.-]+)"', out).group(1)) for k in ("x", "width"))
        self.assertAlmostEqual(x + w, 100)

    def test_steps_and_embed(self):
        body = f.rle(["A", "A", "B"]) + f.g("2-", "C")
        self.assertEqual(body, '<g data-step="1-2">A</g><g data-step="3">B</g><g data-step="2-">C</g>')
        fig = f.steps(10, 10, body, "图", ["一", "二", "三"])
        self.assertEqual(fig.count("<li>"), 3)
        self.assertEqual(f.embed("x<!--FIG:a-->y", {"a": "FIG"}), "xFIGy")
        with self.assertRaises(KeyError):
            f.embed("<!--FIG:nope-->", {})


@unittest.skipUnless(shutil.which("node"), "需要 node 编译公式")
class PreviewTest(unittest.TestCase):
    def test_preview_page_builds(self):
        import figpreview

        fig = f.svg(100, 40, f.mathtext(50, 20, "x_1") + f.rect(0, 0, 9, 9, 0.3, color=2), "图")
        page, log = figpreview.preview_page(fig, Path(tempfile.mkdtemp()), "demo")
        html = page.read_text(encoding="utf-8")
        self.assertIn("<figure><svg", html)
        self.assertIn("<math", html.split("<foreignObject x=", 1)[1])
        self.assertIn("--fig-2:", html)
        # 预览页没有章标题，只该有这一条 ERROR
        errors = [line for line in log.splitlines() if line.startswith("ERROR")]
        self.assertEqual(len(errors), 1, log)
        self.assertIn("<h2>", errors[0])


if __name__ == "__main__":
    unittest.main()
