---
name: url-to-kami
description: 'Read content from any URL (articles, blog posts, tweets, docs) and typeset it into a beautiful HTML document using the Kami design system. Use this skill whenever the user provides a URL and wants it turned into a readable, printable, or shareable document — even if they say "make this pretty", "turn this into a PDF", "save this article", "read this link", or "format this page". Triggers on URLs paired with any document or formatting intent.'
---

# URL to Kami — Turn Any Web Page into a Beautiful Document

Take a URL, extract its content, and typeset it into a warm parchment, ink-blue accented HTML document using Kami's editorial design system.

## Workflow

### Step 1 · Extract content from the URL

Use the best available extraction method for the URL:

1. **Jina Reader** (primary): `https://r.jina.ai/<url>` — clean Markdown, no API key, no JS needed
2. **curl + text extraction** (fallback): `curl -s <url>` then strip HTML tags with simple regex or Python. **Only use if the user has not previously denied this method for this domain.**
3. **browser-harness** (last resort): for JS-rendered pages where Jina fails. Use `--timeout 60` or higher for heavy sites like X/Twitter. See `references/x-extraction.md` for X-specific patterns.

```bash
# Primary: Jina Reader (with API Key for X/Twitter, otherwise no key needed)
curl -s "https://r.jina.ai/https://example.com/article" \
  -H "Accept: text/plain"

# For X/Twitter URLs — API Key REQUIRED
curl -s "https://r.jina.ai/http://x.com/username/status/123..." \
  -H "Authorization: Bearer jina_..." \
  -H "Accept: text/plain"

# Fallback: direct curl + text extraction
curl -sL "https://example.com/article" | python3 -c "
import sys, re
html = sys.stdin.read()
# Strip tags
text = re.sub(r'<[^>]+>', ' ', html)
# Collapse whitespace
text = re.sub(r'\s+', ' ', text)
print(text[:50000])  # limit to avoid overflow
"
```

**Special cases:**

| Site type | Strategy |
|---|---|
| X/Twitter posts | **Try Jina Reader without API Key first**: `curl -s "https://r.jina.ai/http://x.com/..." -H "Accept: text/plain"`. Many public tweets extract fine without auth. Only if blocked by login wall, retry **with API Key**: `curl -s "https://r.jina.ai/http://x.com/..." -H "Authorization: Bearer jina_..." -H "Accept: text/plain"`. If both fail, try `r.jina.ai/http://nitter.net/...`. **If all automated methods fail** (Jina empty, Nitter dead, curl blocked by SSL/TLS), use the **browser tool** (`browser_navigate`) as the reliable fallback: navigate to the tweet URL, wait for hydration, then use `browser_console` with JS to extract `document.querySelector('[data-testid="tweetText"]')?.innerText` and image URLs from `document.querySelectorAll('img[src*="twimg"]')`. See `references/x-extraction.md` for the full browser-extraction pattern. |
| Medium, Substack, Ghost blogs | Jina works well |
| Substack with images | Jina extracts image URLs in Markdown; use `curl -sL <page>` + regex to find `substackcdn.com/image/fetch/` URLs. The `$` and `!` characters in URLs require careful shell escaping — use single-quoted curl commands or Python extraction. See `references/substack-image-extraction.md`. |
| GitHub README | Jina works; append `#readme` if needed |
| Docs sites (ReadTheDocs, Docusaurus) | Jina usually works; may need browser-harness for sidebar-stripped content |
| Paywalled news | Jina may get paywall; try textise dot iitty or textise dot iitty |
| Next.js / heavy JS apps (e.g. `epicproduct.engineer`) | Jina often returns "Application error: a client-side exception". Use **browser-harness** or **curl + Python HTML parse** (see `references/js-rendered-sites.md`) |
| arXiv papers (`arxiv.org/abs/...`) | Jina extracts the abstract page metadata only (title, authors, abstract). For the full paper content, **download the PDF** (`curl -L -o paper.pdf "https://arxiv.org/pdf/<id>"`) and extract with `pymupdf`/`fitz`. See `references/arxiv-extraction.md` for the full recipe. |

After extraction, keep:
- Title (from `<title>` or first H1)
- Author (from byline, meta tags, or "by Author Name")
- Publish date (from meta tags or URL)
- Main body text (strip nav, ads, comments, footers)
- Key images (first 1-3 relevant images)

### Step 2 · Analyze, translate, and structure the content

**Default language: Chinese.** Unless the user explicitly says "keep in English" / "保留原文" / "不要翻译", translate all extracted content into Chinese. This includes:
- Title → 中文标题
- Body text → 中文正文
- Quotes → 中文引用（保留原文作者名、公司名、技术术语）
- Section headings → 中文章节标题
- Metadata (author, source) → 保留原文，但可附加中文说明

**When NOT to translate:**
- Proper nouns: company names, product names, person names (Apple, OpenAI, Sam Altman)
- Technical terms: JWT, API, React, Kubernetes (keep English, optionally add 中文注释)
- Code snippets, URLs, file paths
- Direct quotes where the original phrasing is iconic or analytically important

Read the extracted content and decide the best Kami document type:

| Content type | Kami template | Why |
|---|---|---|
| Single article / blog post / essay | `long-doc` | Full narrative flow with sections |
| News article / short report | `one-pager` | Condensed, scannable |
| Thread / collection of tweets | `long-doc` or `one-pager` | Depends on length |
| Technical documentation / README | `long-doc` | Code blocks, structured sections |
| Research paper / analysis | `long-doc` | Dense, citations, figures |
| Interview / Q&A | `long-doc` | Dialogue format |

Distill and translate the raw content:
1. **Extract**: pull title, author, date, key claims, quotes, data points
2. **Translate to Chinese**: translate all prose content while preserving proper nouns and technical terms
3. **Structure**: map to template sections (header, summary, body sections, conclusion)
4. **Clean**: remove ads, nav, "read more", cookie banners, comment sections
5. **Enhance**: identify 1-3 key quotes worth highlighting; note any data that could become a simple chart

### Step 3 · Build the Kami HTML document

Load the Kami skill and follow its workflow. The Kami skill is located at `~/.agents/skills/kami/`. Templates are in `assets/templates/`, build script is at `scripts/build.py`.

1. **Language**: **Chinese by default** — use `*.html` templates from `~/.agents/skills/kami/assets/templates/`. Only use `*-en.html` if user explicitly said "keep in English" / "保留原文" / "不要翻译"
2. **Document type**: from Step 2's analysis
3. **Template**: copy the matching template from `~/.agents/skills/kami/assets/templates/`
   - **Chinese content** → use `*.html` templates (not `*-en.html`)
   - English content (only when user explicitly requested) → use `*-en.html`
4. **Fill content**:
   - Title → `.header .title` or `<h1>`
   - Author + date → `.header .subtitle` or meta line
   - Body → sections with `<h2>` headings auto-derived from content structure
   - Key quote → `<blockquote class="pull-quote">`
   - Source URL → footer as "Originally from: <url>"

5. **Metadata**: fill `<meta name="author">`, `<meta name="description">`, `<meta name="keywords">`

6. **Build**: run Kami's build script. Note: `build.py` works with template names, not arbitrary paths. Use WeasyPrint directly for custom filled HTML files:
   ```bash
   # Option A: If you placed your file in kami's directory as a named template
   cd ~/.agents/skills/kami
   python3 scripts/build.py --verify

   # Option B: Direct WeasyPrint (recommended for one-off files)
   python3 -c "from weasyprint import HTML; HTML('/path/to/your/filled.html').write_pdf('/path/to/output.pdf')"

   # Option C: Chrome Headless (macOS fallback — use when WeasyPrint fails)
   # WeasyPrint on macOS often fails with "cannot load library 'libgobject-2.0-0'"
   # because SIP blocks DYLD_LIBRARY_PATH. Chrome Headless is the reliable fallback.
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --headless --disable-gpu --print-to-pdf="/path/to/output.pdf" \
     --no-margins --run-all-compositor-stages-before-draw \
     --virtual-time-budget=5000 "file:///path/to/your/filled.html"
   ```

   **Build priority:** Try WeasyPrint first (better typography, page headers/footers). If it fails on macOS with the libgobject error, immediately fall back to Chrome Headless. Do not attempt to fix WeasyPrint's GTK dependencies — it's a known macOS SIP limitation.

   **Font note:** Before building Chinese documents, the Kami `ensure-fonts.sh` script may fail with `unbound variable` errors on some environments. This does not block building — the HTML templates include CDN font fallbacks (`https://cdn.jsdelivr.net/gh/tw93/Kami@main/assets/fonts/...`) that WeasyPrint or Chrome can use. Do not let font script failures stop the build.

7. **Output formats**: HTML + PDF (default). If user says "share" or "post", also generate PNG using `pdftoppm`.

### Step 4 · Save to Downloads

Save outputs to `~/Downloads` to avoid polluting the working directory:

```bash
# Ensure Downloads exists
mkdir -p ~/Downloads

# HTML source
~/Downloads/<slugified-title>.html

# PDF (via Kami build.py)
~/Downloads/<slugified-title>.pdf

# PNG preview (if requested)
~/Downloads/<slugified-title>.png
```

Naming: slugify the article title (lowercase, hyphens, no special chars). If no clear title, use `document-from-url-<timestamp>`.

## Content quality guidelines

When extracting and structuring:

- **Preserve the author's voice** — don't rewrite into corporate speak
- **Data over adjectives** — if the article has numbers, keep them prominent
- **One highlight per section** — don't bold everything
- **Source attribution** — always include the original URL in the footer
- **Length-aware**: articles >3000 words → use `long-doc` with TOC; <1500 words → `one-pager`
- **Images from X/Twitter**: when local download of `pbs.twimg.com` images fails (SSL/TLS issues), embed the remote URLs directly in HTML `<img src>` tags. WeasyPrint fetches them during PDF build. No local download needed.
- **Code blocks in X threads**: long-form X threads often contain substantial code snippets (TypeScript, Python). Preserve them in `<pre><code>` blocks with language classes. Do not strip or simplify code — it's often the core value of the thread.

## When this skill triggers

- User pastes a URL and says "make this readable", "turn this into a PDF", "save this article"
- User says "read this link and make it pretty"
- User provides a URL with any document/formatting intent
- User says "I want to print this page" or "share this article"
- **Default output is Chinese** — even if the source article is in English, the document will be translated to Chinese unless user explicitly says otherwise

## When NOT to use

- User just wants a summary without formatting → use plain text summarization
- User wants to edit the original web page → this creates a new document, doesn't modify the source
- URL is a video, image, or binary file → this skill handles text content only
- User wants interactive/dashboard output → Kami is for static documents

## Example

**User:** "Read this and make it into a nice document: https://blog.example.com/ai-trends-2025"

**Skill does:**
1. `curl -s "https://r.jina.ai/https://blog.example.com/ai-trends-2025"`
2. Extracts title "AI Trends 2025", author "Jane Smith", 5 key trends with data
3. **Translates all content to Chinese** (保留英文专有名词如 OpenAI, GPT-4)
4. Chooses `long-doc.html` template (Chinese, article-length) — NOT `long-doc-en.html`
### 5. X Embed API (limited)
For public tweets, `https://publish.twitter.com/oembed?url=...` sometimes returns embed HTML, but this also increasingly requires auth.

## Dual-output pattern: Kami + wiki from same source

When the user wants both a Kami document and a wiki ingest from the same URL, use this sequence to avoid double-fetching:

1. **Extract** via Jina Reader (or fallback) → get raw markdown text
2. **Build Kami** → fill template, generate HTML + PDF
3. **Reuse for wiki** → extract raw text from the generated HTML via regex strip-tags → save as `raw/articles/<slug>.md`
4. **Create concept** → synthesize structured concept page from the same content

This ensures both outputs are consistent and avoids a second network request.

## Session records

- **2026-06-04**: `x.com/Saboo_Shubham_/status/2062220865643982875` (long-form tweet thread on Generative UI). Jina Reader **without API key succeeded** — returned full ~35KB article text cleanly with all code blocks preserved. Document typeset into Kami long-doc (9 chapters, 336KB PDF via Chrome Headless).
- **2026-06-04**: `x.com/TheAhmadOsman/status/2058745340895870985` (long-form tweet thread on LLM Engineering Projects). Jina Reader **without API key succeeded** — returned full ~45KB article text with 22 embedded image references. Document typeset into Kami long-doc (9 chapters incl. 12-week schedule, 429KB PDF via Chrome Headless). Both cases confirm Jina's reliability for public X threads without auth.
- **2026-06-02**: `x.com/0x_rody/status/2061019244595233135` (long-form tweet thread). Jina Reader **without API key succeeded** — returned full 9.5KB article text cleanly. This validates the "try without key first" fallback ordering for public tweets. Document was then typeset into Kami long-doc. WeasyPrint failed with `libgobject-2.0-0` error (macOS SIP limitation); immediately fell back to Chrome Headless which produced a 254KB PDF successfully.
- **2026-05-25**: `x.com/cyrilXBT/status/2058373087330959829` (long-form tweet thread). Jina Reader **without API key succeeded** — returned full 26KB article text cleanly. Document was then typeset into Kami long-doc. (Historical: also ingested into llm-wiki, which was archived and removed on 2026-07-30 — the wiki-output path no longer applies. The ordering insight remains valid: when multiple outputs are needed from one source, build Kami first — it fetches and structures the content — then derive secondary outputs from the generated HTML via regex strip-tags, avoiding a second network fetch.)
- **2026-05-24**: `x.com/regent0x_/status/2057419591618302029` (long-form tweet thread with 11 images). Jina Reader returned empty. Direct curl to x.com and pbs.twimg.com failed with `LibreSSL SSL_ERROR_SYSCALL`. browser-harness unavailable (editable install path broken). Resolution: used **browser tool** (`browser_navigate` → wait for hydration → `browser_console` JS extraction). Got full tweet text via `document.querySelector('article')?.innerText` and image URLs via `document.querySelectorAll('img[src*="twimg"]')`. Images embedded via remote URLs (WeasyPrint fetched during PDF build). Document built successfully as 18-page Kami long-doc.
- **2026-05-03**: `epicproduct.engineer` (Next.js app). Jina returned "Application error: a client-side exception". Direct curl succeeded (179KB HTML). Python regex extraction yielded full article text. browser-harness failed due to Chrome DevTools not being live. Resolution: curl + Python parse. See `references/js-rendered-sites.md` for full pattern.
- **2025-05-01**: Attempted to extract `https://x.com/ashpreetbedi/status/2049904901371633815`. All automated methods failed. Jina returned empty. Nitter instances returned empty. browser-harness timed out at 30s. Resolution: asked user to paste content directly.
