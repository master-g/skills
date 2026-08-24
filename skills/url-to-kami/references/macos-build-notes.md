# macOS Kami Build Notes

Session-tested recipes for building Kami documents on macOS, where WeasyPrint's GTK dependencies are blocked by SIP.

## WeasyPrint Failure Pattern

On macOS, WeasyPrint fails with:

```
OSError: cannot load library 'libgobject-2.0-0': dlopen(libgobject-2.0-0, 0x0002): ...
```

This is **expected and unfixable** — SIP blocks DYLD_LIBRARY_PATH, preventing GTK library loading. Do not attempt to install GTK or fix WeasyPrint. Use Chrome Headless immediately.

## Chrome Headless Build Command

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu --print-to-pdf="/path/to/output.pdf" \
  --no-margins --run-all-compositor-stages-before-draw \
  --virtual-time-budget=5000 \
  "file:///path/to/your/filled.html"
```

**Flags explained:**
- `--no-margins` — removes browser default margins so CSS @page rules control spacing
- `--run-all-compositor-stages-before-draw` — ensures fonts and images are fully loaded before capture
- `--virtual-time-budget=5000` — gives 5 seconds for JS/fonts to settle; increase for heavy pages

**Output:** Chrome writes `340357 bytes written to file ...` on success. The "Trying to load the allocator multiple times" and "DEPRECATED_ENDPOINT" warnings are harmless.

## Font Fallback Behavior

The Kami `scripts/ensure-fonts.sh` font downloader may fail with `unbound variable` errors on some shell environments. This **does not block building** because:

1. HTML templates include CDN `@font-face` fallbacks:
   ```css
   src: url("../fonts/TsangerJinKai02-W04.ttf") format("truetype"),
        url("https://cdn.jsdelivr.net/gh/tw93/Kami@main/assets/fonts/TsangerJinKai02-W04.ttf") format("truetype");
   ```
2. Chrome Headless can fetch CDN fonts at render time
3. WeasyPrint (when it works) can also fetch CDN fonts

**Do not** let font script failures stop the build process. Proceed directly to HTML → PDF conversion.

## PNG Preview Generation

After PDF is built, generate a cover preview:

```bash
# Single page preview (cover page)
pdftoppm -r 150 -f 1 -l 1 -png input.pdf /tmp/cover
cp /tmp/cover-01.png output-cover.png

# All pages (for inspection)
pdftoppm -r 150 -png input.pdf /tmp/pages
# Produces: /tmp/pages-01.png, /tmp/pages-02.png, ...
```

Note: `pdftoppm` numbering is zero-padded (`-01`, `-02`), not `-1`, `-2`.

## Cleanup after preview generation

Preview PNGs generated during development should be cleaned up to avoid cluttering `~/Downloads`:

```bash
rm ~/Downloads/*-preview*.png ~/Downloads/quant-career-preview*.png
```

**Important:** The user may deny `rm` commands via terminal tool. If cleanup is blocked, do not retry — the files are harmless and the user can remove them manually.

## Verified Environment

- macOS (Apple Silicon and Intel)
- Google Chrome installed at `/Applications/Google Chrome.app/`
- `pdftoppm` available via poppler (`brew install poppler`)
