/* tufte-reader 分步图：figure.steps 里带 data-step 的元素是帧，ol.step-captions 的第 k 项是第 k 步的说明。
   只在页面有分步图时内联。没有脚本和打印时显示最后一步，由 interactive.css 和构建盖的 data-step-last 负责。 */
(function () {
  /* data-step 的写法与 build.py 的 step_ranges 一致："3"、"3-5"、"3-"（到最后一步）、"1,4-6" */
  function covers(spec, k, n) {
    return spec.split(",").some(function (part) {
      var m = /^\s*(\d+)\s*(-\s*(\d*))?\s*$/.exec(part);
      if (!m) return false;
      var a = +m[1];
      var b = m[2] ? (m[3] ? +m[3] : n) : a;
      return a <= k && k <= b;
    });
  }
  document.querySelectorAll("figure.steps").forEach(function (fig) {
    var list = fig.querySelector("ol.step-captions");
    if (!list) return;
    var caps = [].filter.call(list.children, function (el) {
      return el.tagName === "LI";
    });
    var frames = [].filter.call(
      fig.querySelectorAll("[data-step]"),
      function (el) {
        return !el.closest(".step-captions");
      }
    );
    var n = caps.length;
    if (!n || !frames.length) return;

    var ui = document.createElement("div");
    ui.className = "controls step-ui";
    ui.setAttribute("role", "group");
    ui.setAttribute("aria-label", "分步图");
    ui.innerHTML =
      '<button type="button" aria-label="上一步">←</button>' +
      '<input type="range" min="1" max="' +
      n +
      '" step="1" value="1" aria-label="步骤" />' +
      '<button type="button" aria-label="下一步">→</button>' +
      '<output aria-live="polite"></output>';
    var prev = ui.children[0];
    var range = ui.children[1];
    var next = ui.children[2];
    var count = ui.children[3];
    var cur = 0;

    function show(k) {
      k = Math.max(1, Math.min(n, k));
      if (k === cur) return;
      cur = k;
      frames.forEach(function (el) {
        el.classList.toggle(
          "step-on",
          covers(el.getAttribute("data-step"), k, n)
        );
      });
      caps.forEach(function (el, i) {
        el.classList.toggle("step-on", i === k - 1);
      });
      range.value = k;
      range.setAttribute("aria-valuetext", "第 " + k + " 步，共 " + n + " 步");
      count.textContent = "第 " + k + " / " + n + " 步";
      /* 不用 disabled：按钮在焦点上被禁用时，键盘焦点会丢回页面开头 */
      prev.setAttribute("aria-disabled", k === 1);
      next.setAttribute("aria-disabled", k === n);
    }
    prev.addEventListener("click", function () {
      show(cur - 1);
    });
    next.addEventListener("click", function () {
      show(cur + 1);
    });
    range.addEventListener("input", function () {
      show(+range.value);
    });
    list.before(ui);
    fig.classList.add("js");
    show(1);
  });
})();
