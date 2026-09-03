# Social media extraction recipes

Reference for pulling raw material from Twitter/X and other social platforms when the user's source is a social link. Use this when the user provides a URL to a tweet, thread, or social post that contains an article, analysis, or substantive content you need to convert into a page.

## Twitter/X links

### The problem

X/t.co short links often redirect to external articles (Substack, blogs, etc.). Direct extraction via `curl` or `jina.ai` frequently fails because:

- t.co links require following redirects, which may be blocked by the user's security policy
- X article pages use JavaScript rendering; standard text extraction returns only the tweet shell, not the linked content
- Browser automation may land on an intermediate page where the article selector returns null after navigation

### Working strategy (fallback chain)

1. **Try `autocli` first** — it reads Twitter/X (and 55+ other sites) through the user's logged-in Chrome session, which bypasses both the JS-rendering and the login-wall problems: `autocli read <url>` extracts the main content as Markdown. If autocli is unavailable or returns only the tweet shell (no article body), proceed to step 2.

2. **Try a generic extractor, then search for mirrors** — `jina-reader` (or plain WebFetch) sometimes captures the linked article. Failing that, search with `tinyfish search query "<author name> + distinctive phrase from the tweet>"` (fall back to native WebSearch only if tinyfish is rate-limited). This often surfaces aggregator mirrors (threadreader etc.), blog posts quoting the same content, or related analysis that fills in gaps.

3. **Use what you have** — if only the tweet summary is available, build the page from that plus any related material found in step 2. Mark gaps with `[DATA NEEDED]` rather than fabricate.

### What NOT to do

- Do NOT loop the same failing extraction (same tool, same selector/URL) more than twice — switch to the next rung of the chain instead
- Do NOT attempt `curl -L` on t.co links if the user has blocked redirect-following commands
- Do NOT invent article content to fill out a template — a shorter honest page beats a fabricated one

## Language matching

Output language follows the skill-wide default: Simplified Chinese unless the user explicitly requested another language (see SKILL.md Step 1). Verbatim quotes from the source keep their original language. The templates ship `lang="en"` — set `lang="zh-CN"` on Chinese pages.
