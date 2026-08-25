import mermaid from "mermaid";

function getMermaidTheme(): "default" | "dark" {
  return document.documentElement.classList.contains("dark")
    ? "dark"
    : "default";
}

// CJK-capable font stack for diagram text; mermaid's default ("trebuchet ms")
// has no CJK glyphs and Chinese labels fall back inconsistently.
const FONT_FAMILY =
  '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif';

async function renderMermaid() {
  closeOverlay();
  mermaid.initialize({
    startOnLoad: false,
    theme: getMermaidTheme(),
    fontFamily: FONT_FAMILY,
  });

  document.querySelectorAll<HTMLElement>("pre.mermaid").forEach((el) => {
    if (el.dataset.source) {
      // mermaid.run() replaces the element's content with the rendered SVG, so
      // a re-render must restore the source first — otherwise mermaid parses
      // its own SVG output and renders a syntax-error diagram.
      el.removeAttribute("data-processed");
      el.textContent = el.dataset.source;
      el.style.removeProperty("display");
    } else {
      // First pass: stash the original source so theme switches can restore it.
      el.dataset.source = el.textContent ?? "";
    }
  });

  await mermaid.run({ querySelector: "pre.mermaid" });
}

// --- Click-to-zoom overlay ------------------------------------------------

let overlay: HTMLDivElement | null = null;

function openOverlay(svg: SVGSVGElement) {
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "diagram-overlay";
    const content = document.createElement("div");
    content.className = "diagram-overlay-content";
    overlay.appendChild(content);
    overlay.addEventListener("click", closeOverlay);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeOverlay();
    });
    document.body.appendChild(overlay);
  }
  const clone = svg.cloneNode(true) as SVGSVGElement;
  const box = svg.viewBox?.baseVal;
  clone.removeAttribute("width");
  clone.style.maxWidth = "none";
  clone.style.height = "auto";
  // Enlarge beyond the inline render, capped to the viewport.
  clone.style.width = box?.width
    ? `${Math.round(Math.min(box.width * 1.6, window.innerWidth * 0.92))}px`
    : "92vw";
  overlay.querySelector(".diagram-overlay-content")?.replaceChildren(clone);
  overlay.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeOverlay() {
  if (!overlay?.classList.contains("open")) return;
  overlay.classList.remove("open");
  document.body.style.overflow = "";
}

// Delegated, so it keeps working after theme re-renders replace the SVGs.
document.addEventListener("click", (e) => {
  const pre = (e.target as HTMLElement).closest?.("pre.mermaid");
  const svg = pre?.querySelector("svg");
  if (svg && svg.getAttribute("aria-roledescription") !== "error")
    openOverlay(svg);
});

document.addEventListener("DOMContentLoaded", renderMermaid);
window.addEventListener("theme-changed", renderMermaid);
