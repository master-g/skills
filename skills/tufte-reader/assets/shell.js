/* tufte-reader 骨架脚本：明暗两态切换。初始主题由 <head> 里的脚本在首绘前定下（存储值，否则跟随系统）。
   图标取自 Lucide（ISC，许可见 vendor/LICENSE-lucide.txt）的 sun / moon；按钮显示「点了会切到的」那一态。 */
(function () {
  var root = document.documentElement;
  var btn = document.querySelector(".theme-toggle");
  if (!btn) return;
  var SVG =
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
  var MOON =
    SVG +
    '<path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401"/></svg>';
  var SUN =
    SVG +
    '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>';
  function sync() {
    var dark = root.dataset.theme === "dark";
    btn.innerHTML = dark ? SUN : MOON;
    btn.title = dark ? "切换到浅色" : "切换到深色";
    btn.setAttribute("aria-label", btn.title);
  }
  btn.addEventListener("click", function () {
    var next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try {
      localStorage.setItem("tufte-reader-theme", next);
    } catch (e) {}
    sync();
  });
  sync();
})();

/* 网络字体：页面先用系统字体排版，这里把用到的字体文件成批请求，到齐后设 data-fonts="web"，
   tufte.css 据此换上网络字体，全页只换一次。分两批：先请求视口附近（已经排版的章和章以外的部分）
   用到的文件，到齐就换；再请求其余各章的，它们只影响还没排版的章，到了也看不出换字。
   第一批超过 LIMIT 还没到齐就这次不换（读者已经在读，换字会打断），文件照常下完进缓存。
   两批都到齐后记一个标记，下次打开时 <head> 里的脚本（build.py 的 FONT_READY）在首绘前就启用网络字体，
   这里不用再做什么。离线或加载失败时一直用系统字体。 */
(function () {
  var LIMIT = 3000;
  var start = Date.now();
  var root = document.documentElement;
  if (root.dataset.fonts === "web") return;
  if (!document.fonts || !window.Promise || !window.Set) return;
  /* 用到的字：公式、插图、代码各有自己的字体，里面的字不算，否则会多请求它们才用得上的分片 */
  var OWN_FONT = /^(math|svg|pre|code|script|style)$/i;
  function chars(nodes) {
    var text = "";
    nodes.forEach(function (root) {
      var walker = document.createTreeWalker(root, 5, function (n) {
        return n.nodeType === 1 && OWN_FONT.test(n.nodeName) ? 2 : 1;
      });
      var n;
      while ((n = walker.nextNode())) if (n.nodeType === 3) text += n.data;
    });
    return Array.from(new Set(text)).join("");
  }
  /* content-visibility 跳过排版的章：章内元素的 checkVisibility 为 false */
  function skipped(e) {
    var chapter = e.closest("article.chapter");
    var probe = chapter && chapter.firstElementChild;
    return !!(
      probe &&
      probe.checkVisibility &&
      !probe.checkVisibility({ contentVisibilityAuto: true })
    );
  }
  /* 粗体的文件只按粗体字请求，否则每个汉字分片都要多下一份 */
  function load(blocks, bolds) {
    var all = chars(blocks);
    var bold = chars(bolds);
    var seen = {};
    var jobs = [];
    document.fonts.forEach(function (f) {
      var font =
        f.style +
        " " +
        f.weight +
        ' 1em "' +
        f.family.replace(/["']/g, "") +
        '"';
      if (seen[font]) return;
      seen[font] = true;
      jobs.push(
        document.fonts.load(font, parseInt(f.weight, 10) >= 600 ? bold : all)
      );
    });
    return Promise.all(jobs);
  }
  var links = [].slice.call(document.querySelectorAll('link[data-tr="font"]'));
  Promise.all(
    links.map(function (l) {
      if (l.sheet) return null;
      return new Promise(function (resolve, reject) {
        l.addEventListener("load", resolve);
        l.addEventListener("error", reject);
      });
    })
  )
    .then(function () {
      var blocks = [].slice.call(document.body.children);
      var bolds = [].slice.call(
        document.querySelectorAll("strong, b, th, .newthought")
      );
      function near(e) {
        return !skipped(e);
      }
      return load(blocks.filter(near), bolds.filter(near)).then(function () {
        if (Date.now() - start <= LIMIT) root.dataset.fonts = "web";
        return load(blocks, bolds);
      });
    })
    .then(function () {
      localStorage.setItem("tufte-reader-fonts:" + location.pathname, "1");
    })
    .catch(function () {});
})();
