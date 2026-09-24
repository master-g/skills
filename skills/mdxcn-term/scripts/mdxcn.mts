// Usage: echo '<props json>' | node mdxcn.mts <graph> [TITLE]
// Prints the framed figure inside a ``` fence. Props match mdxcn's React API.
import * as g from "./graphs.mts";

export const GRAPHS: Record<string, (props: never) => string> = {
  bars: g.asciiBars,
  bullet: g.asciiBullet,
  callout: g.asciiCallout,
  cells: g.asciiCells,
  changelog: g.asciiChangelog,
  check: g.asciiCheck,
  compare: g.asciiCompare,
  diff: g.asciiDiff,
  funnel: g.asciiFunnel,
  gantt: g.asciiGantt,
  invoice: g.asciiInvoice,
  kpi: g.asciiKpi,
  matrix: g.asciiMatrix,
  meter: g.asciiMeter,
  quote: g.asciiQuote,
  rank: g.asciiRank,
  sheet: g.asciiSheet,
  slope: g.asciiSlope,
  spark: g.asciiSpark,
  spec: g.asciiSpec,
  stack: g.asciiStack,
  stat: g.asciiStat,
  steps: g.asciiSteps,
  table: g.asciiTable,
  timeline: g.asciiTimeline,
  tree: g.asciiTree,
  uptime: g.asciiUptime,
  waffle: g.asciiWaffle,
  waterfall: g.asciiWaterfall,
};

export function draw(
  name: string,
  props: Record<string, unknown>,
  title?: string
) {
  const fn = GRAPHS[name];
  if (!fn)
    throw new Error(
      `unknown graph "${name}". one of: ${Object.keys(GRAPHS).join(", ")}`
    );
  return (
    "```\n" + fn({ ...props, ...(title ? { title } : {}) } as never) + "\n```"
  );
}

if (import.meta.main) {
  const [name, title] = process.argv.slice(2);
  if (!name) {
    console.error(
      `usage: echo '<json>' | node mdxcn.mts <graph> [TITLE]\ngraphs: ${Object.keys(GRAPHS).join(", ")}`
    );
    process.exit(2);
  }
  let input = "";
  for await (const chunk of process.stdin) input += chunk;
  try {
    console.log(draw(name, JSON.parse(input), title));
  } catch (error) {
    console.error(`mdxcn: ${(error as Error).message}`);
    process.exit(1);
  }
}
