from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "4d4e2a6dede73cfca7cf6c02009bf14480eeb131b47db4691e3eb751dbb5b981"
TARGET_TEMPLATES = {
    "01-exploration-code-approaches.html",
    "02-exploration-visual-designs.html",
    "03-code-review-pr.html",
    "04-code-understanding.html",
    "05-design-system.html",
    "06-component-variants.html",
    "11-status-report.html",
    "12-incident-report.html",
    "14-research-feature-explainer.html",
    "15-research-concept-explainer.html",
    "16-implementation-plan.html",
    "17-pr-writeup.html",
}
NON_TARGET_TEMPLATE_HASHES = {
    "07-prototype-animation.html": "3d585d8c6a8eb565e0a4241d2065461c44ba22bf84bfdc1e4ac48ab9a7f0c16d",
    "08-prototype-interaction.html": "aba8e9b2cc60898bea2f2df963171401c3f07743809039785066f9526db7b709",
    "09-slide-deck.html": "e191d49c28569e5f2ae09ed3bc4dc3f8ef25f90f1c842b1458f7b43ef5153291",
    "10-svg-illustrations.html": "1380bb696b5c983f4f605b13819a5de9f8d93a9fe982c6e9e9e707c26e490bb6",
    "13-flowchart-diagram.html": "1bd5e80e3363c77b262867a4b03ec39cbc2ce82af88650de5e238407680ff4cf",
    "18-editor-triage-board.html": "a2a4ba2691c2532dbe67da5bbeb183bbdee5e9027c7006fba6dce18de7347988",
    "19-editor-feature-flags.html": "8fd1aa16175614bea196672cd8f9b119b4ddb5b4768bf0bcb4bb05d6588787ab",
    "20-editor-prompt-tuner.html": "b2e1e46643bb908cb01e73600f40a5506a175869a65ad446992f22eacd0b0877",
}
TARGET_METADATA = {
    "01-exploration-code-approaches.html": (
        '<meta name="effective-html-family" content="approach-comparison">',
    ),
    "02-exploration-visual-designs.html": (
        '<meta name="effective-html-family" content="visual-directions">',
    ),
    "03-code-review-pr.html": (
        '<meta name="effective-html-family" content="code-review">',
    ),
    "04-code-understanding.html": (
        '<meta name="effective-html-family" content="code-understanding">',
    ),
    "05-design-system.html": (
        '<meta name="effective-html-family" content="design-system-reference">',
    ),
    "06-component-variants.html": (
        '<meta name="effective-html-family" content="component-variants">',
    ),
    "11-status-report.html": (
        '<meta name="effective-html-family" content="status-report">',
    ),
    "12-incident-report.html": (
        '<meta name="effective-html-family" content="incident-report">',
    ),
    "14-research-feature-explainer.html": (
        '<meta name="effective-html-family" content="technical-explainer">',
        '<meta name="effective-html-variant" content="feature-api">',
    ),
    "15-research-concept-explainer.html": (
        '<meta name="effective-html-family" content="technical-explainer">',
        '<meta name="effective-html-variant" content="concept">',
    ),
    "16-implementation-plan.html": (
        '<meta name="effective-html-family" content="implementation-plan">',
    ),
    "17-pr-writeup.html": (
        '<meta name="effective-html-family" content="pr-writeup">',
    ),
}
FAMILY_SIGNATURES = {
    "01-exploration-code-approaches.html": (
        "common-ground",
        "decision-stage",
        "recommendation",
    ),
    "02-exploration-visual-designs.html": (
        "decision-brief",
        "direction-stage",
        "selection-guidance",
    ),
    "03-code-review-pr.html": (
        "review-position",
        "risk-topology",
        "finding-evidence",
    ),
    "04-code-understanding.html": (
        "system-orientation",
        "execution-trace",
        "trust-boundary",
    ),
    "05-design-system.html": (
        "system-principles",
        "foundation-reference",
        "usage-guardrails",
    ),
    "06-component-variants.html": (
        "variant-question",
        "live-variant-lab",
        "implementation-contract",
    ),
    "11-status-report.html": (
        "delivery-position",
        "material-movement",
        "accountable-carryover",
    ),
    "12-incident-report.html": (
        "incident-state",
        "causal-chain",
        "prevention-work",
    ),
    "14-research-feature-explainer.html": (
        "behavior-summary",
        "execution-stage",
        "Configuration",
        "Gotchas",
    ),
    "15-research-concept-explainer.html": (
        "mechanism",
        "lab-stage",
        "worked-comparison",
    ),
    "16-implementation-plan.html": (
        "execution-spine",
        "dependency-stage",
        "Risks",
        "Verification",
    ),
    "17-pr-writeup.html": (
        "author-intent",
        "change-tour",
        "review-focus",
    ),
}


class ClaudeDocumentLanguageContractTests(unittest.TestCase):
    def test_bundled_source_matches_planning_hash(self) -> None:
        source = SKILL_ROOT / "assets" / "claude.design.md"

        self.assertTrue(source.is_file())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), SOURCE_SHA256)

    def test_operational_reference_traces_source_without_external_path(self) -> None:
        reference = (
            SKILL_ROOT / "references" / "claude-technical-document-language.md"
        ).read_text()

        self.assertIn("../assets/claude.design.md", reference)
        self.assertIn(SOURCE_SHA256, reference)
        self.assertNotIn("/Users/", reference)
        self.assertIn("#faf9f5", reference.lower())
        self.assertIn("#cc785c", reference.lower())
        self.assertIn("#efe9de", reference.lower())
        self.assertIn("#181715", reference.lower())

    def test_skill_activates_overlay_only_for_target_templates(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        match = re.search(
            r"<!-- claude-document-language:start -->(.*?)"
            r"<!-- claude-document-language:end -->",
            skill,
            re.DOTALL,
        )

        self.assertIsNotNone(match)
        overlay_scope = match.group(1)
        normalized_scope = " ".join(overlay_scope.split())
        for template in TARGET_TEMPLATES:
            self.assertIn(template, overlay_scope)
        self.assertIn("the other 8 templates", overlay_scope)
        self.assertIn("explicitly requests another design language", normalized_scope)

    def test_reference_defines_family_and_variant_metadata(self) -> None:
        reference = (
            SKILL_ROOT / "references" / "claude-technical-document-language.md"
        ).read_text()

        expected_markers = (
            '<meta name="effective-html-family" content="approach-comparison">',
            '<meta name="effective-html-family" content="visual-directions">',
            '<meta name="effective-html-family" content="technical-explainer">',
            '<meta name="effective-html-variant" content="feature-api">',
            '<meta name="effective-html-variant" content="concept">',
            '<meta name="effective-html-family" content="implementation-plan">',
            '<meta name="effective-html-family" content="design-system-reference">',
            '<meta name="effective-html-family" content="component-variants">',
            '<meta name="effective-html-family" content="code-review">',
            '<meta name="effective-html-family" content="code-understanding">',
            '<meta name="effective-html-family" content="status-report">',
            '<meta name="effective-html-family" content="incident-report">',
            '<meta name="effective-html-family" content="pr-writeup">',
        )
        for marker in expected_markers:
            self.assertIn(marker, reference)

    def test_reference_keeps_typography_offline_and_content_first(self) -> None:
        reference = (
            SKILL_ROOT / "references" / "claude-technical-document-language.md"
        ).read_text()

        self.assertIn("system font", reference.lower())
        self.assertIn("reader job", reference.lower())
        self.assertIn("factual hierarchy", reference.lower())
        self.assertIn("marketing navigation", reference.lower())
        self.assertIn("dark technical stage", reference.lower())

    def test_non_target_templates_remain_byte_identical(self) -> None:
        template_root = SKILL_ROOT / "assets" / "templates"

        for name, expected_hash in NON_TARGET_TEMPLATE_HASHES.items():
            with self.subTest(template=name):
                actual_hash = hashlib.sha256((template_root / name).read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected_hash)

    def test_target_templates_publish_exact_family_metadata(self) -> None:
        template_root = SKILL_ROOT / "assets" / "templates"

        for name, expected_markers in TARGET_METADATA.items():
            html = (template_root / name).read_text()
            for marker in expected_markers:
                with self.subTest(template=name, marker=marker):
                    self.assertIn(marker, html)

    def test_target_templates_share_offline_tokens_and_responsive_contract(self) -> None:
        template_root = SKILL_ROOT / "assets" / "templates"
        canonical_tokens = ("#faf9f5", "#efe9de", "#181715", "#cc785c")

        for name in TARGET_TEMPLATES:
            html = (template_root / name).read_text()
            normalized = html.lower()
            with self.subTest(template=name):
                for token in canonical_tokens:
                    self.assertIn(token, normalized)
                self.assertIn("@media", normalized)
                self.assertRegex(
                    normalized,
                    r"font-family:\s*(?:-apple-system|system-ui|ui-sans-serif)",
                )
                self.assertNotRegex(
                    normalized,
                    r"(?:src|href)\s*=\s*[\"']https?://",
                )
                self.assertNotIn("acme", normalized)

    def test_each_target_exposes_its_reader_job_signature(self) -> None:
        template_root = SKILL_ROOT / "assets" / "templates"

        for name, signatures in FAMILY_SIGNATURES.items():
            html = (template_root / name).read_text()
            for signature in signatures:
                with self.subTest(template=name, signature=signature):
                    self.assertIn(signature, html)

    def test_concept_lab_keeps_node_label_in_sync_with_buttons(self) -> None:
        html = (
            SKILL_ROOT
            / "assets"
            / "templates"
            / "15-research-concept-explainer.html"
        ).read_text()

        self.assertGreaterEqual(
            len(re.findall(r"nVal\.textContent\s*=\s*nodes\.length", html)),
            2,
        )

    def test_evals_cover_all_active_family_grammars(self) -> None:
        evals = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text())["evals"]
        eval_ids = [evaluation["id"] for evaluation in evals]

        self.assertEqual(eval_ids, sorted(set(eval_ids)))
        by_id = {evaluation["id"]: evaluation for evaluation in evals}
        self.assertIn("technical-explainer", " ".join(by_id[2]["assertions"]))
        self.assertIn("approach-comparison", " ".join(by_id[3]["assertions"]))
        self.assertIn("feature-api", " ".join(by_id[4]["assertions"]))
        self.assertIn("implementation-plan", " ".join(by_id[6]["assertions"]))
        self.assertIn("不要替我补估时或画假界面", by_id[6]["prompt"])
        self.assertIn("status-report", " ".join(by_id[1]["assertions"]))
        self.assertIn("code-review", " ".join(by_id[7]["assertions"]))
        self.assertIn("code-understanding", " ".join(by_id[8]["assertions"]))
        self.assertIn("incident-report", " ".join(by_id[9]["assertions"]))
        self.assertIn("pr-writeup", " ".join(by_id[10]["assertions"]))
        self.assertIn("visual-directions", " ".join(by_id[11]["assertions"]))
        self.assertIn("design-system-reference", " ".join(by_id[12]["assertions"]))
        self.assertIn("component-variants", " ".join(by_id[13]["assertions"]))

    def test_visual_acceptance_receipt_is_complete(self) -> None:
        receipt_path = (
            SKILL_ROOT / "evals" / "claude-document-language-review.md"
        )

        self.assertTrue(receipt_path.is_file())
        receipt = receipt_path.read_text()
        self.assertIn("7984fdd65078afb5b12aabb740ff2f586d6658c7", receipt)
        self.assertIn("1280 × 900", receipt)
        self.assertIn("390 × 844", receipt)
        self.assertIn("A2 decision: accepted", receipt)
        for eval_id in (2, 3, 4, 6):
            self.assertIn(f"Eval {eval_id}", receipt)

    def test_design_expression_acceptance_receipt_is_complete(self) -> None:
        receipt_path = (
            SKILL_ROOT / "evals" / "claude-design-expression-review.md"
        )

        self.assertTrue(receipt_path.is_file())
        receipt = receipt_path.read_text()
        self.assertIn("7984fdd65078afb5b12aabb740ff2f586d6658c7", receipt)
        self.assertIn("1280 × 900", receipt)
        self.assertIn("390 × 844", receipt)
        self.assertIn("A2 decision: accepted", receipt)
        self.assertIn("02-exploration-visual-designs.html", receipt)
        self.assertIn("05-design-system.html", receipt)
        self.assertIn("06-component-variants.html", receipt)
        self.assertIn(
            "6a455ee911daa15edd11da5a8f94d13cf339ff23b7cb6aa029b9d28b9e7ec559",
            receipt,
        )
        self.assertIn(
            "a55ca79396d3504272da8e7ced0c911baca42243152dac8c79e6b6ce91a180ab",
            receipt,
        )
        self.assertIn(
            "6eb09302bd7dd3a5414be9efc166c914c0f32d1c8fecf384fe0a2f7633813acd",
            receipt,
        )

    def test_engineering_operations_visual_acceptance_receipt_is_complete(self) -> None:
        receipt_path = (
            SKILL_ROOT / "evals" / "claude-engineering-operations-review.md"
        )

        self.assertTrue(receipt_path.is_file())
        receipt = receipt_path.read_text()
        self.assertIn("7984fdd65078afb5b12aabb740ff2f586d6658c7", receipt)
        self.assertIn("1280 × 900", receipt)
        self.assertIn("390 × 844", receipt)
        self.assertIn("A2 decision: accepted", receipt)
        for eval_id in (1, 7, 8, 9, 10):
            self.assertIn(f"Eval {eval_id}", receipt)


if __name__ == "__main__":
    unittest.main()
