#!/usr/bin/env node
/* math.mjs 页面.html —— 把页面里的 LaTeX 公式编译成 MathML，就地改写。由 build.py 调用。

   定界符：行内 \( … \) 或 $ … $（pandoc 规则：开 $ 后、闭 $ 前不能是空白，闭 $ 后不能紧跟数字，
   于是「$5 和 $8」不会被当成公式；内容含中文且不在 \text{} 里的也不算）；块级 \[ … \] 或 $$ … $$。
   <pre> <code> <script> <style> <math> 内部不碰。
   块级公式包进 <span class="math-display">：span 在 <p> 里也合法，窄栏里横向滚动而不是撑破版心。
   编译产物带 <annotation encoding="application/x-tex">，保留 LaTeX 源便于复查。 */
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const temml = require("../assets/vendor/temml/temml.cjs");
const CSS = readFileSync(
  new URL("../assets/vendor/temml/Temml-Local.css", import.meta.url),
  "utf8"
)
  .replace(/@font-face\s*\{[^}]*\}/g, "") // 外链 woff2：页面必须离线可开
  .replace(/^math \{[\s\S]*?\}\n/m, ""); // 字体栈由 tufte.css 统一给

const file = process.argv[2];
if (!file) {
  console.error("用法：math.mjs 页面.html");
  process.exit(2);
}
let html = readFileSync(file, "utf8");
const SKIP = /(<(pre|code|script|style|math)\b[\s\S]*?<\/\2\s*>)/g;
const count = { inline: 0, block: 0 };
const errors = [];
const warns = [];
const CJK = /[　-〿一-鿿＀-￯]/;

// HTML 源码里 < > & 必须写成实体，TeX 要的是字符本身
const unescape = (t) =>
  t.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");

const visible = (t) =>
  t.replace(/\\[a-zA-Z]+|\\./g, "").replace(/[{}\s^_&]/g, "").length;

const render = (tex, display) => {
  tex = unescape(tex.trim());
  count[display ? "block" : "inline"]++;
  const out = temml.renderToString(tex, {
    displayMode: display,
    throwOnError: false,
    annotate: true,
  });
  const short = tex.length > 60 ? tex.slice(0, 60) + "…" : tex;
  if (/class="temml-error"|color:#b22222|merror/.test(out)) errors.push(short);
  // 渲染宽度约等于「可见字符数 × 10px」：去掉命令名、花括号、上下标符号后计数（2304.10557 实测校准）。
  // 正文栏约 616px，块级公式单行超过约 55 个可见字符放不下。
  if (display && Math.max(...tex.split(/\\\\/).map(visible)) > 55)
    warns.push(`块级公式过长，用 aligned 在 = 或 + 前断行：${short}`);
  // 行内 MathML 不会自动断行；超过约 25 个可见字符在手机上会撑宽页面，窄屏下改为可横向滚动
  if (!display && visible(tex) > 25)
    return `<span class="math-inline-long">${out}</span>`;
  return display ? `<span class="math-display">${out}</span>` : out;
};

/* 单 $ 扫描：被拒的候选只跳过开 $，不吞后文。与 build.py 的 single_dollar_spans 同一套规则。 */
const singleDollar = (s) => {
  let out = "",
    i = 0;
  while (i < s.length) {
    const a = s.indexOf("$", i);
    if (a < 0) break;
    const openOk =
      !(a && "\\$".includes(s[a - 1])) &&
      a + 1 < s.length &&
      !/[\s$]/.test(s[a + 1]);
    let b = openOk ? s.indexOf("$", a + 1) : -1;
    while (b > 0 && /[\s\\]/.test(s[b - 1])) b = s.indexOf("$", b + 1);
    const inner = b > 0 ? s.slice(a + 1, b) : "";
    const ok =
      b > 0 &&
      !inner.includes("\n") &&
      !/\d/.test(s[b + 1] || "") &&
      !CJK.test(inner.replace(/\\text\{[^}]*\}/g, ""));
    if (ok) {
      out += s.slice(i, a) + render(inner, false);
      i = b + 1;
    } else {
      out += s.slice(i, a + 1);
      i = a + 1;
    }
  }
  return out + s.slice(i);
};

html = html
  .split(SKIP)
  .map((seg, i) => {
    if (i % 3 === 1) return seg; // 跳过块本体
    if (i % 3 === 2) return ""; // 捕获的标签名
    seg = seg
      .replace(/\$\$([\s\S]+?)\$\$/g, (_, t) => render(t, true))
      .replace(/\\\[([\s\S]+?)\\\]/g, (_, t) => render(t, true))
      .replace(/\\\(([\s\S]+?)\\\)/g, (_, t) => render(t, false));
    return singleDollar(seg);
  })
  .join("");

if ((count.inline || count.block) && !html.includes('data-tr="math"')) {
  const tag = `<style data-tr="math">${CSS}</style>`;
  html = html.includes("<!--TR:CSS-->")
    ? html.replace("<!--TR:CSS-->", `${tag}\n    <!--TR:CSS-->`)
    : html.replace("</head>", `${tag}\n  </head>`);
}
writeFileSync(file, html);
for (const e of errors) console.log(`ERROR 公式编译出错：${e}`);
for (const w of warns) console.log(`WARN ${w}`);
console.log(`公式    行内 ${count.inline} 个，块级 ${count.block} 个`);
