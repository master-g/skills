# JS-Rendered Sites Extraction — Patterns & Pitfalls

## Problem

Modern web apps (Next.js, React SPA, Vue, etc.) often fail with Jina Reader because:
1. Jina's headless browser hits a client-side exception ("Application error: a client-side exception has occurred")
2. The site requires JS hydration before content appears in the DOM
3. The site blocks non-browser user-agents

## Extraction hierarchy for JS-heavy sites

Try in this order, stopping at first success:

### 1. Jina Reader (fastest, worth trying first)
```bash
curl -s "https://r.jina.ai/https://example.com/page" -H "Accept: text/plain"
```
**When it fails:** Returns "Application error" or empty content.

### 2. Direct curl + Python HTML text extraction
```bash
curl -sL "https://example.com/page" -o /tmp/page.html
python3 -c "
import re
with open('/tmp/page.html') as f:
    html = f.read()
# Remove scripts and styles
clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
# Strip tags
clean = re.sub(r'<[^>]+>', ' ', clean)
# Collapse whitespace
clean = re.sub(r'\s+', ' ', clean)
print(clean[:50000])
"
```
**Pitfall:** If the user has previously denied `curl` for this domain, skip this step and go to browser-harness.

### 3. browser-harness (CDP via user's real Chrome)
Requires Chrome to be running with remote debugging port open.

**Pre-flight check:**
```bash
curl -s http://127.0.0.1:9222/json/version
```
If this returns JSON, DevTools is live. If not, start Chrome:
```bash
# Kill any existing Chrome with remote debugging
pkill -f "remote-debugging-port=9222"

# Start headless Chrome with remote debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check \
  --user-data-dir=/tmp/chrome-debug-profile \
  --headless=new &

# Wait and verify
curl -s http://127.0.0.1:9222/json/version
```

**Then use browser-harness:**
```bash
browser-harness <<'PY'
from helpers import new_tab, goto, page_info, js
import time

new_tab()
goto("https://example.com/page")
time.sleep(6)  # Wait for JS hydration

info = page_info()
print("Title:", info.get('title'))

text = js("""
  const article = document.querySelector('article')
    || document.querySelector('main')
    || document.querySelector('[class*="content"]')
    || document.querySelector('[class*="article"]')
    || document.body;
  return article.innerText;
""")
print(text[:40000])
PY
```

**Pitfall:** `browser-harness` may fail with "CDP WS handshake failed: HTTP 404" if Chrome's profile picker is open or if the WebSocket endpoint is stale. Fix: ensure Chrome started cleanly with `--no-first-run` and a fresh `--user-data-dir`.

### 4. Chrome Headless direct PDF/screenshot (last resort)
If all text extraction fails, capture a PDF and OCR or read visually:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu \
  --print-to-pdf="/tmp/output.pdf" \
  --no-margins \
  --run-all-compositor-stages-before-draw \
  --virtual-time-budget=5000 \
  "https://example.com/page"
```

## Session records

- **2026-05-03**: `epicproduct.engineer` (Next.js app). Jina returned "Application error: a client-side exception". Direct curl succeeded (179KB HTML). Python regex extraction yielded full article text. browser-harness failed due to Chrome DevTools not being live. Resolution: curl + Python parse.
