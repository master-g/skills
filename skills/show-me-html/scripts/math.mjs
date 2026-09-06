#!/usr/bin/env node
/* math.mjs 页面.html —— 把页面里的 LaTeX 公式编译成 MathML，就地改写。
   由 build.py 在找到 node 时调用；也可以单独跑。

   定界符：行内 \( … \) 或 $ … $（pandoc 规则：开 $ 后、闭 $ 前不能是空白，闭 $ 后不能紧跟数字，
   于是「$5 和 $8」不会被当成公式；内容含中文且不在 \text{} 里的也不算）；块级 \[ … \] 或 $$ … $$。
   <pre> <code> <script> <style> 内部不碰。
   行内堆叠分数（\frac）由 build.py 的 <mfrac> 检查发 WARN。
   编译产物带 <annotation encoding="application/x-tex">，骨架的 Markdown 导出靠它还原 LaTeX 源。 */
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const temml = require("../assets/vendor/temml/temml.cjs");
const CSS = readFileSync(
  new URL("../assets/vendor/temml/Temml-Local.css", import.meta.url),
  "utf8"
)
  .replace(/@font-face\s*\{[^}]*\}/g, "") // 外链 woff2：页面必须离线可开
  .replace(/^math \{[\s\S]*?\}\n/m, ""); // 字体栈由 show-me.css 统一给

const file = process.argv[2];
if (!file) {
  console.error("用法：math.mjs 页面.html");
  process.exit(2);
}
let html = readFileSync(file, "utf8");
const SKIP = /(<(pre|code|script|style)\b[\s\S]*?<\/\2\s*>)/g;
const count = { inline: 0, block: 0 };
const CJK = /[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]/;

const render = (tex, display) => {
  tex = tex.trim();
  count[display ? "block" : "inline"]++;
  return temml.renderToString(tex, {
    displayMode: display,
    throwOnError: false,
    annotate: true,
  });
};

/* 单 $ 扫描：pandoc 规则（开 $ 后、闭 $ 前非空白，闭 $ 后非数字，不跨行），
   另加「内容含中文（\text{} 之外）不算公式」。被拒的候选只跳过开 $，不吞后文。
   与 build.py 的 single_dollar_spans 保持同一套规则。 */
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

if ((count.inline || count.block) && !html.includes('data-show-me="math"')) {
  const tag = `<style data-show-me="math">${CSS}</style>`;
  html = html.includes("<!--SHOW-ME:CSS-->")
    ? html.replace("<!--SHOW-ME:CSS-->", `${tag}\n    <!--SHOW-ME:CSS-->`)
    : html.replace("</head>", `${tag}\n  </head>`);
}
writeFileSync(file, html);
console.log(`公式    行内 ${count.inline} 个，块级 ${count.block} 个`);
