# Claude design-expression visual review

## Review record

- Date: 2026-07-24
- Baseline commit: `7984fdd65078afb5b12aabb740ff2f586d6658c7`
- Compared versions: baseline templates and upgraded design-expression templates
- Viewports: desktop at 1280 × 900; mobile at 390 × 844
- A2 decision: accepted
- Decision scope: templates 02, 05, and 06
- Decision capture: the visual authority selected option `1 — 接受本批次`

The review compared each baseline fixture with the upgraded template at the same viewport.
The visual authority accepted the batch after inspecting the desktop and mobile contact sheets.
Prompt-specific factual fidelity remains covered by eval assertions rather than inferred from
fixture screenshots.

## Accepted fixtures

### Template 02 — visual directions

- The baseline behaved like an exploration gallery: its alternatives used different content and
  offered little shared decision context.
- The upgrade establishes a decision brief and common criteria, then compares four directions with
  identical product copy, explicit fit and risk notes, and an assumption-bound recommendation.
- The light/dark control updates all four artboards. Both review widths render without
  document-level horizontal overflow.

### Template 05 — design-system reference

- The baseline was a generated token and component inventory with sample-company residue.
- The upgrade explains system principles before foundations, shows the foundations in composition,
  and closes with concrete do, avoid, and accessibility guardrails.
- The desktop reference index reaches each section. On mobile it becomes a two-row, internally
  scrollable index without creating document-level horizontal overflow.

### Template 06 — component variants

- The baseline exposed visual treatments but did not connect the chosen treatment to product
  meaning or an implementation API.
- The upgrade frames the variant question, provides a dark live laboratory, explains contextual
  fit, and emits a synchronized implementation contract.
- Variant choice, padding, border weight, and restrained elevation all update live. The controls
  remain keyboard-operable and do not issue a fake permission request.

## Hash record

| Template                             | Baseline SHA-256                                                   | Accepted SHA-256                                                   |
| ------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `02-exploration-visual-designs.html` | `feea09c9003d7d7db6726ff1548177998f2e10777cb7dc5f5953ae56b0724c64` | `6a455ee911daa15edd11da5a8f94d13cf339ff23b7cb6aa029b9d28b9e7ec559` |
| `05-design-system.html`              | `b492cc28d3663edae8050cc7f8cd2d693c6601146d5a363e84e69b0f0cdc46ca` | `a55ca79396d3504272da8e7ced0c911baca42243152dac8c79e6b6ce91a180ab` |
| `06-component-variants.html`         | `9dd462d163e3004cc136bb6fcef22135a626beea77817533037830517d4a7429` | `6eb09302bd7dd3a5414be9efc166c914c0f32d1c8fecf384fe0a2f7633813acd` |

## Mechanical evidence

- The active-family contract now covers twelve templates; eight non-target templates retain their
  recorded baseline hashes.
- Evals 11, 12, and 13 exercise the visual-directions, design-system-reference, and
  component-variants reader jobs.
- All three templates pass `scripts/check.py` without hard failures or advisory warnings.
- Embedded JavaScript passes `node --check`.
- Browser console and page-error collections are empty.
- All three templates have zero document-level horizontal overflow at 1280 × 900 and 390 × 844.
- The unit-test suite and JSON/Python syntax gates pass after receipt capture.
