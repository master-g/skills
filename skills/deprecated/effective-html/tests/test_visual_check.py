from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(SKILL_ROOT))

from scripts import visual_check


def probe_result(
    viewport: int = 390,
    doc_w: int | None = None,
    overflowers: list[str] | None = None,
    squeezed: list[str] | None = None,
    contrast: list[dict] | None = None,
) -> dict:
    return {
        "viewport": viewport,
        "docW": doc_w if doc_w is not None else viewport,
        "docH": 2000,
        "overflowers": overflowers or [],
        "squeezed": squeezed or [],
        "contrast": contrast or [],
    }


class AssessTests(unittest.TestCase):
    def errors(self, result: dict) -> list[str]:
        return visual_check.assess(result, 390)[0]

    def warns(self, result: dict) -> list[str]:
        return visual_check.assess(result, 390)[1]

    def test_clean_page_has_no_findings(self) -> None:
        self.assertEqual(self.errors(probe_result()), [])
        self.assertEqual(self.warns(probe_result()), [])

    def test_horizontal_overflow_is_error(self) -> None:
        errors = self.errors(probe_result(doc_w=497, overflowers=["div=485px"]))
        self.assertEqual(len(errors), 1)
        self.assertIn("497px", errors[0])
        self.assertIn("div=485px", errors[0])

    def test_squeezed_column_is_error(self) -> None:
        errors = self.errors(probe_result(squeezed=['h3 "标题…" 56px wide x ~14 lines']))
        self.assertEqual(len(errors), 1)
        self.assertIn("squeezed", errors[0])

    def test_contrast_below_3_is_error(self) -> None:
        pair = {"ratio": 1.26, "fg": "rgb(222,215,204)", "bg": "rgb(245,240,232)",
                "count": 26, "example": 'code "mRecycled=true"'}
        errors = self.errors(probe_result(contrast=[pair]))
        self.assertEqual(len(errors), 1)
        self.assertIn("1.26:1", errors[0])

    def test_contrast_between_3_and_4_5_is_warn(self) -> None:
        pair = {"ratio": 4.18, "fg": "rgb(125,122,115)", "bg": "rgb(24,23,21)",
                "count": 20, "example": 'span.dim "// comment"'}
        self.assertEqual(self.errors(probe_result(contrast=[pair])), [])
        self.assertEqual(len(self.warns(probe_result(contrast=[pair]))), 1)


class WrapTests(unittest.TestCase):
    def test_srcdoc_escapes_quotes_and_markup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "fixture.html"
            target.write_text(
                '<!DOCTYPE html><html><body><p title="a & b">x</p></body></html>'
            )
            wrapper = visual_check.wrap(target, 390, Path(directory), with_probe=True)
            content = wrapper.read_text()
            self.assertIn('srcdoc="', content)
            self.assertNotIn('<p title="a & b">', content)  # must be escaped
            self.assertIn("&lt;p title=&quot;a &amp; b&quot;&gt;", content)

    def test_probe_is_injected_before_body_close(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "fixture.html"
            target.write_text("<!DOCTYPE html><html><body><p>x</p></body></html>")
            wrapper = visual_check.wrap(target, 390, Path(directory), with_probe=True)
            self.assertIn("visual-check-result", wrapper.read_text())


BROKEN_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><style>
  body { margin: 0; font-family: sans-serif; }
  .narrow { width: 56px; }
  .narrow h3 { font-size: 20px; line-height: 1.2; }
  .chip { background: #f5f0e8; color: #ded7cc; padding: 2px 6px; }
  .wide { width: 900px; }
</style></head><body>
  <div class="narrow"><h3>双路径固化了被否决的方案标题</h3></div>
  <p><span class="chip">mRecycled=true</span></p>
  <div class="wide">overflowing block</div>
</body></html>
"""

# Both blocks below look broken to a probe that reads raw rgba and audits
# inactive controls: the text would measure 1.62:1 against undiluted coral, and
# the disabled button 2.34:1. Composited and exempted, neither is a defect.
TRANSLUCENT_AND_DISABLED_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><style>
  body { margin: 0; background: #ffffff; font-family: sans-serif; color: #3d3d3a; }
  .wash { background: rgba(217, 119, 87, 0.06); padding: 12px; }
  .wash p { color: #a9583e; margin: 0; }
  button[disabled] { color: #87867f; background: #d1cfc5; border: 0; padding: 6px 10px; }
</style></head><body>
  <div class="wash"><p>Coral label on a six percent coral wash</p></div>
  <button disabled>Copy diff</button>
</body></html>
"""

CLEAN_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><style>
  body { margin: 0; font-family: sans-serif; color: #3d3d3a; }
  code { background: #f5f0e8; color: #3d3d3a; padding: 2px 6px; }
</style></head><body>
  <h1>A normal heading that wraps at word boundaries</h1>
  <p>Body copy with <code>inline.code()</code> on a light chip, all readable.</p>
</body></html>
"""


@unittest.skipUnless(
    visual_check.find_browser(), "no Chrome-family browser available"
)
class EndToEndTests(unittest.TestCase):
    def run_gate(self, html: str) -> tuple[bool, str]:
        browser = visual_check.find_browser()
        assert browser is not None
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "fixture.html"
            target.write_text(html)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = visual_check.check_file(browser, target, [390], None)
            return result, output.getvalue()

    def test_broken_page_reports_all_three_defect_classes(self) -> None:
        ok, output = self.run_gate(BROKEN_PAGE)
        self.assertFalse(ok)
        self.assertIn("horizontal overflow", output)
        self.assertIn("squeezed text column", output)
        self.assertIn("contrast 1.26:1", output)

    def test_clean_page_passes(self) -> None:
        ok, output = self.run_gate(CLEAN_PAGE)
        self.assertTrue(ok, output)

    def test_translucent_background_and_disabled_control_are_not_errors(self) -> None:
        ok, output = self.run_gate(TRANSLUCENT_AND_DISABLED_PAGE)
        self.assertTrue(ok, output)
        self.assertNotIn("Copy diff", output)


if __name__ == "__main__":
    unittest.main()
