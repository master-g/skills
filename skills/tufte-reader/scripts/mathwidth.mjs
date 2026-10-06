/* mathwidth.mjs —— 估算一段 Temml 输出的 MathML 排出来有多宽，单位 em（相对公式字号）。
   构建时没有浏览器，量不了真实宽度；这里按 MathML 的结构粗算：记号按字符数，分式取分子分母的较宽者，
   上下标按 0.7 倍，矩阵按各列最宽的格相加。用读本里 45 条块级公式在 Chrome 里的实测宽度校准过，
   误差大多在 ±15% 以内，只用来判断「放不放得下」，不用来排版。 */

const SCRIPT = 0.7; // 上下标、非显示样式的分式相对正文的大小
const GLYPH = { mi: 0.54, mn: 0.5, mtext: 0.46, mo: 0.62 };
const BIG_OP = /[∑∏∐⋃⋂⨁⨂∫∮]/u;
const TIGHT_OP = /^[()[\]{}|‖⟨⟩.,;:!′'/]$/u; // 两侧不留运算符间距的记号
const PX_PER_EM = 20; // 只用来换算 Temml 写死的 pt，取正文字号

const parse = (xml) => {
  const root = { tag: "#root", attrs: "", kids: [] };
  const stack = [root];
  const re = /<(\/?)([a-zA-Z][\w-]*)((?:"[^"]*"|[^>"])*?)(\/?)>|([^<]+)/g;
  for (let m; (m = re.exec(xml));) {
    const top = stack[stack.length - 1];
    if (m[5] !== undefined) top.kids.push({ text: decode(m[5]) });
    else if (m[1]) stack.length > 1 && stack.pop();
    else {
      const node = { tag: m[2], attrs: m[3], kids: [] };
      top.kids.push(node);
      if (!m[4]) stack.push(node);
    }
  }
  return root;
};

const decode = (t) =>
  t
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&#x([0-9a-f]+);/gi, (_, h) =>
      String.fromCodePoint(parseInt(h, 16))
    );

const attr = (node, name) =>
  (new RegExp(`\\b${name}="([^"]*)"`).exec(node.attrs) || [])[1];

const length = (v) => {
  const m = /(-?[\d.]+)(em|pt|px)?/.exec(v || "");
  if (!m) return 0;
  const n = parseFloat(m[1]);
  return m[2] === "pt"
    ? (n * 4) / 3 / PX_PER_EM
    : m[2] === "px"
      ? n / PX_PER_EM
      : n;
};

const styleLength = (node, prop) =>
  length(
    (new RegExp(`(?:^|;)\\s*${prop}:([^;]+)`).exec(attr(node, "style") || "") ||
      [])[1]
  );

const text = (node) => node.kids.map((k) => k.text ?? text(k)).join("");

const sum = (nodes, display) =>
  nodes.reduce((w, k) => w + width(k, display), 0);

// display：当前是否显示样式（分式用全尺寸）。进入分式、上下标之后变成 false
function width(node, display) {
  if (node.text !== undefined) return 0;
  const kids = node.kids.filter((k) => k.text === undefined);
  const margin =
    styleLength(node, "margin-left") + styleLength(node, "margin-right");
  switch (node.tag) {
    case "annotation":
      return 0;
    case "mi":
    case "mn":
    case "mtext":
      return [...text(node)].length * GLYPH[node.tag] + margin;
    case "mo": {
      const t = text(node);
      if (BIG_OP.test(t)) return display ? 1.3 : 0.9;
      const space =
        TIGHT_OP.test(t) || attr(node, "fence") ? (t === "," ? 0.17 : 0) : 0.5;
      return [...t].length * GLYPH.mo + space;
    }
    case "mspace":
      return length(attr(node, "width"));
    case "mfrac": {
      const k = display ? 1 : SCRIPT;
      return k * Math.max(...kids.map((c) => width(c, false))) + 0.25;
    }
    case "msub":
    case "msup":
    case "msubsup":
      return (
        width(kids[0], display) +
        SCRIPT * Math.max(...kids.slice(1).map((c) => width(c, false)))
      );
    case "munder":
    case "mover":
    case "munderover":
      return Math.max(
        width(kids[0], display),
        ...kids.slice(1).map((c) => SCRIPT * width(c, false))
      );
    case "msqrt":
      return sum(kids, display) + 0.75;
    case "mroot":
      return width(kids[0], display) + 0.9;
    case "mstyle": {
      const d = attr(node, "displaystyle");
      return sum(kids, d === undefined ? display : d === "true") + margin;
    }
    case "mtable": {
      const inner = attr(node, "displaystyle") === "true";
      const cols = [];
      for (const row of kids)
        row.kids
          .filter((c) => c.tag === "mtd")
          .forEach((cell, i) => {
            const w =
              sum(cell.kids, inner) +
              styleLength(cell, "padding-left") +
              styleLength(cell, "padding-right");
            cols[i] = Math.max(cols[i] || 0, w);
          });
      return cols.reduce((a, b) => a + b, 0);
    }
    default:
      return sum(kids, display) + margin;
  }
}

// 0.95：上面的系数整体偏宽约 5%
export const estimate = (mathml) => 0.95 * width(parse(mathml), true);
