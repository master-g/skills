#!/usr/bin/env node
/* mermaid.mjs 页面.html —— 把页面里的 <pre class="mermaid"> 编译成内联 SVG，就地改写。由 build.py 调用。

   编译器是 vendor 的 ondine（Rust 写的 Mermaid 编译器，wasm）：语法按 Mermaid，布局与外观是 ondine 自己的。
   SVG 的颜色、字体、线宽读 --ondine-* 变量，tufte.css 把它们接到页面的 token 上，切换明暗主题不用重新编译。
   源码留在页面里，是图的唯一来源：每次构建先拆掉上一次的产物，再从源码重新编译，改图只改源码。
   产物是 div.mermaid-figure：checkbox 和它的 label（「源码」开关，tufte.css 让它平时隐藏、悬停时出现）、SVG、
   原样的 <pre class="mermaid">（平时隐藏，勾选后代替 SVG 显示）。不用脚本，与边注的 ⊕ 同一种做法。
   源码按 HTML 写：< 和 & 写成 &lt; &amp;（标签里换行写 &lt;br&gt;），编译前还原。
   排版宽度：普通插图按正文栏，横向的流程图放不下时 ondine 自动改成纵向；figure.fullwidth 里的按通栏。
   图题（figure 里的 marginnote 或 figcaption）写进 aria-label；源码写了 accTitle 的，ondine 自己给 <title>。
   图内 id 与开关的 id 按图在页面里的次序编号：每次全部重新编译，次序不变，重复构建的结果也不变。 */
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

// 拆掉上一次的产物，只留源码。拆的时候认宽松的写法：开标签写错的也要拆开，免得留下旧图，交给检查报错
const UNWRAP_RE =
  /<div class="mermaid-figure"\s*>[\s\S]*?(<pre\b[^>]*\bclass="[^"]*\bmermaid\b[^>]*>[\s\S]*?<\/pre\s*>)\s*<\/div\s*>/g;
const html = readFileSync(file, "utf8");
const bare = html.replace(UNWRAP_RE, "$1");
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

const out = bare.replace(
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
    try {
      const r = ondine.render(src, { idPrefix: `mmd${seq}-`, maxWidth: max });
      ok++;
      if (r.width > max)
        warns.push(
          `Mermaid 图${where}排出来宽 ${Math.round(r.width)}px，超过${wide ? "通栏" : "正文栏"}的 ${max}px，会缩小显示：` +
            "缩短标签或用 &lt;br&gt; 断行、改成纵向（TD），或放进 figure.fullwidth"
        );
      // ondine 把 max-width:100% 写在 SVG 的内联样式里，会压过 tufte.css 里 .scroll-x 的 max-width:none；
      // 去掉它，尺寸交给 tufte.css 的 figure svg（同样是 max-width:100%、height:auto）
      let svg = r.svg.replace('style="max-width:100%;height:auto;', 'style="');
      if (cap && !svg.includes("aria-labelledby="))
        svg = svg.replace("<svg ", `<svg aria-label="${cap}" `);
      const id = `mmd-${seq}`;
      return (
        `<div class="mermaid-figure"><input type="checkbox" id="${id}" class="mermaid-toggle" />` +
        `<label for="${id}" class="mermaid-switch" title="在图与 Mermaid 源码之间切换"></label>${svg}${whole}</div>`
      );
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
