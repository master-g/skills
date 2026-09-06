/* show-me 图表运行时 —— 只有工具函数，没有图型。
   页面出现 data-chart 时由 build.py 内联到 JS 占位符处；图型代码从 assets/gallery/ 复制。
   颜色一律写 token（var(--ink) / var(--ink-45) / var(--chart-hero)），fill/stroke 里的 var() 会被搬进 style。 */
window.showMeChart = (function () {
  const NS = "http://www.w3.org/2000/svg";
  const PAINT = new Set(["fill", "stroke"]);
  const el = (p, t, a = {}) => {
    const n = document.createElementNS(NS, t);
    let style = "";
    for (const k in a) {
      if (a[k] == null) continue;
      if (PAINT.has(k) && String(a[k]).includes("var("))
        style += `${k}:${a[k]};`;
      else if (k === "style") style += a[k] + ";";
      else n.setAttribute(k, a[k]);
    }
    if (style) n.setAttribute("style", style);
    p.appendChild(n);
    return n;
  };
  const txt = (p, a, s) => {
    const n = el(p, "text", a);
    n.textContent = s;
    return n;
  };
  const tip = (n, s) => {
    const t = document.createElementNS(NS, "title");
    t.textContent = s;
    n.appendChild(t);
  };
  /* 确定性伪随机：演示数据与肌理抖动刷新后长得一样，截图可回归 */
  const rnd = (i, k) =>
    Math.abs(((i * 73856093) ^ (k * 19349663)) % 1000) / 1000;
  const D2R = Math.PI / 180;
  const pol = (cx, cy, r, deg) => [
    cx + r * Math.cos(deg * D2R),
    cy + r * Math.sin(deg * D2R),
  ];
  const sect = (cx, cy, r0, r1, a0, a1) => {
    const big = a1 - a0 > 180 ? 1 : 0;
    const [xa, ya] = pol(cx, cy, r1, a0),
      [xb, yb] = pol(cx, cy, r1, a1);
    const [xc, yc] = pol(cx, cy, r0, a1),
      [xd, yd] = pol(cx, cy, r0, a0);
    return `M${xa} ${ya} A${r1} ${r1} 0 ${big} 1 ${xb} ${yb} L${xc} ${yc} A${r0} ${r0} 0 ${big} 0 ${xd} ${yd} Z`;
  };
  /* 手绘感圆：圆周叠两个慢波加噪声，seed 定形 */
  const blob = (x, y, r, seed) => {
    const n = Math.max(14, Math.round(r * 1.6)),
      pts = [];
    for (let t = 0; t < n; t++) {
      const a = (t / n) * Math.PI * 2;
      const w =
        1 +
        0.055 * Math.sin(a * 2 + seed * 7) +
        0.04 * Math.sin(a * 3 + seed * 13) +
        (rnd(seed + t, 3) - 0.5) * 0.03;
      pts.push([x + Math.cos(a) * r * w, y + Math.sin(a) * r * w]);
    }
    let d = `M${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
    for (let t = 0; t < n; t++) {
      const p = pts[t],
        q = pts[(t + 1) % n];
      d += ` Q${p[0].toFixed(1)} ${p[1].toFixed(1)} ${((p[0] + q[0]) / 2).toFixed(1)} ${((p[1] + q[1]) / 2).toFixed(1)}`;
    }
    return d + " Z";
  };
  const motion = !matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fmt = (v, d = 0) =>
    Number(v).toLocaleString("en-US", {
      maximumFractionDigits: d,
      minimumFractionDigits: d,
    });

  /* reveal：滚入视野才画，滚出视野停；figure 里的 .fig-replay 按钮重播。
     循环定时器与 rAF 登记在 svg 上，停/重播前清掉 —— 循环图型不停会一直逼出重绘，
     页面越长越贵（图滚出视口后开销反而更高）。静态图画完即摘掉观察，永不重画。
     reduced-motion 下同样画：CSS 动画为 none，循环图型自己看 motion 决定走静态末帧。 */
  const reveal = (svg, fn) => {
    const stop = () => {
      const live = (svg._timers || []).length;
      (svg._timers || []).forEach((t) => {
        clearInterval(t);
        cancelAnimationFrame(t);
      });
      svg._timers = [];
      svg._live = false;
      return live;
    };
    const go = () => {
      stop();
      // 只清图形，保留无障碍契约要求的 <title>/<desc>
      [...svg.children].forEach((c) => {
        if (!/^(title|desc)$/i.test(c.tagName)) c.remove();
      });
      svg._live = true;
      fn(svg, { keep: (t) => svg._timers.push(t), motion });
    };
    /* 两道阈值：露出 20% 起画，完全离开才停 —— 中间的部分可见不来回切。 */
    const io = new IntersectionObserver(
      (es) => {
        const r = es[es.length - 1].intersectionRatio;
        if (r >= 0.2) {
          if (!svg._live) go();
        } else if (r === 0 && svg._live && !stop()) io.unobserve(svg);
      },
      { threshold: [0, 0.2] }
    );
    io.observe(svg);
    const btn = svg.closest("figure")?.querySelector(".fig-replay");
    if (btn) btn.addEventListener("click", go);
    svg._replay = go;
  };
  return { el, txt, tip, rnd, pol, sect, blob, reveal, motion, fmt, NS };
})();
