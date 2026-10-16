/* ── 定尺卡（share-card）：视口比卡窄时整张等比缩小，卡内几何不变 ── */
(function () {
  var sheets = document.querySelectorAll(".sheet");
  if (!sheets.length) return;
  var fit = function () {
    sheets.forEach(function (s) {
      var stage = s.parentElement;
      s.style.transform = "";
      stage.style.height = "";
      var k = Math.min(1, stage.clientWidth / s.offsetWidth);
      if (k < 1) {
        s.style.transform = "scale(" + k + ")";
        stage.style.height = s.offsetHeight * k + "px";
        stage.style.justifyContent = "flex-start";
      } else {
        stage.style.justifyContent = "";
      }
    });
  };
  fit();
  addEventListener("resize", fit);
})();
/* ── 滑块填充 ──────────────────────────────────────────────────────
   轨道的已填充部分由 --slider-value 驱动。骨架始终同步这个变量，
   因而只使用滑块的页面不依赖条件内联的组件行为 JS。 */
(function () {
  function sync(el) {
    var min = Number(el.min || 0),
      max = Number(el.max === "" ? 100 : el.max);
    var pct = max === min ? 0 : ((Number(el.value) - min) / (max - min)) * 100;
    el.style.setProperty("--slider-value", pct + "%");
  }
  document.querySelectorAll('input[type="range"]').forEach(sync);
  /* 事件委托：后插进来的滑块也照样跟着走 */
  document.addEventListener("input", function (e) {
    if (e.target.matches && e.target.matches('input[type="range"]'))
      sync(e.target);
  });
})();

/* ── 代码工具条：换行 / 复制 ──
   给每个 pre > code 注入两个按钮。工具条带 data-md-skip，导出 Markdown 时不出现。
   复制走 navigator.clipboard，失败时退回 execCommand；反馈先行，不等 promise。 */
(function () {
  function mk(label, title) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "btn";
    b.setAttribute("data-variant", "outline");
    b.title = title;
    b.textContent = label;
    return b;
  }
  function copyText(text) {
    try {
      return navigator.clipboard.writeText(text);
    } catch (e) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
      } catch (e2) {}
      ta.remove();
    }
  }
  document.querySelectorAll("pre > code").forEach(function (code) {
    var pre = code.parentNode;
    if (pre.querySelector(".code-tools")) return;
    var bar = document.createElement("div");
    bar.className = "code-tools";
    bar.setAttribute("data-md-skip", "");
    var wrap = mk("换行", "切换自动换行");
    wrap.setAttribute("aria-pressed", "false");
    wrap.addEventListener("click", function () {
      var on = pre.dataset.wrap !== "on";
      pre.dataset.wrap = on ? "on" : "off";
      wrap.setAttribute("aria-pressed", String(on));
    });
    var copy = mk("复制", "复制代码");
    copy.addEventListener("click", function () {
      copy.textContent = "已复制";
      setTimeout(function () {
        copy.textContent = "复制";
      }, 1600);
      copyText(code.textContent.replace(/\n$/, ""));
    });
    bar.appendChild(wrap);
    bar.appendChild(copy);
    pre.appendChild(bar);
  });
})();

/* ── 主题三态切换 ── */
(function () {
  var root = document.documentElement;
  var mq = matchMedia("(prefers-color-scheme: dark)");
  function apply(t) {
    root.dataset.theme = t;
    root.classList.toggle(
      "dark",
      t === "dark" || (t === "system" && mq.matches)
    );
    document.querySelectorAll("[data-theme-set]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.themeSet === t));
    });
  }
  document.querySelectorAll("[data-theme-set]").forEach(function (b) {
    b.addEventListener("click", function () {
      var t = b.dataset.themeSet;
      try {
        t === "system"
          ? localStorage.removeItem("show-me-theme")
          : localStorage.setItem("show-me-theme", t);
      } catch (e) {}
      apply(t);
    });
  });
  mq.addEventListener("change", function () {
    if (root.dataset.theme === "system") apply("system");
  });
  apply(root.dataset.theme || "system");
})();

/* ── 复制为 Markdown ──
遍历 #doc（或 [data-md-root]）生成 GFM。跳过 [data-md-skip] / [hidden] / 脚本 / 弹层。 */
(function () {
  var SKIP = new Set([
    "SCRIPT",
    "STYLE",
    "TEMPLATE",
    "DIALOG",
    "NOSCRIPT",
    "SVG",
    "CANVAS",
  ]);
  var INLINE_ONLY = new Set([
    "A",
    "CODE",
    "STRONG",
    "B",
    "EM",
    "I",
    "DEL",
    "S",
    "SPAN",
    "KBD",
    "SMALL",
    "ABBR",
    "MARK",
    "SUP",
    "SUB",
    "BR",
    "IMG",
    "TIME",
    "MATH",
    "U",
    "Q",
    "LABEL",
    "OUTPUT",
  ]);
  /* 组件容器与目录生成器的排除表保持一致。容器里的标题级别由组件文档固定
        （卡片头 h3、item / alert 用 h4），和所在节无关；导出时改排到当前节标题的下一级，
        否则会出现 h2 直跳 h4、工单卡与泳道同为 h3。outline 是最近一个节标题的级别。 */
  var COMPONENT = ".card, .fig-box, .alert, .item, .accordion, .dialog, .empty";
  var outline = 1;

  function skipped(el) {
    return (
      SKIP.has(el.tagName.toUpperCase()) ||
      el.hasAttribute("data-md-skip") ||
      el.hasAttribute("hidden") ||
      el.getAttribute("aria-hidden") === "true"
    );
  }
  function txt(s) {
    return (s || "").replace(/\s+/g, " ");
  }

  function inline(node) {
    var out = "";
    node.childNodes.forEach(function (n) {
      if (n.nodeType === 3) {
        out += txt(n.nodeValue);
        return;
      }
      if (n.nodeType !== 1 || skipped(n)) return;
      var t = n.tagName.toUpperCase(),
        inner = inline(n);
      if (t === "MATH") {
        /* 公式导出 LaTeX 源：build 编译时留下的 annotation；没有就退回可读文本 */
        var ann = n.querySelector('annotation[encoding="application/x-tex"]');
        var tex = ann ? ann.textContent.trim() : txt(n.textContent).trim();
        out +=
          n.getAttribute("display") === "block"
            ? "\n\n$$" + tex + "$$\n\n"
            : "$" + tex + "$";
        return;
      }
      if (t === "BR") out += "  \n";
      else if (t === "IMG")
        out +=
          "![" + (n.alt || "") + "](" + (n.getAttribute("src") || "") + ")";
      else if (
        t === "CODE" ||
        t === "KBD" ||
        n.classList.contains("badge") ||
        n.classList.contains("kbd")
      )
        out += inner.trim() ? "`" + inner.trim() + "`" : "";
      else if (t === "A") {
        var href = n.getAttribute("href") || "";
        out +=
          href && !href.startsWith("#")
            ? "[" + inner.trim() + "](" + href + ")"
            : inner;
      } else if (t === "STRONG" || t === "B")
        out += inner.trim() ? "**" + inner.trim() + "**" : "";
      else if (t === "EM" || t === "I")
        out += inner.trim() ? "*" + inner.trim() + "*" : "";
      else if (t === "DEL" || t === "S")
        out += inner.trim() ? "~~" + inner.trim() + "~~" : "";
      else out += inner;
    });
    return out;
  }

  function cell(el) {
    return inline(el).trim().replace(/\|/g, "\\|").replace(/\n/g, " ");
  }

  function table(el) {
    var rows = Array.from(el.querySelectorAll("tr")).filter(function (r) {
      return !skipped(r);
    });
    if (!rows.length) return "";
    /* 没有表头行的表：全部行当数据，列名留空占位 ——
          否则第一行数据会被当成表头，语义就错了 */
    var hasTh = !!rows[0].querySelector("th");
    var head = rows[0],
      body = hasTh ? rows.slice(1) : rows;
    var cols = Array.from(head.children).map(function (c, i) {
      return hasTh ? cell(c) : "列" + (i + 1);
    });
    var out =
      "| " +
      cols.join(" | ") +
      " |\n|" +
      cols
        .map(function () {
          return " --- ";
        })
        .join("|") +
      "|\n";
    body.forEach(function (r) {
      out += "| " + Array.from(r.children).map(cell).join(" | ") + " |\n";
    });
    return out;
  }

  function list(el, depth) {
    var ordered = el.tagName === "OL",
      i = 0,
      out = "";
    Array.from(el.children).forEach(function (li) {
      if (li.tagName !== "LI" || skipped(li)) return;
      i++;
      var marker = ordered ? i + ". " : "- ";
      var pad = "  ".repeat(depth);
      var sub = "";
      var own = document.createElement("div");
      Array.from(li.childNodes).forEach(function (n) {
        if (n.nodeType === 1 && (n.tagName === "UL" || n.tagName === "OL"))
          /* 深层嵌套拍平到本级：GFM 对超过 4–5 层的子列表解析不稳，保内容齐整优先 */
          sub += list(n, depth < 6 ? depth + 1 : depth);
        else own.appendChild(n.cloneNode(true));
      });
      var text = inline(own).trim();
      if (text) out += pad + marker + text + "\n";
      out += sub;
    });
    return out;
  }

  function block(el, depth) {
    var out = "";
    Array.from(el.children).forEach(function (n) {
      if (skipped(n)) return;
      var t = n.tagName.toUpperCase();
      if (t === "SUMMARY")
        return; /* DETAILS 分支已单独输出，这里再走一遍会裸文本重复 */
      if (/^H[1-6]$/.test(t)) {
        var lv = +t[1],
          box = n.closest(COMPONENT),
          up;
        if (box) {
          /* 以最外层组件里最高的标题为下一级，组件内部的相对层级照旧（卡头 h3 + 卡内 h4） */
          while ((up = box.parentElement.closest(COMPONENT))) box = up;
          var top = Math.min.apply(
            null,
            Array.from(box.querySelectorAll("h1,h2,h3,h4,h5,h6")).map(
              function (h) {
                return +h.tagName[1];
              }
            )
          );
          lv = Math.min(outline + 1 + lv - top, 6);
        } else outline = lv;
        out += "\n" + "#".repeat(lv) + " " + inline(n).trim() + "\n\n";
      } else if (t === "P") {
        var s = inline(n).trim();
        if (s) out += s + "\n\n";
      } else if (t === "UL" || t === "OL") {
        out += list(n, 0) + "\n";
      } else if (t === "PRE") {
        var code = n.querySelector("code");
        var lang =
          (code && (code.className.match(/language-([\w+-]+)/) || [])[1]) || "";
        out +=
          "```" +
          lang +
          "\n" +
          /* 取 code 的文本而不是 pre 的：pre 里还有骨架注入的工具条 */
          ((code || n).textContent || "").replace(/\n+$/, "") +
          "\n```\n\n";
      } else if (t === "TABLE") {
        out += table(n) + "\n";
      } else if (t === "MATH") {
        var ann2 = n.querySelector('annotation[encoding="application/x-tex"]');
        out +=
          "$$" +
          (ann2 ? ann2.textContent.trim() : txt(n.textContent).trim()) +
          "$$\n\n";
      } else if (t === "HR") {
        out += "---\n\n";
      } else if (t === "BLOCKQUOTE" || n.classList.contains("alert")) {
        out +=
          block(n, depth)
            .trim()
            .split("\n")
            .map(function (l) {
              return l ? "> " + l : ">";
            })
            .join("\n") + "\n\n";
      } else if (n.classList.contains("tabs")) {
        /* Markdown 没有标签页：每个标签导出成小标题 + 它的面板，隐藏的面板也要出。 */
        n.querySelectorAll('[role="tablist"] > [role="tab"]').forEach(
          function (tab) {
            out += "**" + inline(tab).trim() + "**\n\n";
            var panel = document.getElementById(
              tab.getAttribute("aria-controls")
            );
            if (panel) out += block(panel, depth);
          }
        );
      } else if (t === "DETAILS") {
        var sum = n.querySelector("summary");
        if (sum) out += "**" + inline(sum).trim() + "**\n\n";
        out += block(n, depth);
      } else if (t === "DL") {
        Array.from(n.children).forEach(function (d) {
          if (d.tagName === "DT") out += "**" + inline(d).trim() + "** — ";
          else if (d.tagName === "DD") out += inline(d).trim() + "\n\n";
        });
      } else if (
        n.children.length === 0 ||
        Array.from(n.children).every(function (c) {
          return INLINE_ONLY.has(c.tagName);
        })
      ) {
        var s2 = inline(n).trim();
        if (s2) out += s2 + "\n\n";
      } else {
        out += block(n, depth);
      }
    });
    return out;
  }

  function toMarkdown() {
    var root =
      document.querySelector("[data-md-root]") ||
      document.getElementById("doc") ||
      document.body;
    outline = 1;
    var md = block(root, 0)
      .replace(/\n{3,}/g, "\n\n")
      .trim();
    var title = document.title;
    /* 正文里只要有一级标题就不再拼 <title>：否则 eyebrow 段落排在 h1 前时，
          导出会得到两个「# 」（anti-patterns.md #2）。 */
    var hasH1 = /^# /m.test(md);
    return (hasH1 ? "" : "# " + title + "\n\n") + md + "\n";
  }

  /* 暴露给页面用：需要「下载 .md」之类的额外入口时调用它，不要另写一份转换器。 */
  window.showMeMarkdown = toMarkdown;

  document.querySelectorAll("[data-copy-md]").forEach(function (btn) {
    var icons = btn.querySelectorAll("svg, i");
    btn.addEventListener("click", async function () {
      var md = toMarkdown();
      /* 反馈先行：剪贴板图标换成对勾 1.6s。不等待 writeText —— 权限 pending 时它可能永不 settle。
      SVG 没有 hidden 反射属性，必须操作属性本身 */
      if (icons.length >= 2) {
        icons[0].setAttribute("hidden", "");
        icons[1].removeAttribute("hidden");
      }
      btn.setAttribute("data-variant", "secondary");
      setTimeout(function () {
        if (icons.length >= 2) {
          icons[0].removeAttribute("hidden");
          icons[1].setAttribute("hidden", "");
        }
        btn.setAttribute("data-variant", "outline");
      }, 1600);
      try {
        await navigator.clipboard.writeText(md);
      } catch (e) {
        var ta = document.createElement("textarea");
        ta.value = md;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try {
          document.execCommand("copy");
        } catch (e2) {}
        ta.remove();
      }
    });
  });
})();

/* ── 右侧目录：扫描 #doc 的 h2/h3 生成条目，指示条随滚动滑动到当前节。
移植自 VitePress 的 outline：scroll（rAF 节流）+ 标题绝对位置比较。
标题加 data-toc-skip 可豁免；点击时立即定位指示条，平滑滚动途中不跟跳。
h3 收在所属 h2 下面，只展开当前节和键盘焦点所在的组。
目录只在版心右侧放得下时显示；放不下时工具条下边线改为阅读进度。 ── */
(function () {
  var doc = document.getElementById("doc");
  var aside = document.querySelector(".toc");
  if (!doc || !aside) return;
  var inner = aside.querySelector(".toc-inner");
  var list = aside.querySelector(".toc-list");
  var marker = aside.querySelector(".toc-marker");
  var headings = Array.from(doc.querySelectorAll("h2, h3")).filter(
    function (h) {
      /* 组件容器内的标题不是节标题：卡片头的 h3、折叠面板的标题都不得进目录。
            否则统计数字写成标题时会产出「7」「91 → 39」这类孤儿条目（anti-patterns.md #1）。 */
      return (
        !h.closest("[data-toc-skip]") &&
        !h.closest("[data-md-skip]") &&
        !h.closest(
          ".card, .fig-box, .alert, .item, .accordion, .dialog, .empty"
        )
      );
    }
  );
  if (headings.length < 2) return;

  /* h3 嵌进前一个 h2 的子列表；没有前置 h2 的 h3 按顶层处理。
     子列表外包一层 .toc-subs 做收起动画（grid 行 0fr ↔ 1fr），只给真有 h3 的 h2 建 */
  var n = 0,
    group = null,
    groups = [];
  headings.forEach(function (h) {
    if (!h.id) h.id = "toc-" + ++n;
    var li = document.createElement("li");
    var a = document.createElement("a");
    a.className = "toc-link";
    a.href = "#" + h.id;
    a.textContent = a.title = h.textContent.trim();
    li.appendChild(a);
    if (h.tagName === "H2" || !group) {
      list.appendChild(li);
      group = h.tagName === "H2" ? { li: li, link: a, box: null } : null;
      return;
    }
    if (!group.box) {
      group.box = document.createElement("div");
      group.box.className = "toc-subs";
      group.ul = document.createElement("ul");
      group.ul.className = "toc-list nested";
      group.box.appendChild(group.ul);
      group.li.appendChild(group.box);
      group.link.setAttribute("aria-expanded", "false");
      groups.push(group);
    }
    group.ul.appendChild(li);
  });
  document.body.classList.add("has-toc");

  var chrome = document.querySelector(".page-chrome");
  var bar = null;
  if (chrome) {
    bar = document.createElement("div");
    bar.className = "read-progress";
    bar.setAttribute("aria-hidden", "true");
    bar.setAttribute("data-md-skip", "");
    chrome.appendChild(bar);
  }

  var side = false,
    prev = null,
    skipOnce = false;

  /* 放得下 = 版心 + 目录列 + 两侧 gutter ≤ 视口宽。用一个隐藏探针让浏览器自己算这几个变量：
     页面可能改写 --page，rem / vw / 100% 都由它换算；--page:100% 时探针宽过视口，目录自然不出 */
  var probe = document.createElement("div");
  probe.style.cssText =
    "position:absolute;visibility:hidden;height:0;" +
    "width:calc(var(--page) + var(--toc-w) + var(--toc-gap) + 2 * var(--gutter))";
  function fits(compact) {
    document.body.classList.toggle("toc-compact", compact);
    return probe.offsetWidth <= document.documentElement.clientWidth;
  }
  function layout() {
    document.body.appendChild(probe);
    var on = fits(false) || fits(true);
    probe.remove();
    if (!on) document.body.classList.remove("toc-compact");
    if (on !== side) {
      side = on;
      document.body.classList.toggle("toc-side", on);
    }
    geom = null;
  }

  function topOf(el) {
    var t = 0;
    while (el !== document.body) {
      if (el === null)
        return NaN; /* display:none 的元素拿不到位置，自然被过滤 */
      t += el.offsetTop;
      el = el.offsetParent;
    }
    return t;
  }

  function rootItem(el) {
    while (el && el.parentElement !== list) el = el.parentElement;
    return el;
  }

  /* 展开的组 = 当前节所在的组 ∪ 键盘焦点所在的组；.open 与 aria-expanded 同源。
     只认 :focus-visible：鼠标点过的链接留着焦点，不该在滚走之后还撑开那一组 */
  function sync() {
    var f = document.activeElement,
      kbd = false;
    if (f && aside.contains(f)) {
      try {
        kbd = f.matches(":focus-visible");
      } catch (e) {
        kbd = true;
      }
    }
    var cur = rootItem(prev),
      focused = kbd ? rootItem(f) : null;
    groups.forEach(function (g) {
      var open = g.li === cur || g.li === focused;
      g.box.classList.toggle("open", open);
      g.link.setAttribute("aria-expanded", String(open));
    });
  }

  /* 指示条的参照是 .toc-inner（sticky，自身可滚动）：按两者的视口坐标差算，与嵌套层级无关。
     animate=false 时不走 top 过渡，用于组展开、收起途中逐帧贴住激活项 */
  function place(animate) {
    if (!prev || !side) {
      marker.style.top = "";
      marker.style.opacity = "0";
      return;
    }
    var top =
      prev.getBoundingClientRect().top -
      inner.getBoundingClientRect().top -
      inner.clientTop +
      inner.scrollTop +
      (prev.offsetHeight - marker.offsetHeight) / 2;
    if (!animate) marker.style.transition = "none";
    marker.style.top = top + "px";
    marker.style.opacity = "1";
    if (!animate) {
      void marker.offsetTop; /* 先让无过渡的位置生效，再恢复过渡 */
      marker.style.transition = "";
    }
  }

  function activate(hash) {
    if (prev) prev.classList.remove("active");
    prev = null;
    if (hash) {
      var links = list.querySelectorAll("a");
      for (var i = 0; i < links.length; i++) {
        if (links[i].getAttribute("href") === hash) {
          prev = links[i];
          break;
        }
      }
    }
    if (prev) prev.classList.add("active");
    sync();
    place(true);
  }

  /* 组的高度在动画里逐帧变化：每帧（布局之后、绘制之前）把指示条贴回激活项 */
  if (window.ResizeObserver && groups.length) {
    var ro = new ResizeObserver(function () {
      place(false);
    });
    groups.forEach(function (g) {
      ro.observe(g.box);
    });
  }

  var geom =
    null; /* 缓存的标题几何：resize 后失效，滚动时不再逐个读 offsetTop */
  function measure() {
    /* 判定线 = 锚点跳转后标题停下的位置：html 的 scroll-padding-top（让出 sticky 工具条）加标题自己的
       scroll-margin-top。只算后者时，点目录跳过去的那一节停在线下，激活的会是上一节 */
    var pad =
      parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) ||
      0;
    geom = headings
      .map(function (h) {
        return {
          id: h.id,
          top: topOf(h),
          sm: pad + (parseFloat(getComputedStyle(h).scrollMarginTop) || 0),
        };
      })
      .filter(function (x) {
        return !isNaN(x.top);
      })
      .sort(function (a, b) {
        return a.top - b.top;
      });
  }

  function setActive() {
    if (!side) return;
    if (skipOnce) {
      skipOnce = false;
      return;
    }
    if (!geom) measure();
    var items = geom;
    if (!items.length) return activate(null);
    if (scrollY < 1) return activate(null); /* 页顶：无激活项 */
    if (
      Math.ceil(scrollY + innerHeight) >= document.documentElement.scrollHeight
    )
      return activate(
        "#" + items[items.length - 1].id
      ); /* 页底：激活最后一项 */
    var active = null;
    for (var i = 0; i < items.length; i++) {
      if (items[i].top > scrollY + items[i].sm + 4) break;
      active = items[i].id;
    }
    activate(active ? "#" + active : null);
  }

  /* 阅读进度：读到 #doc 底边算 100%，直接赋值、不带过渡 */
  function progress() {
    if (side || !bar) return;
    var end = doc.getBoundingClientRect().bottom + scrollY - innerHeight;
    var t = end > 0 ? Math.min(1, Math.max(0, scrollY / end)) : 1;
    bar.style.transform = "scaleX(" + t + ")";
  }

  function update() {
    setActive();
    progress();
  }

  aside.addEventListener("click", function (e) {
    var a = e.target instanceof Element ? e.target.closest("a") : null;
    if (a && a.hash) {
      skipOnce = true;
      activate(a.hash);
    }
  });
  aside.addEventListener("focusin", sync);
  aside.addEventListener("focusout", function () {
    setTimeout(sync, 0); /* focusout 时焦点还没落到下一个元素上 */
  });
  var ticking = false;
  addEventListener(
    "scroll",
    function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        ticking = false;
        update();
      });
    },
    { passive: true }
  );
  addEventListener("resize", function () {
    layout();
    update();
    place(false);
  });
  addEventListener("load", function () {
    /* 等浏览器恢复滚动位置后再定位一次 */
    layout();
    update();
  });
  layout();
  update();
})();
