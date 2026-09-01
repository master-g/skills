# Research: `anthropics/html-effectiveness` template assessment

## Scope and provenance

- Primary source: [`anthropics/html-effectiveness`](https://github.com/anthropics/html-effectiveness)
- Audited commit: [`58c305be97f47b26b678f2c07dec01d4242268ec`](https://github.com/anthropics/html-effectiveness/tree/58c305be97f47b26b678f2c07dec01d4242268ec)
- Compared with: `docs/plans/2026-09-01-001-refactor-show-me-html-visual-system-plan.md`
- Inventory basis: repository `README.md`, `index.html`, and all 20 numbered HTML files fetched from that commit. The temporary source snapshot was removed after the audit. No secondary sources were consulted.

## Summary

The repository validates the plan’s central decision: task identity comes primarily from macrostructure and purpose-built interaction, not from switching palettes. Its strongest reusable ideas are side-by-side judgment surfaces, evidence-first spatial layouts, live specimen/control stages, timelines, selected-node detail rails, and editors that export the user’s work. It is not a production shell to copy wholesale: the examples have inconsistent accessibility, limited theme/print/reduced-motion handling, several mobile overflow risks, duplicated per-file CSS/JS, and unsafe or fragile `innerHTML` patterns.

## Complete template inventory

| File                                  | Family / reader job           | Structural fingerprint                                                                               | Interaction / reusable mechanism                                                                             |
| ------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `01-exploration-code-approaches.html` | Exploration / decision        | Three equal approach columns, each code + pro/con matrix + evidence chips; recommendation below      | CSS grid collapses to one column                                                                             |
| `02-exploration-visual-designs.html`  | Exploration / visual judgment | 2×2 live artboards with rationale under each                                                         | Sticky light/dark surface control; radio-driven class toggle                                                 |
| `03-code-review-pr.html`              | Code review                   | PR header, risk-map jump links, annotated diff ledger, collapsed low-risk files, next-step checklist | Anchors, native `details`, checkbox checklist, temporary target highlight                                    |
| `04-code-understanding.html`          | Code understanding            | Main execution path plus sticky key-files/gotchas rail; numbered call-stack spine                    | Inline SVG; mutually exclusive native `details` snippets                                                     |
| `05-design-system.html`               | Design reference              | Sequential specimen catalog: color, type, spacing, shape/elevation, components                       | Tokenized CSS; native controls; horizontally scrollable spacing ruler                                        |
| `06-component-variants.html`          | Component prototyping         | Variant matrix below a sticky control rail; hovered specimen emits JSX below                         | Range/radio/checkbox controls update root CSS variables; `data-snippet`                                      |
| `07-prototype-animation.html`         | Motion prototyping            | Dominant stage + easing rail + timing track + copy-paste CSS                                         | Class-driven state machine; easing token swapped at runtime                                                  |
| `08-prototype-interaction.html`       | Interaction prototyping       | Narrow live mock beside design-decision annotations and open questions                               | Native drag/drop with insertion indicator                                                                    |
| `09-slide-deck.html`                  | Presentation                  | Full-viewport, scroll-snapped, content-specific slides                                               | Arrow/space keys, `scrollIntoView`, `IntersectionObserver`, fixed counter                                    |
| `10-svg-illustrations.html`           | Illustration sheet            | Large figure plates with captions, export action, palette/rules appendix                             | Standalone inline SVG; serialize to Blob and download                                                        |
| `11-status-report.html`               | Status report                 | KPI band, highlights, shipped table, velocity chart, carryover block                                 | Responsive KPI grid; accessible SVG chart label                                                              |
| `12-incident-report.html`             | Incident report               | Severity metadata, dark TL;DR, chronological spine, root-cause diff, impact table, actions           | Wide-screen fixed TOC; anchors; no custom state logic                                                        |
| `13-flowchart-diagram.html`           | Diagram explainer             | Large flowchart paired with sticky selected-node detail rail and legend                              | Click nodes to update detail; keyed data object                                                              |
| `14-research-feature-explainer.html`  | Feature explainer             | Sticky file-aware nav, TL;DR, collapsible request steps, tabbed configuration, gotchas, FAQ          | Native `details`; small custom tabs                                                                          |
| `15-research-concept-explainer.html`  | Concept explainer             | Model laboratory first, comparison table, sticky glossary                                            | Deterministic hash/ring renderer, sliders, add/remove/reset, hover-linked glossary                           |
| `16-implementation-plan.html`         | Plan                          | Summary strip, milestone spine, data flow, paired mockups, key code, risks, open questions           | Mostly static; explicit responsive transformations                                                           |
| `17-pr-writeup.html`                  | Reviewer communication        | TL;DR, before/after, reading-order file tour, numbered review focus, tests, rollout                  | Native `details`; sticky TOC                                                                                 |
| `18-editor-triage-board.html`         | Direct-manipulation editor    | Four semantic lanes with counts/points and sticky export toolbar                                     | Data-driven DOM render, drag/drop, tag filter, reset, Markdown clipboard export                              |
| `19-editor-feature-flags.html`        | Config editor                 | Grouped settings list plus sticky pending-change/diff rail                                           | Native checkboxes, dependency validation, diff/full JSON export, reset, focus-visible toggle                 |
| `20-editor-prompt-tuner.html`         | Text editor                   | Editor/preview split with variable legend and three live samples                                     | Plain-text-controlled `contenteditable`, caret preservation, slot validation, live preview, clipboard export |

The gallery itself (`index.html`) groups these into nine reader-job categories and uses a consistent card index with custom inline-SVG thumbnails. `README.md` explicitly defines every example as self-contained, dependency-free HTML with no build step.

## Cross-template findings

### 1. Macrostructures

The same visual system supports sharply different compositions: judgment grids (`01`, `02`), evidence ledgers (`03`, `17`), execution spines (`04`, `12`, `16`), specimen fields (`05`, `06`, `10`), dominant live stages (`07`, `08`, `15`), viewport panels (`09`), scan-first report bands (`11`), model-plus-detail rails (`13`), and direct-manipulation workspaces (`18`–`20`). This directly supports plan R4 and the family/signature approach in U6.

A repeated useful pattern is **overview → spatial evidence → decision/action**: `01` ends with a recommendation, `03` with next steps, `13` with selected-node detail, `16` with risks/open questions, and editor templates with export. This is a stronger recipe contract than ornamental styling.

### 2. Typography and color

All templates share essentially one token vocabulary: ivory canvas (`#FAF9F5`), slate text (`#141413`), clay accent (`#D97757`), oat secondary surface (`#E3DACC`), olive success (`#788C5D`), warm grays, plus occasional rust/sky. Typography consistently assigns serif to editorial headings, sans to prose/UI, and mono to paths, metadata, code, timings, and controls. Sources: every numbered file’s `:root`, especially `05-design-system.html`.

The restraint creates coherence, but the repository demonstrates **structural variety inside one palette**, not 20 visual themes. This is strong evidence for the plan’s one owned token layer and against resurrecting `--style` packs. Do not copy exact colors or the ubiquitous serif/mono/uppercase eyebrow as the new product identity; use semantic roles and validate both themes.

### 3. Interaction patterns

The best interactions expose the artifact’s core question:

- controls mutate CSS tokens/specimens (`02`, `06`, `07`);
- native disclosure progressively reveals evidence (`03`, `04`, `14`, `17`);
- visual nodes drive a stable detail rail (`13`);
- a live model makes an abstract rule observable (`15`);
- direct manipulation ends in a portable export (`18`–`20`);
- slide navigation uses platform scrolling plus minimal JS (`09`).

Reusable implementation mechanisms include root custom properties, semantic `data-*` keys, small data objects rendered into DOM, native `details`, inline SVG, CSS state classes, `IntersectionObserver`, clipboard with `file://` fallback, Blob download, and deterministic fixture data. These fit the plan’s no-framework/single-file constraints.

### 4. Responsive and accessibility evidence

Positive evidence:

- all files declare viewport metadata and `lang="en"`;
- grids commonly collapse at 640–960px (`01`, `02`, `05`, `06`, `11`, `13`, `15`–`17`, `19`, `20`);
- long code/diagrams use `overflow-x:auto` (`03`–`07`, `10`, `12`–`17`, `19`);
- several diagrams use `role="img"`/`aria-label` or decorative `aria-hidden` (`02`, `04`, `09`, `11`);
- `19` gives its custom toggle a real checkbox, `aria-label`, and `:focus-visible` styling;
- native `details`, buttons, inputs, labels, tables, lists, headings, and anchors are used widely.

However, accessibility is uneven and must not be inferred from visual quality. Custom tabs in `14` lack tablist/tab/tabpanel roles and keyboard semantics; clickable SVG groups in `13`, the task row in `07`, and cards in `06` are not keyboard controls; drag/drop in `08` and `18` has no implemented keyboard alternative; hidden radio controls in `02`/`06` remove native focus; `15` glossary linkage is hover-only; most templates have no explicit focus treatment; none implements a general reduced-motion policy; only `02` demos a limited dark surface switch; none provides print rules. These gaps reinforce plan R2/R3/R5/R6/R8 rather than offering code to adopt directly.

### 5. Anti-AI-slop techniques worth adopting

- **Content-specific geometry:** the shape follows the reader task; equal generic cards are not the universal default.
- **Visible evidence, not decorative claims:** diffs, file paths, source ranges, state matrices, timelines, diagrams, tables, snippets, and concrete controls dominate the page.
- **Each interaction answers a real question:** easing comparison, dependency warnings, ownership movement, node detail, triage ordering, or template substitution.
- **Explicit boundaries and omissions:** `08` names omitted auto-scroll/drop animation; `16` labels mockups “not pixel-final”; `17` states what was deliberately not done; `10` publishes drawing rules.
- **A restrained shared language:** one palette, three type roles, modest radii, mostly borders instead of gratuitous shadows/gradients.
- **Reader-directed annotation:** rationale under artboards, “where to focus,” gotchas, risk maps, legends, and open questions replace generic summaries.
- **Export closes the loop:** `10`, `18`, `19`, and `20` turn interaction back into a portable artifact.

The repository’s fictional sample data is explicitly disclosed in `README.md`. In `show-me-html`, equivalent structures must still obey R7: never invent metrics, file facts, test results, or operational claims from absent source material.

## Patterns that should **not** be copied into `skills/show-me-html`

1. **Per-template duplicated CSS/JS.** The 20 files repeat tokens, reset, typography, panels, and control logic. That is appropriate for independent demos, but conflicts with the plan’s owned shared CSS and behavior contract.
2. **Exact visual branding.** Ivory/clay/oat/olive plus serif headings and mono-uppercase eyebrows appears in nearly every file. Copying it verbatim would replace one generic voice with another and violate the plan’s capped-eyebrow decision.
3. **Unsafe/fragile HTML insertion.** `13` sets trusted repository strings through `innerHTML`; `15`, `18`, `19`, and `20` also render HTML strings. These examples use fixed data/escaping in places, but the pattern must not accept generated or user-controlled HTML in the production shell.
4. **Mouse/drag-only controls.** `06` hover-to-preview, `07` clickable div, `08`/`18` drag-only reordering, `13` clickable SVG groups, and `15` hover glossary need semantic controls and keyboard equivalents.
5. **Custom controls that suppress native focus.** `02` and `06` hide radios with `display:none`; `05` replaces checkbox appearance without a visible focus rule; `20` removes the editor focus outline without a replacement.
6. **Motion without reduced-motion handling.** `02` loops decorative bobbing; `07` uses spring overshoot and confetti broadly; `09` smooth-scrolls full screens. The plan correctly limits overshoot and requires reduced-motion behavior.
7. **Incomplete theme/print model.** A limited stage-only dark toggle in `02` is not theme parity; the files provide no print system. Keep the plan’s three-state theme and dark-print regression contract.
8. **Known narrow-screen hazards.** `16` intentionally keeps an SVG at `min-width:760px`; `18` bottoms out at a two-column board; `09` uses fixed `100vh`; wide tables and sticky toolbars can still overflow/reflow poorly. Do not treat “has media queries” as responsive acceptance.
9. **Nondeterministic model behavior.** `15` uses `Math.random()`/`Date.now()` for add/remove after its deterministic initial hash. Test fixtures should use seeded/stable state.
10. **Decorative/fabricated status language.** `11` says “auto-generated” and contains metrics; `16` gives effort estimates; `17` states measured latency. These are fictional examples per `README.md`, not permission to synthesize facts in generated work artifacts.
11. **Pill proliferation and hover ornament.** Many files use uppercase pills/chips and lift/outline hover treatments. Use only when the semantics require compact status or selection.

## Specific amendments to the approved redesign plan

### Requirements

- **Amend R4:** require each recipe fingerprint to define not just geometry but an explicit reader loop: **orientation/overview → evidence or manipulation → decision/action/export** where applicable. Repository evidence: `01`, `03`, `13`, `16`, `18`–`20`.
- **Amend R5:** explicitly prohibit hover-only disclosure and non-semantic clickable containers/SVG groups, in addition to limiting motion and eyebrows. Require keyboard parity for drag/reorder recipes.
- **Amend R6:** add fixed-viewport and sticky-region checks: `100vh`, wide diagram minimum widths, multi-lane boards, sticky toolbars/rails, and long mono identifiers must be tested at 390/500px.
- **Amend R7:** add “fictional/demo labeling does not relax factual-content rules”; status metrics, estimates, file paths, and test claims require source evidence.
- **Amend R8:** require deterministic interaction state. Randomized demos must be seedable or replaced by fixed fixtures.

### Technical decisions

- Add **native-first interaction primitives** to the design decision: `details`, labeled inputs, buttons, tables, anchors, and semantic lists before custom widgets.
- Define a small reusable **selected-item → detail-rail** pattern for `flowchart`/`code-understanding`, driven by text-safe data assignment rather than arbitrary `innerHTML`.
- Define **stage/control-rail custom-property hooks** for component, animation, and visual-direction prototypes; the repository shows this can remain tiny and framework-free (`02`, `06`, `07`).
- Define an **export adapter contract** for editor recipes so triage/config/text editors serialize authoritative state without adding duplicate global export UI (`18`–`20`).
- Preserve family coherence through semantic typography roles, but do not encode repository-specific serif/mono-uppercase styling as the fingerprint itself.

### Implementation units

- **U3:** add fixed-viewport fallback rules (`100dvh`/content overflow), sticky-region collision rules, and a documented replacement focus style whenever native appearance/outline is suppressed.
- **U4:** include tabs, clickable diagrams, contenteditable, and drag/reorder in the state fixture; require keyboard behavior, focus, and non-hover access rather than appearance alone.
- **U5:** add source checks for unsafe generated-content sinks (`innerHTML` with non-static content), `display:none` on interactive inputs without an accessible replacement, and clickable non-controls lacking role/tabindex/keyboard handling. Keep checks narrow to avoid false positives.
- **U6:** extend fingerprint contracts with the concrete signatures evidenced here: comparison matrix + recommendation; diff ledger + margin comments; execution spine + gotcha rail; specimen stage + controls; selected-node detail; model laboratory; KPI band; chronological incident spine; lanes/change rail/editor-preview split.
- **U7:** add editor export acceptance for Markdown, JSON/diff, and text-template state; add manual keyboard reorder coverage for triage and interaction prototypes.

### Tests

Add focused cases to the existing proposed harness:

1. color-disabled screenshots or computed checks still distinguish all 20 structures;
2. keyboard-only operation for tabs, diagram nodes, disclosures, slide navigation, editor controls, and reorder alternatives;
3. reduced-motion for looping animation, state celebrations, and slide scrolling;
4. 390/500px checks for 4-lane boards, sticky toolbar + sidebar, `100vh` slides, wide SVGs, tables, and long paths;
5. editor export round-trips preserve ordering, booleans, unknown template slots, newlines, and clipboard fallback output;
6. deterministic fixture replay produces identical DOM/state after reset;
7. no user/generated content reaches an unsafe HTML sink;
8. dark/system/print coverage remains mandatory because the source repository does not provide it.

### Risks

- **Fingerprint imitation risk:** copying these exact surfaces/palette creates a recognizable clone rather than an owned system. Mitigate by extracting reader mechanics, not styling.
- **Accessibility debt hidden by polish:** visually convincing demos contain keyboard/focus/ARIA gaps. Mitigate with semantic fixtures and keyboard acceptance, not screenshot review alone.
- **Shared-CSS flattening risk:** centralizing all styles can erase the repository’s strongest lesson—task-specific geometry. Mitigate with mechanically checked recipe signatures.
- **Interaction scope creep:** live editors and model labs can become mini-apps. Keep interactions only when they answer the recipe’s central question and always provide export/reset.
- **Unsafe rendering risk:** repository-fixed strings make `innerHTML` appear harmless. Production inputs are different; use `textContent`, DOM construction, or tightly escaped trusted fragments.
- **Responsive false confidence:** media queries exist but do not prove 390px usability. Keep manual family-level review plus automated overflow checks.

## Sources

- [`README.md`](https://github.com/anthropics/html-effectiveness/blob/58c305be97f47b26b678f2c07dec01d4242268ec/README.md) — repository purpose, self-contained/no-dependency contract, fictional-data disclosure.
- [`index.html`](https://github.com/anthropics/html-effectiveness/blob/58c305be97f47b26b678f2c07dec01d4242268ec/index.html) — canonical count, nine-category inventory, gallery macrostructure and shared palette.
- `01-exploration-code-approaches.html` through `20-editor-prompt-tuner.html` at the audited commit — complete shipped template inventory and implementation evidence summarized above.
- Upstream `LICENSE` — MIT, copyright Anthropic PBC 2026.
- `docs/plans/2026-09-01-001-refactor-show-me-html-visual-system-plan.md` — approved plan under comparison.

## Gaps

No browser rendering, contrast calculation, keyboard execution, viewport probe, or print test was available in this read-only audit. Accessibility and responsive findings are therefore source-code findings, not claims of runtime conformance. Repository history outside the supplied commit snapshot was not examined.
