#!/usr/bin/env node
/* math.mjs 页面.html —— 把页面里的 LaTeX 公式编译成 MathML，就地改写。由 build.py 调用。

   定界符：行内 \( … \) 或 $ … $（pandoc 规则：开 $ 后、闭 $ 前不能是空白，闭 $ 后不能紧跟数字，
   于是「$5 和 $8」不会被当成公式；内容含中文且不在 \text{} 里的也不算）；块级 \[ … \] 或 $$ … $$。
   $ … $ 内部可以换行（格式化工具会折行），连续空白按一个空格处理；内部出现 < 即跨越了标签，不算公式。
   <pre> <code> <script> <style> <math> <svg> 内部不碰；只有 <svg> 里的 <foreignObject> 例外，那里是 HTML，
   插图的公式标签写在里面（图元库的 mathtext），按行内公式编译。
   块级公式包进 <span class="math-display">：span 在 <p> 里也合法，窄栏里横向滚动而不是撑破版心。
   编译产物带 <annotation encoding="application/x-tex">，保留 LaTeX 源便于复查。 */
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const temml = require("../assets/vendor/temml/temml.cjs");
import { estimate } from "./mathwidth.mjs";
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
const SKIP = /(<(pre|code|script|style|math|svg)\b[\s\S]*?<\/\2\s*>)/g;
const count = { inline: 0, block: 0, figure: 0 };
const errors = [];
const warns = [];
const CJK = /[　-〿一-鿿＀-￯]/;

// HTML 源码里 < > & 必须写成实体，TeX 要的是字符本身
const unescape = (t) =>
  t.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");

/* 行内公式估算宽度超过这么多 em 就算「长公式」。窄屏（390 宽）的正文栏约 20em，三层嵌套的列表里剩 15em 左右。
   按宽度判断，不数源码字符：\partial、\cdot 这些命令在源码里不算字符，排出来却各占一个字宽。 */
const INLINE_LONG_EM = 14;

/* Firefox 内核把「文字 + 箭头 + 文字」这样的上下标当成一个可伸缩的运算符：标注不缩小，箭头被拉长，
   公式比 Chrome 里宽出一截（\\underbrace{…}_{\\text{the}\\to\\text{cat}} 实测宽 40%）。
   这里把结果改成各内核一致：没写 stretchy 的箭头标成不伸缩；munder / mover / munderover 里
   作上下标的 mrow 显式写上缩小一级。重音记号是 mo，不是 mrow，不受影响。 */
const ARROW_RE = /<mo>([←-⇿⟵-⟿])<\/mo>/gu;
const SCRIPT_HOSTS = new Set(["munder", "mover", "munderover"]);
const SCRIPT_STYLE = ' style="math-depth:add(1);font-size:math;"';
const portable = (mathml) => {
  const stack = [];
  return mathml
    .replace(ARROW_RE, '<mo stretchy="false">$1</mo>')
    .replace(
      /<(\/?)([a-z]+)((?:"[^"]*"|[^>"])*?)(\/?)>/g,
      (m, close, tag, attrs, self) => {
        if (close) {
          stack.pop();
          return m;
        }
        const host = stack[stack.length - 1];
        const nth = host ? ++host.kids : 0;
        if (!self) stack.push({ tag, kids: 0 });
        return host &&
          SCRIPT_HOSTS.has(host.tag) &&
          nth > 1 &&
          tag === "mrow" &&
          !attrs.includes("style=")
          ? `<mrow${attrs}${SCRIPT_STYLE}>`
          : m;
      }
    );
};

const render = (tex, display, inFigure) => {
  tex = unescape(tex.trim());
  if (!display) tex = tex.replace(/\s+/g, " ");
  count[inFigure ? "figure" : display ? "block" : "inline"]++;
  const out = portable(
    temml.renderToString(tex, {
      displayMode: display,
      throwOnError: false,
      annotate: true,
    })
  );
  const short = tex.length > 60 ? tex.slice(0, 60) + "…" : tex;
  if (/class="temml-error"|color:#b22222|merror/.test(out)) errors.push(short);
  if (display) return renderBlock(out, short);
  // 行内 MathML 不会自动断行，长的在手机上会撑宽页面，窄屏下改为可横向滚动
  if (!display && !inFigure && estimate(out) > INLINE_LONG_EM)
    return `<span class="math-inline-long">${out}</span>`;
  return out;
};

/* 块级公式的宽度检查。基准是 1280 宽的窗口：正文栏 616px、字号 20px，即 30.8em；更宽的窗口栏也更宽。
   带编号的公式还要给编号和它前面的间隔让出位置。超出的公式在页面上横向滚动，所以是 WARN。 */
const COL_EM = 30.8;
const TAG_GAP_EM = 1.5; // 与 tufte.css 里 .eq-tag 的 padding-left 一致
const TAG_RE =
  /<mtable displaystyle="true" style="width:100%;"><mtr class="tml-tageqn"><mtd style="padding:0;width:50%;"><\/mtd><mtd>([\s\S]*)<\/mtd><mtd style="padding:0;width:50%;"><mtext class="tml-tag">([^<]*)<\/mtext><\/mtd><\/mtr><\/mtable>/;

/* Temml 把 \tag 排成一张占满整栏的三列表格，编号放在右边那一列里；公式一宽，右列被挤没，
   编号就贴上甚至压住公式（各浏览器表现不同）。这里把编号从 MathML 里取出来，交给 tufte.css 的三栏网格：
   公式居中，编号靠右，中间至少隔 TAG_GAP_EM，放不下时整行横向滚动。 */
const renderBlock = (out, short) => {
  let tag = "";
  out = out.replace(TAG_RE, (_, body, label) => {
    tag = label;
    return body;
  });
  if (out.includes("tml-tag"))
    warns.push(
      `带编号的公式没能把编号移出来，窄栏里编号可能压住公式；多行编号拆成每行一个 $$…\\tag{n}$$：${short}`
    );
  const room = COL_EM - (tag ? [...tag].length * 0.5 + TAG_GAP_EM : 0);
  const need = estimate(out);
  if (need > room)
    warns.push(
      `块级公式估计宽 ${need.toFixed(0)}em，正文栏${tag ? "扣掉编号后" : ""}只有 ${room.toFixed(0)}em（1280 宽的窗口），会横向滚动；用 aligned 在 = 或 + 前断行：${short}`
    );
  return tag
    ? `<span class="math-display tagged">${out}<span class="eq-tag">${tag}</span></span>`
    : `<span class="math-display">${out}</span>`;
};

/* 单 $ 扫描：被拒的候选只跳过开 $，不吞后文。与 build.py 的 single_dollar_spans 同一套规则。 */
const singleDollar = (s, inFigure) => {
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
      !inner.includes("<") &&
      !/\d/.test(s[b + 1] || "") &&
      !CJK.test(inner.replace(/\\text\{[^}]*\}/g, ""));
    if (ok) {
      out += s.slice(i, a) + render(inner, false, inFigure);
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
    if (i % 3 === 1)
      // 跳过块本体；<svg> 里的 <foreignObject> 除外
      return /^<svg\b/i.test(seg)
        ? seg.replace(
            /(<foreignObject\b[^>]*>)([\s\S]*?)(<\/foreignObject\s*>)/gi,
            (_, open, body, close) => open + singleDollar(body, true) + close
          )
        : seg;
    if (i % 3 === 2) return ""; // 捕获的标签名
    seg = seg
      .replace(/\$\$([\s\S]+?)\$\$/g, (_, t) => render(t, true))
      .replace(/\\\[([\s\S]+?)\\\]/g, (_, t) => render(t, true))
      .replace(/\\\(([\s\S]+?)\\\)/g, (_, t) => render(t, false));
    return singleDollar(seg);
  })
  .join("");

if (
  (count.inline || count.block || count.figure) &&
  !html.includes('data-tr="math"')
) {
  const tag = `<style data-tr="math">${CSS}</style>`;
  html = html.includes("<!--TR:CSS-->")
    ? html.replace("<!--TR:CSS-->", `${tag}\n    <!--TR:CSS-->`)
    : html.replace("</head>", `${tag}\n  </head>`);
}
writeFileSync(file, html);
for (const e of errors) console.log(`ERROR 公式编译出错：${e}`);
for (const w of warns) console.log(`WARN ${w}`);
console.log(
  `公式    行内 ${count.inline} 个，块级 ${count.block} 个` +
    (count.figure ? `，图内 ${count.figure} 个` : "")
);
