#!/usr/bin/env node
/* mermaid.mjs 页面.html —— 把页面里的 <pre class="mermaid"> 编译成内联 SVG，就地改写。由 build.py 调用。

   编译器是 vendor 的 pele（JS 写的 Mermaid 渲染器）：语法按 Mermaid，布局与外观是 pele 自己的。
   SVG 的颜色、字体读 --pele-* 变量，show-me.css 把它们接到页面的 token 上，切换主题不用重新编译。
   源码留在页面里，是图的唯一来源：每次构建先拆掉上一次的产物，再从源码重新编译，改图只改源码。
   产物是 div.mermaid-figure：SVG（一版或宽窄两版）加原样的 <pre class="mermaid">（show-me.css 把它隐藏，
   「复制为 Markdown」把它导出成 mermaid 代码块）。
   宽窄两版：先按 WIDE_PX 排一版；排出来比 PHONE_PX 宽的，再按 NARROW_PX 排一版，pele 会把横向的流程图改成纵向。
   第二版确实变窄了就两版都留（class 为 diagram-wide / diagram-narrow，show-me.css 按视口只显示一版）；
   没变窄（时序图这类不能重排的）只留宽版并发 WARN。
   源码按 HTML 写：< 和 & 写成 &lt; &amp;（标签里换行写 &lt;br&gt;），编译前还原。 */
import { readFileSync, writeFileSync } from "node:fs";
import { PeleError, render } from "../assets/vendor/pele/pele.mjs";

const WIDE_PX = 720; // 48rem 版心里图框的可用宽度约 728px
const NARROW_PX = 340; // 390px 手机视口里图框的可用宽度约 318px，340 的图缩到九成多
const PHONE_PX = 400; // 不超过这个宽度的图在手机上基本按原大显示，不用第二版
const CROWDED_PX = 960; // 宽版超过它，在 720 的图框里缩到 0.75 倍以下，11px 的连线标签接近 8px 的渲染下限
const FONT_PX = 13;
/* pele 默认在 200px 处折行、层间距约 50px，直链图会比手绘的高出近一倍。这三个值是 2026-11 用两张真实页面的
   手绘图对照后定的；源码自带 frontmatter 或 %%{init}%% 时不注入，由作者自己负责。 */
const LAYOUT =
  '%%{init: {"flowchart": {"wrappingWidth": 360, "rankSpacing": 20, "nodeSpacing": 20}}}%%\n';

const file = process.argv[2];
if (!file) {
  console.error("用法：mermaid.mjs 页面.html");
  process.exit(2);
}
/* 构建时没有浏览器，pele 自带的字宽表按窄一些的西文字体估，标签会顶出框。
   这里按字符分档估算，单位 em，宁宽勿窄；汉字按 1em。 */
const CJK =
  /[\u2e80-\u9fff\uac00-\ud7af\uf900-\ufaff\ufe30-\ufe4f\uff00-\uffef]/u;
const EM = [
  [/[ijl.,:;'|I]/, 0.3],
  [/[ !]/, 0.35],
  [/[frt()[\]{}"`]/, 0.45],
  [/[mwMW@%]/, 0.97],
  [/[A-Z&]/, 0.75],
];
const BOLD = 1; // pele 的 style 位
const MONO = 4;
function em(c, style) {
  if (CJK.test(c)) return 1;
  if (style & MONO) return 0.6;
  return EM.find(([re]) => re.test(c))?.[1] ?? 0.62;
}
const measurer = {
  width: (text, size, style) =>
    [...text].reduce((w, c) => w + em(c, style), 0) *
    size *
    (style & BOLD ? 1.06 : 1),
};

// 拆掉上一次的产物，只留源码
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

/* pele 的 SVG 自带 role="graphics-document document" 和写死的 width / height / max-width:100%。
   页面的无障碍契约要 role="img"；尺寸改成「最宽不超过排出来的宽度」，小图不会被 .fig svg 的 width:100% 拉大。 */
function adapt(r, cls) {
  let svg = r.svg
    .replace(/ role="[^"]*"/, ' role="img"')
    .replace(/ width="[\d.]+" height="[\d.]+"/, "")
    .replace(
      'style="max-width:100%;height:auto;',
      `style="max-width:${Math.ceil(r.width)}px;`
    );
  if (cls) svg = svg.replace('class="pele ', `class="${cls} pele `);
  return svg;
}

const out = bare.replace(
  /<pre class="mermaid"\s*>([\s\S]*?)<\/pre\s*>/g,
  (whole, body) => {
    seq++;
    const where = `第 ${seq} 幅`;
    const raw = unescape(body)
      .replace(/^\s*\n/, "")
      .trimEnd();
    const own = /^\s*---/.test(raw) || raw.includes("%%{");
    const src = own ? raw : LAYOUT + raw;
    const opts = { measurer, fontSize: FONT_PX };
    try {
      const wide = render(src, {
        ...opts,
        idPrefix: `mmd${seq}-`,
        maxWidth: WIDE_PX,
      });
      let svgs = adapt(wide, "");
      if (wide.width > CROWDED_PX)
        warns.push(
          `Mermaid 图${where}排出来宽 ${Math.round(wide.width)}px，放进图框要缩到 ${(WIDE_PX / wide.width).toFixed(2)} 倍，字会偏小：` +
            "把主流向改成 TD、缩短标签或用 &lt;br&gt; 断行，或拆成两幅"
        );
      if (wide.width > PHONE_PX) {
        const narrow = render(src, {
          ...opts,
          idPrefix: `mmd${seq}n-`,
          maxWidth: NARROW_PX,
        });
        if (narrow.width <= PHONE_PX)
          svgs = adapt(wide, "diagram-wide") + adapt(narrow, "diagram-narrow");
        else
          warns.push(
            `Mermaid 图${where}宽 ${Math.round(wide.width)}px，按 ${NARROW_PX}px 重排后仍有 ${Math.round(narrow.width)}px，` +
              "手机上会整体缩小：减少并排的节点或生命线，或拆成两幅"
          );
      }
      ok++;
      return `<div class="mermaid-figure">${svgs}${whole}</div>`;
    } catch (e) {
      if (!(e instanceof PeleError)) throw e;
      // 消息形如「Parse error on line 4: / 源码 / ^ / Expecting …」，最后一行是要点
      const reason = e.message
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .pop();
      const n = e.line ? e.line - (own ? 0 : 1) : 0; // 注入的布局参数占了第一行
      const text = raw.split("\n")[n - 1]?.trim();
      const line = n
        ? `源码第 ${n} 行第 ${e.column} 列${text ? `（${text}）` : ""}，`
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
