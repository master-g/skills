/* ── 回复：读者在决定块上作答、按节写评论，一键汇总成一段 Markdown（components.md「决定块」「回复」）。
   只在 <body data-reply> 的页面由 build.py 内联。window.showMeReply() 是唯一的汇总逻辑，工具条按钮和 --snap 都调它。
   读者状态的形状：{decisions: {决定块标识: [所选选项名, …]}, comments: {节标题: 评论原文}}。
   加载顺序：标记里的选中状态 → 页面带的初始状态（<script type="application/json" data-reply-state>）→ 本地存储。 ── */
(function () {
  var doc =
    document.querySelector("[data-md-root]") ||
    document.getElementById("doc") ||
    document.body;
  /* 节标题的排除表与目录生成器、Markdown 导出器一致：组件容器里的标题不是节 */
  var COMPONENT = ".card, .fig-box, .alert, .item, .accordion, .dialog, .empty";
  var SVG = "http://www.w3.org/2000/svg";
  /* 图标路径取自 lucide（ISC，assets/vendor/LICENSE-lucide.txt）：运行时生成的按钮拿不到构建期替换的 data-lucide */
  var ICONS = {
    reply: ["M20 18v-2a4 4 0 0 0-4-4H4", "m9 17-5-5 5-5"],
    check: ["M20 6 9 17l-5-5"],
  };

  function txt(s) {
    return (s || "").replace(/\s+/g, " ").trim();
  }
  function icon(name) {
    var svg = document.createElementNS(SVG, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "1em");
    svg.setAttribute("height", "1em");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("class", "lucide");
    ICONS[name].forEach(function (d) {
      var p = document.createElementNS(SVG, "path");
      p.setAttribute("d", d);
      svg.appendChild(p);
    });
    return svg;
  }
  function button(cls) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "btn " + cls;
    b.setAttribute("data-variant", "outline");
    b.setAttribute("data-size", "sm");
    return b;
  }
  function list(items) {
    return items.join("、");
  }

  /* ── 决定块：选项名是 label 里去掉说明（small）和建议标记之后的文字 ── */
  function optionTitle(label, input) {
    if (!label) return txt(input.value);
    var copy = label.cloneNode(true);
    copy.querySelectorAll("input, small, .decision-tag").forEach(function (n) {
      n.remove();
    });
    return txt(copy.textContent);
  }
  var blocks = Array.from(doc.querySelectorAll("fieldset.decision")).map(
    function (fs, i) {
      var id = fs.getAttribute("data-decision") || "decision-" + (i + 1);
      var inputs = fs.querySelectorAll(
        'input[type="radio"], input[type="checkbox"]'
      );
      var options = Array.from(inputs).map(function (input) {
        var label = input.closest("label");
        var o = {
          input: input,
          title: optionTitle(label, input),
          suggested: input.hasAttribute("data-suggested"),
        };
        /* 单选靠 name 分组：从标识派生，两个决定块撞名也不会并成一组 */
        if (input.type === "radio") input.name = "decision-" + id;
        var note = label && label.querySelector("small");
        if (o.suggested && label && !label.querySelector(".decision-tag")) {
          var tag = document.createElement("span");
          tag.className = "badge decision-tag";
          tag.textContent = "建议";
          label.insertBefore(document.createTextNode(" "), note);
          label.insertBefore(tag, note);
        }
        /* 无障碍名由各段文字直接拼成：选项名、「建议」、说明之间不留空白，读屏会连成一串 */
        if (note) label.insertBefore(document.createTextNode(" "), note);
        return o;
      });
      return {
        id: id,
        question: txt((fs.querySelector("legend") || {}).textContent),
        multi: !!fs.querySelector('input[type="checkbox"]'),
        options: options,
      };
    }
  );
  function titles(options) {
    return options.map(function (o) {
      return o.title;
    });
  }
  function chosen(b) {
    return b.options.filter(function (o) {
      return o.input.checked;
    });
  }
  function decisionLine(b) {
    var picked = titles(chosen(b));
    var hint = titles(
      b.options.filter(function (o) {
        return o.suggested;
      })
    );
    var adopted =
      picked.length === hint.length &&
      picked.every(function (t) {
        return hint.indexOf(t) >= 0;
      });
    var answer;
    if (!picked.length)
      answer = hint.length
        ? "未作答（建议是 " + list(hint) + "）"
        : "未作答（没有建议项）";
    else if (!hint.length) answer = list(picked) + "（没有建议项）";
    else if (adopted) answer = list(picked) + "（采纳建议）";
    else {
      answer = list(picked) + "（改选，建议是 " + list(hint);
      if (b.multi) {
        var extra = picked.filter(function (t) {
          return hint.indexOf(t) < 0;
        });
        var missed = hint.filter(function (t) {
          return picked.indexOf(t) < 0;
        });
        if (extra.length) answer += "；加选 " + list(extra);
        if (missed.length) answer += "；未选 " + list(missed);
      }
      answer += "）";
    }
    return "- " + b.question + "：" + answer;
  }

  /* ── 评论：正文每个顶层节（h1 / h2）一个入口，插在标题后面 ── */
  var sections = [];
  var keys = {};
  Array.from(doc.querySelectorAll("h1, h2")).forEach(function (h) {
    if (
      h.closest(COMPONENT) ||
      h.closest("[data-toc-skip]") ||
      h.closest("[data-md-skip]") ||
      h.closest("fieldset.decision")
    )
      return;
    var title = txt(h.textContent);
    if (!title) return;
    /* 同名的节各自一条：从第二个起加序号。回复里写的节标题就是这个键，照抄回复写的初始状态能回到原来那一节 */
    var key = title;
    for (var n = 2; keys[key]; n++) key = title + "（" + n + "）";
    keys[key] = true;
    var i = sections.length + 1;
    var box = document.createElement("div");
    box.className = "reply-comment";
    box.setAttribute("data-md-skip", "");
    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "btn";
    toggle.setAttribute("data-variant", "ghost");
    toggle.setAttribute("data-size", "sm");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", "reply-comment-" + i);
    var panel = document.createElement("div");
    panel.className = "reply-comment-panel";
    panel.id = "reply-comment-" + i;
    panel.hidden = true;
    var area = document.createElement("textarea");
    area.className = "textarea";
    area.rows = 3;
    area.setAttribute("aria-label", "对「" + title + "」的评论");
    area.placeholder = "写下对这一节的意见，会随回复一起复制";
    panel.appendChild(area);
    /* 打印稿：textarea 按框高裁切，评论原文另放一段文字随节印出 */
    var printed = document.createElement("p");
    printed.className = "reply-comment-print";
    box.appendChild(toggle);
    box.appendChild(panel);
    box.appendChild(printed);
    h.after(box);
    var s = {
      key: key,
      area: area,
      toggle: toggle,
      panel: panel,
      printed: printed,
    };
    sections.push(s);
    toggle.addEventListener("click", function () {
      setCommentOpen(s, panel.hidden);
    });
    area.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        setCommentOpen(s, false);
        toggle.focus();
      }
    });
  });
  function setCommentOpen(s, on) {
    s.panel.hidden = !on;
    s.toggle.setAttribute("aria-expanded", String(on));
    if (on) s.area.focus();
  }
  function setComment(s, value) {
    s.area.value = value;
    paintComment(s);
  }
  function paintComment(s) {
    var has = !!s.area.value.trim();
    s.toggle.textContent = has ? "评论（已写）" : "评论";
    s.printed.textContent = has ? "读者评论：" + s.area.value.trim() : "";
  }
  function comments() {
    return sections.filter(function (s) {
      return s.area.value.trim();
    });
  }
  function commentItem(s) {
    var quoted = s.area.value
      .replace(/\s+$/, "")
      .replace(/^\s*\n/, "")
      .split("\n")
      .map(function (l) {
        return l.trim() ? "  > " + l.replace(/\s+$/, "") : "  >";
      });
    return "- 「" + s.key + "」\n" + quoted.join("\n");
  }

  function toReply() {
    var out = "# 回复：" + txt(document.title) + "\n";
    if (blocks.length)
      out += "\n## 决定\n\n" + blocks.map(decisionLine).join("\n") + "\n";
    var written = comments();
    if (written.length)
      out += "\n## 评论\n\n" + written.map(commentItem).join("\n") + "\n";
    if (!blocks.length && !written.length) out += "\n读者没有写评论。\n";
    return out;
  }
  window.showMeReply = toReply;

  /* ── 状态：本地存储的键含页面路径和决定块集合的签名，页面重做后决定块变了，旧状态不套到新页面上 ── */
  function hash(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0).toString(16);
  }
  var KEY =
    "show-me-reply:" +
    location.pathname +
    ":" +
    hash(
      blocks
        .map(function (b) {
          return (
            b.id + (b.multi ? "[]" : "") + "=" + titles(b.options).join("|")
          );
        })
        .join(";")
    );
  function snapshot() {
    var state = { decisions: {}, comments: {} };
    blocks.forEach(function (b) {
      state.decisions[b.id] = titles(chosen(b));
    });
    sections.forEach(function (s) {
      state.comments[s.key] = s.area.value;
    });
    return state;
  }
  /* 只动状态里有记录的键：没有记录不等于取消选中，标记里预先写好的选中状态要留着 */
  function applyState(state) {
    if (!state || typeof state !== "object") return;
    var d = state.decisions || {},
      c = state.comments || {};
    blocks.forEach(function (b) {
      if (!Array.isArray(d[b.id])) return;
      b.options.forEach(function (o) {
        o.input.checked = d[b.id].indexOf(o.title) >= 0;
      });
    });
    sections.forEach(function (s) {
      if (typeof c[s.key] === "string") setComment(s, c[s.key]);
    });
  }
  function readInitialState() {
    var el = document.querySelector(
      'script[type="application/json"][data-reply-state]'
    );
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      console.warn("回复：初始状态数据不是合法的 JSON，已忽略");
      return null;
    }
  }
  function stored() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "null");
    } catch (e) {
      return null;
    }
  }
  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(snapshot()));
    } catch (e) {}
    paintCounts();
  }

  /* ── 回复按钮：工具条上一个（图标 + 已作答计数），页尾一个（带完整说明和清空作答） ──
     反馈先行，同「复制为 Markdown」：图标换成对勾 1.6s，不等待写入 —— 权限 pending 时它可能永不 settle。
     写入用骨架的 window.showMeCopy：骨架脚本内联在本运行时之后，所以点击时再取 */
  function replyButton(cls) {
    var b = button(cls);
    var idle = icon("reply"),
      done = icon("check");
    done.setAttribute("hidden", "");
    b.appendChild(idle);
    b.appendChild(done);
    b.addEventListener("click", function () {
      idle.setAttribute("hidden", "");
      done.removeAttribute("hidden");
      b.setAttribute("data-variant", "secondary");
      setTimeout(function () {
        idle.removeAttribute("hidden");
        done.setAttribute("hidden", "");
        b.setAttribute("data-variant", "outline");
      }, 1600);
      window.showMeCopy(toReply());
    });
    return b;
  }

  /* 工具条：按钮紧挨在页面标题的右端、「复制为 Markdown」之前。目录在侧时操作区只有目录列宽，放不下第三组按钮，
     所以把标题和回复按钮包成一组放在版心列里 */
  var barBtn = replyButton("reply-copy");
  var barCount = document.createElement("span");
  barCount.className = "reply-count";
  barBtn.appendChild(barCount);
  var anchor = document.querySelector("[data-copy-md]");
  var title = document.querySelector(".page-chrome .chrome-title");
  if (title) {
    var lead = document.createElement("div");
    lead.className = "chrome-lead";
    title.before(lead);
    lead.appendChild(title);
    lead.appendChild(barBtn);
  } else if (anchor) anchor.before(barBtn);

  /* 页尾：读完再回复，顺带放清空作答。整节不进 Markdown 导出 */
  var foot = document.createElement("section");
  foot.className = "reply-foot";
  foot.setAttribute("data-md-skip", "");
  var status = document.createElement("p");
  status.setAttribute("aria-live", "polite");
  var actions = document.createElement("div");
  actions.className = "reply-foot-actions";
  var footBtn = replyButton("reply-copy-foot");
  footBtn.append("复制回复");
  var clearBtn = button("reply-clear");
  clearBtn.setAttribute("data-variant", "ghost");
  clearBtn.textContent = "清空作答";
  actions.appendChild(footBtn);
  actions.appendChild(clearBtn);
  foot.appendChild(status);
  foot.appendChild(actions);
  (doc.tagName === "MAIN" ? doc : doc.querySelector("main") || doc).appendChild(
    foot
  );

  function paintCounts() {
    var answered = blocks.filter(function (b) {
      return chosen(b).length;
    }).length;
    var written = comments().length;
    var words = [];
    if (blocks.length)
      words.push("已作答 " + answered + "/" + blocks.length + " 个决定");
    words.push(written + " 条评论");
    barCount.textContent =
      (blocks.length ? answered + "/" + blocks.length + " · " : "") + written;
    barBtn.title = "复制回复：" + words.join("，");
    barBtn.setAttribute("aria-label", barBtn.title);
    status.textContent =
      words.join("，") +
      "。复制回复后贴回给 Agent；作答和评论保存在这个浏览器里，刷新后还在。";
  }

  /* 清空要点两次：第一次只把按钮换成确认文字，3 秒内再点才清。不用 confirm()，它会卡住无头浏览器 */
  var armed = null;
  clearBtn.addEventListener("click", function () {
    if (!armed) {
      clearBtn.textContent = "再点一次清空";
      clearBtn.setAttribute("data-variant", "destructive");
      armed = setTimeout(disarm, 3000);
      return;
    }
    disarm();
    try {
      localStorage.removeItem(KEY);
    } catch (e) {}
    blocks.forEach(function (b) {
      b.options.forEach(function (o) {
        o.input.checked = o.input.defaultChecked;
      });
    });
    sections.forEach(function (s) {
      setComment(s, "");
    });
    applyState(readInitialState());
    paintCounts();
  });
  function disarm() {
    clearTimeout(armed);
    armed = null;
    clearBtn.textContent = "清空作答";
    clearBtn.setAttribute("data-variant", "ghost");
  }

  doc.addEventListener("change", function (e) {
    if (e.target.closest && e.target.closest("fieldset.decision")) save();
  });
  sections.forEach(function (s) {
    s.area.addEventListener("input", function () {
      paintComment(s);
      save();
    });
  });

  /* 初始状态的 <script> 可能写在本运行时之后：等文档解析完再恢复 */
  function restore() {
    applyState(readInitialState());
    applyState(stored());
    paintCounts();
  }
  sections.forEach(paintComment);
  paintCounts();
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", restore);
  else restore();
})();
