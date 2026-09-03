# Interaction patterns

Index of working vanilla-JS patterns and which bundled template implements each. When a page needs one of these, read the implementing template and lift its code — it is tested, dependency-free, and styled to the design system. Don't reinvent.

All patterns share three ground rules: vanilla JS only (no framework, no CDN), keyboard reachable, and state lives in the DOM or plain objects (no store abstractions for a single page).

| Pattern                            | Template                                                                                                     | Essence & gotchas                                                                                                                                                                                                                                       |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Keyboard-navigable deck**        | `09-slide-deck.html`                                                                                         | Full-viewport sections; `keydown` on ArrowLeft/Right/Space drives `scrollIntoView`; IntersectionObserver keeps the counter in sync when the user scrolls manually. Gotcha: guard against focus being inside an input.                                   |
| **Collapsible blocks**             | `03`, `04`, `17`                                                                                             | Native `<details>/<summary>` — free keyboard/a11y. Rotate a chevron with `details[open] summary::after`. `17` shows rich card-style summaries (filename + stats + diff inside).                                                                         |
| **Single-open accordion**          | `12-incident-report.html`                                                                                    | Listen for the `toggle` event; on open, close the others. Use when open sections are tall (code, diffs) and two open at once would disorient.                                                                                                           |
| **Drag & drop with indicator**     | `08` (list reorder), `18` (kanban across columns)                                                            | Native `dragstart/dragover/drop`, ~40 lines. The drop _indicator line_ positioned from the mouse-nearest row edge is what makes it feel polished — `08` has the cleanest version. Gotcha: `e.preventDefault()` in `dragover` or drop never fires.       |
| **Live preview / knobs**           | `06` (sliders+radios → component + code snippet), `19` (toggles → JSON diff), `20` (text → rendered preview) | One `render()` reads all inputs and rewrites the output; every input's `input`/`change` event calls it. No diffing needed at this scale.                                                                                                                |
| **contenteditable editor**         | `20-editor-prompt-tuner.html`                                                                                | Plain-text extraction via TreeWalker (handles `<br>`/`<div>` line breaks); re-highlights slots like `{{name}}` on input. Gotcha: never `innerHTML`-rewrite the node the user is typing in without cursor bookkeeping — `20` shows the working approach. |
| **Light/dark stage toggle**        | `02-exploration-visual-designs.html`                                                                         | Scoped CSS variables: `.stage.dark { --fg: …; --line: …; }` and components only reference the scoped vars. One classList.toggle flips a whole region. Good for "show this in both modes" comparisons.                                                   |
| **Parameterized motion**           | `07-prototype-animation.html`                                                                                | Animation curve/duration as CSS custom properties; buttons call `style.setProperty('--ease', …)`. Lets the viewer _feel_ alternatives instead of reading their names.                                                                                   |
| **Clickable SVG diagram**          | `13-flowchart-diagram.html`                                                                                  | SVG nodes carry `data-id`; one click listener on the SVG maps id → detail object → fills the side panel; `.active` class moves the highlight. Scales to any node count with no per-node JS.                                                             |
| **Dependency guardrails in forms** | `19-editor-feature-flags.html`                                                                               | On every change, validate the whole state object (e.g. flag enabled but its `requires` flag is off) and render warnings inline. Validation lives in one function next to `render()`.                                                                    |
| **Copy/export to clipboard**       | `17`, `18`, `19`                                                                                             | Build markdown/JSON from current state, `navigator.clipboard.writeText`, flash the button label ("Copied ✓", revert after ~1.2s). Makes a static page a _source_ other tools can consume — cheap and disproportionately useful for boards and editors.  |
| **Sticky TOC with scroll sync**    | `03`, `12`, `17`                                                                                             | Sticky sidebar of anchor links; sections carry `scroll-margin-top`. Optional IntersectionObserver to highlight the current section.                                                                                                                     |
| **Tabs / segmented switch**        | `14-research-feature-explainer.html`                                                                         | Radio-group semantics: buttons toggle `aria-selected` + panel visibility. Keep panels in the DOM (display toggle) so anchors and find-in-page still work.                                                                                               |

## Widget index (cross-template lookup)

When composing a page from one template but needing a part that lives in another, use this table to find working markup+CSS to lift. Numbers are template file prefixes in `assets/templates/`.

| Widget                                       | Lives in               | Note                                              |
| -------------------------------------------- | ---------------------- | ------------------------------------------------- |
| Stat / metric tiles                          | `11`                   | big number + eyebrow label + delta                |
| Bar chart (pure CSS/SVG)                     | `11`                   | category comparison                               |
| Vertical timeline                            | `12`                   | incident chronology; adapts to any dated sequence |
| Milestone / phase rows                       | `16`                   | plan stages with status                           |
| Comparison table (multi-option)              | `01`, `16`             | column-per-option with verdict row                |
| Code block w/ hand-rolled highlighting       | `01`, `03`, `04`, `14` | `<span>` classes, no highlighter dependency       |
| Diff view (+/− lines)                        | `03`, `17`             | olive/rust tinted rows, mono                      |
| Expandable file card (name + stats + diff)   | `03`, `17`             | `<details>` with rich summary                     |
| Rollout / progress indicator                 | `17`                   | staged percentage row                             |
| Kanban column + card                         | `18`                   | with point estimates and tag chips                |
| Toggle switch                                | `19`                   | accessible checkbox-based                         |
| Tag/pill filter row                          | `18`                   | click-to-filter cards                             |
| Sliders with value readout                   | `06`, `15`             | label + range + live output                       |
| Radio segmented control                      | `06`, `14`             | variant/tab switching                             |
| Clickable SVG flowchart nodes                | `13`                   | data-id → detail panel                            |
| Hand-drawn-style SVG illustrations           | `10`                   | queue / retry / fan-out; downloadable             |
| Architecture / sequence SVG                  | `04`, `16`             | layered boxes with mono labels                    |
| Slide frame + deck progress bar              | `09`                   | full-viewport sections                            |
| Callout / warning block                      | `12`, `14`, `19`       | clay left-border emphasis                         |
| Sticky TOC sidebar                           | `03`, `12`, `17`       | anchor list + scroll-margin                       |
| Recommended-card treatment                   | `01`                   | border + badge, not background change             |
| Live preview pane                            | `06`, `20`             | input → render() → output                         |
| JSON / config diff preview                   | `19`                   | current vs pending state                          |
| Completion micro-animation (check, confetti) | `07`                   | CSS-only, parameterized easing                    |
| Drop-position indicator line                 | `08`                   | the polish that makes drag feel right             |
| Empty-state designs (4 styles)               | `02`                   | also shows light/dark variants                    |

If a needed widget isn't here or in the chosen template, build it from `design-system.md` idioms rather than importing a library — and consider whether a simpler existing widget already does the job.

## Persistence (optional add-on)

No template persists state, by design — they're snapshots. If the user asks for a board/editor that _remembers_ (a real working tool), add localStorage: serialize the same state object `render()` uses, load-or-default on startup, save on every mutation, and include a visible "Reset" affordance. Mention the page now stores data locally.

## When to add interactivity at all

Interactivity must serve the reader's job, not demonstrate effort. A status report with tabs hiding half the status is worse than a scrollable one. The test: _does the interaction let the reader do their job faster or understand something prose can't convey?_ If it only adds novelty, leave the page static — restraint reads as quality.
