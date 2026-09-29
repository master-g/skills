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
