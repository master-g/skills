"""python3 skills/tufte-reader/tests/test_figprobe.py"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
import figprobe  # noqa: E402

SCRIPT = SKILL / "scripts" / "figprobe.py"

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>t</title></head>
<body style="margin: 0; font: 16px sans-serif">
{body}
</body></html>
"""


def figure(caption, rect_width):
    return (f'<div class="mermaid-figure"><svg class="pele pele-flowchart" aria-label="{caption}" '
            f'width="420" height="80" viewBox="0 0 420 80"><g class="pele-nodes"><g class="pele-node" data-id="A">'
            f'<rect x="10" y="10" width="{rect_width}" height="60" fill="none" stroke="black"/>'
            f'<text x="{10 + rect_width / 2}" y="45" text-anchor="middle">A rather long label</text>'
            "</g></g></svg></div>")


@unittest.skipUnless(figprobe.find_chrome(), "没有找到 Chrome")
class FigprobeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def probe(self, page):
        out = self.tmp / "out"
        run = subprocess.run([sys.executable, str(SCRIPT), str(page), "-o", str(out)],
                             capture_output=True, text=True, timeout=120)
        return run, out

    def write(self, body):
        page = self.tmp / "page.html"
        page.write_text(PAGE.format(body=body), encoding="utf-8")
        return page

    def test_label_wider_than_box_fails_and_names_the_figure(self):
        run, _ = self.probe(self.write(figure("Roomy", 400) + figure("Cramped", 20)))
        self.assertEqual(run.returncode, 1, run.stdout)
        lines = run.stdout.splitlines()
        cramped = [l for l in lines if "Cramped" in l]
        self.assertEqual(len(cramped), 1, run.stdout)
        self.assertIn("越界", cramped[0])
        self.assertNotIn("越界", next(l for l in lines if "Roomy" in l))
        self.assertTrue(lines[-1].startswith("未通过"), run.stdout)

    def test_roomy_box_passes(self):
        run, out = self.probe(self.write(figure("Roomy", 400)))
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertTrue(run.stdout.splitlines()[-1].startswith("通过：1 幅"), run.stdout)
        for theme in ("light", "dark"):
            self.assertGreater((out / f"page-{theme}.png").stat().st_size, 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["page-dark.png", "page-light.png"])

    def test_page_without_mermaid_passes_with_zero(self):
        run, _ = self.probe(self.write("<p>没有图。</p>"))
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertTrue(run.stdout.splitlines()[-1].startswith("通过：0 幅"), run.stdout)

    def test_figure_not_drawn_by_pele_fails_instead_of_counting_zero(self):
        run, _ = self.probe(self.write(figure("Other", 400).replace("pele pele-flowchart", "ondine ondine-flowchart")))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("认不出", next(l for l in run.stdout.splitlines() if "Other" in l))

    @unittest.skipUnless(shutil.which("node"), "构建 Mermaid 要 node")
    def test_built_specimen_passes(self):
        page = self.tmp / "specimen.html"
        shutil.copy(SKILL / "assets" / "specimen.html", page)
        subprocess.run([sys.executable, str(SKILL / "scripts" / "build.py"), str(page)],
                       check=True, capture_output=True, timeout=120)
        run, _ = self.probe(page)
        self.assertEqual(run.returncode, 0, run.stdout)
        compiled = page.read_text(encoding="utf-8").count('class="pele pele-')
        self.assertGreater(compiled, 0)
        self.assertEqual(int(re.search(r"(\d+) 幅 Mermaid 图", run.stdout).group(1)), compiled, run.stdout)


if __name__ == "__main__":
    unittest.main()
