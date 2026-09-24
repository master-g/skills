// Self-check: every example, in English and with CJK labels, draws a frame whose lines share one width.
// Run: bun check.mts (or node)
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { draw } from "./mdxcn.mts";

const examples = JSON.parse(
  readFileSync(new URL("./examples.json", import.meta.url), "utf8")
);
// Independent of frame.mts on purpose, so a broken widthOf cannot grade itself.
const WIDE =
  /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}\u3000-\u303F\uFF01-\uFF60\uFFE0-\uFFE6]|\p{Extended_Pictographic}/u;
const columns = (line: string) =>
  [...line].reduce((sum, char) => sum + (WIDE.test(char) ? 2 : 1), 0);

const ENUMS = new Set([
  "state",
  "sign",
  "type",
  "kind",
  "size",
  "align",
  "days",
]);

function cjk(value: unknown, key = ""): unknown {
  if (ENUMS.has(key)) return value;
  if (typeof value === "string") return `${value}中文`;
  if (Array.isArray(value)) return value.map((item) => cjk(item, key));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([k, v]) => [k, cjk(v, k)])
    );
  }
  return value;
}

function assertFramed(name: string, fenced: string) {
  const lines = fenced.split("\n").slice(1, -1);
  const widths = new Set(lines.map(columns));
  assert.equal(widths.size, 1, `${name}: uneven frame\n${fenced}`);
}

for (const [name, props] of Object.entries(examples)) {
  assertFramed(name, draw(name, props as never));
  assertFramed(`${name} (cjk)`, draw(name, cjk(props) as never, "复盘"));
}

const long = draw("callout", {
  title: "注意",
  body: "p95 超过 800ms 之后，我们在 14:11 回滚了缓存开关，复盘文档还没有写完，需要在周五之前补上根因分析和后续行动项。",
});
assertFramed("callout (long cjk)", long);
assert.ok(
  long.includes("p95 超过 800ms"),
  "wrap keeps the spaces around mixed text"
);

console.log(`ok: ${Object.keys(examples).length} graphs, en + cjk`);
