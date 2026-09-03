#!/usr/bin/env python3
r"""Mechanical review gate for effective-html outputs.

Usage: python3 check.py path/to/output.html [more.html ...]

Checks each file for:
  ERROR  - external resource loads (script/link/img/iframe src, CSS url()/@import)
  ERROR  - leftover placeholders (lorem ipsum, [Insert ...])
  ERROR  - template sample-data leakage ("Acme")
  ERROR  - missing viewport meta / <title> / lang attribute
  ERROR  - missing <meta charset> (without it CJK text and math glyphs garble)
  WARN   - raw TeX math (\frac, \sqrt, $$...$$, ...) with no KaTeX assets —
           run scripts/katex.py, unless the page is showing TeX source as content
  WARN   - [DATA NEEDED: ...] gap markers (intentional, but must be surfaced to the user)
  WARN   - TBD/TODO/FIXME markers (fine as real content, e.g. a diff or task board)
  WARN   - {{...}} placeholder-style syntax (prompt slot / shown template — or a forgotten placeholder)
  WARN   - JS runtime network calls (fetch/WebSocket/XHR/sendBeacon) breaking self-containment
  WARN   - lang/CJK mismatch (Chinese page not declaring lang="zh-...")
  WARN   - console.log leftovers, very small file
  WARN   - family-scoped Claude technical-document language drift

Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
import re
import sys
import pathlib

# Resource-loading attributes that must not point at the network.
# <a href> is deliberately not matched: outbound links are fine, loads are not.
EXTERNAL_RES = re.compile(
    r'(?:<(?:script|img|iframe|video|audio|source|embed|object)\b[^>]*\bsrc\s*=\s*["\'](?:https?:)?//'
    r'|<link\b[^>]*\bhref\s*=\s*["\'](?:https?:)?//'
    r'|url\(\s*["\']?(?:https?:)?//'
    r'|@import\s+["\'](?:https?:)?//)',
    re.IGNORECASE,
)

PLACEHOLDERS = [
    (re.compile(r"lorem ipsum", re.IGNORECASE), "lorem ipsum filler"),
    (re.compile(r"\[(?:insert|your|add)\b[^\]]{0,60}\]", re.IGNORECASE), "[Insert ...] style placeholder"),
]

SAMPLE_DATA = re.compile(r"\bAcme\b")
DATA_NEEDED = re.compile(r"\[DATA NEEDED:[^\]]*\]")

# TBD/TODO/FIXME is WARN not ERROR: it is often real content (a shown diff, a
# task board), and forcing "fix every ERROR" would push editing the user's data.
TODO_MARKER = re.compile(r"\b(?:TBD|TODO|FIXME|XXX)\b")

# {{...}} is WARN not ERROR: it is often legit content — a prompt-tuner slot,
# or template syntax shown in a code sample — not a forgotten placeholder.
# The (?<![$=]) lookbehind excludes GitHub Actions `${{ }}` and JSX `={{ }}`,
# which are always code idioms, never leftover placeholders.
PLACEHOLDER_BRACE = re.compile(r"(?<![$=])\{\{[^}]{1,60}\}\}")

# JS-initiated network I/O also breaks self-containment; regex-level heuristic,
# WARN not ERROR because string literals in displayed code samples can match.
JS_NETWORK = re.compile(
    r"(?:\bfetch\s*\(\s*[\"'`]https?://"
    r"|new\s+(?:WebSocket|EventSource)\s*\(\s*[\"'`]"
    r"|\bXMLHttpRequest\b"
    r"|navigator\.sendBeacon\s*\()"
)

# Raw TeX constructs that should have gone through scripts/katex.py. WARN not
# ERROR: pages ABOUT TeX legitimately show its source as content, and JS code
# samples can contain "$$" or backslash sequences.
RAW_TEX = re.compile(
    r"(?:\\frac\{|\\sqrt\{|\\sum_|\\int_|\\prod_|\\lim_"
    r"|\\begin\{(?:equation|align|gather|math)\*?\}"
    r"|\$\$[^$\n]{1,200}\$\$)"
)
# Rendered math is marked by class="katex"; vendored assets contain "KaTeX".
# Un-rendered math-tex spans and un-spliced placeholders intentionally do NOT
# match, so forgetting to run katex.py still warns.
KATEX_MARKER = re.compile(r"katex", re.IGNORECASE)

ACTIVE_CLAUDE_FAMILIES = {
    "approach-comparison",
    "visual-directions",
    "code-review",
    "code-understanding",
    "design-system-reference",
    "component-variants",
    "status-report",
    "incident-report",
    "technical-explainer",
    "implementation-plan",
    "pr-writeup",
}
CLAUDE_TOKEN_ROLES = {
    "--canvas": "#faf9f5",
    "--surface-card": "#efe9de",
    "--surface-dark": "#181715",
    "--coral": "#cc785c",
}
GRADIENT = re.compile(r"\b(?:linear|radial|conic)-gradient\s*\(", re.IGNORECASE)
GLASS_EFFECT = re.compile(r"\bbackdrop-filter\s*:", re.IGNORECASE)
DROP_SHADOW = re.compile(r"\bfilter\s*:[^;]*drop-shadow\s*\(", re.IGNORECASE)
BOX_SHADOW = re.compile(r"\bbox-shadow\s*:\s*([^;]+)", re.IGNORECASE)


def meta_content(text: str, wanted_name: str) -> str | None:
    """Read a meta value without assuming attribute order."""
    for tag in re.findall(r"<meta\b[^>]*>", text, re.IGNORECASE):
        attributes = dict(
            (name.lower(), value)
            for name, _, value in re.findall(
                r"""([:\w-]+)\s*=\s*(["'])(.*?)\2""",
                tag,
                re.DOTALL,
            )
        )
        if attributes.get("name", "").lower() == wanted_name.lower():
            return attributes.get("content")
    return None


def has_heavy_shadow(text: str) -> bool:
    """Flag large blurred shadows while allowing restrained hairline depth."""
    for declaration in BOX_SHADOW.findall(text):
        lengths = []
        for value in re.findall(r"(-?\d+(?:\.\d+)?)px", declaration):
            try:
                lengths.append(abs(float(value)))
            except ValueError:  # regex should only yield floats; skip anything odd
                continue
        if lengths and max(lengths) > 18:
            return True
    return False


def claude_design_warnings(text: str) -> list[str]:
    family = meta_content(text, "effective-html-family")
    if family not in ACTIVE_CLAUDE_FAMILIES:
        return []

    warnings = []
    missing_roles = []
    for role, value in CLAUDE_TOKEN_ROLES.items():
        assignment = re.compile(
            rf"{re.escape(role)}\s*:\s*{re.escape(value)}\b",
            re.IGNORECASE,
        )
        if not assignment.search(text):
            missing_roles.append(f"{role}: {value}")
    if missing_roles:
        warnings.append(
            f"Claude-language drift ({family}): missing canonical token role(s): "
            + ", ".join(missing_roles)
            + " — inspect before delivery; a material-driven deviation may be accepted"
        )

    if not re.search(r"@media\b", text, re.IGNORECASE):
        warnings.append(
            f"Claude-language drift ({family}): no responsive @media treatment found "
            "— inspect desktop and mobile before delivery"
        )

    decorative_effects = []
    if GRADIENT.search(text):
        decorative_effects.append("gradient")
    if GLASS_EFFECT.search(text):
        decorative_effects.append("backdrop-filter")
    if DROP_SHADOW.search(text):
        decorative_effects.append("drop-shadow")
    if has_heavy_shadow(text):
        decorative_effects.append("heavy box-shadow")
    if decorative_effects:
        warnings.append(
            f"Claude-language drift ({family}): decorative effect(s) found: "
            + ", ".join(decorative_effects)
            + " — prefer flat surfaces and restrained depth unless the material requires it"
        )

    return warnings


def check(path: pathlib.Path) -> bool:
    errors, warns = [], []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"{path}: ERROR cannot read: {e}")
        return False

    for m in EXTERNAL_RES.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        errors.append(f"external resource load at line {line}: {m.group(0)[:70]!r}")

    for pattern, label in PLACEHOLDERS:
        hits = pattern.findall(text)
        if hits:
            errors.append(f"{label} x{len(hits)}: first = {hits[0][:60]!r}")

    n_acme = len(SAMPLE_DATA.findall(text))
    if n_acme:
        errors.append(
            f'"Acme" appears {n_acme}x — template sample data leaked '
            f"(ignore only if the content is genuinely about an Acme)"
        )

    if not re.search(r'<meta[^>]+name\s*=\s*["\']viewport', text, re.IGNORECASE):
        errors.append("missing <meta name=viewport>")
    if not re.search(r"<title>[^<]+</title>", text, re.IGNORECASE):
        errors.append("missing or empty <title>")
    if not re.search(r'<html[^>]+lang\s*=', text, re.IGNORECASE):
        errors.append("missing lang attribute on <html>")

    if not re.search(r'<meta[^>]+charset\s*=', text, re.IGNORECASE):
        errors.append(
            "missing <meta charset=...> — without it browsers may mis-decode the "
            "file (CJK text and math glyphs garble); templates all ship utf-8"
        )

    m_lang = re.search(r'<html[^>]+lang\s*=\s*["\']?([A-Za-z-]+)', text, re.IGNORECASE)
    n_cjk = len(re.findall(r"[一-鿿]", text))
    if m_lang and n_cjk >= 50 and not m_lang.group(1).lower().startswith("zh"):
        warns.append(
            f'page has {n_cjk} CJK characters but lang="{m_lang.group(1)}" — '
            f'Chinese pages should declare lang="zh-CN"'
        )

    gaps = DATA_NEEDED.findall(text)
    if gaps:
        warns.append(f"{len(gaps)} [DATA NEEDED] gap(s) remain — surface these to the user: {gaps[:3]}")
    n_todo = len(TODO_MARKER.findall(text))
    if n_todo:
        warns.append(
            f"TBD/TODO/FIXME marker x{n_todo} — fine if it is real content "
            f"(a diff, a task board); a placeholder you wrote is not"
        )
    n_brace = len(PLACEHOLDER_BRACE.findall(text))
    if n_brace:
        warns.append(
            "{{...}} placeholder-style syntax x" + str(n_brace) +
            " — fine if it is a prompt slot or shown template/code; "
            "fill it if you forgot to"
        )
    for m in JS_NETWORK.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        warns.append(f"possible JS network call at line {line}: {m.group(0)[:50]!r} — self-contained pages must not load from the network at runtime")
    n_tex = len(RAW_TEX.findall(text))
    if n_tex and not KATEX_MARKER.search(text):
        warns.append(
            f"raw TeX math x{n_tex} but no KaTeX in the page — render it with "
            f"scripts/katex.py (prerender or inline); fine only if the page "
            f"shows TeX source as content"
        )
    if "console.log" in text:
        warns.append("console.log leftover in shipped page")
    if len(text) < 2000:
        warns.append(f"file is only {len(text)} bytes — suspiciously small for a finished page")
    warns.extend(claude_design_warnings(text))

    for e in errors:
        print(f"{path.name}: ERROR {e}")
    for w in warns:
        print(f"{path.name}: WARN  {w}")
    if not errors and not warns:
        print(f"{path.name}: OK")
    elif not errors:
        print(f"{path.name}: OK ({len(warns)} warning(s))")
    return not errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    results = [check(pathlib.Path(p)) for p in argv[1:]]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
