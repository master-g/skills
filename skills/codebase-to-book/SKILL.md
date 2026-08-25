---
name: codebase-to-book
license: MIT
description: >-
  Turn a codebase into a publication-quality technical book rendered as a
  bilingual Astro web artifact. Spawn this skill whenever the user wants to
  "analyze a repo and produce a book", "reverse-engineer a codebase into
  chapters", "write a 'from-source' book about project X", or any variant
  ("把这个仓库变成一本书", "为某个 repo 生成架构解析书"). Default output: Simplified
  Chinese (`book-zh/`). The skill scaffolds a sibling repository whose name ends
  in `-from-source`, fills it with the Astro template and `book-zh/` markdown,
  runs the seven-phase
  analyze-codebase-to-book prompt to produce chapters, then launches the dev
  server so the user can browse the result.
---

# Codebase-to-Book

Turns a source repository into a long-form technical book (architecture, patterns, internals) rendered by an Astro static site bundled with the skill. The web template is the artifact; the seven-phase prompt is the engine.

## What this skill produces

```
<source-repo>-from-source/
├── book-zh/                # Simplified Chinese chapters (default output)
├── book/                   # English chapters (optional; empty by default)
├── web/                    # Astro 5 + React 19 + Tailwind v4 site
│   ├── package.json
│   ├── astro.config.mjs
│   ├── src/
│   │   ├── book.config.ts          # Source of truth for parts/chapters
│   │   ├── content.config.ts       # Globs ../book and ../book-zh
│   │   ├── i18n/ui.ts              # siteTitle/tagline/disclaimer
│   │   ├── pages/                  # /, /<slug>, /zh/, /zh/<slug>
│   │   ├── layouts/, components/, plugins/, scripts/, styles/
│   │   └── public/
│   └── tsconfig.json
└── .reference/             # Phase-1 raw research notes (gitignore)
```

`book-zh/chNN-slug.md` filenames must match `chapters[i].slug` in `web/src/book.config.ts`. Mismatches silently break the chapter pages.

## When this skill triggers

- "Turn this codebase into a book" / "把这个 repo 写成一本书"
- "Generate a 'from-source' technical book about <repo>"
- "Analyze <path> like the Bedrock-from-Source project"
- "Reverse-engineer the architecture of <project> into chapters"
- "我想用这个 repo 生成一本架构书" / "做一本 repo 的源码解析书"

If the user only wants short documentation, a README, or a single architecture diagram, prefer a lighter approach — this skill is for full multi-chapter books.

## Workflow

### Step 1 — Confirm inputs

Required from the user (ask if missing):

| Input          | Default                                          | Notes                                                                           |
| -------------- | ------------------------------------------------ | ------------------------------------------------------------------------------- |
| `SOURCE_PATH`  | —                                                | Absolute path to the repo to analyze                                            |
| `PROJECT_NAME` | basename of `SOURCE_PATH`                        | Display name; used in siteTitle                                                 |
| `OUTPUT_LANG`  | `zh`                                             | `zh` writes to `book-zh/`; `en` writes to `book/`                               |
| `OUTPUT_DIR`   | `<parent-of-SOURCE_PATH>/<basename>-from-source` | Sibling of source repo                                                          |
| `GITHUB_URL`   | empty                                            | Optional; appears in header + footer                                            |
| `DEPLOY_URL`   | empty                                            | Optional; public origin for SEO canonical + OG tags. Leave empty for local-only |

Confirm `SOURCE_PATH` exists and that `OUTPUT_DIR` does not already contain a populated `web/` (refuse to overwrite without explicit user permission).

### Step 2 — Scaffold the output directory

Copy the bundled template into `OUTPUT_DIR`, then substitute project-specific placeholders so mid-workflow previews don't show literal markers:

```bash
mkdir -p "$OUTPUT_DIR"
cp -R "<skill-dir>/assets/web-template" "$OUTPUT_DIR/web"
mkdir -p "$OUTPUT_DIR/book" "$OUTPUT_DIR/book-zh" "$OUTPUT_DIR/.reference"

# Substitute __PROJECT_NAME__ markers in ui.ts so the preview isn't broken
# before Phase 3 rewrites them with final copy.
# BSD + GNU sed compatible: write to a temp file, then move.
UI_TS="$OUTPUT_DIR/web/src/i18n/ui.ts"
sed "s/__PROJECT_NAME__/$PROJECT_NAME/g" "$UI_TS" > "$UI_TS.tmp" && mv "$UI_TS.tmp" "$UI_TS"

# Optional: if DEPLOY_URL provided, template astro.config.mjs site field.
if [ -n "$DEPLOY_URL" ]; then
  ASTRO_CONFIG="$OUTPUT_DIR/web/astro.config.mjs"
  sed "s|https://example.com|$DEPLOY_URL|g" "$ASTRO_CONFIG" > "$ASTRO_CONFIG.tmp" && mv "$ASTRO_CONFIG.tmp" "$ASTRO_CONFIG"
fi

# .gitignore the research scratch + node_modules
cat > "$OUTPUT_DIR/.gitignore" <<'EOF'
.reference/
web/node_modules/
web/dist/
web/.astro/
EOF
```

The skill directory (`<skill-dir>`) is wherever this `SKILL.md` lives. In Claude Code that is normally `~/.claude/skills/codebase-to-book/`.

### Step 3 — Install web dependencies

Use **bun** by default:

```bash
cd "$OUTPUT_DIR/web"
bun install
```

Fallback order if `bun` is not on PATH: `pnpm install` → `npm install`. Pick the first available; do not interactively prompt.

### Step 4 — Run the seven-phase analysis

Read `references/prompt.md` (relative to the skill directory) — that file holds the full prompt text. Substitute the placeholders before running:

- `{{SOURCE_PATH}}` → user-supplied source path
- `{{OUTPUT_DIR}}` → scaffolded sibling directory
- `{{OUTPUT_LANG}}` → `zh` (default) or `en`
- `{{OUTPUT_BOOK_DIR}}` → `$OUTPUT_DIR/book-zh` (zh) or `$OUTPUT_DIR/book` (en)
- `{{PROJECT_NAME}}` → display name

Then execute the seven phases in order. Phase responsibilities:

| Phase          | Output                                                    | Notes                                       |
| -------------- | --------------------------------------------------------- | ------------------------------------------- |
| 1. Exploration | `OUTPUT_DIR/.reference/phase1-<subsystem>.md`             | Parallel subagents, one per subsystem       |
| 2. Audience    | `.reference/phase2-positioning.md`                        | Audience + thesis + value                   |
| 3. Structure   | `web/src/book.config.ts` populated; user-approved outline | **Get user sign-off before Phase 4**        |
| 4. Writing     | `book-zh/chNN-slug.md` (or `book/`)                       | Each chapter 300-800 lines                  |
| 5. Review      | `.reference/phase5-review.md`                             | 2-3 review subagents                        |
| 6. Revision    | Updated chapter files + book.config.ts                    | Apply review feedback                       |
| 7. Audit       | Sanitized chapter files                                   | Replace any verbatim source with pseudocode |

In Phase 3, also update `web/src/i18n/ui.ts`: replace `__PROJECT_NAME__` markers in `siteTitle.en` / `siteTitle.zh` with `PROJECT_NAME`, and rewrite `siteTagline` / `heroDescription` / `disclaimer` to fit the project. If the user supplied `GITHUB_URL`, set `githubUrl` in both languages.

Slug discipline (critical):

- Chapter slugs in `book.config.ts` use kebab-case with zero-padded numbers: `ch01-intro`, `ch12-runtime`.
- Markdown filenames in `book-zh/` (and `book/`) must match exactly: `ch01-intro.md`.
- Mismatches cause empty pages with no error — verify after Phase 4.

### Step 5 — Launch the dev server

After all seven phases finish:

```bash
cd "$OUTPUT_DIR/web"
bun run dev
```

The site serves at `http://localhost:4321` by default. English ToC at `/`, Chinese at `/zh/`.

If the user wants to preview the scaffold mid-way (e.g. after Phase 3 to inspect the outline), `bun run dev` works with empty book directories — the index page renders a "no chapters yet" notice.

## Template details

- **Stack**: Astro 6 (static), React 19, Tailwind v4, Mermaid 11.
- **Mermaid rendering**: `web/src/plugins/remark-mermaid-raw.mjs` rewrites ` ```mermaid ` blocks to placeholder divs containing the source; `web/src/scripts/mermaid-init.ts` runs `mermaid.run()` on `DOMContentLoaded`. Theme switches restore the stashed source and re-render with the other theme. Clicking a rendered diagram opens a zoom overlay (click or Esc to close).
- **Interactive React diagrams**: `web/src/components/InteractiveDiagrams.astro` is a stub. To attach a React component to a chapter, populate `chapterDiagrams[chapterNumber]`, import the component, and add the corresponding render branch. Add `d3` / `framer-motion` to `package.json` if the components need them — they are not in the template by default.
- **Bilingual routing**: `/` → English (uses `chapter.title`), `/zh/` → Simplified Chinese (uses `chapter.titleZh`). Both routes consume the same `book.config.ts`.

## Common failure modes

| Symptom                                                 | Cause                                                                        | Fix                                                                                                                       |
| ------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Chapter page is blank                                   | Slug mismatch between `book.config.ts` and markdown filename                 | Rename markdown or update slug; they must be identical                                                                    |
| Mermaid blocks render as code                           | `mermaid-init.ts` not loaded; usually a build error elsewhere                | Check browser console; rerun `bun run dev` after fixing                                                                   |
| Index page shows "no chapters yet"                      | `parts` / `chapters` arrays empty                                            | Phase 3 didn't update `book.config.ts`                                                                                    |
| `bun install` fails with peer warnings                  | Old bun version (< 1.1)                                                      | Upgrade bun, or fall back to `pnpm install`                                                                               |
| Chinese characters render as boxes                      | Font loading issue                                                           | The template loads Source Serif 4 + JetBrains Mono via fontsource; confirm fonts are bundled                              |
| Mermaid diagrams unreadable in dark mode (low contrast) | Hardcoded `fill:#XXX` / `classDef` color directives override theme switching | Remove all `style`/`classDef` color lines; let the theme control colors; use `subgraph` grouping for semantic distinction |

## When to stop and ask the user

- Before scaffolding if `OUTPUT_DIR` already exists with content.
- After Phase 3, with the proposed outline. Do not start Phase 4 (the expensive phase) without sign-off.
- If the source repo has fewer than ~3 substantial subsystems — the seven-phase format may be overkill. Suggest a shorter structure.
- If the user asks for output in a language other than Chinese or English — adapt the prompt accordingly and edit `ui.ts` so both `en` and `zh` strings reflect the chosen language.

## Reference

- `references/prompt.md` — Full seven-phase prompt with placeholders.
- `assets/web-template/` — Astro site template copied into each output directory.
