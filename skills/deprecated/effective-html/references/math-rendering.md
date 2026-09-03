# Math rendering

KaTeX with base64-embedded fonts — the only math pipeline for this skill. It renders offline, keeps the one-file promise (self-containment check stays green), and beats MathML on typographic quality for anything past a trivial expression.

## Decision rule

| Material                                                               | Do                                                 |
| ---------------------------------------------------------------------- | -------------------------------------------------- |
| Real math: derivations, integrals, matrices, >1–2 non-trivial formulas | **This pipeline** (Mode A or B below)              |
| One trivial expression (`x²`, `a/b`, `√2`) and page weight matters     | Plain Unicode or hand-written MathML — zero assets |
| Anything else                                                          | Never                                              |

Hard nevers: no CDN KaTeX/MathJax links (breaks self-containment — `check.py` ERROR), no formula screenshots (unselectable, blurry on zoom), no raw unrendered TeX left in the page (`check.py` warns).

## The assets

`assets/katex/` — KaTeX 0.16.11, vendored once by `scripts/katex.py bundle`:

| File                 | Size    | Contents                                                             |
| -------------------- | ------- | -------------------------------------------------------------------- |
| `katex.inline.css`   | ~367 KB | All `@font-face` srcs rewritten to base64 woff2 data URIs (20 fonts) |
| `katex.min.js`       | ~275 KB | KaTeX renderer (UMD — also `require()`-able in node)                 |
| `auto-render.min.js` | ~3.5 KB | `renderMathInElement` helper                                         |

**Never read these files into the conversation.** ~650 KB of minified bytes is context poison. You write placeholders; `scripts/katex.py` splices the bytes on disk.

Refresh or rebuild (idempotent; needs network only when the manifest is stale):

```bash
python3 <skill-path>/scripts/katex.py bundle              # verify / no-op if current
python3 <skill-path>/scripts/katex.py bundle --force      # re-download
python3 <skill-path>/scripts/katex.py bundle --slim --force  # drop Fraktur/Script/SansSerif/Typewriter (~25% smaller CSS)
```

## Mode A — pre-rendered (default for read-only pages)

Reports, explainers, decks — anything whose formulas are fixed at authoring time. Renders at build time, ships **zero JS**, paints instantly, works with JS disabled. Needs `node` on PATH.

Author every formula as an explicit span — no delimiter guessing, no currency false positives:

```html
<p>inline: <span class="math-tex">e^{i\pi}+1=0</span> — and display:</p>
<span class="math-tex" data-display="block"
  >\int_0^1 x^2\,dx = \tfrac{1}{3}</span
>
```

Rules:

- HTML-escape inside the span: `&lt;` `&gt;` `&amp;`. TeX never contains raw tags.
- `data-display="block"` for display math; omit for inline.
- Include only the CSS placeholder: `<!--KATEX_CSS-->` in `<head>`. Skip the JS placeholders entirely.

Then render:

```bash
python3 <skill-path>/scripts/katex.py prerender page.html
python3 <skill-path>/scripts/katex.py inline page.html   # splices the CSS placeholder
```

## Mode B — auto-render in the browser (interactive pages)

Only when the page injects **new** formulas at runtime — a slider driving a live model, a tuner echoing math. Ships the JS (~280 KB) and renders on `DOMContentLoaded`.

```html
<head>
  …
  <!--KATEX_CSS-->
</head>
<body>
  …content with \( E = mc^2 \) and \[ \nabla^2 \Psi = 0 \] …

  <!--KATEX_JS-->
  <!--KATEX_AUTO_RENDER-->
  <script>
    document.addEventListener("DOMContentLoaded", function () {
      renderMathInElement(document.body, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "\\[", right: "\\]", display: true },
          { left: "\\(", right: "\\)", display: false },
        ],
        throwOnError: false,
      });
    });
  </script>
</body>
```

Delimiter discipline:

- Prefer `\(…\)` / `\[…\]`. Skip bare `$…$` on any page that also mentions prices or dollars — auto-render will happily "render" `$5 and $10` into math. If `$…$` is unavoidable, escape literal dollars as `\$`.
- Runtime-injected formulas: after adding them to the DOM, call `renderMathInElement(newNode, opts)` again on just that node.

## Aftermath

- Re-run `check.py` and `visual_check.py` after splicing. Two new warnings are expected and ignorable on spliced pages: `{{...}} placeholder-style syntax` and `console.log leftover` — both come from the vendored minified library, not your content.
- Formula-heavy pages get heavy: CSS alone adds ~370 KB. Never attach KaTeX "just in case" — only when math is actually present.
- Bad TeX renders as KaTeX's red error text (`throwOnError:false`, `strict:"ignore"`) so one typo can't blank the page — but scan the rendered output for red before shipping.
- `<meta charset="utf-8">` is mandatory (all templates have it). Without it, browsers mis-decode the file and both CJK text and pre-rendered math glyphs garble.
- KaTeX sizes itself relative to body text (`.katex { font-size: 1.21em }`) — the templates' body sizes already look right; don't override it globally.
