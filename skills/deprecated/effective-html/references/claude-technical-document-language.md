# Claude technical-document language

Use this overlay only for the twelve technical-document selections listed below. It translates the
bundled Claude marketing design source into an operational language for technical documents; it is
not permission to reproduce marketing navigation, pricing, calls to action, footer chrome, logos, or
licensed fonts.

## Source and authority

- Provenance asset: [`../assets/claude.design.md`](../assets/claude.design.md)
- Pinned SHA-256: `4d4e2a6dede73cfca7cf6c02009bf14480eeb131b47db4691e3eb751dbb5b981`
- The asset is an unchanged source record. Do not load it during ordinary generation.
- This reference is the generation-time contract. It keeps the source's visual principles while
  discarding marketing-only components.

Authority resolves in this order:

1. The reader job, factual hierarchy, and supplied material.
2. An explicit user request for another design language.
3. The document-family grammar in this reference.
4. The shared visual invariants in this reference.
5. The base rules in `design-system.md`.

If a lower rule conflicts with a higher rule, follow the higher rule. Never invent a metric, surface,
interaction, or section merely to satisfy the visual language.

## Activation and metadata

Every active output keeps these markers in `<head>` after synthesis:

| Template                              | Reading job                 | Required metadata                                                                                                                    |
| ------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `01-exploration-code-approaches.html` | Compare approaches          | `<meta name="effective-html-family" content="approach-comparison">`                                                                  |
| `02-exploration-visual-designs.html`  | Compare visual directions   | `<meta name="effective-html-family" content="visual-directions">`                                                                    |
| `03-code-review-pr.html`              | Review a code change        | `<meta name="effective-html-family" content="code-review">`                                                                          |
| `04-code-understanding.html`          | Trace a codebase flow       | `<meta name="effective-html-family" content="code-understanding">`                                                                   |
| `05-design-system.html`               | Reference a design system   | `<meta name="effective-html-family" content="design-system-reference">`                                                              |
| `06-component-variants.html`          | Evaluate component variants | `<meta name="effective-html-family" content="component-variants">`                                                                   |
| `11-status-report.html`               | Assess delivery status      | `<meta name="effective-html-family" content="status-report">`                                                                        |
| `12-incident-report.html`             | Reconstruct an incident     | `<meta name="effective-html-family" content="incident-report">`                                                                      |
| `14-research-feature-explainer.html`  | Understand a feature or API | `<meta name="effective-html-family" content="technical-explainer">` and `<meta name="effective-html-variant" content="feature-api">` |
| `15-research-concept-explainer.html`  | Understand a concept        | `<meta name="effective-html-family" content="technical-explainer">` and `<meta name="effective-html-variant" content="concept">`     |
| `16-implementation-plan.html`         | Evaluate a plan             | `<meta name="effective-html-family" content="implementation-plan">`                                                                  |
| `17-pr-writeup.html`                  | Present a change for review | `<meta name="effective-html-family" content="pr-writeup">`                                                                           |

Do not add these markers to other templates. The marker is an activation seam for instructions,
tests, and advisory checks; it is not visible branding.

## Shared operational core

### Canonical roles

Use these role names in active templates. Compatibility aliases may point old template variables at
the new roles while migrating.

```css
:root {
  --canvas: #faf9f5;
  --surface-soft: #f5f0e8;
  --surface-card: #efe9de;
  --surface-dark: #181715;
  --surface-dark-elevated: #252320;
  --ink: #141413;
  --body: #3d3d3a;
  --muted: #6c6a64;
  --hairline: #e6dfd8;
  --coral: #cc785c;
  --coral-active: #a9583e;
  --on-dark: #faf9f5;
  --on-dark-soft: #a09d96;
  --success: #5db872;
  --warning: #d4a017;
  --error: #c64545;
  --serif: ui-serif, Georgia, "Times New Roman", serif;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --section-space: clamp(64px, 8vw, 96px);
  --card-pad: 32px;
}
```

The page floor is cream, not pure white. Cream cards and dark technical surfaces create pacing.
Coral is the sole brand accent and must remain scarce: one decisive accent moment per view region is
usually enough. Semantic green, amber, and red communicate state only.

### Editorial typography

- Use the system font stacks above; load no remote or embedded brand font.
- Display headings use the serif stack at weight 400 with negative tracking. Prefer scale and
  whitespace over bold weight.
- Body copy uses the sans stack at weight 400; labels may use 500.
- Code, measurements, status, and compact metadata use the mono stack.
- Keep readable measures narrow enough for technical prose. A wide stage can interrupt the measure
  for comparison, code, diagrams, or an interactive model.

### Surface rhythm

- Let the canvas carry most prose without wrapping every section in a card.
- Use `--surface-card` for grouped editorial evidence, not as a default container around everything.
- A dark technical stage must contain decision-relevant material: real code, an execution path,
  a comparison matrix, a working explanatory model, or a dependency view.
- Omit the dark technical stage when the material does not benefit from it.
- Use coral for the recommendation, active state, key transition, or one short callout—not for every
  heading, border, badge, and icon.
- Coral text on `--surface-card` measures 2.71:1 and fails the visual gate. On any card, soft, or
  dark surface use `--coral-active` (4.19:1 on card) instead; `--coral` is for text on `--canvas`
  only. This applies to kickers, eyebrows, labels, metrics, and icons alike.
- Major bands use the section rhythm; cards normally use 32px desktop padding and 20–24px on mobile.

### Shape and depth

- Use 8px for controls, 12px for ordinary cards, and 16px only for a dominant stage.
- Prefer color-block contrast and hairlines over shadows.
- A faint neutral shadow is acceptable for a raised interaction or dominant recommendation. Avoid
  repeated floating cards, colored shadows, gradients, and glass effects.
- Avoid decorative icon circles, stock-illustration heroes, and uniform card grids that erase
  information hierarchy.

### Responsive and accessible behavior

- Preserve a coherent reading order when columns collapse.
- Test near 1280px and 390px; use an explicit responsive treatment when a desktop layout has multiple
  columns, sticky chrome, tables, diagrams, or code.
- Keep controls native, keyboard reachable, visibly focused, and large enough to operate by touch.
- Let code scroll horizontally rather than becoming unreadable through forced wrapping.
- Respect `prefers-reduced-motion` when an interaction animates.

## Document-family grammars

The families share visual DNA, not an interchangeable page shell. Their content order, density, and
signature surface must remain visibly different.

### Approach comparison

Reader job: make a decision.

1. State the decision and constraints.
2. Establish common ground before differences.
3. Put like-for-like evidence into a comparison stage; a dark stage is appropriate when it improves
   judgment.
4. Separate trade-offs from the recommendation.
5. Make one recommendation visually dominant and explain the conditions that would change it.

Do not use three equal feature cards when the options are not equally viable. The comparison should
read horizontally where useful and conclude decisively.

### Visual directions

Reader job: compare visual approaches and choose a direction.

1. Start with the design question, product context, and criteria shared by every direction.
2. Render each direction at a comparable scale before explaining it.
3. Attach rationale, strengths, risks, and suitable contexts to the rendered evidence.
4. Preserve useful environmental controls such as light/dark surfaces when they expose real
   differences.
5. Close with selection guidance or a recommendation and name what would change it.

The signature is decision brief → shared criteria → direction stage → trade-offs → selection
guidance. Artboards may repeat for like-for-like comparison, but their surrounding evidence must not
become four interchangeable decorative cards.

### Design-system reference

Reader job: find the rule or primitive needed to build consistently.

1. Orient the reader with the system's principles, source, scope, and authority.
2. Present foundations as named roles and usage rules, not an unprioritized swatch dump.
3. Keep tokens, typography, spacing, shape, and state semantics easy to scan and copy.
4. Show core components only where they demonstrate how foundations compose.
5. Close with constraints, accessibility expectations, and common misuse.

The signature is system principles → foundation reference → composition examples → usage guardrails.
Dense reference material may use a dark token stage, but the page remains an indexed reference rather
than a marketing gallery.

### Component variants

Reader job: understand which component treatment fits a context and inspect its implementation
contract.

1. State the variant decision and the attributes under evaluation.
2. Put working controls beside the live evidence they affect.
3. Compare variants using the same content and state so treatment is the only moving variable.
4. Make one selected variant, its fit, and its trade-offs inspectable without relying on hover.
5. Keep generated code or props synchronized with every control and selected variant.

The signature is variant question → live variant lab → contextual fit → implementation contract.
The laboratory is the dominant interactive stage; a static card matrix with decorative knobs is not
enough.

### Technical explainer — feature/API variant

Reader job: understand behavior well enough to operate or integrate it.

1. Lead with the behavior and who it affects.
2. Show the request or execution path.
3. Present configuration and examples next to the stage they control.
4. Distinguish breaking behavior, additive behavior, defaults, and operational gotchas.
5. End with a compact operational reference or next action.

The signature surface is a dark, product-like technical stage carrying real code, terminal output, or
an execution path. If the material has none, keep the explanation on cream surfaces rather than
inventing product chrome.

### Technical explainer — concept variant

Reader job: build a correct mental model.

1. Name the concept and the intuition.
2. Explain the mechanism in causal order.
3. Use a worked example or interactive laboratory to make the mechanism observable.
4. Compare the concept with the nearest alternative only after the model is established.
5. Close with boundaries, failure modes, or a glossary when the material supports them.

The signature surface is the worked laboratory. It may be a dark technical stage when that contrast
helps the reader focus on changing state; the interaction must teach, not decorate.

### Implementation plan

Reader job: judge feasibility and sequence.

1. Lead with objective, constraints, and completion evidence.
2. Show ordered work and dependencies before implementation detail.
3. Keep risks adjacent to the units or decisions they threaten.
4. Use diagrams and tables for dependency or impact relationships, not for ornamental density.
5. End with verification and unresolved decisions, never fabricated estimates.

The signature is an execution spine: objective → sequence → dependencies → risks → verification.
Avoid turning the plan into a comparison grid or a dashboard of equal stat cards.

### Code review

Reader job: reach and act on a reviewer-owned verdict.

1. Lead with the review position and the conditions that block approval.
2. Map risk before asking the reader to inspect files.
3. Attach every finding to concrete line-level or file-level evidence.
4. Separate blocking findings, optional improvements, and already-safe areas.
5. Close with the smallest reviewer-owned action list that changes the verdict.

The signature is verdict → risk topology → finding evidence → next action. Code and diffs may form
the dark technical stage. The review must not read like the author's explanation of why the change
exists.

### Code understanding

Reader job: build a navigable mental trace of a subsystem.

1. Orient the reader with the subsystem's purpose and trust or state boundary.
2. Show the execution path before expanding individual implementation stages.
3. Explain stages in causal order and attach code to the stage it proves.
4. Distinguish control flow, data ownership, and side effects.
5. Close with boundaries, failure modes, and safe change points.

The signature is orientation → execution trace → code-backed stages → boundaries. A dark execution
stage is appropriate when it makes the causal path easier to follow; do not scatter the path across
equal feature cards.

### Status report

Reader job: assess delivery position and decide what needs attention next.

1. Lead with the period's position, not a grid of isolated metrics.
2. Name material movement since the prior state.
3. Present shipped work and metrics only where they support that movement.
4. Surface risks, decisions, and ownership before secondary detail.
5. Close with accountable carryover.

The signature is delivery position → material movement → evidence → risks and decisions → carryover.
Numbers remain mono evidence, not decorative scorecards; unsupported metrics disappear.

### Incident report

Reader job: reconstruct what happened, why it happened, and what prevents recurrence.

1. Lead with severity, present state, and the bounded impact.
2. Reconstruct chronology from detection through mitigation.
3. Connect timeline evidence to the causal chain rather than treating it as a log.
4. Separate root cause, contributing conditions, and impact.
5. Close with owned prevention work and its verification state.

The signature is incident state → chronology → causal chain → impact → prevention work. Semantic
state colors carry severity; coral remains an editorial accent rather than a danger color.

### PR write-up

Reader job: understand the author's case and focus the review.

1. Lead with intent and the user or system behavior that changes.
2. Establish the before/after delta before touring files.
3. Guide the reader through files in dependency or behavior order.
4. Name review focus and unresolved uncertainty explicitly.
5. Close with test evidence and rollout conditions.

The signature is author intent → behavior delta → change tour → review focus → test and rollout
evidence. It shares change-document vocabulary with code review, but never claims a reviewer verdict.

## Synthesis check

Before writing an active-family artifact:

1. Identify the reader job and choose the matching grammar.
2. Inventory the material; delete unsupported slots.
3. Keep the family marker and optional variant marker.
4. Apply the canonical roles and editorial hierarchy.
5. Choose at most one dominant technical stage, only when content earns it.
6. Check that headings alone express the document's argument.
7. Run the normal hard checker, inspect family-scoped warnings, then perform desktop and mobile visual
   review.

Warnings are prompts to inspect, not aesthetic proof. A mechanically clean artifact can still fail
visual review, and a material-driven deviation can be accepted when it serves the reader better.
