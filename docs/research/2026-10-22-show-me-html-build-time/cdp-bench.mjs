// One headless Chrome, CDP over Node's built-in WebSocket: 3 probe loads + 4 full-page screenshots.
// usage: node cdp-bench.mjs <dir with probe.html and page.html> [block-fonts]
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const dir = process.argv[2];
const block = process.argv[3] === "block-fonts";
const t0 = performance.now();
const args = [
  "--headless=new",
  "--remote-debugging-port=0",
  "--hide-scrollbars",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "cdp-bench-"))}`,
];
if (block)
  args.push(
    "--host-resolver-rules=MAP fonts.googleapis.com ~NOTFOUND, MAP fonts.gstatic.com ~NOTFOUND"
  );
const chrome = spawn(
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  [...args, "about:blank"]
);
const wsUrl = await new Promise((ok) => {
  let buf = "";
  chrome.stderr.on("data", (d) => {
    buf += d;
    const m = buf.match(/ws:\/\/\S+/);
    if (m) ok(m[0]);
  });
});
const ws = new WebSocket(wsUrl);
await new Promise((r) => ws.addEventListener("open", r));
let seq = 0;
const pending = new Map();
const events = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)(m.result ?? m);
    pending.delete(m.id);
  } else if (m.method) events.push(m);
});
const send = (method, params = {}, sessionId) =>
  new Promise((ok) => {
    const id = ++seq;
    pending.set(id, ok);
    ws.send(JSON.stringify({ id, method, params, sessionId }));
  });
const { targetId } = await send("Target.createTarget", { url: "about:blank" });
const { sessionId } = await send("Target.attachToTarget", {
  targetId,
  flatten: true,
});
const S = (m, p) => send(m, p, sessionId);
await S("Page.enable");
await S("Runtime.enable");
await S("Emulation.setEmulatedMedia", {
  features: [{ name: "prefers-reduced-motion", value: "reduce" }],
});
const tStart = performance.now();
const load = async (file, w, h = 900) => {
  await S("Emulation.setDeviceMetricsOverride", {
    width: w,
    height: h,
    deviceScaleFactor: 1,
    mobile: false,
  });
  events.length = 0;
  await S("Page.navigate", { url: pathToFileURL(join(dir, file)).href });
  while (!events.some((e) => e.method === "Page.loadEventFired"))
    await new Promise((r) => setTimeout(r, 20));
};
const timings = [];
for (const w of [500, 1024, 1280]) {
  const t = performance.now();
  await load("probe.html", w);
  let title = "";
  while (!title.startsWith("PROBE|")) {
    await new Promise((r) => setTimeout(r, 100));
    title = (
      await S("Runtime.evaluate", {
        expression: "document.title",
        returnByValue: true,
      })
    ).result.value;
  }
  timings.push(`probe ${w}: ${((performance.now() - t) / 1000).toFixed(2)}s`);
}
for (const theme of ["light", "dark"]) {
  const { identifier } = await S("Page.addScriptToEvaluateOnNewDocument", {
    source: `try{localStorage.setItem("show-me-theme","${theme}")}catch(e){}`,
  });
  for (const w of [500, 1280]) {
    const t = performance.now();
    await load("page.html", w);
    const h = (
      await S("Runtime.evaluate", {
        expression: "document.documentElement.scrollHeight",
        returnByValue: true,
      })
    ).result.value;
    await S("Emulation.setDeviceMetricsOverride", {
      width: w,
      height: Math.min(h, 16000),
      deviceScaleFactor: 1,
      mobile: false,
    });
    await new Promise((r) => setTimeout(r, 300));
    const lines = (
      await S("Runtime.evaluate", {
        expression: "document.querySelectorAll('#loc line').length",
        returnByValue: true,
      })
    ).result.value;
    const shot = await S("Page.captureScreenshot", { format: "png" });
    writeFileSync(
      join(dir, `cdp-${theme}-${w}.png`),
      Buffer.from(shot.data, "base64")
    );
    timings.push(
      `shot ${theme} ${w}: ${((performance.now() - t) / 1000).toFixed(2)}s, chart lines ${lines}`
    );
  }
  await S("Page.removeScriptToEvaluateOnNewDocument", { identifier });
}
console.log(timings.join("\n"));
console.log(
  `startup ${((tStart - t0) / 1000).toFixed(2)}s, work ${((performance.now() - tStart) / 1000).toFixed(2)}s, total ${((performance.now() - t0) / 1000).toFixed(2)}s, block-fonts=${block}`
);
chrome.kill();
process.exit(0);
