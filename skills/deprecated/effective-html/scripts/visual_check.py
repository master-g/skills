#!/usr/bin/env python3
"""Visual review gate for effective-html outputs.

Usage: python3 visual_check.py path/to/output.html [more.html ...]
       [--widths 390,768,1280] [--shots-dir DIR] [--no-shots]

Renders each file in headless Chrome/Chromium at three viewport widths and
fails on the layout defects that check.py cannot see:

  ERROR  horizontal overflow (document wider than the viewport)
  ERROR  squeezed text column (heading/paragraph wrapped to a vertical
         strip: taller than ~6 lines while narrower than ~4 characters)
  ERROR  text/background contrast ratio below 3:1
  WARN   text/background contrast ratio between 3:1 and 4.5:1 (WCAG AA)

Screenshots of every (file, width) render are saved for the mandatory human
look — pass --shots-dir to choose where. The script detects real rendered
geometry with a JS probe, so it needs a Chrome-family browser:

  $VISUAL_CHECK_BROWSER / $CHROME_PATH, else Google Chrome (macOS app or
  PATH), Chromium, or Edge.

Exit 0 if no errors (warnings allowed), 1 on errors, 2 if the gate itself
cannot run (no browser found). A gate that cannot run is NOT a passed gate —
say so instead of claiming the page was visually verified.
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

DEFAULT_WIDTHS = [390, 768, 1280]
MAX_SHOT_HEIGHT = 16000
BROWSER_CANDIDATES = [
    os.environ.get("VISUAL_CHECK_BROWSER"),
    os.environ.get("CHROME_PATH"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]

RESULT_RE = re.compile(
    r'<pre id="visual-check-result"[^>]*>(.*?)</pre>', re.DOTALL
)

# Wrapper around the target via an srcdoc iframe. Load-bearing for two reasons:
# headless Chrome clamps the window to ~500px minimum, and srcdoc iframes
# inherit the parent origin (unlike file:// iframes), so the wrapper's script
# may read the probe result out of the inner document. The skill's outputs are
# self-contained by contract, so inlining the whole file into srcdoc is safe.
WRAPPER_JS = r"""
window.addEventListener('load', function () {
  var pre = document.createElement('pre');
  pre.id = 'visual-check-result';
  pre.style.display = 'none';
  try {
    var inner = document.getElementById('vcf').contentDocument
      .getElementById('visual-check-result');
    pre.textContent = inner ? inner.textContent : '{"probeError": "probe result missing inside srcdoc iframe — page JS may have crashed before the probe ran"}';
  } catch (e) {
    pre.textContent = '{"probeError": "cannot read srcdoc iframe: ' + e.name + '"}';
  }
  document.documentElement.appendChild(pre);
});
"""

# Injected before </body>; runs synchronously once the DOM is parsed and
# writes its findings as JSON into a hidden <pre> we extract from --dump-dom.
PROBE_JS = r"""
(function () {
  var SVG_NS = 'http://www.w3.org/2000/svg';
  function run() {
  function parseRGB(s) {
    var m = /rgba?\(([^)]+)\)/.exec(s || '');
    if (!m) return null;
    var p = m[1].split(',');
    var n = function (i) { var v = parseFloat(p[i]); return isNaN(v) ? 0 : v; };
    return { r: n(0), g: n(1), b: n(2), a: p.length > 3 && !isNaN(parseFloat(p[3])) ? parseFloat(p[3]) : 1 };
  }
  function cls(el) {
    var c = el.className;
    if (c && c.baseVal !== undefined) c = c.baseVal;
    return String(c || '').trim().split(/\s+/)[0];
  }
  function sel(el) {
    var s = el.tagName.toLowerCase();
    if (el.id) return s + '#' + el.id;
    var c = cls(el);
    return c ? s + '.' + c : s;
  }
  // A collapsed panel keeps its geometry while an ancestor's overflow clips it
  // away. Such text is laid out but never seen, so judging its contrast reports
  // defects nobody can look at — and against the wrong backdrop, since the point
  // it claims to occupy is showing something else entirely.
  function clipped(el, r) {
    for (var n = el.parentElement; n && n.nodeType === 1; n = n.parentElement) {
      var cs = getComputedStyle(n);
      if (cs.overflow === 'visible' && cs.overflowX === 'visible' &&
          cs.overflowY === 'visible') continue;
      var pr = n.getBoundingClientRect();
      if (r.right <= pr.left || r.left >= pr.right ||
          r.bottom <= pr.top || r.top >= pr.bottom) return true;
    }
    return false;
  }
  function visible(el) {
    var cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    // A closed <details> skips rendering its contents, but they keep a computed
    // display and a non-zero rect — they look laid out to every check here
    // while occupying a region of the page that is showing something else.
    if (el.closest('details:not([open])') && !el.closest('summary')) return false;
    var r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    return !clipped(el, r);
  }
  function directText(el) {
    var t = '';
    for (var i = 0; i < el.childNodes.length; i++) {
      if (el.childNodes[i].nodeType === 3) t += el.childNodes[i].textContent;
    }
    return t.trim();
  }
  function bgOf(el) {
    // A translucent background must be composited over what shows through it.
    // Returning the raw rgba (e.g. a 6% coral wash) reads as full-strength
    // coral and invents contrast errors that the eye never sees.
    var layers = [];
    for (var node = el; node && node.nodeType === 1; node = node.parentElement) {
      var c = parseRGB(getComputedStyle(node).backgroundColor);
      if (!c || c.a <= 0) continue;
      layers.push(c);
      if (c.a >= 1) break;
    }
    return composite(layers, { r: 255, g: 255, b: 255, a: 1 });
  }
  function composite(layers, base) {
    var out = base;
    for (var i = layers.length - 1; i >= 0; i--) {
      var l = layers[i];
      out = {
        r: l.r * l.a + out.r * (1 - l.a),
        g: l.g * l.a + out.g * (1 - l.a),
        b: l.b * l.a + out.b * (1 - l.a),
        a: 1
      };
    }
    return out;
  }
  // What sits behind a label is whatever is painted under it, which the DOM
  // ancestry only approximates: an absolutely positioned caption sits outside
  // the box it descends from, and an SVG label sits on a sibling <rect>. Hit-
  // test the label's centre instead, and keep the ancestor walk as the fallback
  // for anything the test cannot reach (below the render height, or hidden from
  // hit-testing by pointer-events).
  function stackBackdrop(el) {
    if (!document.elementsFromPoint) return null;
    var r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return null;
    var x = r.left + r.width / 2, y = r.top + r.height / 2;
    if (x < 0 || y < 0 || x > document.documentElement.clientWidth) return null;
    var stack = document.elementsFromPoint(x, y);
    if (!stack || !stack.length) return null;
    var svgSkip = { text: 1, tspan: 1, g: 1, svg: 1, defs: 1, marker: 1 };
    var layers = [];
    for (var i = 0; i < stack.length; i++) {
      var n = stack[i];
      // The element's own background IS the text's backdrop; only its
      // descendants sit at or above the text and must not count as one.
      if (n !== el && el.contains(n)) continue;
      var c;
      if (n.namespaceURI === SVG_NS) {
        if (svgSkip[n.tagName.toLowerCase()]) continue;
        c = parseRGB(getComputedStyle(n).fill);
      } else {
        c = parseRGB(getComputedStyle(n).backgroundColor);
      }
      if (!c || c.a <= 0) continue;
      layers.push(c);
      if (c.a >= 1) break;
    }
    if (!layers.length) return null;
    return composite(layers, { r: 255, g: 255, b: 255, a: 1 });
  }
  function lum(c) {
    function f(x) { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  }
  function ratio(fg, bg) {
    var l1 = lum(fg), l2 = lum(bg);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }
  function rgb(c) { return 'rgb(' + Math.round(c.r) + ',' + Math.round(c.g) + ',' + Math.round(c.b) + ')'; }

  var docEl = document.documentElement;
  var vp = docEl.clientWidth;
  var docW = docEl.scrollWidth;
  var docH = Math.max(document.body ? document.body.scrollHeight : 0, docEl.scrollHeight);

  // 1. horizontal overflow — list root-most offenders (skip nested duplicates)
  var overflowers = [];
  if (docW > vp + 1) {
    var all = document.querySelectorAll('body *');
    for (var i = 0; i < all.length && overflowers.length < 8; i++) {
      var el = all[i];
      if (el.id === 'visual-check-result') continue;
      var r = el.getBoundingClientRect();
      if (r.width <= vp + 1) continue;
      var nested = false;
      var node = el.parentElement;
      while (node) {
        if (node.getBoundingClientRect().width > vp + 1) { nested = true; break; }
        node = node.parentElement;
      }
      if (!nested) overflowers.push(sel(el) + '=' + Math.round(r.width) + 'px');
    }
  }

  // 2. squeezed text columns — many lines tall, only a few characters wide
  var squeezed = [];
  document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,dt,dd,td,th,summary,blockquote').forEach(function (el) {
    if (squeezed.length >= 8 || !visible(el)) return;
    var r = el.getBoundingClientRect();
    var cs = getComputedStyle(el);
    var fs = parseFloat(cs.fontSize) || 16;
    var lh = parseFloat(cs.lineHeight);
    if (isNaN(lh)) lh = 1.2 * fs;
    var lines = r.height / lh;
    if (lines > 6 && r.width < 4 * fs) {
      squeezed.push(sel(el) + ' "' + (el.textContent || '').trim().slice(0, 24) + '…" ' +
        Math.round(r.width) + 'px wide x ~' + Math.round(lines) + ' lines');
    }
  });

  // 3. contrast — every element with direct text, deduped per (fg, bg) pair
  var pairs = {};
  document.querySelectorAll('body *').forEach(function (el) {
    if (el.id === 'visual-check-result') return;
    // WCAG 1.4.3 exempts inactive controls; a greyed-out button is meant to
    // read as unavailable, and darkening it to pass would misreport its state.
    if (el.closest('[disabled], [aria-disabled="true"]')) return;
    var t = directText(el);
    if (!t || !visible(el)) return;
    // SVG text renders in `fill`, not `color`; reading `color` there reports a
    // colour the diagram never paints.
    var cs = getComputedStyle(el);
    var svg = el.namespaceURI === SVG_NS;
    var fg = parseRGB(svg ? cs.fill : cs.color);
    if (!fg) return;
    var bg = stackBackdrop(el) || bgOf(el);
    var a = fg.a;
    var eff = { r: a * fg.r + (1 - a) * bg.r, g: a * fg.g + (1 - a) * bg.g, b: a * fg.b + (1 - a) * bg.b };
    var rr = ratio(eff, bg);
    if (rr >= 4.5) return;
    var key = rgb(eff) + '|' + rgb(bg);
    if (!pairs[key]) {
      pairs[key] = { ratio: Math.round(rr * 100) / 100, fg: rgb(eff), bg: rgb(bg), count: 0,
                     example: sel(el) + ' "' + t.slice(0, 24) + '"' };
    }
    pairs[key].count++;
  });
  var contrast = Object.keys(pairs).map(function (k) { return pairs[k]; })
    .sort(function (a, b) { return a.ratio - b.ratio; }).slice(0, 10);

  var pre = document.createElement('pre');
  pre.id = 'visual-check-result';
  pre.style.display = 'none';
  pre.textContent = JSON.stringify({
    viewport: vp, docW: docW, docH: docH,
    overflowers: overflowers, squeezed: squeezed, contrast: contrast
  });
  docEl.appendChild(pre);
  }
  // Injected before </body>, this would otherwise measure a layout the page has
  // not finished building: its own end-of-body scripts have not run, and text
  // metrics are still settling — enough to read overlapping boxes for elements
  // that never overlap. Wait for load, which still precedes the wrapper's own.
  if (document.readyState === 'complete') run();
  else window.addEventListener('load', run);
})();
"""


def find_browser() -> str | None:
    for candidate in BROWSER_CANDIDATES:
        if candidate and pathlib.Path(candidate).exists():
            return candidate
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def chrome(browser: str, url: str, width: int, height: int, extra: list[str]) -> str:
    """Run headless Chrome, return stdout. Raises on non-zero exit."""
    cmd = [
        browser, "--headless", "--disable-gpu", "--hide-scrollbars",
        # Virtual time lets the wrapper's iframe finish loading and the probe
        # finish running before --dump-dom / --screenshot are taken.
        "--virtual-time-budget=8000",
        f"--window-size={width},{height}", *extra, url,
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"browser exited {proc.returncode}: {proc.stderr[:300]}")
    return proc.stdout


def wrap(target: pathlib.Path, width: int, workdir: pathlib.Path, with_probe: bool) -> pathlib.Path:
    """Inline `target` into an srcdoc iframe exactly `width` px wide."""
    source = target.read_text(encoding="utf-8")
    if with_probe:
        probe_tag = f"<script>{PROBE_JS}</script>"
        source = (
            source.replace("</body>", probe_tag + "</body>", 1)
            if "</body>" in source
            else source + probe_tag
        )
    wrapper = workdir / f"wrapper-{width}-{with_probe}.html"
    wrapper.write_text(
        '<!DOCTYPE html><html><body style="margin:0;background:#fff">'
        f'<iframe id="vcf" srcdoc="{html_mod.escape(source, quote=True)}" '
        f'style="width:{width}px;height:8000px;border:0;display:block"></iframe>'
        f"<script>{WRAPPER_JS}</script>"
        "</body></html>",
        encoding="utf-8",
    )
    return wrapper


def probe(browser: str, target: pathlib.Path, width: int, workdir: pathlib.Path) -> dict:
    """Render `target` at a true `width`-px CSS viewport, return probe JSON."""
    wrapper = wrap(target, width, workdir, with_probe=True)
    dom = chrome(browser, wrapper.resolve().as_uri(), 1400, 8100, ["--dump-dom"])
    match = RESULT_RE.search(dom)
    if not match:
        raise RuntimeError(
            "probe result missing from rendered DOM — page JS may have crashed "
            "before the probe ran (check the browser console)"
        )
    result = json.loads(html_mod.unescape(match.group(1)))
    if "probeError" in result:
        raise RuntimeError(result["probeError"])
    return result


def shoot(
    browser: str, target: pathlib.Path, width: int, doc_height: int, out_png: pathlib.Path,
) -> None:
    height = min(doc_height + 80, MAX_SHOT_HEIGHT)
    with tempfile.TemporaryDirectory(prefix="visual-check-shot-") as tmp:
        wrapper = wrap(target, width, pathlib.Path(tmp), with_probe=False)
        chrome(
            browser, wrapper.resolve().as_uri(),
            max(width, 500), height,  # headless clamps window width to ~500px
            [f"--screenshot={out_png}"],
        )


def assess(result: dict, width: int) -> tuple[list[str], list[str]]:
    """Turn one probe result into ERROR/WARN strings."""
    errors, warns = [], []
    vp, doc_w = result["viewport"], result["docW"]
    if doc_w > vp + 1:
        offenders = ", ".join(result["overflowers"][:5]) or "unknown element"
        errors.append(
            f"[{width}px] horizontal overflow: document is {doc_w}px wide in a "
            f"{vp}px viewport — widest: {offenders}"
        )
    for item in result["squeezed"]:
        errors.append(f"[{width}px] squeezed text column: {item}")
    for pair in result["contrast"]:
        message = (
            f"[{width}px] contrast {pair['ratio']}:1 for {pair['example']} "
            f"({pair['fg']} on {pair['bg']}, x{pair['count']})"
        )
        if pair["ratio"] < 3.0:
            errors.append(message)
        else:
            warns.append(message + " — below WCAG AA 4.5:1")
    return errors, warns


def check_file(
    browser: str, path: pathlib.Path, widths: list[int], shots_dir: pathlib.Path | None,
) -> bool:
    # Findings repeat identically at every width (contrast pairs especially),
    # so dedupe by message and report the widths each was seen at.
    findings: dict[str, tuple[str, set[int]]] = {}  # message -> (severity, widths)
    probe_failures: list[str] = []
    try:
        path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"{path.name}: ERROR cannot read: {e}")
        return False

    for width in widths:
        with tempfile.TemporaryDirectory(prefix="visual-check-") as tmp:
            try:
                result = probe(browser, path, width, pathlib.Path(tmp))
            except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
                probe_failures.append(f"[{width}px] render probe failed: {e}")
                continue
        for severity, messages in (("ERROR", assess(result, width)[0]), ("WARN", assess(result, width)[1])):
            for message in messages:
                key = message.split("] ", 1)[1]
                findings.setdefault(key, (severity, set()))[1].add(width)
        if shots_dir is not None:
            shots_dir.mkdir(parents=True, exist_ok=True)
            out_png = shots_dir / f"{path.stem}-{width}px.png"
            try:
                shoot(browser, path, width, result["docH"], out_png)
            except (RuntimeError, subprocess.TimeoutExpired) as e:
                key = f"screenshot failed: {e}"
                findings.setdefault(key, ("WARN", set()))[1].add(width)

    n_errors = 0
    for message in probe_failures:
        print(f"{path.name}: ERROR {message}")
        n_errors += 1
    for key, (severity, seen) in sorted(
        findings.items(), key=lambda kv: (kv[1][0] != "ERROR", kv[0])
    ):
        at = "/".join(str(w) for w in sorted(seen))
        print(f"{path.name}: {severity.ljust(5)} [{at}px] {key}")
        n_errors += severity == "ERROR"
    if not findings and not probe_failures:
        print(f"{path.name}: OK ({len(widths)} widths rendered)")
    elif n_errors == 0:
        n_warns = sum(1 for s, _ in findings.values() if s == "WARN")
        print(f"{path.name}: OK ({n_warns} warning(s))")
    return n_errors == 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=pathlib.Path)
    parser.add_argument(
        "--widths", default=",".join(str(w) for w in DEFAULT_WIDTHS),
        help="comma-separated viewport widths (default: %(default)s)",
    )
    parser.add_argument(
        "--shots-dir", type=pathlib.Path, default=None,
        help="directory for rendered screenshots (default: a fresh temp dir, printed)",
    )
    parser.add_argument("--no-shots", action="store_true", help="skip screenshots")
    args = parser.parse_args(argv)

    try:
        widths = [int(w) for w in args.widths.split(",") if w.strip()]
    except ValueError:
        print(f"visual-check: invalid --widths {args.widths!r}")
        return 2
    if not widths:
        print("visual-check: no widths given")
        return 2

    browser = find_browser()
    if browser is None:
        print(
            "visual-check: ERROR no Chrome-family browser found — the visual gate "
            "CANNOT run. Install Chrome/Chromium/Edge or set VISUAL_CHECK_BROWSER. "
            "Do not claim the page was visually verified."
        )
        return 2

    shots_dir = None if args.no_shots else (args.shots_dir or pathlib.Path(
        tempfile.mkdtemp(prefix="effective-html-shots-")
    ))
    results = [check_file(browser, p, widths, shots_dir) for p in args.files]
    if shots_dir is not None:
        print(f"visual-check: screenshots in {shots_dir} — open and look at every width")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
