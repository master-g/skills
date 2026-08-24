# Design system

The shared visual language of all 20 templates. Use this when composing sections, components, or whole pages that the chosen template doesn't already provide. The goal is that anything you build from this file looks native next to template-derived parts.

## Canonical tokens

Use this `:root` block for new compositions. (Templates vary slightly in gray naming — `--gray-150` vs `--gray-50` — but the hex values are identical across all 20 files. When extending an existing template, follow *its* names.)

```css
:root {
  --ivory:  #FAF9F5;   /* page background */
  --white:  #FFFFFF;   /* card / panel surface */
  --slate:  #141413;   /* primary text, strong borders */
  --clay:   #D97757;   /* THE accent — links, active states, one highlight per view */
  --clay-d: #B85C3E;   /* clay hover/pressed */
  --oat:    #E3DACC;   /* warm secondary surface (tags, soft fills) */
  --olive:  #788C5D;   /* success / additions / positive */
  --rust:   #B04A3F;   /* danger / deletions / negative */
  --gray-100: #F0EEE6; /* subtle fill (code bg, zebra rows) */
  --gray-200: #E6E3DA; /* slightly stronger fill */
  --gray-300: #D1CFC5; /* hairline borders */
  --gray-500: #87867F; /* secondary text, captions */
  --gray-700: #3D3D3A; /* body text on light fills */
  --serif: ui-serif, Georgia, "Times New Roman", serif;
  --sans:  system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono:  ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
```

System font stacks only — never load a web font. They render instantly, work offline, and look right on every OS.

## Color discipline

This is what separates the style from generic AI output:

- **Clay is scarce.** One accent moment per view region: the active nav item, the recommended card's border, the key number. If clay appears more than ~3 times in a viewport, the page has lost its hierarchy.
- **Olive and rust are semantic only** — added/removed, pass/fail, up/down. Never decorative.
- **Grays do the work.** Hierarchy comes from the warm gray ramp (500 for captions, 700 for body, slate for emphasis), not from color.
- **No gradients, no glassmorphism, no colored shadows.** Shadows are neutral and quiet: `0 1px 2px rgba(20,20,19,.06)` resting, `0 4px 10px rgba(20,20,19,.08)` raised, `0 12px 28px rgba(20,20,19,.12)` floating/modal.
- **Inline fills must survive dark surfaces.** Any element carrying a background fill (`code` chips, tags, badges) needs an explicit variant inside dark cards and code panels: dark-elevated fill (`#3c3934`-range) with on-dark text — the global light fill inherits light text on dark surfaces and becomes unreadable. Text/fill contrast stays ≥ 4.5:1 everywhere; verify with `scripts/visual_check.py`, never by eye.

## Typography

| Role | Face | Treatment |
|---|---|---|
| Display heading (h1) | serif | weight 500, `clamp(28px, 4vw, 44px)`, line-height ~1.1, letter-spacing −0.015em; an `<em>` inside may take clay for one keyword |
| Section heading (h2) | serif | weight 500, 22–26px |
| Eyebrow / kicker | mono | 11–12px, uppercase, letter-spacing 0.1em, gray-500; often preceded by a 24px clay dash (`::before` with `width:24px; height:1.5px; background:var(--clay)`) |
| Body | sans | 14–16.5px, line-height 1.55, slate or gray-700 |
| Caption / meta | sans or mono | 12–13px, gray-500 |
| Code | mono | 12.5–13.5px on gray-100, radius 8px |

The serif/sans/mono triad is the voice of the system: serif says "considered", mono says "technical", sans carries the load. Don't add weights beyond 400/500/600.

## Layout & spacing

- **Wrap**: `max-width: 920–1120px; margin: 0 auto; padding: 0 32px` (24px on mobile). Reading-heavy pages go narrower (760–860px measure).
- **Section rhythm**: 56–72px between major sections; 20–28px between heading and content.
- **Borders**: `1.5px solid var(--gray-300)` is the standard hairline. Emphasis = switch color to slate, not width to 3px.
- **Radius**: 6px small (tags), 8–10px standard (buttons, code), 12–14px cards/panels. Pills are `999px`.
- **Two-column shell** (review pages, reports, explainers): `grid-template-columns: minmax(0,1fr) 280px; gap:48px`, sidebar `position:sticky; top:24px`, single breakpoint collapses to `1fr` at **880–960px**. One breakpoint is usually enough — these are tools, not marketing sites.
- Anchored sections need `scroll-margin-top: 24px` (plus `html{scroll-behavior:smooth}`) so TOC jumps don't bury headings.

## Component idioms

- **Card**: white surface, hairline border, 12px radius, 18–24px padding. Recommended/active card: border-color slate or clay + floating shadow — not a background color change.
- **Tag/pill**: mono 10–11px uppercase, 2–4px × 8–10px padding, oat or gray-100 fill, 6px or full radius.
- **Table**: no vertical rules; hairline row separators; mono for numbers; header row in eyebrow style. Zebra with gray-100 only if rows > ~8.
- **Stat tile**: big serif or mono number (28–40px), eyebrow label above, optional olive/rust delta below.
- **Callout**: gray-100 fill (or oat for warm emphasis), 3px clay left border, 14–18px padding. One per screenful at most.
- **Diff lines**: additions `rgba(120,140,93,.12)` bg + olive `+`; deletions `rgba(176,74,63,.10)` bg + rust `−`; mono throughout. See template 03.
- **Inline SVG diagrams**: hairline strokes (1.5px), token colors, mono 10–11px labels, nodes as rounded rects with white fill. Hand-drawn-adjacent, never clip-art. See templates 10/13/16.

## Motion

Subtle and purposeful: 120–280ms transitions, `ease` or a custom cubic-bezier, on border-color / background / transform only. `prefers-reduced-motion` matters for anything that auto-animates. No entrance animations on content pages — motion belongs to feedback (hover, toggle, completion), not decoration.

## Responsive & robustness

- Test mentally at 390px and 1280px; the single breakpoint should handle both.
- **Bare `1fr`/`auto` tracks assume short sample content — real content breaks them.** Grid tracks holding user-length content use `minmax(0, 1fr)`; grid/flex children get `min-width: 0`; long mono strings (file paths, identifiers) get `overflow-wrap: anywhere` or a `max-width` in `ch`. Without this, one long real-world string squeezes sibling columns to a vertical strip or pushes the whole page past the viewport.
- `box-sizing: border-box` on `*`, `margin: 0` on body — every template starts this way.
- Images: avoid external images entirely; the system's answer to illustration is inline SVG.
- If the page is likely to be printed (reports, plans), a minimal `@media print` hiding interactive chrome is a nice touch — not required.
