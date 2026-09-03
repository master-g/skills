#!/usr/bin/env node
/* Batch KaTeX renderer for katex.py prerender.
 *
 * Reads a JSON array from stdin:  [{"tex": "...", "display": true|false}, ...]
 * Writes a JSON array to stdout with the rendered HTML strings in the same
 * order. Uses the vendored UMD katex.min.js via require().
 *
 * Never throws on a TeX error: a bad formula renders as KaTeX's red error
 * text (throwOnError:false) so one typo can't block the whole page.
 */

const path = require("path");
const katex = require(
  path.join(__dirname, "..", "assets", "katex", "katex.min.js")
);

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
  let jobs;
  try {
    jobs = JSON.parse(input);
  } catch (err) {
    process.stderr.write(`katex_prerender: bad JSON input: ${err.message}\n`);
    process.exit(1);
  }
  const rendered = jobs.map((job) =>
    katex.renderToString(String(job.tex), {
      displayMode: Boolean(job.display),
      throwOnError: false,
      strict: "ignore",
      output: "html",
    })
  );
  process.stdout.write(JSON.stringify(rendered));
});
