#!/usr/bin/env python3
"""Vendor and inline a fully self-contained KaTeX bundle for effective-html pages.

Two subcommands:

  bundle  Download a pinned KaTeX release from jsDelivr and rewrite its CSS so
          every @font-face src is a base64 woff2 data URI. Output lands in
          assets/katex/. Idempotent: re-running with the same version/mode and
          intact files is a no-op. Use --force to re-download, --slim to drop
          rarely used font families (Fraktur/Script/SansSerif/Typewriter).

  inline  Splice the vendored assets into an HTML file, replacing the three
          placeholders:
              <!--KATEX_CSS-->         -> <style>…katex css with base64 fonts…</style>
              <!--KATEX_JS-->          -> <script>…katex.min.js…</script>
              <!--KATEX_AUTO_RENDER--> -> <script>…auto-render.min.js…</script>
          Run AFTER the page is otherwise finished, then re-run check.py.

The point of this two-step flow: the agent never pastes ~700 KB of vendored
JS/CSS into its context — it writes placeholders and this script does the
byte-level splicing on disk.

Usage:
  python3 katex.py bundle [--version 0.16.11] [--slim] [--force]
  python3 katex.py inline page.html [more.html ...] [--assets DIR]

Exit codes: 0 ok, 1 error, 2 usage.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS = SKILL_ROOT / "assets" / "katex"
DEFAULT_VERSION = "0.16.11"
CDN = "https://cdn.jsdelivr.net/npm/katex@{version}/dist"

# Families dropped by --slim: decorative alphabets almost never needed for the
# explainers/reports this skill produces. Main/Math/AMS/Size*/Caligraphic stay.
SLIM_DROP = re.compile(r"KaTeX_(Fraktur|Script|SansSerif|Typewriter)")

CSS_PLACEHOLDER = "<!--KATEX_CSS-->"
JS_PLACEHOLDER = "<!--KATEX_JS-->"
AUTO_PLACEHOLDER = "<!--KATEX_AUTO_RENDER-->"

UA = {"User-Agent": "effective-html-katex-bundler/1.0"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- bundle

def build_inline_css(css: str, version: str, slim: bool) -> tuple[str, list[dict]]:
    """Rewrite katex.min.css: every @font-face src becomes a woff2 data URI."""
    if slim:
        # Drop whole @font-face blocks for decorative families.
        css = re.sub(
            r"@font-face\{font-family:" + SLIM_DROP.pattern + r"[^}]*\}",
            "",
            css,
        )

    # Font files actually referenced (woff2 only — every modern browser reads it).
    needed = sorted(set(re.findall(r"url\(fonts/([^)]+\.woff2)\)", css)))
    if not needed:
        raise RuntimeError("no woff2 font references found in KaTeX CSS — upstream format changed?")

    manifest_fonts = []
    for name in needed:
        if slim and SLIM_DROP.search(name):
            continue
        data = fetch(f"{CDN.format(version=version)}/fonts/{name}")
        b64 = base64.b64encode(data).decode("ascii")
        # Replace the full src list (woff2+woff+ttf) with the single data URI.
        pattern = re.compile(
            r"src:url\(fonts/" + re.escape(name) + r"\)[^;}]*"
        )
        replacement = f'src:url(data:font/woff2;base64,{b64}) format("woff2")'
        css, n = pattern.subn(replacement, css)
        if n != 1:
            raise RuntimeError(f"expected exactly 1 src for {name}, replaced {n}")
        manifest_fonts.append({"file": name, "bytes": len(data), "sha256": sha256(data)})

    # Any leftover non-data font url() means the rewrite missed something.
    leftovers = [u for u in re.findall(r"url\(([^)]*)\)", css) if not u.startswith("data:")]
    if leftovers:
        raise RuntimeError(f"un-embedded font URLs remain: {leftovers[:3]}")
    return css, manifest_fonts


def cmd_bundle(args: argparse.Namespace) -> int:
    assets: Path = args.assets
    manifest_path = assets / "MANIFEST.json"

    if manifest_path.exists() and not args.force:
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, ValueError):  # unreadable or malformed manifest -> rebuild
            manifest = {}
        intact = all(
            (assets / f["name"]).exists()
            and sha256((assets / f["name"]).read_bytes()) == f["sha256"]
            for f in manifest.get("outputs", [])
        )
        if (
            manifest.get("version") == args.version
            and manifest.get("slim") == args.slim
            and intact
        ):
            print(f"katex bundle already vendored ({args.version}, "
                  f"{'slim' if args.slim else 'full'}) at {assets} — nothing to do")
            return 0
        print("existing bundle differs or is damaged — rebuilding")

    assets.mkdir(parents=True, exist_ok=True)
    base = CDN.format(version=args.version)
    print(f"downloading KaTeX {args.version} from jsDelivr ({'slim' if args.slim else 'full'} fonts)…")

    raw_css = fetch(f"{base}/katex.min.css").decode("utf-8")
    inline_css, fonts = build_inline_css(raw_css, args.version, args.slim)
    katex_js = fetch(f"{base}/katex.min.js")
    auto_js = fetch(f"{base}/contrib/auto-render.min.js")

    outputs = [
        ("katex.inline.css", inline_css.encode("utf-8")),
        ("katex.min.js", katex_js),
        ("auto-render.min.js", auto_js),
    ]
    manifest = {
        "version": args.version,
        "slim": args.slim,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": base,
        "fonts": fonts,
        "outputs": [
            {"name": name, "bytes": len(data), "sha256": sha256(data)}
            for name, data in outputs
        ],
    }
    for name, data in outputs:
        (assets / name).write_bytes(data)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    total = sum(o["bytes"] for o in manifest["outputs"])
    print(f"wrote {len(outputs)} files ({total:,} bytes total, "
          f"{len(fonts)} woff2 fonts embedded) to {assets}")
    for o in manifest["outputs"]:
        print(f"  {o['name']:<22} {o['bytes']:>9,} bytes")
    return 0


# --------------------------------------------------------------------------- prerender

# Authoring contract for pre-rendered math:
#   <span class="math-tex">e^{i\pi}+1=0</span>                    (inline)
#   <span class="math-tex" data-display="block">\int_0^1 x^2</span>  (display)
# TeX source is HTML-escaped in the page; formulas never contain literal tags.
MATH_SPAN = re.compile(
    r'<span\b[^>]*class="[^"]*\bmath-tex\b[^"]*"([^>]*)>(.*?)</span>',
    re.DOTALL,
)
DISPLAY_ATTR = re.compile(r'data-display\s*=\s*["\']block["\']')


def cmd_prerender(args: argparse.Namespace) -> int:
    node = shutil.which("node")
    if not node:
        print("error: prerender needs node on PATH (auto-render mode does not) — "
              "install node or use the <!--KATEX_JS--> placeholders instead", file=sys.stderr)
        return 1
    helper = Path(__file__).with_name("katex_prerender.js")
    ok = True
    for page in args.pages:
        path = Path(page)
        text = path.read_text(encoding="utf-8")
        spans = list(MATH_SPAN.finditer(text))
        if not spans:
            print(f"{path.name}: no math-tex spans — nothing to render")
            continue
        jobs = [
            {"tex": html.unescape(m.group(2)),
             "display": bool(DISPLAY_ATTR.search(m.group(1)))}
            for m in spans
        ]
        proc = subprocess.run(
            [node, helper], input=json.dumps(jobs),
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            print(f"{path.name}: ERROR renderer failed: {proc.stderr.strip()[:200]}", file=sys.stderr)
            ok = False
            continue
        try:
            rendered = json.loads(proc.stdout)
        except ValueError:
            print(f"{path.name}: ERROR renderer returned non-JSON output: "
                  f"{proc.stdout.strip()[:200]!r}", file=sys.stderr)
            ok = False
            continue
        if not isinstance(rendered, list) or len(rendered) != len(spans):
            print(f"{path.name}: ERROR renderer returned {len(rendered)} results "
                  f"for {len(spans)} spans", file=sys.stderr)
            ok = False
            continue
        out, last = [], 0
        for m, html_out in zip(spans, rendered):
            out.append(text[last:m.start()])
            out.append(html_out)
            last = m.end()
        out.append(text[last:])
        text = "".join(out)
        path.write_text(text, encoding="utf-8")
        n_display = sum(1 for j in jobs if j["display"])
        print(f"{path.name}: pre-rendered {len(spans)} formula(s) "
              f"({n_display} display, {len(spans) - n_display} inline)")
        if JS_PLACEHOLDER in text or AUTO_PLACEHOLDER in text:
            print(f"{path.name}: note: JS placeholders remain — keep them only if "
                  f"the page injects NEW formulas at runtime; otherwise delete "
                  f"{JS_PLACEHOLDER} / {AUTO_PLACEHOLDER} to save ~280 KB")
    return 0 if ok else 1


# --------------------------------------------------------------------------- inline

def splice(path: Path, assets: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if all(p not in text for p in (CSS_PLACEHOLDER, JS_PLACEHOLDER, AUTO_PLACEHOLDER)):
        if "data:font/woff2" in text and "katex" in text.lower():
            print(f"{path.name}: placeholders already replaced — skipping")
            return True
        print(f"{path.name}: ERROR no KaTeX placeholders found "
              f"(expected {CSS_PLACEHOLDER} etc.)", file=sys.stderr)
        return False

    missing = [n for n in ("katex.inline.css", "katex.min.js", "auto-render.min.js")
               if not (assets / n).exists()]
    if missing:
        print(f"{path.name}: ERROR vendored assets missing: {missing} — "
              f"run `python3 {Path(__file__).name} bundle` first", file=sys.stderr)
        return False

    blocks = {
        CSS_PLACEHOLDER: "<style>\n" + (assets / "katex.inline.css").read_text("utf-8") + "\n</style>",
        JS_PLACEHOLDER: "<script>\n" + (assets / "katex.min.js").read_text("utf-8") + "\n</script>",
        AUTO_PLACEHOLDER: "<script>\n" + (assets / "auto-render.min.js").read_text("utf-8") + "\n</script>",
    }
    added = 0
    for placeholder, block in blocks.items():
        if placeholder in text:
            text = text.replace(placeholder, block, 1)
            added += len(block)
        else:
            print(f"{path.name}: note: {placeholder} not present, skipped")

    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: spliced {added:,} bytes of KaTeX assets "
          f"(final size {len(text.encode('utf-8')):,} bytes)")
    return True


def cmd_inline(args: argparse.Namespace) -> int:
    ok = all(splice(Path(p), args.assets) for p in args.pages)
    return 0 if ok else 1


# --------------------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_bundle = sub.add_parser("bundle", help="download + vendor the KaTeX assets")
    p_bundle.add_argument("--version", default=DEFAULT_VERSION)
    p_bundle.add_argument("--slim", action="store_true",
                          help="drop Fraktur/Script/SansSerif/Typewriter fonts")
    p_bundle.add_argument("--force", action="store_true", help="re-download even if current")
    p_bundle.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    p_bundle.set_defaults(func=cmd_bundle)

    p_inline = sub.add_parser("inline", help="splice vendored assets into HTML placeholder pages")
    p_inline.add_argument("pages", nargs="+", help="HTML files containing the placeholders")
    p_inline.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    p_inline.set_defaults(func=cmd_inline)

    p_pre = sub.add_parser("prerender", help="render math-tex spans at build time (needs node)")
    p_pre.add_argument("pages", nargs="+", help="HTML files containing math-tex spans")
    p_pre.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    p_pre.set_defaults(func=cmd_prerender)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
