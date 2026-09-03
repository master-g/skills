from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts import check  # pyright: ignore[reportMissingImports] — resolved via sys.path above


VALID_ACTIVE_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="effective-html-family" content="approach-comparison">
  <title>Decision</title>
  <style>
    :root {
      --canvas: #faf9f5;
      --surface-card: #efe9de;
      --surface-dark: #181715;
      --coral: #cc785c;
    }
    body { background: var(--canvas); }
    @media (max-width: 700px) { body { padding: 1rem; } }
  </style>
</head>
<body><main><h1>A concrete decision</h1><p>BODY_PAYLOAD</p></main></body>
</html>
"""


class CheckerContractTests(unittest.TestCase):
    def run_check(self, html: str) -> tuple[bool, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.html"
            path.write_text(html)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = check.check(path)
            return result, output.getvalue()

    def test_complete_active_family_has_no_design_warning(self) -> None:
        result, output = self.run_check(VALID_ACTIVE_PAGE.replace("BODY_PAYLOAD", "x" * 2200))

        self.assertTrue(result)
        self.assertNotIn("Claude-language drift", output)
        self.assertIn("fixture.html: OK", output)

    def test_all_extended_claude_families_are_scoped(self) -> None:
        families = (
            "visual-directions",
            "code-review",
            "code-understanding",
            "design-system-reference",
            "component-variants",
            "status-report",
            "incident-report",
            "pr-writeup",
        )

        for family in families:
            html = VALID_ACTIVE_PAGE.replace(
                'content="approach-comparison"',
                f'content="{family}"',
            ).replace("BODY_PAYLOAD", "x" * 2200)
            result, output = self.run_check(html)
            with self.subTest(family=family):
                self.assertTrue(result)
                self.assertNotIn("Claude-language drift", output)

    def test_missing_invariant_warns_without_failing(self) -> None:
        html = VALID_ACTIVE_PAGE.replace("      --coral: #cc785c;\n", "")
        result, output = self.run_check(html.replace("BODY_PAYLOAD", "x" * 2200))

        self.assertTrue(result)
        self.assertIn("Claude-language drift", output)
        self.assertIn("--coral: #cc785c", output)
        self.assertIn("OK (1 warning(s))", output)

    def test_decorative_effects_warn_without_failing(self) -> None:
        html = VALID_ACTIVE_PAGE.replace(
            "body { background: var(--canvas); }",
            "body { background: linear-gradient(#fff, #eee); backdrop-filter: blur(12px); }",
        )
        result, output = self.run_check(html.replace("BODY_PAYLOAD", "x" * 2200))

        self.assertTrue(result)
        self.assertIn("Claude-language drift", output)
        self.assertIn("gradient", output)
        self.assertIn("backdrop-filter", output)

    def test_heavy_shadow_with_unitless_zero_warns_without_failing(self) -> None:
        html = VALID_ACTIVE_PAGE.replace(
            "body { background: var(--canvas); }",
            "body { background: var(--canvas); box-shadow: 0 12px 32px rgba(0,0,0,.2); }",
        )
        result, output = self.run_check(
            html.replace("BODY_PAYLOAD", "x" * 2200)
        )

        self.assertTrue(result)
        self.assertIn("Claude-language drift", output)
        self.assertIn("heavy box-shadow", output)

    def test_unmarked_legacy_page_is_not_scoped_into_design_warnings(self) -> None:
        html = VALID_ACTIVE_PAGE.replace(
            '  <meta name="effective-html-family" content="approach-comparison">\n',
            "",
        ).replace(
            "body { background: var(--canvas); }",
            "body { background: linear-gradient(#fff, #eee); }",
        )
        result, output = self.run_check(html.replace("BODY_PAYLOAD", "x" * 2200))

        self.assertTrue(result)
        self.assertNotIn("Claude-language drift", output)

    def test_existing_hard_failures_still_fail(self) -> None:
        html = VALID_ACTIVE_PAGE.replace(
            "<body>",
            '<body><img src="https://example.com/tracker.png">',
        )
        result, output = self.run_check(
            html.replace("BODY_PAYLOAD", "Acme " + "x" * 2200)
        )

        self.assertFalse(result)
        self.assertIn("ERROR external resource load", output)
        self.assertIn('ERROR "Acme" appears', output)

    def test_raw_tex_without_katex_warns(self) -> None:
        html = VALID_ACTIVE_PAGE.replace(
            "BODY_PAYLOAD",
            "The identity \\frac{a}{b} = c and $$x^2+y^2=z^2$$ hold. " + "x" * 2200,
        )
        result, output = self.run_check(html)

        self.assertTrue(result)
        self.assertIn("raw TeX math", output)
        self.assertIn("scripts/katex.py", output)

    def test_tex_with_katex_assets_does_not_warn(self) -> None:
        rendered = (
            '<span class="katex"><span class="katex-mathml">'
            "<math><semantics><mrow><mi>a</mi></mrow></semantics></math>"
            "</span></span>"
        )
        html = VALID_ACTIVE_PAGE.replace(
            "BODY_PAYLOAD", rendered + "x" * 2200
        )
        result, output = self.run_check(html)

        self.assertTrue(result)
        self.assertNotIn("raw TeX math", output)

    def test_missing_charset_fails(self) -> None:
        html = VALID_ACTIVE_PAGE.replace('  <meta charset="utf-8">\n', "")
        result, output = self.run_check(html.replace("BODY_PAYLOAD", "x" * 2200))

        self.assertFalse(result)
        self.assertIn("missing <meta charset", output)

    def test_batch_check_continues_after_an_earlier_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.html"
            second = Path(directory) / "second.html"
            first.write_text("<html><body>broken</body></html>")
            second.write_text(
                VALID_ACTIVE_PAGE.replace("BODY_PAYLOAD", "x" * 2200)
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                result = check.main(["check.py", str(first), str(second)])

            self.assertEqual(result, 1)
            self.assertIn("first.html: ERROR", output.getvalue())
            self.assertIn("second.html: OK", output.getvalue())


if __name__ == "__main__":
    unittest.main()
