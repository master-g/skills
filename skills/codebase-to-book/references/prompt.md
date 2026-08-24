# Codebase-to-Book Analysis Prompt

Use this prompt verbatim (with placeholders filled in) to drive the seven-phase analysis.
Output language defaults to Simplified Chinese (`book-zh/`); set `OUTPUT_LANG=en` to write
English (`book/`) instead.

Inputs the orchestrator must fill before invoking:

| Placeholder | Meaning | Example |
|---|---|---|
| `{{SOURCE_PATH}}` | Absolute path to the codebase being analyzed | `/Users/me/code/foo` |
| `{{OUTPUT_DIR}}` | Output directory (already scaffolded with `web/` template) | `/Users/me/code/foo-from-source` |
| `{{OUTPUT_LANG}}` | `zh` (default) or `en` | `zh` |
| `{{OUTPUT_BOOK_DIR}}` | `{{OUTPUT_DIR}}/book-zh` if `zh`, else `{{OUTPUT_DIR}}/book` | `/Users/me/code/foo-from-source/book-zh` |
| `{{PROJECT_NAME}}` | Display name for the book / siteTitle | `Foo` |

---

## The Prompt

```
Analyze the source code at {{SOURCE_PATH}} and produce a comprehensive technical
book about its architecture, patterns, and internals. Default output language:
{{OUTPUT_LANG}}. Write chapters as markdown files in {{OUTPUT_BOOK_DIR}}/.
Update {{OUTPUT_DIR}}/web/src/book.config.ts with the parts/chapters structure
and {{OUTPUT_DIR}}/web/src/i18n/ui.ts with the project's siteTitle / siteTagline /
heroDescription / disclaimer / githubUrl (replace `__PROJECT_NAME__` placeholders
with {{PROJECT_NAME}}).

The book reads like a professional technical publication — the kind a senior
engineer would buy to deeply understand a system. Not documentation. Not a
tutorial. A book that teaches how the system works, why each decision was made,
and what patterns the reader can steal for their own projects.

Two readers must be served simultaneously:
- Technical leaders who want architecture and design rationale (skip code blocks
  and Deep Dive callouts)
- Senior engineers who want implementation-level understanding (read everything,
  including Deep Dives)

When OUTPUT_LANG is `zh`, write in Simplified Chinese. Use Chinese punctuation
in prose; keep code identifiers and technical terms (struct names, trait names,
API names) in English. Keep paragraphs tight; no filler.

---

## Phase 1: Exploration

Launch parallel subagents, one per major subsystem, to read the first-party source
exhaustively. **Cap parallel agents at 4-6.** If the repo has more subsystems than
that, cluster them (e.g. merge "CLI" + "TUI" into "User Interface") rather than
spawning more agents.

**Scope — skip these paths in every agent's reading:**

- VCS + build artifacts: `.git/`, `dist/`, `build/`, `target/`, `out/`, `.astro/`, `.next/`, `.cache/`
- Dependencies + lockfiles: `node_modules/`, `vendor/`, `.venv/`, `venv/`, `__pycache__/`, `*.lock`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.lock`, `poetry.lock`, `bun.lockb`
- Secrets: `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, any file a reasonable `.gitignore` excludes
- Generated / minified: `*.min.js`, `*.map`, vendored fonts, binary blobs

If the repo has vendored SDKs the reader needs context on, summarize from their
official docs rather than reading the copy in tree.

Each agent documents:

- Architecture and module boundaries
- Key abstractions (types, interfaces, core classes)
- Data flow (how information moves through the system)
- Design patterns (what patterns are used and why)
- Integration points (how this module connects to others)
- Surprising decisions (anything non-obvious or clever)

Save raw research notes to {{OUTPUT_DIR}}/.reference/phase1-<subsystem>.md. Treat
.reference/ as gitignored scratch space — research notes only, not the final book.
Never paste `.env` contents, API keys, or other secrets into notes even if
encountered accidentally.

## Phase 2: Audience and Positioning

Before structuring the book, define:

- **Primary audience**: Who is this book for? What do they already know? What do
  they want to learn?
- **Core thesis**: What is the ONE big insight about this system? Every chapter
  must connect back to this thesis. Usually: "Here is the architectural bet
  this system makes, and here is how every subsystem serves that bet."
- **What makes it worth a book**: Why can't someone just read the source? Value
  comes from narrative, cross-cutting patterns, design rationale, and
  transferable lessons.

Save to {{OUTPUT_DIR}}/.reference/phase2-positioning.md.

## Phase 3: Structure

Organize the book as if the reader were building the system from scratch. Each
chapter solves one clear problem the next chapter depends on. The reader never
encounters a concept that requires a later chapter to understand.

- **Parts**: Group chapters into 5-7 thematic parts. Each part has a one-line
  epigraph that frames the section.
- **Chapter ordering**:
  1. Foundations (startup, state, communication with externals)
  2. Core loop (the main execution cycle)
  3. Capabilities built on the core (tools, plugins, extensions)
  4. Advanced patterns (multi-agent, orchestration, coordination)
  5. Supporting infrastructure (UI, networking, persistence)
  6. Performance and optimization
  7. Epilogue: synthesis, transferable lessons, forward look
- **Chapter sizing**: 300-800 lines each. Split if >800. Merge if <200.

Present the full outline (part names, chapter titles, 2-3 bullets per chapter)
and write it into {{OUTPUT_DIR}}/web/src/book.config.ts:
- Each chapter slug: `chNN-kebab-title` (zero-padded). The markdown file in
  {{OUTPUT_BOOK_DIR}}/ MUST match: `chNN-kebab-title.md`.
- Fill `title`/`titleZh` and `description`/`descriptionZh` for every chapter.
  When OUTPUT_LANG is `zh`, write rich Chinese in `*Zh` fields and concise
  English fallbacks in the non-Zh fields. When OUTPUT_LANG is `en`, write
  English first; `*Zh` fields can mirror the English string.
- Fill `parts` similarly with `title`/`titleZh` and `epigraph`/`epigraphZh`.

Also update {{OUTPUT_DIR}}/web/src/i18n/ui.ts: replace the `__PROJECT_NAME__`
markers in `siteTitle` (en + zh) with {{PROJECT_NAME}}, and rewrite
`siteTagline` / `heroDescription` / `disclaimer` to fit this codebase.

Get user approval on the outline before writing chapters.

## Phase 4: Writing

Write each chapter FROM SCRATCH using the Phase 1 analysis as research notes.
Do not restructure the analysis — rewrite as narrative prose. Save each chapter
to {{OUTPUT_BOOK_DIR}}/chNN-slug.md with the slug from book.config.ts.

### Chapter Template

1. **Opening** (2-3 paragraphs)
   - What problem does this layer/subsystem solve?
   - Why does it exist? What would break without it?
   - Explicit backward reference to the previous chapter
   - What the reader will understand by the end

2. **Body**
   - Prose for narrative and rationale (the "why")
   - Mermaid diagrams for architecture, data flow, state machines
   - Pseudocode for key patterns (rules below)
   - Tables for reference material

3. **Deep Dive sections** (optional, inline)
   - Callouts for implementation detail leaders can skip
   - Readable independently without losing the chapter narrative

4. **Apply This** (closing)
   - Exactly 5 transferable patterns
   - Each pattern: name → problem it solves → how to adapt it → pitfall to watch
   - Concrete enough to act on, abstract enough to transfer

### Voice

- Expert peer doing a deep technical review
- Direct, opinionated. "This is clever because…" / "This is the wrong
  abstraction for…" / "The reason this exists is…"
- Every sentence teaches something
- Show what was NOT built and why — the road not taken is often more instructive
- For Chinese output: keep prose in 简体中文, technical terms in English

### Code blocks

- Pseudocode only. NEVER reproduce verbatim source.
- 3-5 blocks per chapter max. Each 5-15 lines.
- Different variable names from the source.
- Label as illustrative: `// Pseudocode — illustrates the pattern` /
  `// 伪代码 — 展示模式`.
- One sentence before the block (what it shows). One paragraph after (why).

### Diagrams

- Mermaid only — `` ```mermaid ``-fenced blocks. The web template renders them.
- Diagram types: `graph TD`/`graph LR` (architecture), `sequenceDiagram`
  (request/response), `stateDiagram-v2` (state machines), `flowchart TD`
  (decision trees), `gantt` (timelines).
- 2-4 diagrams per chapter; more for the core loop and tool subsystems.
- **Never hardcode colors** in `style X fill:#XXX` or `classDef ... fill:#XXX`
  directives. They override the Mermaid theme and produce unreadable diagrams
  in dark mode (light fills + light text = near-zero contrast). Let the theme
  control colors — the template's `mermaid-init.ts` switches `default`/`dark`
  automatically based on the `html.dark` class. When a diagram needs semantic
  grouping (e.g. "pure vs textual", "durable vs pointer"), use `subgraph`
  blocks instead of colors — subgraphs render readably in both themes. Prose
  should reference subgraph names, not color names ("the `Durable` group", not
  "the green nodes").

### Cross-references

- Every chapter starts with an explicit backward reference to the previous one
- Forward references when a concept will be expanded later
- One canonical home per concept — other chapters reference, not re-explain

## Phase 5: Editorial Review

Launch 2-3 review subagents, each covering a section. Each evaluates:

1. Opening quality: hooks? connects to previous chapter?
2. Flow: sections that drag, repeat, or list facts without building insight
3. Content cuts: reference-manual content that doesn't serve the narrative;
   code blocks that are too long
4. Missing content: gaps where the reader would be confused
5. Diagrams needed: places where a diagram would replace a wall of text
6. Cross-chapter consistency: voice, formatting, terminology, contradictions
7. Specific fixes: 5-10 sentences/paragraphs to rewrite, with reasons

Compile all review feedback into a single prioritized action plan.

## Phase 6: Revision

Apply review feedback in one pass:
- Structural changes: split/merge chapters, fix broken refs
- Deduplication: each concept explained once, cross-referenced elsewhere
- Content cuts: remove enumeration, trim bloated sections, compress reference
  material into tables
- Content additions: worked examples, hooks, missing diagrams
- Consistency: standardize Apply This sections, fix repeated phrases, verify
  cross-references

If chapters change number/slug, update book.config.ts and rename markdown files
in lockstep.

## Phase 7: Source Code Compliance Audit

**This is a re-check, not the first line of defense.** Phase 4 already enforced
"pseudocode only, never verbatim source". Phase 7 treats every remaining code
block as suspect and sweeps for anything that slipped through:

- REPLACE any block that is verbatim or near-verbatim with pseudocode using
  different variable names
- ANNOTATE type signatures with `// Illustrative` / `// 仅作示意`
- VERIFY no proprietary prompt text, internal constants, or exact function
  implementations remain
- STRIP any secret-shaped string that leaked from Phase 1 notes (tokens,
  keys, internal URLs, customer names)
- SCAN Mermaid diagrams for hardcoded `style`/`classDef` color directives
  (`fill:#XXX`, `stroke:#XXX`). These override theme switching and produce
  unreadable diagrams in dark mode. Remove them; let the theme control colors.
  If a diagram relied on colors for semantic grouping, rewrite it with
  `subgraph` blocks and update any prose that referenced color names.

The book teaches patterns and architecture. It must not enable reconstruction
of the exact source code.
```

---

## Adaptation notes for the skill

- The web template already renders mermaid (`web/src/scripts/mermaid-init.ts`)
  and bilingual chapter pages. Phase 4 only needs to write markdown to
  `book/` and `book-zh/`.
- `book.config.ts` is the single source of truth. Pages, sidebars, and the
  index ToC all derive from it. Slug mismatches cause silent 404s.
- Empty `parts` / `chapters` arrays are valid — the index page renders a "no
  chapters yet" notice. Useful for previewing the scaffold before Phase 4
  finishes.
- For OUTPUT_LANG=zh, the analysis writes Chinese chapters under `book-zh/`.
  English (`book/`) can stay empty if the user does not want a bilingual book;
  the EN site simply renders an empty ToC. To make EN match, mirror chapters
  into `book/`. The skill default is Chinese-only.
