# Claude engineering and operations visual review

## Review record

- Date: 2026-07-24
- Baseline commit: `7984fdd65078afb5b12aabb740ff2f586d6658c7`
- Compared versions: verified pre-change fixtures and the five upgraded templates
- Viewports: desktop at 1280 × 900; mobile at 390 × 844
- A2 decision: accepted
- Decision scope: one release decision covering all five migrated grammars
- Decision capture: the visual authority selected option `1 — 五份全部接受，继续最终收尾`
- Release rule: one rejected template returns to its owning implementation unit

The comparison contact sheets place each baseline on the left and its upgrade on the right.
Rows are ordered as code review, code understanding, status report, incident report, and PR
write-up. Browser evidence was captured from separate explicit local roots for baseline and
current files.

## Baseline integrity

| Eval | Template | Baseline SHA-256 | Current SHA-256 |
|---|---|---|---|
| Eval 7 | `03-code-review-pr.html` | `f03ab7590f9962b3add85d3ae65076d66a6462b77af353eea455d315d64ac1f6` | `38dd4c8384e4cd693048bdd8ae3a4739957798c30783985024712a914015297d` |
| Eval 8 | `04-code-understanding.html` | `e4aed5fd3f203c22a6034cd488e0a302d523b6cecef737204dc4aac721aa76e4` | `52dc7b2a0e32e10d463ca9b8fc5cc19c0a89c55ea034f08bdef203f82f7cd351` |
| Eval 1 | `11-status-report.html` | `6468f720bab1d016657a9ed25c1049ec42f1810b230f486a5f3130427614bc7c` | `0e881efa7411deb383d8a053d3a11055d65ac1507521c6f737a80c5faa1bd845` |
| Eval 9 | `12-incident-report.html` | `e787d6a64eca1ccd77fd9fa18849400356895ed2717ceb26dad2638fcc3261a9` | `2eca06721e1b5d0c13446f5eb0c2110a2b253956d2cc5aac7548fed90707c617` |
| Eval 10 | `17-pr-writeup.html` | `9ad6ee2d3e7de11d6b1430a01d3ca439771c373af0145f68acbe764a038c8485` | `fc0145a58082935959c7e975d916d953cf145e88208d1c543c2485280126e2af` |

## Decision notes

### Eval 7 — code review

- The baseline begins with PR metadata and a file inventory, so the reviewer position is inferred
  only after reading line comments.
- The upgrade makes the merge verdict immediate, groups files by behavioral risk, anchors both
  blockers in dark finding-evidence stages, and closes on narrow re-review actions.
- The risk anchors and native evidence expansion work at both viewports.

### Eval 8 — code understanding

- The baseline separates a small request diagram from a long callstack and sidebar, requiring the
  reader to assemble the causal path.
- The upgrade opens with system orientation, turns the five stages into one dark execution trace,
  attaches source evidence to those stages, and gives the trust boundary its own conclusion.
- The source excerpts preserve single-open behavior; the mobile grid fix removed document-level
  overflow without hiding code content.

### Eval 1 — status report

- The baseline opens with four equal KPI cards, which gives merges, deploys, incidents, and flaky
  tests equal narrative weight.
- The upgrade states the delivery position first, uses three material movements as evidence,
  separates runtime proof from delivery proof, and makes carryover accountable.
- The mobile table becomes readable records and all supplied status evidence remains visible.

### Eval 9 — incident report

- The baseline has a clear chronology but treats current state, root cause, impact, and actions as
  successive report sections without a causal overview.
- The upgrade makes severity and resolved state immediate, preserves the observed timeline,
  exposes the four-link causal chain, and maps prevention work to owners and dates.
- Timeline, causal chain, impact evidence, and prevention rows remain in one coherent mobile order.

### Eval 10 — PR write-up

- The baseline spends its opening on prompt metadata and a generic summary before reaching why and
  file-by-file context.
- The upgrade leads with author intent and behavior delta, orders the change tour causally, and
  separates review focus, proof, and rollout responsibility.
- Native expansion works; long code remains horizontally operable inside its stage while the
  document itself has no horizontal overflow.

## Mechanical and runtime evidence

- All five templates pass `scripts/check.py` with no hard failures or advisory warnings.
- Every final page has zero document-level horizontal overflow at 1280 × 900 and 390 × 844.
- Desktop sticky navigation is active where supplied by the grammar.
- Code-review anchors update the target hash; code-review and PR-write-up `<details>` controls open.
- Code-understanding source excerpts keep exactly one item open after interaction.
- The PR write-up's mobile code stage has a 278 px viewport over 405 px of scrollable code.
- All ten final viewport captures loaded without page errors or console messages.
- Eval JSON is valid, IDs are unique and ordered, and Eval 1 plus Evals 7–10 cover all five
  engineering and operations grammars.
- The eleven non-target templates remain byte-identical to their frozen hashes.

## A2 decision

Accepted as one five-template release after direct review of the desktop and mobile comparison
sheets. The decision covers Evals 1, 7, 8, 9, and 10 and closes the human visual gate.
