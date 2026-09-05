---
name: codebase-to-book
license: MIT
description: 将源码仓库写成多章节技术书，并生成可浏览的 Astro 站点；用于明确的源码解析书请求。
---

# Codebase-to-Book

Turns a source repository into a long-form technical book (architecture, patterns, internals) rendered by an Astro static site bundled with the skill. The web template is the artifact; the seven-phase prompt is the engine.

## What this skill produces

```
<source-repo>-from-source/
├── book-zh/                # Simplified Chinese chapters (default output)
├── book/                   # English chapters (optional; empty by default)
├── web/                    # Astro + React + Tailwind site
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

Resolve from the request and workspace. Ask only for missing inputs that cannot use the defaults:

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

Use the phases as a workflow guide, sized to the repository and requested book. Phase responsibilities:

| Phase          | Output                                             | Notes                                              |
| -------------- | -------------------------------------------------- | -------------------------------------------------- |
| 1. Exploration | `OUTPUT_DIR/.reference/phase1-<subsystem>.md`      | Scoped source reading; delegate only if authorized |
| 2. Audience    | `.reference/phase2-positioning.md`                 | Audience + thesis + value                          |
| 3. Structure   | `web/src/book.config.ts` populated; agreed outline | Confirm only an unresolved outline                 |
| 4. Writing     | `book-zh/chNN-slug.md` (or `book/`)                | Length follows the material                        |
| 5. Review      | `.reference/phase5-review.md`                      | Review within authorized execution mode            |
| 6. Revision    | Updated chapter files + book.config.ts             | Apply review feedback                              |
| 7. Audit       | Sanitized chapter files                            | Replace any verbatim source with pseudocode        |

In Phase 3, also update `web/src/i18n/ui.ts`: replace `__PROJECT_NAME__` markers in `siteTitle.en` / `siteTitle.zh` with `PROJECT_NAME`, and rewrite `siteTagline` / `heroDescription` / `disclaimer` to fit the project. If the user supplied `GITHUB_URL`, set `githubUrl` in both languages.

Slug discipline (critical):

- Chapter slugs in `book.config.ts` use kebab-case with zero-padded numbers: `ch01-intro`, `ch12-runtime`.
- Markdown filenames in `book-zh/` (and `book/`) must match exactly: `ch01-intro.md`.
- Mismatches cause empty pages with no error — verify after Phase 4.

### Step 5 — Build and inspect the site

After writing and revision, use the package manager selected during installation (the example uses bun):

```bash
cd "$OUTPUT_DIR/web"
bun run build
bun run dev
```

Read the actual server URL from its output. Open the requested language ToC and representative chapter pages; verify chapter links, content, Mermaid rendering and light/dark readability. Fix failures caused by this output. Build success or starting the server alone is not completion.

The default port is 4321. English ToC is `/`, Chinese is `/zh/`. Report untested behavior explicitly when browser inspection is unavailable.

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
- After Phase 3 only if the audience, scope or outline remains unresolved and affects the book. A supplied or already approved outline, or explicit authorization to proceed with a reasonable structure, does not need another sign-off.
- Adapt the structure to a small repository without filling unnecessary parts or chapters.
- Other output languages require a corresponding routing/i18n decision; clarify that decision if it cannot be inferred.

## Reference

- `references/prompt.md` — Full seven-phase prompt with placeholders.
- `assets/web-template/` — Astro site template copied into each output directory.
