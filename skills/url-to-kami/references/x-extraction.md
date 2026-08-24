# X / Twitter Content Extraction — Current State (2026)

## Problem

X/Twitter is aggressively gated behind login walls and heavy JavaScript rendering. Most automated extraction methods that worked in 2023–2024 are broken as of 2025–2026.

## What no longer works

| Method | Status | Notes |
|--------|--------|-------|
| Direct `curl` to x.com | ❌ Broken | Requires JS execution + auth cookies; LibreSSL SSL_ERROR_SYSCALL common |
| `r.jina.ai/http://nitter.net/...` | ❌ Dead | Nitter.net is defunct |
| `r.jina.ai/http://nitter.privacydev.net/...` | ⚠️ Intermittent | Some instances still up but unreliable |

## What works (in order)

### 0. Jina Reader without API key (try first for public tweets)

As of 2026-06, Jina Reader **often succeeds on public tweets without any authentication**:

```bash
curl -s "https://r.jina.ai/http://x.com/USERNAME/status/STATUS_ID" \
  -H "Accept: text/plain"
```

**Session validation:**
- 2026-06-09: `x.com/RitOnchain/status/2063967087933136971` — returned full ~17KB article text cleanly
- 2026-06-04: `x.com/Saboo_Shubham_/status/2062220865643982875` — full ~35KB with code blocks
- 2026-06-04: `x.com/TheAhmadOsman/status/2058745340895870985` — full ~45KB with 22 images
- 2026-06-02: `x.com/0x_rody/status/2061019244595233135` — full 9.5KB cleanly
- 2026-05-25: `x.com/cyrilXBT/status/2058373087330959829` — full 26KB cleanly

Only if this returns empty or a login wall, escalate to the methods below.

### 1. tinyfish browser session + Hermes browser tools (most reliable for X in 2026)

When Jina Reader fails due to X's login wall or JavaScript requirements, `tinyfish browser session create` provides a remote headless browser that can render X's JS-heavy frontend.

```bash
# Create a remote browser session
tinyfish browser session create --url https://x.com/USERNAME/status/STATUS_ID
# Returns: {"session_id":"...","cdp_url":"...","base_url":"..."}
```

Then use Hermes `browser_navigate` and `browser_console` tools:

```javascript
// Full tweet text (including all paragraphs)
document.querySelector('article').innerText

// Author info
document.querySelector('[data-testid="User-Name"]')?.innerText

// Images (filter for media URLs)
Array.from(document.querySelectorAll('img[src*="twimg"]'))
  .map(img => img.src)
  .filter(src => src.includes('media'))

// Timestamp
document.querySelector('time')?.dateTime
```

**Key advantages over browser-harness:**
- Does not require local Chrome with DevTools enabled
- Works in headless/automated environments
- Session auto-expires (no manual cleanup needed)

**Pitfall:** The default `browser_snapshot` may show a truncated view. Always use `browser_console` with `expression` to run JS and get the full `innerText` of the `article` element.

**Image handling:** If local download of Twitter CDN images fails (common SSL_ERROR_SYSCALL with LibreSSL), embed the remote `pbs.twimg.com` URLs directly in HTML `<img src>` tags. WeasyPrint or Chrome Headless will fetch them during PDF build.

### 2. Browser tool extraction (fallback when tinyfish unavailable)

When tinyfish is not available, use Hermes browser tools directly:

```javascript
// Tweet text
document.querySelector('[data-testid="tweetText"]')?.innerText

// For long threads, article innerText captures all paragraphs
document.querySelector('article')?.innerText
```

**Pitfall:** Same truncation risk as above — prefer `browser_console` over `browser_snapshot` for full text.

### 3. Ask the user to paste the text directly

**Fastest when all automated methods fail.** If the user can see the tweet in their browser, ask them to copy-paste the text. Then proceed with Kami typesetting immediately.

### 4. browser-harness with extended timeout

X's frontend is extremely heavy. Use at least 60s timeout and wait 5+ seconds after navigation:

```python
browser-harness <<'PY'
import asyncio
from helpers import new_tab, goto, js

async def main():
    await new_tab()
    await goto("https://x.com/USERNAME/status/STATUS_ID")
    await asyncio.sleep(5)  # Critical: X needs time to hydrate

    tweet = await js("""
        const el = document.querySelector('[data-testid=\"tweetText\"]');
        return el ? el.innerText : null;
    """)
    print(tweet)

asyncio.run(main())
PY
```

**Pitfall:** Default 30s timeout is almost always insufficient for X. Use `--timeout 60` or more.

### 5. Try alternative Nitter instances

As of 2025-05, these have been observed to work sporadically:
- `nitter.privacydev.net`
- `nitter.poast.org`

Test with:
```bash
curl -s "https://r.jina.ai/http://nitter.privacydev.net/USERNAME/status/STATUS_ID"
```

### 6. X Embed API (limited)

For public tweets, `https://publish.twitter.com/oembed?url=...` sometimes returns embed HTML, but this also increasingly requires auth.

## Decision tree

```
Is it a public tweet?
├── YES → Try Jina Reader without API key first
│         └── Success? → Use the extracted text
│         └── Empty/login wall? → Try tinyfish browser session
│               └── Success? → Use browser_console extraction
│               └── Fail? → Try browser-harness (if available)
│                     └── Fail? → Ask user to paste text
└── NO (private tweet) → Ask user to paste text directly
```

## Session records

- **2026-06-09**: `x.com/RitOnchain/status/2063967087933136971` (long-form tweet thread). Jina Reader **without API key succeeded** — returned full ~17KB article text cleanly. This validates the "try without key first" strategy continues to work as of mid-2026.
- **2026-06-04**: `x.com/Saboo_Shubham_/status/2062220865643982875` (long-form tweet thread on Generative UI). Jina Reader **without API key succeeded** — returned full ~35KB article text cleanly with all code blocks preserved.
- **2026-06-04**: `x.com/TheAhmadOsman/status/2058745340895870985` (long-form tweet thread on LLM Engineering Projects). Jina Reader **without API key succeeded** — returned full ~45KB article text with 22 embedded image references.
- **2026-06-02**: `x.com/0x_rody/status/2061019244595233135` (long-form tweet thread). Jina Reader **without API key succeeded** — returned full 9.5KB article text cleanly.
- **2026-05-25**: `x.com/cyrilXBT/status/2058373087330959829` (long-form tweet thread). Jina Reader **without API key succeeded** — returned full 26KB article text cleanly.
- **2026-05-24**: `x.com/regent0x_/status/2057419591618302029` (long-form tweet thread with 11 images). Jina Reader returned empty. Direct curl to x.com and pbs.twimg.com failed with `LibreSSL SSL_ERROR_SYSCALL`. browser-harness unavailable. Resolution: used **browser tool** (`browser_navigate` → wait for hydration → `browser_console` JS extraction). Got full tweet text via `document.querySelector('article')?.innerText`.
- **2025-05-01**: `x.com/ashpreetbedi/status/2049904901371633815`. All automated methods failed. Jina returned empty. Nitter instances returned empty. browser-harness timed out at 30s. Resolution: asked user to paste content directly.
