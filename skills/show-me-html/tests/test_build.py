import hashlib
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
BUILD = SKILL / "scripts" / "build.py"
FIXTURES = Path(__file__).parent / "fixtures"
CSS = SKILL / "assets" / "show-me.css"

RECIPES = runpy.run_path(str(BUILD))["RECIPES"]


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

    def test_repeated_eyebrows_warn(self):
        page = self.copy_fixture()
        html = page.read_text(encoding="utf-8").replace(
            "<h1>", '<p class="eyebrow">周报</p><p class="eyebrow">状态</p><h1>', 1
        )
        page.write_text(html, encoding="utf-8")

        result = run_build(page)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("eyebrow", result.stdout + result.stderr)


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

    def test_layout_docs_define_every_visual_contract(self):
        layouts = (SKILL / "references" / "layouts.md").read_text(encoding="utf-8")
        self.assertEqual(layouts.count("**视觉契约**"), len(RECIPES))
        for recipe in RECIPES:
            with self.subTest(recipe=recipe):
                self.assertIn(f"`{recipe}`", layouts)


if __name__ == "__main__":
    unittest.main()
