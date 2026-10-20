#!/usr/bin/env node
/* mermaid.mjs 页面.html —— 把页面里的 <pre class="mermaid"> 编译成内联 SVG，就地改写。由 build.py 调用。

   编译器是 vendor 的 ondine（Rust 写的 Mermaid 编译器，wasm）：语法按 Mermaid，布局与外观是 ondine 自己的。
   SVG 的颜色、字体、线宽读 --ondine-* 变量，tufte.css 把它们接到页面的 token 上，切换明暗主题不用重新编译。
   源码按 HTML 写：< 和 & 写成 &lt; &amp;（标签里换行写 &lt;br&gt;），编译前还原。
   排版宽度：普通插图按正文栏，横向的流程图放不下时 ondine 自动改成纵向；figure.fullwidth 里的按通栏。
   图题（figure 里的 marginnote 或 figcaption）写进 aria-label；源码写了 accTitle 的，ondine 自己给 <title>。
   图内 id 的前缀取自源码的哈希：重复构建不变，不同的图不重复。 */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { create, RenderError } from "../assets/vendor/ondine/Render.js";

/* 1280 宽的窗口里正文栏 616px，通栏（正文栏 + 间隔 + 页边注）约 985px，各留一点余量 */
const COL_PX = 600;
const PAGE_PX = 980;

const file = process.argv[2];
if (!file) {
  console.error("用法：mermaid.mjs 页面.html");
  process.exit(2);
}
const wasm = readFileSync(
  new URL(
    "../assets/vendor/ondine/internal/all.generated.wasm",
    import.meta.url
  )
);
const ondine = create({ modules: { all: new WebAssembly.Module(wasm) } });

const html = readFileSync(file, "utf8");
const errors = [];
const warns = [];
let ok = 0;
let seq = 0;

const unescape = (t) =>
  t.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
// 图题去掉标签后放进属性值：原文已经是 HTML 文本，只需转义引号。
// 标签的 > 可能被格式化工具折到下一行
const CAPTION_RE =
  /<span class="marginnote"\s*>([\s\S]*?)<\/span\s*>|<figcaption\b[^>]*>([\s\S]*?)<\/figcaption\s*>/;
const caption = (figure) => {
  const m = figure.match(CAPTION_RE);
  return m
    ? (m[1] ?? m[2])
        .replace(/<annotation\b[\s\S]*?<\/annotation\s*>/g, "") // 公式已编译，只留 MathML 的字
        .replace(/<[^>]+>/g, "")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/"/g, "&quot;")
    : "";
};

const out = html.replace(
  /<pre class="mermaid"\s*>([\s\S]*?)<\/pre\s*>/g,
  (whole, body, at, s) => {
    seq++;
    const before = s.slice(0, at);
    const open = before.lastIndexOf("<figure");
    const inFigure = open >= 0 && before.indexOf("</figure", open) < 0;
    const figure = inFigure ? s.slice(open, s.indexOf("</figure", at)) : "";
    const wide = /^<figure\b[^>]*\bclass="[^"]*\bfullwidth\b/.test(figure);
    const max = wide ? PAGE_PX : COL_PX;
    const cap = caption(figure.replace(whole, ""));
    const where = cap ? `「${cap.slice(0, 24)}」` : `第 ${seq} 幅`;

    const src = unescape(body)
      .replace(/^\s*\n/, "")
      .trimEnd();
    const prefix = `m${createHash("sha1").update(src).digest("hex").slice(0, 8)}-`;
    try {
      const r = ondine.render(src, { idPrefix: prefix, maxWidth: max });
      ok++;
      if (r.width > max)
        warns.push(
          `Mermaid 图${where}排出来宽 ${Math.round(r.width)}px，超过${wide ? "通栏" : "正文栏"}的 ${max}px，会缩小显示：` +
            "缩短标签或用 &lt;br&gt; 断行、改成纵向（TD），或放进 figure.fullwidth"
        );
      return cap && !r.svg.includes("aria-labelledby=")
        ? r.svg.replace("<svg ", `<svg aria-label="${cap}" `)
        : r.svg;
    } catch (e) {
      if (!(e instanceof RenderError)) throw e;
      // 消息形如「Parse error on line 4: / 源码 / ^ / Expecting …」，最后一行是要点
      const reason = e.message
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .pop();
      const text = src.split("\n")[e.line - 1]?.trim();
      const line = e.line
        ? `源码第 ${e.line} 行第 ${e.column} 列${text ? `（${text}）` : ""}，`
        : "";
      errors.push(`Mermaid 图${where}编译失败，${line}${reason}`);
      return whole;
    }
  }
);

if (out !== html) writeFileSync(file, out);
for (const e of errors) console.log(`ERROR ${e}`);
for (const w of warns) console.log(`WARN ${w}`);
console.log(
  `Mermaid 编译 ${ok} 幅` + (errors.length ? `，失败 ${errors.length} 幅` : "")
);
