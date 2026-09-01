# 交互配方

basecoat 覆盖不到的交互，代码在这里。**照抄，不要重写** —— 这些都已经处理过键盘可达性与边界情况。

组件自身的交互（标签页、下拉菜单、对话框、折叠）由 basecoat 或浏览器原生提供，见 `components.md`。

共同约束：

- 所有可操作元素必须是真 `<button>` / `<a>` / `<input>`，或带 `tabindex="0"` + 键盘处理。
- 页面 chrome（工具条、筛选器、导出按钮）加 `data-md-skip`，否则会被复制进 Markdown。
- 自动播放的动效包在 `@media (prefers-reduced-motion: no-preference)` 里。
- 交互图必须在图头写明能怎么操作（「拖动这个循环」「挑一个改动」），否则读者不会发现它能动。

---

## 拖拽排序（看板 / 优先级列表）

原生 HTML5 拖放，附带键盘替代路径 —— 只有鼠标能用的看板等于没做无障碍。

```html
<div class="board" data-md-skip-controls>
  <section class="col" data-col="todo">
    <h3>待处理 <span class="badge" data-count>0</span></h3>
    <div class="slot"></div>
  </section>
  <section class="col" data-col="doing">
    <h3>进行中 <span class="badge" data-count>0</span></h3>
    <div class="slot"></div>
  </section>
</div>
```

```css
.board {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
}
.slot {
  min-height: 6rem;
  display: grid;
  gap: 0.5rem;
  align-content: start;
  padding: 0.5rem;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius);
}
.slot.over {
  border-color: var(--color-primary);
  background: var(--color-accent);
}
.ticket {
  cursor: grab;
}
.ticket.dragging {
  opacity: 0.5;
}
```

```js
let dragged = null;
document.querySelectorAll(".ticket").forEach((el) => {
  el.draggable = true;
  el.tabIndex = 0;
  el.addEventListener("dragstart", () => {
    dragged = el;
    el.classList.add("dragging");
  });
  el.addEventListener("dragend", () => {
    el.classList.remove("dragging");
    dragged = null;
    recount();
  });
  // 键盘替代：← → 在列之间移动
  el.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const slots = [...document.querySelectorAll(".slot")];
    const i = slots.indexOf(el.closest(".slot"));
    const next = slots[i + (e.key === "ArrowRight" ? 1 : -1)];
    if (next) {
      next.appendChild(el);
      el.focus();
      recount();
    }
  });
});
document.querySelectorAll(".slot").forEach((slot) => {
  slot.addEventListener("dragover", (e) => {
    e.preventDefault();
    slot.classList.add("over");
  });
  slot.addEventListener("dragleave", () => slot.classList.remove("over"));
  slot.addEventListener("drop", (e) => {
    e.preventDefault();
    slot.classList.remove("over");
    if (dragged) slot.appendChild(dragged);
    recount();
  });
});
function recount() {
  document
    .querySelectorAll(".col")
    .forEach(
      (c) =>
        (c.querySelector("[data-count]").textContent =
          c.querySelectorAll(".ticket").length)
    );
}
recount();
```

## 幻灯片键盘导航

```js
const slides = [...document.querySelectorAll(".slide")];
let cur = 0;
const show = (i) => {
  cur = Math.max(0, Math.min(slides.length - 1, i));
  slides[cur].scrollIntoView({ behavior: "smooth" });
  document.getElementById("pageno").textContent =
    `${cur + 1} / ${slides.length}`;
  location.hash = "s" + (cur + 1);
};
addEventListener("keydown", (e) => {
  if (["ArrowRight", "PageDown", " "].includes(e.key)) {
    e.preventDefault();
    show(cur + 1);
  }
  if (["ArrowLeft", "PageUp"].includes(e.key)) {
    e.preventDefault();
    show(cur - 1);
  }
  if (e.key === "Home") show(0);
  if (e.key === "End") show(slides.length - 1);
});
show(+(location.hash.match(/\d+/) || [1])[0] - 1);
```

页面上必须写明「← → 翻页」，否则读者不知道能翻。

## 旋钮驱动实时预览

```html
<div class="field">
  <label for="k-radius">圆角 <output for="k-radius">8</output>px</label>
  <input
    type="range"
    id="k-radius"
    min="0"
    max="24"
    value="8"
    data-bind="--demo-radius"
    data-unit="px"
  />
</div>
<div class="preview" style="border-radius: var(--demo-radius, 8px)">…</div>
```

```js
document.querySelectorAll("[data-bind]").forEach((inp) => {
  const out = document.querySelector(`output[for="${inp.id}"]`);
  const sync = () => {
    document.documentElement.style.setProperty(
      inp.dataset.bind,
      inp.value + (inp.dataset.unit || "")
    );
    if (out) out.textContent = inp.value;
    document.querySelectorAll("[data-snippet]").forEach(render);
  };
  inp.addEventListener("input", sync);
  sync();
});
```

`data-snippet` 是随旋钮更新的 markup 展示块 —— 读者要能把调好的结果抄走，否则旋钮只是玩具。

滑块本身长什么样归骨架管，见下方「滑块与其它原生控件」。

## 图（figure）的固定外壳

一页里出现两张以上交互图时，全部套同一个外壳：**编号 + 标题 + 操作提示 + 内容 + 图注**。

```html
<figure class="fig">
  <div class="fig-box">
    <div class="fig-head">
      <span class="fig-title">图 2 — 钱花到哪儿去了</span>
      <span class="fig-hint" data-md-skip>拖动这个循环</span>
    </div>
    <!-- 控件与画面。所有控件加 data-md-skip -->
  </div>
  <figcaption>
    累计成本按 token 归属拆开。前缀带线性增长，负载带按平方增长 ——
    所以它最终一定赢。
  </figcaption>
</figure>
```

```css
.fig {
  margin: 2.25rem 0;
}
.fig-box {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-card);
  padding: 1rem 1rem 1.25rem;
}
.fig-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.25rem 0.75rem;
  margin-bottom: 1rem;
}
.fig-title {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.fig-hint,
.fig figcaption {
  color: var(--color-muted-foreground);
}
.fig-hint {
  font-size: 0.72rem;
}
.fig figcaption {
  margin-top: 0.6rem;
  padding: 0 0.25rem;
  font-size: 0.78rem;
  line-height: 1.7;
}
```

**图内也要有间距节奏，不要让每个元素自己声明 margin。**
和骨架的 `main > section > * + *` 同一套思路 —— 间距由「谁排在谁后面」决定：

```css
.fig-box > * + * {
  margin-top: 1rem;
}
/* 紧耦合的一对：后者是前者的标签或刻度，贴紧才读得出从属 */
.fig-axis + .bars {
  margin-top: 0.5rem;
}
.strip + .strip-legend {
  margin-top: 0.25rem;
}
/* 角标溢出 svg 上下缘时，后面那块要让开 */
.plot + * {
  margin-top: 1.75rem;
}
```

元素自己带 margin 的写法在**只有一张图**时看不出问题，多一张就露馅：
`.chips { margin-top: 1rem }` 在「条带在上、按钮在下」的图里是对的，
换成「按钮在上、条带在下」的图，按钮上方就是 2rem、下方是 **0** —— 按钮直接贴着条带。
这个 bug 真发生过，而且只有人眼看得出来。

三条硬要求：

- **`fig-hint` 不能省。**「挑一个改动」「拖动这个循环」「拖动切换点」—— 没有它，一半读者不会发现图能动。
- **图注承载论点，不重复标题。** 每条 `figcaption` 单独拎出来也要是一句成立的结论。
- 图头、控件、旋钮全部 `data-md-skip`；标题与图注**不加**，它们要进 Markdown 导出。

## 先写模型，再写图

一页里多张图讲同一件事时，**先写出那个模型函数，三张图和正文里的每个数字都从它派生**。
这不是代码复用，是正确性保证 —— 没人手打过数字，数字就不可能编错。

```js
/* 例：agent 循环的逐回合成本模型。三张图 + 正文金额都调用它 */
const M = 1e6,
  READ = 0.1,
  WRITE = 1.25;
function simulate(P0, D, bases) {
  const rows = [];
  let cum = 0;
  for (let i = 0; i < bases.length; i++) {
    const p = bases[i],
      L = P0 + i * D;
    const switched = i > 0 && bases[i] !== bases[i - 1];
    let read = 0,
      write = 0;
    /* 第 0 回合、以及任何切换的回合，整份上下文都要重写进缓存（无读价）；L 在 i=0 时正好等于 P0 */
    if (i === 0 || switched) write = L + D;
    else {
      read = L;
      write = D;
    }
    const cost = (read * READ * p + write * WRITE * p) / M;
    cum += cost;
    rows.push({ n: i + 1, cost, cum, base: p, switched });
  }
  return rows;
}
```

正文里写「这趟往返花掉 $1.17」时，那个 $1.17 应该是 `simulate(...)` 跑出来的，不是抄进 HTML 的。
模型建好之后，先在命令行跑一遍对齐已知数字，再开始画图。

## 入屏自播一次

图第一次进视口时自己演示一帧，之后不再打扰，另配一个手动重播。

```js
const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;

/* 首次进入视口触发一次，然后断开 */
function onReveal(el, fn) {
  if (REDUCE) {
    fn();
    return;
  }
  const io = new IntersectionObserver(
    ([e]) => {
      if (e.isIntersecting) {
        io.disconnect();
        fn();
      }
    },
    { threshold: 0.35 }
  );
  io.observe(el);
}

onReveal(document.getElementById("fig2"), play);
```

重播按钮用文字标签就够：`<button class="linkish">[重放]</button>`。

数字本身的动效走下面的「数字滚动（odometer）」，**不要再另写一个数值插值函数** ——
两套东西做同一件事，页面上就会出现两种手感。

## 相对基线的差值图

回答「这个策略比对照组好还是差」时，**不要画两条绝对成本曲线让读者自己比**，画差值：
一条 Δ 曲线加一条零线，零线上方与下方填不同颜色。翻过零线的那一刻就是结论。

```html
<svg
  viewBox="0 0 1000 260"
  preserveAspectRatio="none"
  role="img"
  aria-label="相对于对照组的累计差，零线以上为更差"
>
  <defs>
    <clipPath id="below">
      <rect id="clip-below" x="0" width="1000"></rect>
    </clipPath>
    <clipPath id="above">
      <rect id="clip-above" x="0" y="0" width="1000"></rect>
    </clipPath>
  </defs>
  <path
    id="fill-below"
    fill="var(--chart-3)"
    fill-opacity=".24"
    clip-path="url(#below)"
  ></path>
  <path
    id="fill-above"
    fill="var(--chart-1)"
    fill-opacity=".24"
    clip-path="url(#above)"
  ></path>
  <path
    id="line"
    fill="none"
    stroke="var(--chart-1)"
    stroke-width="2"
    vector-effect="non-scaling-stroke"
  ></path>
  <line
    id="zero"
    x1="0"
    x2="1000"
    stroke="var(--chart-5)"
    stroke-dasharray="3 5"
    vector-effect="non-scaling-stroke"
  ></line>
</svg>
```

```js
/* delta[] 是「本策略 − 对照组」的累计差。纵轴要把零线摆进画面，上下各留 12% 余量。 */
const flat = Math.max(...delta) - Math.min(...delta) === 0;
const lo = flat ? -0.05 : Math.min(0, ...delta);
const span = (flat ? 0.05 : Math.max(0, ...delta)) - lo,
  pad = span * 0.12;
const X = (i) => (i / (delta.length - 1)) * 1000;
const Y = (v) => 260 - ((v - (lo - pad)) / (span + pad * 2)) * 260;
const zeroY = Y(0);

const line = delta.map((v, i) => `${i ? "L" : "M"} ${X(i)} ${Y(v)}`).join(" ");
const area = `${line} L ${X(delta.length - 1)} ${zeroY} L 0 ${zeroY} Z`;
document.getElementById("line").setAttribute("d", line);
document
  .getElementById("line")
  .setAttribute(
    "stroke",
    delta.at(-1) > 0 ? "var(--chart-1)" : "var(--chart-3)"
  );
["fill-below", "fill-above"].forEach((id) =>
  document.getElementById(id).setAttribute("d", area)
);
document.getElementById("zero").setAttribute("y1", zeroY);
document.getElementById("zero").setAttribute("y2", zeroY);
document.getElementById("clip-below").setAttribute("y", zeroY);
document
  .getElementById("clip-below")
  .setAttribute("height", Math.max(0, 260 - zeroY));
document
  .getElementById("clip-above")
  .setAttribute("height", Math.max(0, zeroY));
```

零线的两侧各写一行小字说明方向（「↑ 比不做还贵」/「↓ 省下来的钱」），否则读者要猜哪边是好。
`vector-effect="non-scaling-stroke"` 必须写 —— `preserveAspectRatio="none"` 会把线宽也拉变形。

## 术语 tooltip

给外行读者补词，又不打断行文。词条集中放一处，正文只写引用。

```html
<span class="gloss-wrap"
  ><button type="button" class="gloss">稳定前缀</button
  ><span class="gloss-pop" data-md-skip
    >请求之间逐字节相同的那段开头。所有可缓存的东西都住在这里。</span
  ></span
>
```

```css
.gloss {
  appearance: none;
  background: none;
  border: 0;
  padding: 0;
  font: inherit;
  color: inherit;
  cursor: help;
  text-decoration: underline dotted var(--color-border);
  text-underline-offset: 3px;
}
.gloss:is(:hover, :focus-visible) {
  text-decoration-color: var(--color-primary);
}
.gloss-wrap {
  position: relative;
  display: inline-block;
}
.gloss-pop {
  position: absolute;
  z-index: 40;
  left: 50%;
  bottom: 100%;
  transform: translateX(-50%);
  margin-bottom: 0.5rem;
  width: min(19rem, 78vw);
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-card);
  color: var(--color-muted-foreground);
  font-size: 0.8rem;
  font-weight: 400;
  line-height: 1.6;
  text-align: left;
  display: none;
  pointer-events: none; /* 不要用 visibility/opacity，见下 */
}
.gloss-wrap:is(:hover, :focus-within) .gloss-pop {
  display: block;
}
.gloss-pop[data-below] {
  bottom: auto;
  top: 100%;
  margin: 0.5rem 0 0;
}
```

```js
/* 贴视口边时横向夹回来；靠页顶时翻到下方 */
document.querySelectorAll(".gloss-wrap").forEach((w) => {
  const pop = w.querySelector(".gloss-pop");
  const place = () => {
    pop.style.transform = "translateX(-50%)";
    delete pop.dataset.below;
    if (w.getBoundingClientRect().top < 190) pop.dataset.below = "";
    const r = pop.getBoundingClientRect(),
      pad = 12;
    let shift = 0;
    if (r.left < pad) shift = pad - r.left;
    else if (r.right > innerWidth - pad) shift = innerWidth - pad - r.right;
    if (shift) pop.style.transform = `translateX(calc(-50% + ${shift}px))`;
  };
  w.addEventListener("pointerenter", place);
  w.addEventListener("focusin", place);
});
```

四个坑：

- **藏浮层必须用 `display: none`，不能用 `visibility: hidden` 或 `opacity: 0`。**
  绝对定位元素即使不可见也照样撑出横向滚动，`build.py` 的窄屏检查会直接报 ERROR。
  代价是没有淡入过渡 —— 值得。
- 触发器必须是真 `<button>`，键盘能 focus，`:focus-within` 才生效。
- 浮层加 `data-md-skip`，否则每个术语的解释都会掉进 Markdown 导出里，正文被切碎。
- `.gloss-wrap` 内部不能有多余空白，否则术语和标点之间会多出一个空格；用示例里那种把 `>` 折到下一行的写法。

## 用动效编码论点，不要用它装饰

一段动效要么承载页面的论点，要么就不该存在。

反例与正例是同一张图：讲「缓存失效只向右流动」时，把失效的层级涂成均匀的红色块，
读者只知道「这几块变红了」；**换成一道从 position 0 向右扫过去、逐层错开的渐变**，
方向本身就成了论据 —— 读者不用读图注也知道失效是往哪边跑的。

```css
.seg {
  position: relative;
}
.seg::after {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 0;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent,
    color-mix(in oklab, var(--color-destructive) 34%, transparent)
  );
}
.seg[data-state="hit"]::after {
  animation: seg-wipe 0.45s var(--ease-expo) both;
  animation-delay: var(--wipe-delay, 0s); /* 逐层错开，波才看得出方向 */
}
@keyframes seg-wipe {
  from {
    width: 0;
  }
  to {
    width: 100%;
  }
}
@media (prefers-reduced-motion: reduce) {
  .seg[data-state="hit"]::after {
    animation: none;
    width: 100%;
  }
}
```

```js
tiers.forEach((el, k) => {
  if (k < from) {
    delete el.dataset.state;
    return;
  }
  el.style.setProperty("--wipe-delay", (k - from) * 0.08 + "s");
  el.dataset.state = "";
  delete el.dataset.state;
  void el.offsetWidth; // 强制回流，动画才会重放
  el.dataset.state = "hit";
});
```

`void el.offsetWidth` 那一行不能省：CSS 动画只在类名**变化**时触发，同一个状态重复设置
不会重放，波就只在第一次点击时出现。

## 滑块与其它原生控件

**滑块的样式由骨架给，页面不要自己写，也不要靠 basecoat。**
basecoat 只覆盖 `.field > input[type=range]` 与 `.input[type=range]` 两种包裹；
页面自造一个 `.knob` 之类的壳把滑块包进去，两个都不命中，滑块就退回操作系统外观 ——
macOS 上是一条亮蓝色粗轨道，跟任何调色板都不搭。**它不报错，只是难看。**

骨架连裸 `input[type=range]` 一起兜住了，所以随便怎么包都对；`build.py` 有一道 WARN
守着那段样式别被删掉。轨道的已填充部分由 `--slider-value` 驱动，骨架自带一段事件委托
在同步它 —— 不要指望 basecoat JS，那份 JS 只有页面用到 tabs / dropdown 时才会被内联。

旋钮的标签这样写，值靠右、等宽、随拖动实时更新：

```html
<label class="knob">
  <span class="knob-label"
    >前缀 P₀ <output for="k-p0" id="k-p0-out">15K</output></span
  >
  <input
    type="range"
    id="k-p0"
    min="2000"
    max="60000"
    step="1000"
    value="15000"
  />
</label>
```

## 控件用等宽，正文用正文字体

图里的 chips、旋钮标签、统计数字全部走 `var(--font-mono)`，正文保持 `--font-sans`。
这一条是「仪表盘感」的全部来源：控件是仪器，正文是文章，两者不该是同一种声音。
中文控件文案都很短，等宽的缺点在这个尺度上看不出来。

**分类色与语义色别混。** 模型身份、数据序列走 `var(--chart-1..5)`；
「坏了 / 比对照组差 / 失效」走 `var(--color-destructive)`。同一张图里两者同时存在很常见
（条带按模型上色、曲线按好坏上色），分错了读者就读不出哪个是身份、哪个是判断。

## 数字滚动（odometer）

统计数字瞬跳，读者看不出哪个数变了。让每一位像里程表一样滚过去，变化本身就成了信息。

**不要为此引库。** Motion 的浏览器版 140 KB（gzip 46 KB），而本 skill 的页面是单文件、
逐份转发的，没有跨页缓存可摊薄；Calligraph 更是 React 组件（peer deps 是 react + react-dom），
在原生页面里根本用不了。下面这段是从 Calligraph 的 Slots 里把做法搬出来的原生实现，
连缓动一起不到 120 行。

```css
.odo {
  display: inline-flex;
  align-items: baseline;
  font-variant-numeric: tabular-nums;
}
.odo-static {
  display: inline-block;
  white-space: pre;
}
.odo-col {
  position: relative;
  display: inline-block;
  vertical-align: top;
  line-height: 1.15;
  mask-image: linear-gradient(
    to bottom,
    transparent 0,
    #000 0.3em,
    #000 calc(100% - 0.3em),
    transparent 100%
  );
  mask-repeat: no-repeat;
  mask-size: 100% 100%;
  -webkit-mask-image: linear-gradient(
    to bottom,
    transparent 0,
    #000 0.3em,
    #000 calc(100% - 0.3em),
    transparent 100%
  );
  -webkit-mask-repeat: no-repeat;
  -webkit-mask-size: 100% 100%;
}
.odo-w {
  visibility: hidden;
} /* 宽度撑子，同时定住基线 */
.odo-d {
  position: absolute;
  inset: 0 0 auto 0;
  text-align: center;
}
.odo-text {
  /* 给导出与读屏用，视觉上不占位 */
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
```

```js
/* ── 缓动。与骨架的 --ease-expo / --ease-spring 是同一条曲线 ── */
const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
const EASE = {
  expo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  spring: (t) => {
    const z = 0.72,
      w = 2 * Math.PI * 1.7,
      wd = w * Math.sqrt(1 - z * z);
    if (t >= 1) return 1;
    return (
      1 -
      Math.exp(-z * w * t) *
        (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t))
    );
  },
};

/* ── 数字滚动（odometer）───────────────────────────────────────────────
   做法借自 Calligraph 的 Slots（React + Motion），这里是原生实现。三个关键决定：

   1. 每一位只渲染 10 个 span，按环形距离钳到 ±1 行 —— 窗口附近永远只有三个数字，
      不是一条 0–9 的长纸带。
   2. 每一位各记一个**不封顶**的计数器 cum：9→0 时 cum 加 1 而不是减 9，
      所以进位是往前滚，不会倒回去。
   3. 上下用 mask 淡出，不用 overflow:hidden —— 后者会把行内基线搞坏，
      数字就和旁边的 "$" 对不齐了。

   静止时 cum 是整数，数字正好停在窗口中央，读起来是清楚的。这也是不能直接用
   v / 10^p 连续推位置的原因：那样静止时个位会停在两个数之间。

   用法：const set = odometer(el, (v) => "$" + v.toFixed(2)); set(1.17);
   set() 可以每帧调（滑块拖动），只有位数变化时才会重建 DOM。 */
function odometer(el, format, opts = {}) {
  const dur = REDUCE ? 0 : (opts.duration ?? 420);
  const stag = REDUCE ? 0 : (opts.stagger ?? 18);
  const ease = EASE[opts.ease || "spring"];
  const isDigit = (c) => c >= "0" && c <= "9";

  el.classList.add("odo");
  const sr = document.createElement("span");
  sr.className = "odo-text";
  let cols = [],
    shape = null,
    raf = 0,
    prev = null,
    prevValue = 0;

  /* 位数变化时重建。按「从右数第几个数字」继承旧列的 cum，
     $9.70 → $10.05 这种进位才不会让所有列一起乱跳。 */
  function build(str) {
    const inherited = cols
      .slice()
      .reverse()
      .map((c) => c.cum);
    el.textContent = "";
    cols = [];
    const digits = [...str].filter(isDigit).length;
    let seen = 0;
    for (const ch of str) {
      if (!isDigit(ch)) {
        const s = document.createElement("span");
        s.className = "odo-static";
        s.textContent = ch;
        s.setAttribute("aria-hidden", "true");
        s.dataset.mdSkip = "";
        el.appendChild(s);
        continue;
      }
      const fromRight = digits - 1 - seen;
      const col = document.createElement("span");
      col.className = "odo-col";
      col.setAttribute("aria-hidden", "true");
      /* 十个数字面不能进 Markdown 导出，否则一个数字导出成 "0123456789" ×N。
         导出读的是下面那个 .odo-text。 */
      col.dataset.mdSkip = "";
      const w = document.createElement("span");
      w.className = "odo-w";
      w.textContent = "0";
      col.appendChild(w);
      const faces = [];
      for (let n = 0; n < 10; n++) {
        const d = document.createElement("span");
        d.className = "odo-d";
        d.textContent = n;
        col.appendChild(d);
        faces.push(d);
      }
      const start = inherited[fromRight];
      cols.push({
        faces,
        cum: start === undefined ? Number(ch) : start,
        cur: start === undefined ? Number(ch) : start,
        i: seen,
      });
      el.appendChild(col);
      seen++;
    }
    el.appendChild(sr);
  }

  const mod = (n, m) => ((n % m) + m) % m;

  function paint() {
    for (const c of cols) {
      for (let n = 0; n < 10; n++) {
        let off = mod(n - c.cur, 10);
        if (off > 5) off -= 10;
        const y = -Math.max(-1, Math.min(1, off)) * 100;
        c.faces[n].style.transform = `translateY(${y}%)`;
      }
    }
  }

  function run() {
    const from = cols.map((c) => c.cur);
    const t0 = performance.now();
    cancelAnimationFrame(raf);
    const step = (now) => {
      let busy = false;
      cols.forEach((c, i) => {
        const k = Math.max(0, (now - t0 - i * stag) / (dur || 1));
        if (k < 1) busy = true;
        c.cur = from[i] + (c.cum - from[i]) * ease(Math.min(1, k));
      });
      paint();
      if (busy) raf = requestAnimationFrame(step);
    };
    if (dur === 0) {
      cols.forEach((c) => (c.cur = c.cum));
      paint();
      return;
    }
    raf = requestAnimationFrame(step);
  }

  return function set(value) {
    const str = String(format(value));
    if (str === prev) return;
    const sh = [...str].map((c) => (isDigit(c) ? "#" : c)).join("");
    if (sh !== shape) {
      shape = sh;
      build(str);
    }
    sr.textContent = str;
    el.setAttribute("aria-label", str);
    /* 方向由值本身决定：数字变大就往前滚，变小就往回滚 —— 9→0 才不会
       在「加一」和「减九」之间随机挑一个。 */
    const dir = prev === null ? 1 : Math.sign(value - prevValue) || 1;
    prev = str;
    prevValue = value;
    let seen = 0;
    for (const ch of str) {
      if (!isDigit(ch)) continue;
      const c = cols[seen++];
      const target = Number(ch);
      const old = mod(c.cum, 10);
      let diff = target - old;
      if (dir > 0 && diff < 0) diff += 10;
      if (dir < 0 && diff > 0) diff -= 10;
      c.cum += diff;
    }
    run();
  };
}
```

三个关键决定，照抄时不要改：

- **每一位只渲染 10 个 span，按环形距离钳到 ±1 行。** 窗口附近永远只有三个数字，
  DOM 里不是一条 0–9 的长纸带。
- **每一位各记一个不封顶的计数器 `cum`。** 9→0 时 `cum` 加 1 而不是减 9，进位才是往前滚的。
  静止时 `cum` 是整数，数字正好停在窗口中央 —— 这就是不能直接拿 `v / 10^p` 连续推位置的原因，
  那样静止时个位会停在两个数之间，读起来是糊的。
- **上下用 `mask` 淡出，不用 `overflow: hidden`。** 后者会破坏行内基线，数字就和旁边的
  `$`、`,` 对不齐了。`mask-repeat: no-repeat` 必须写，否则渐变会平铺，等于没遮。
- **`Math.max(0, …)` 那一夹不是防御性代码。** `performance.now()` 在无头浏览器和虚拟时钟下
  会回退，`k` 变负时缓动函数会炸成几千倍，数字直接跳成 `$-2363.285`。这个坑真踩过。

其它注意：

- 十个数字面带 `data-md-skip`，导出读的是 `.odo-text` —— 少了这条，一个数字会导出成
  `0123456789` 重复 N 遍。
- `set()` 可以每帧调（滑块拖动），只有**位数**变化时才重建 DOM。
- `prefers-reduced-motion` 下 duration 归零，直接落位。
- 一页里滚动的数字不要超过一屏能看到的三五个。全页都在滚等于全页都不重要。

## 缓动

骨架给了两条，`--ease-expo` 与 `--ease-spring`，**别再造第三条**。

| token           | 曲线                                             | 用在哪                   |
| --------------- | ------------------------------------------------ | ------------------------ |
| `--ease-expo`   | `cubic-bezier(0.19, 1, 0.22, 1)`                 | 位移、淡入淡出、折叠展开 |
| `--ease-spring` | ζ=0.72 的阻尼弹簧采样成 `linear()`，约 3.8% 过冲 | 数字、尺寸、拖拽落位     |

JS 里要一样的手感就用上面 odometer 代码里的 `EASE.expo` / `EASE.spring` ——
两边是同一条曲线，CSS 动的元素和 JS 动的数字才不会各走各的。

时长：位移与淡入 180–260 ms，数字滚动 400–450 ms，页面级揭示 ≤ 600 ms。
超过 600 ms 的动效读者会开始等它，那就成了负担。

## 可点击的 SVG 节点

```html
<svg viewBox="0 0 720 220" role="img" aria-label="请求处理流程">
  <g
    class="node"
    tabindex="0"
    role="button"
    data-node="ingress"
    aria-label="ingress 节点"
  >
    <rect x="16" y="80" width="140" height="56" rx="8" />
    <text x="86" y="113" text-anchor="middle">ingress</text>
  </g>
</svg>
<aside id="node-detail" aria-live="polite"></aside>
```

```css
svg .node rect {
  fill: var(--color-card);
  stroke: var(--color-border);
  stroke-width: 1.5;
}
svg .node text {
  fill: var(--color-foreground);
  font: 500 12px var(--font-sans);
}
svg .node {
  cursor: pointer;
}
svg .node:is(:hover, :focus-visible) rect {
  stroke: var(--color-primary);
}
svg .node[aria-pressed="true"] rect {
  stroke: var(--color-primary);
  stroke-width: 2.5;
}
```

```js
const DETAIL = { ingress: "<h3>ingress</h3><p>TLS 终止与路由。</p>" /* … */ };
const pick = (g) => {
  document
    .querySelectorAll("svg .node")
    .forEach((n) => n.setAttribute("aria-pressed", String(n === g)));
  document.getElementById("node-detail").innerHTML =
    DETAIL[g.dataset.node] || "";
};
document.querySelectorAll("svg .node").forEach((g) => {
  g.addEventListener("click", () => pick(g));
  g.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      pick(g);
    }
  });
});
```

## 筛选 / 搜索

```js
const q = document.getElementById("filter");
q.addEventListener("input", () => {
  const t = q.value.trim().toLowerCase();
  let n = 0;
  document.querySelectorAll("[data-searchable]").forEach((el) => {
    const hit = !t || el.textContent.toLowerCase().includes(t);
    el.hidden = !hit;
    if (hit) n++;
  });
  document.getElementById("filter-count").textContent = `${n} 项`;
});
```

`hidden` 的元素会被「复制为 Markdown」跳过 —— 筛选后导出得到的正是读者看到的内容。

## 侧栏目录 + 滚动高亮

**骨架已内置，不要手写。** `assets/shell.html` 会扫描 `#doc` 的 h2/h3 自动生成右侧目录：
指示条随滚动滑动到当前节，点击条目平滑跳转。≥80rem 且条目 ≥2 时出现，否则整块不存在。
单个标题豁免加 `data-toc-skip`。目录整块带 `data-md-skip`，不进 Markdown 导出。

## 复制单个代码块

顶部工具条已经能导出整页 Markdown；只有当读者需要**单独**拿走某段代码时才加这个。

```js
document.querySelectorAll("pre").forEach((pre) => {
  const b = document.createElement("button");
  b.className = "btn";
  b.dataset.variant = "ghost";
  b.dataset.size = "icon-sm";
  b.setAttribute("aria-label", "复制代码");
  b.dataset.mdSkip = "";
  b.innerHTML = '<i data-lucide="copy"></i>';
  b.onclick = () => {
    navigator.clipboard.writeText(pre.textContent);
    b.dataset.variant = "secondary";
    setTimeout(() => (b.dataset.variant = "ghost"), 1200);
  };
  pre.style.position = "relative";
  b.style.cssText = "position:absolute;top:.5rem;right:.5rem";
  pre.appendChild(b);
});
```

注意：这段代码在 `build.py` 跑完之后**不会**再被处理，`<i data-lucide>` 是运行时插入的，替换不到。
需要图标时直接把 SVG 源码写进 `innerHTML`，或者改用文字标签。
