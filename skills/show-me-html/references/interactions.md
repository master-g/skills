# 交互配方

basecoat 覆盖不到的交互，代码在这里。**照抄，不要重写** —— 这些都已经处理过键盘可达性与边界情况。

组件自身的交互（标签页、下拉菜单、对话框、折叠）由 basecoat 或浏览器原生提供，见 `components.md`。

共同约束：

- 所有可操作元素必须是真 `<button>` / `<a>` / `<input>`，或带 `tabindex="0"` + 键盘处理。
- 页面 chrome（工具条、筛选器、导出按钮）加 `data-md-skip`，否则会被复制进 Markdown。
- 自动播放的动效包在 `@media (prefers-reduced-motion: no-preference)` 里。

---

## 拖拽排序（看板 / 优先级列表）

原生 HTML5 拖放，附带键盘替代路径 —— 只有鼠标能用的看板等于没做无障碍。

```html
<div class="board" data-md-skip-controls>
  <section class="col" data-col="todo"><h3>待处理 <span class="badge" data-count>0</span></h3>
    <div class="slot"></div>
  </section>
  <section class="col" data-col="doing"><h3>进行中 <span class="badge" data-count>0</span></h3>
    <div class="slot"></div>
  </section>
</div>
```

```css
.board { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr)); }
.slot { min-height: 6rem; display: grid; gap: .5rem; align-content: start;
        padding: .5rem; border: 1px dashed var(--color-border); border-radius: var(--radius); }
.slot.over { border-color: var(--color-primary); background: var(--color-accent); }
.ticket { cursor: grab; }
.ticket.dragging { opacity: .5; }
```

```js
let dragged = null;
document.querySelectorAll('.ticket').forEach(el => {
  el.draggable = true;
  el.tabIndex = 0;
  el.addEventListener('dragstart', () => { dragged = el; el.classList.add('dragging'); });
  el.addEventListener('dragend',   () => { el.classList.remove('dragging'); dragged = null; recount(); });
  // 键盘替代：← → 在列之间移动
  el.addEventListener('keydown', e => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    const slots = [...document.querySelectorAll('.slot')];
    const i = slots.indexOf(el.closest('.slot'));
    const next = slots[i + (e.key === 'ArrowRight' ? 1 : -1)];
    if (next) { next.appendChild(el); el.focus(); recount(); }
  });
});
document.querySelectorAll('.slot').forEach(slot => {
  slot.addEventListener('dragover', e => { e.preventDefault(); slot.classList.add('over'); });
  slot.addEventListener('dragleave', () => slot.classList.remove('over'));
  slot.addEventListener('drop', e => {
    e.preventDefault(); slot.classList.remove('over');
    if (dragged) slot.appendChild(dragged);
    recount();
  });
});
function recount() {
  document.querySelectorAll('.col').forEach(c =>
    c.querySelector('[data-count]').textContent = c.querySelectorAll('.ticket').length);
}
recount();
```

## 幻灯片键盘导航

```js
const slides = [...document.querySelectorAll('.slide')];
let cur = 0;
const show = i => {
  cur = Math.max(0, Math.min(slides.length - 1, i));
  slides[cur].scrollIntoView({ behavior: 'smooth' });
  document.getElementById('pageno').textContent = `${cur + 1} / ${slides.length}`;
  location.hash = 's' + (cur + 1);
};
addEventListener('keydown', e => {
  if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); show(cur + 1); }
  if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); show(cur - 1); }
  if (e.key === 'Home') show(0);
  if (e.key === 'End') show(slides.length - 1);
});
show(+(location.hash.match(/\d+/) || [1])[0] - 1);
```

页面上必须写明「← → 翻页」，否则读者不知道能翻。

## 旋钮驱动实时预览

```html
<div class="field">
  <label for="k-radius">圆角 <output for="k-radius">8</output>px</label>
  <input type="range" id="k-radius" min="0" max="24" value="8" data-bind="--demo-radius" data-unit="px">
</div>
<div class="preview" style="border-radius: var(--demo-radius, 8px)">…</div>
```

```js
document.querySelectorAll('[data-bind]').forEach(inp => {
  const out = document.querySelector(`output[for="${inp.id}"]`);
  const sync = () => {
    document.documentElement.style.setProperty(inp.dataset.bind, inp.value + (inp.dataset.unit || ''));
    if (out) out.textContent = inp.value;
    document.querySelectorAll('[data-snippet]').forEach(render);
  };
  inp.addEventListener('input', sync);
  sync();
});
```

`data-snippet` 是随旋钮更新的 markup 展示块 —— 读者要能把调好的结果抄走，否则旋钮只是玩具。

## 可点击的 SVG 节点

```html
<svg viewBox="0 0 720 220" role="img" aria-label="请求处理流程">
  <g class="node" tabindex="0" role="button" data-node="ingress" aria-label="ingress 节点">
    <rect x="16" y="80" width="140" height="56" rx="8"/>
    <text x="86" y="113" text-anchor="middle">ingress</text>
  </g>
</svg>
<aside id="node-detail" aria-live="polite"></aside>
```

```css
svg .node rect { fill: var(--color-card); stroke: var(--color-border); stroke-width: 1.5; }
svg .node text { fill: var(--color-foreground); font: 500 12px var(--font-sans); }
svg .node { cursor: pointer; }
svg .node:is(:hover, :focus-visible) rect { stroke: var(--color-primary); }
svg .node[aria-pressed="true"] rect { stroke: var(--color-primary); stroke-width: 2.5; }
```

```js
const DETAIL = { ingress: '<h3>ingress</h3><p>TLS 终止与路由。</p>' /* … */ };
const pick = g => {
  document.querySelectorAll('svg .node').forEach(n => n.setAttribute('aria-pressed', String(n === g)));
  document.getElementById('node-detail').innerHTML = DETAIL[g.dataset.node] || '';
};
document.querySelectorAll('svg .node').forEach(g => {
  g.addEventListener('click', () => pick(g));
  g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(g); } });
});
```

## 筛选 / 搜索

```js
const q = document.getElementById('filter');
q.addEventListener('input', () => {
  const t = q.value.trim().toLowerCase();
  let n = 0;
  document.querySelectorAll('[data-searchable]').forEach(el => {
    const hit = !t || el.textContent.toLowerCase().includes(t);
    el.hidden = !hit;
    if (hit) n++;
  });
  document.getElementById('filter-count').textContent = `${n} 项`;
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
document.querySelectorAll('pre').forEach(pre => {
  const b = document.createElement('button');
  b.className = 'btn'; b.dataset.variant = 'ghost'; b.dataset.size = 'icon-sm';
  b.setAttribute('aria-label', '复制代码'); b.dataset.mdSkip = '';
  b.innerHTML = '<i data-lucide="copy"></i>';
  b.onclick = () => { navigator.clipboard.writeText(pre.textContent); b.dataset.variant = 'secondary';
                      setTimeout(() => b.dataset.variant = 'ghost', 1200); };
  pre.style.position = 'relative';
  b.style.cssText = 'position:absolute;top:.5rem;right:.5rem';
  pre.appendChild(b);
});
```

注意：这段代码在 `build.py` 跑完之后**不会**再被处理，`<i data-lucide>` 是运行时插入的，替换不到。
需要图标时直接把 SVG 源码写进 `innerHTML`，或者改用文字标签。
