---
name: effective-html
license: MIT
deprecated: true
description: 'DEPRECATED — use show-me-html instead. Previously: generate polished, self-contained static HTML pages from user intent and raw material. Six families: exploration (compare code approaches, visual design directions), code (PR review summaries, codebase walkthroughs, design systems, component variants), prototypes (animation and interaction demos), communication (slide decks, status reports, incident postmortems, implementation plans, PR write-ups), diagrams and explainers (SVG illustrations, flowcharts, concept explainers), and small editor UIs (triage boards, config editors, live-preview tuners). Use whenever the user wants to SEE something rather than read prose — 做个页面 / 可视化 / 原型 / 看板 / 复盘页 / 汇报页 / make me a page / interactive demo / compare options side by side — even when "HTML" is never said but a rendered, clickable artifact beats markdown. NOT for print/PDF documents, resumes, or landing pages (use kami), nor multi-page production websites.'
---

# effective-html (DEPRECATED)

> **历史档案，不是活动技能入口。** 本文件改名后不再作为 SKILL.md 发现。

> **⚠️ This skill is deprecated.** Use [`show-me-html`](../../show-me-html/SKILL.md) instead — it is the successor and covers the same ground (self-contained HTML pages) with a better design system. This directory is kept for reference only and will not receive updates.

One idea, one self-contained `.html` file. No build step, no dependencies, opens anywhere, lives forever.

This skill turns user intent plus raw material (notes, diffs, data, half-formed ideas) into a polished static HTML page, using the 20 templates from Anthropic's "The unreasonable effectiveness of HTML" as starting points. The pipeline: **intent → dispatch → template → synthesis → review → output**.

The core bet: for many deliverables, a rendered page beats prose. A reviewer clicks through a diff instead of scrolling a wall of text; a stakeholder sees three design directions side by side instead of imagining them; a concept lands because the reader can drag a slider and watch the model respond. Optimize for what the _reader does_ with the page, not for how much it contains.

## Step 1 · Intent extraction (silent checklist)

Before picking a template, make sure four dimensions are clear. This is background verification, not a form — never ask all four.

| Dimension         | What to extract                                             | Example                                                                                            |
| ----------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Job**           | What the reader should be able to DO after opening the page | Decide between two approaches / approve a change / track triage state / feel an interaction        |
| **Audience**      | Who opens it, and in what setting                           | Teammate doing a careful review vs. exec skimming for 30 seconds vs. audience watching a live deck |
| **Interactivity** | Read-only, or does the reader manipulate state?             | A status report is read-only; a triage board must drag; an explainer may need a slider to teach    |
| **Material**      | What content already exists vs. what is missing             | A pasted diff and notes = ready; "make a report" with no data = gaps to surface                    |

Rules:

- If the conversation already answers a dimension, skip it silently.
- If the document type implies it (a postmortem's job is always "understand what broke and prevent recurrence"), skip it.
- If 2+ dimensions are genuinely unclear AND the answer would change the deliverable, ask once, compactly (max 2 sub-questions).
- **Infer content from session context:** If the user loads this skill immediately after another skill (e.g., a deep-research or content-fetch skill such as `storm`, `research`, or `x-to-markdown`) without specifying new content, the material is almost certainly the output of the previous skill. Do not ask "what content?" — use the recently ingested/researched content as the material.
- **Output language: Simplified Chinese by default.** Page headings, labels, body prose, chart annotations, and UI copy are written in 简体中文 unless the user explicitly requests another language ("in English", "用日文写" — an explicit instruction; English source material or an English conversation does NOT count as one). Code, identifiers, technical terms, and verbatim quotes from source material stay in their original language. Set `<html lang="zh-CN">` on Chinese pages — the bundled templates all ship `lang="en"`, so this must be changed during synthesis; when another language is explicitly requested, set `lang` to match it.

## Step 2 · Dispatch

Map the intent to a template. Templates live in `assets/templates/`. First match wins; the decision tree below handles ties.

### Dispatch table

| Reader's job                                                 | Template                              | Interactivity                              |
| ------------------------------------------------------------ | ------------------------------------- | ------------------------------------------ |
| Choose between implementation approaches / tradeoff analysis | `01-exploration-code-approaches.html` | read-only                                  |
| Choose between visual/design directions                      | `02-exploration-visual-designs.html`  | light/dark toggle                          |
| Review a code change (reviewer's perspective)                | `03-code-review-pr.html`              | collapsible diffs, anchor TOC              |
| Understand how a flow/subsystem works in a codebase          | `04-code-understanding.html`          | expandable snippets                        |
| Reference a design system / style guide                      | `05-design-system.html`               | read-only                                  |
| Compare component variants with live knobs                   | `06-component-variants.html`          | sliders, radios, live snippet              |
| Feel an animation / micro-interaction                        | `07-prototype-animation.html`         | parameterized easing                       |
| Feel an interaction mechanic (drag, reorder)                 | `08-prototype-interaction.html`       | native drag & drop                         |
| Watch a presentation / talk through a narrative              | `09-slide-deck.html`                  | keyboard navigation                        |
| Grab reusable SVG illustrations                              | `10-svg-illustrations.html`           | per-SVG download                           |
| Skim project/team status                                     | `11-status-report.html`               | read-only                                  |
| Understand an incident and its follow-ups                    | `12-incident-report.html`             | TOC, checkboxes                            |
| Trace a process/pipeline node by node                        | `13-flowchart-diagram.html`           | clickable nodes → detail panel             |
| Understand a feature/API (docs-style explainer)              | `14-research-feature-explainer.html`  | tabs, expandable details                   |
| Understand a concept (interactive teaching)                  | `15-research-concept-explainer.html`  | sliders driving a live model               |
| Evaluate an implementation plan                              | `16-implementation-plan.html`         | read-only                                  |
| Present a change (author's perspective)                      | `17-pr-writeup.html`                  | expandable file cards                      |
| Triage/prioritize a list of items                            | `18-editor-triage-board.html`         | kanban drag, filters, md export            |
| Edit configuration with guardrails                           | `19-editor-feature-flags.html`        | toggles, dependency warnings, diff preview |
| Tune text/prompts with live preview                          | `20-editor-prompt-tuner.html`         | contenteditable, slot highlighting         |

### Decision tree (use before asking)

- Reader **decides between options** → code/architecture options `01`, visual options `02`
- Reader **understands a code change** → as reviewer `03`, presented by author `17`
- Reader **understands how something works** → this specific codebase `04`, a product feature `14`, a general concept `15`
- Reader **tracks work state** → snapshot in time `11`, what went wrong `12`, what we will build `16`, actively re-prioritizing `18`
- Reader **manipulates data** → cards across columns `18`, settings with constraints `19`, text with feedback `20`
- It's a **live presentation** → `09`. A deck that's really a skimmable doc → `11` or `16` instead; decks punish careful readers.

Ambiguity worth one short question: "review page or write-up?" (who drives — reviewer `03` or author `17`); "report or board?" (read-only `11` or workable `18`).

**No template fits?** That's expected — the 20 are a vocabulary, not a closed set. Compose: take the structurally nearest template for its skeleton, pull interaction patterns from `references/patterns.md`, and build new sections per `references/design-system.md`. A "compare three database schemas" page is `01`'s skeleton with `13`'s SVG idiom inside each card.

<!-- claude-document-language:start -->

### Claude technical-document overlay

Twelve template selections load `references/claude-technical-document-language.md`:

| Template                              | Family                    | Variant       |
| ------------------------------------- | ------------------------- | ------------- |
| `01-exploration-code-approaches.html` | `approach-comparison`     | —             |
| `02-exploration-visual-designs.html`  | `visual-directions`       | —             |
| `03-code-review-pr.html`              | `code-review`             | —             |
| `04-code-understanding.html`          | `code-understanding`      | —             |
| `05-design-system.html`               | `design-system-reference` | —             |
| `06-component-variants.html`          | `component-variants`      | —             |
| `11-status-report.html`               | `status-report`           | —             |
| `12-incident-report.html`             | `incident-report`         | —             |
| `14-research-feature-explainer.html`  | `technical-explainer`     | `feature-api` |
| `15-research-concept-explainer.html`  | `technical-explainer`     | `concept`     |
| `16-implementation-plan.html`         | `implementation-plan`     | —             |
| `17-pr-writeup.html`                  | `pr-writeup`              | —             |

For these selections, read the overlay before synthesis and preserve its `<meta
name="effective-html-family">` marker plus the explainer variant marker where applicable. The overlay
overrides conflicting visual or composition advice in `references/design-system.md`, while reader
job, factual hierarchy, and supplied material remain authoritative.

Do not load the overlay for the other 8 templates. If the user explicitly requests another design
language, do not silently rewrite it into Claude styling; follow the explicit request when
`effective-html` remains the desired delivery workflow.
<!-- claude-document-language:end -->

## Step 2.5 · Material pass

Inventory what exists before laying anything out:

- If the task references the current repo ("review my branch", "explain this module"), gather the material first — `git diff`, read the files — and only then dispatch. The page is only as good as the analysis behind it.
- **If the user's source is a social-media link (Twitter/X, etc.)**, the raw material may be hard to extract. Follow the fallback chain in `references/social-media-extraction.md` — try a direct read, then search for mirrors, then build from what you have. Never fabricate article content to fill a template.
- Extract every fact, number, name, and code reference from the user's material into the page. Real data only.
- Where the template expects content the material doesn't have (a metric tile with no metric, a timeline with no timestamps), do not invent it. Either cut the slot or mark it `[DATA NEEDED: what]` and tell the user. Fabricated numbers in a polished page are worse than gaps — polish makes them credible.
- The bundled templates are filled with fictional "Acme" sample data. Every trace of it must be replaced or removed. Shipping sample content in a real deliverable is this skill's most embarrassing failure mode.

## Step 3 · Layout note, then synthesis

Before writing the file, state the plan in 2-3 sentences of prose (matching the user's language): chosen template, page structure, which interactions, what's missing from the material. This is for transparency, not approval — continue immediately. If the user pushes back, adjust.

Then synthesize:

1. **Read the chosen template in full** before writing. You are learning its structure and idioms, not just copying bytes.
2. **Keep the applicable design system, replace the content.** For active Claude technical-document selections, the overlay's canonical roles and family grammar supersede conflicting template tokens or composition; for every other selection, keep the template's base system. The body content is sample data — replace all of it. Cut sections whose content doesn't exist in your material; a shorter honest page beats a fully-populated hollow one.
3. **Adapt structure freely.** Three approaches in the template but the user has two? Two cards, not two real plus one padded. Need a section the template lacks? Build it from `references/design-system.md` idioms so it looks native.
4. **For new interactions**, check `references/patterns.md` — it indexes which template implements each pattern (drag & drop, keyboard deck, live preview, clickable SVG…) so you can lift working code instead of reinventing it.
5. **Self-containment is absolute.** No CDN scripts, no web fonts, no external images, no framework. System font stacks, inline SVG, vanilla JS. An `<a href>` linking out is fine; a resource _loaded_ from the network is not. The file must render identically offline in ten years.
6. **Math uses the vendored KaTeX pipeline.** When the material contains formulas, follow `references/math-rendering.md`: KaTeX with base64-embedded fonts from `assets/katex/`, pre-rendered via `scripts/katex.py prerender` (read-only pages) or auto-rendered in the browser (interactive pages), spliced in via `scripts/katex.py inline`. Never CDN-link KaTeX/MathJax, never screenshot formulas, never leave raw TeX unrendered (`check.py` warns). Never paste the ~650 KB of vendored assets into the conversation — write the placeholders and let the script splice on disk.
7. **Every control does something.** A button that doesn't work in a prototype is acceptable only if visibly labeled as out of scope. Interactive elements need keyboard access (`<details>`, real `<button>`, focus states) — the templates show how.
8. **Restraint is the style.** One clay accent per view region, generous whitespace, 1.5px hairline borders, no gradients or glassmorphism. When in doubt, remove decoration. Read `references/design-system.md` before inventing any new visual element.

## Step 4 · Review

Two gates, both before declaring done:

**Mechanical gates** — run the bundled checkers:

```bash
python3 <skill-path>/scripts/check.py path/to/output.html
python3 <skill-path>/scripts/visual_check.py path/to/output.html
```

`check.py` verifies self-containment (no external resource loads), no leftover placeholders or template sample data, and required metadata (viewport, title, lang). `visual_check.py` renders the page in headless Chrome at 390/768/1280px and fails on the layout defects a text-level check cannot see: horizontal overflow, text squeezed to a vertical strip (a heading 2 characters wide and 14 lines tall), and text/background contrast below WCAG thresholds — including inline `code` chips whose light fill lands inside dark cards. It saves one screenshot per width and prints the directory. Fix every ERROR; judge each WARN consciously. If no Chrome-family browser is available the script exits 2 — the visual gate did NOT run; say so explicitly instead of claiming it passed.

**Visual gate** — look at the screenshots `visual_check.py` saved. Automated geometry checks don't see everything; you must still verify:

- Nothing looks cramped or collided at either width; the mobile breakpoint actually engages
- Interactions work: click the toggles, drag the cards, press the arrow keys — whatever the page promises (open the file in a real browser for this)
- The page reads top-to-bottom as an argument: headings alone should tell the story
- No AI-slop tells: padded filler prose, a paragraph restating its heading, empty symmetric sections, invented statistics

If JavaScript is non-trivial, also check the browser console for errors.

## Step 5 · Output

- Save as a descriptive kebab-case filename (`auth-refactor-review.html`, not `output.html`) in the working directory, or where the user asked.
- Report: file path, one sentence on what to look at first, and any `[DATA NEEDED]` gaps that remain.
- Offer to open it (`open file.html` on macOS) but don't force it.

## Feedback protocol

When the user gives vague visual feedback ("太挤了", "looks off", "not polished"), don't guess — ask back with current values: "Card padding is currently 20px and the grid gap 14px; loosen to 28px/20px, or is it the line-height (1.55) that feels tight?" Never say "I'll adjust the spacing" without naming the property and the new value.

When feedback is about content ("this misses the point"), go back to Step 1: it's usually the Job dimension that was wrong, not the CSS.

## When not to use this skill

- Print-destined documents — resumes, one-pagers, white papers, letters, PDF slide decks, landing pages → **kami**
- Multi-page production websites with routing, builds, or a backend
- The user explicitly wants a different design language (Material, Tailwind defaults, dark/cyberpunk) — this skill's warm ivory editorial style is deliberate and consistent
- A plain prose answer genuinely serves better (a one-line fact doesn't need a page)

## Reference files

- `references/design-system.md` — canonical tokens, typography, spacing, component idioms, color discipline. Read when composing sections that aren't in the chosen template.
- `references/claude-technical-document-language.md` — source-traceable overlay for templates 01–06, 11, 12, and 14–17. Read for those selections; do not read the bundled source during ordinary generation.
- `references/patterns.md` — interaction pattern index mapped to the template that implements each. Read when adding interactivity.
- `references/social-media-extraction.md` — recipes for pulling raw material from Twitter/X and other social platforms. Read when the user's source is a social link.
- `references/math-rendering.md` — the KaTeX + base64-font math pipeline (Mode A pre-render / Mode B auto-render). Read whenever the material contains formulas.
- `assets/claude.design.md` — unchanged provenance copy of the supplied Claude design source; audit resource, not the generation contract.
- `assets/templates/*.html` — the 20 templates. Always read the chosen one in full.
- `assets/katex/` — vendored KaTeX 0.16.11 (CSS with base64 woff2 fonts + JS, ~650 KB). Never read these files into context; splice via `scripts/katex.py`.
- `scripts/katex.py` — `bundle` vendors/refreshes the KaTeX assets, `prerender` renders `math-tex` spans at build time (needs node), `inline` splices the assets into the placeholders. Run per its own `--help` or `references/math-rendering.md`.
- `scripts/check.py` — text-level mechanical gate (self-containment, placeholders, metadata, charset, unrendered TeX). Always run on the output.
- `scripts/visual_check.py` — rendered mechanical gate (overflow, squeezed columns, contrast at 390/768/1280px; needs Chrome/Chromium). Always run after check.py; it also saves the screenshots for the visual gate.
