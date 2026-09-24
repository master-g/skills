const MIN_INNER = 48;

// Terminal columns: CJK, fullwidth and emoji take 2, everything else 1.
// ponytail: ambiguous-width glyphs (● │ █ …) count as 1; combining marks are not handled.
const WIDE =
  /[\u1100-\u115F\u2E80-\u303E\u3041-\u33FF\u3400-\u4DBF\u4E00-\u9FFF\uA000-\uA4CF\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFF60\uFFE0-\uFFE6\u{1F300}-\u{1F64F}\u{1F900}-\u{1F9FF}\u{20000}-\u{3FFFD}]/u;

function charWidth(char: string) {
  return WIDE.test(char) ? 2 : 1;
}

function widthOf(text: string) {
  let width = 0;
  for (const char of text) width += charWidth(char);
  return width;
}

// Cut to at most `size` columns without splitting a wide character.
function sliceWidth(text: string, size: number, fromEnd = false) {
  const chars = [...text];
  if (fromEnd) chars.reverse();
  let width = 0;
  const kept: string[] = [];
  for (const char of chars) {
    width += charWidth(char);
    if (width > size) break;
    kept.push(char);
  }
  if (fromEnd) kept.reverse();
  return kept.join("");
}

function padEnd(text: string, size: number) {
  const extra = size - widthOf(text);
  if (extra >= 0) {
    return text + " ".repeat(extra);
  }

  return padEnd(sliceWidth(text, size), size);
}

function padStart(text: string, size: number) {
  const extra = size - widthOf(text);
  if (extra >= 0) {
    return " ".repeat(extra) + text;
  }

  return padStart(sliceWidth(text, size, true), size);
}

function dash(count: number) {
  return "-".repeat(Math.max(0, count));
}

function wrapText(text: string, width = 56): string[] {
  // A token is a run of narrow characters or one wide character; keep the source spacing between tokens.
  const tokens = [
    ...text.matchAll(/(\s*)([\u2E80-\uFFE6]|[^\s\u2E80-\uFFE6]+)/gu),
  ];
  if (tokens.length === 0) {
    return [];
  }

  const lines: string[] = [];
  let current = "";

  for (const [, space, word] of tokens) {
    const next = current + (current && space ? " " : "") + word;
    if (current && widthOf(next) > width) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }

  if (current) {
    lines.push(current);
  }

  return lines;
}

function frameAscii(
  title: string | undefined,
  lines: string[],
  minInner = MIN_INNER
) {
  const caption = title?.trim() ? `[ ${title.trim().toUpperCase()} ]` : "";
  const contentWidth = Math.max(0, ...lines.map(widthOf));
  const inner = Math.max(
    minInner,
    contentWidth,
    caption ? widthOf(caption) + 4 : 0
  );
  const span = inner + 2;
  const empty = `| ${" ".repeat(inner)} |`;
  const body = lines.map((line) => `| ${padEnd(line, inner)} |`);
  const top = caption
    ? (() => {
        const label = ` ${caption} `;
        const leftover = Math.max(0, span - widthOf(label));
        const left = Math.floor(leftover / 2);
        const right = leftover - left;
        return `+${dash(left)}${label}${dash(right)}+`;
      })()
    : `+${dash(span)}+`;

  return [top, empty, ...body, empty, `+${dash(span)}+`].join("\n");
}

function rule(size: number) {
  return dash(size);
}

function fillTrack(filled: number, total: number, on = "=", off = "-") {
  const count = Math.min(total, Math.max(0, filled));
  return on.repeat(count) + off.repeat(total - count);
}

function col(text: string, size: number, align: "left" | "right" = "left") {
  return align === "right" ? padStart(text, size) : padEnd(text, size);
}

function colWidth(values: string[]) {
  return Math.max(0, ...values.map(widthOf));
}

function fence(ascii: string) {
  return `\`\`\`\n${ascii}\n\`\`\``;
}

export {
  col,
  colWidth,
  dash,
  fence,
  fillTrack,
  frameAscii,
  padEnd,
  padStart,
  rule,
  widthOf,
  wrapText,
};
export { MIN_INNER };
