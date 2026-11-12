# 维护

改这个技能的样式、骨架或脚本时照这里做；做读本时用不到。`<skill-path>` 是技能根目录。

调字号、行高、间距和栏宽，改 `assets/tufte.css` 开头 `:root` 里的 token（`--text-*`、`--leading-*`、`--space-*`，以及版面的 `--sheet-*`、`--col`、`--note-width` 等），各条规则只引用它们，不在规则里写新的数值。

改了 `assets/tufte.css`、`shell.html`、`shell.js` 或 `scripts/` 之后，运行 `python3 -m unittest discover -s <skill-path>/tests`。然后把 `assets/specimen.html` 复制到临时目录并构建，在 1280px 和 390px 两种宽度、明暗两种主题下各看一遍。specimen 包含全部元素，是这套版式的回归样张。1280px 的明暗两张整页截图由 `python3 <skill-path>/scripts/figprobe.py <构建后的 specimen>` 一次截出，它同时检查每幅 Mermaid 图的标签是否顶出节点框，退出码非零就是有图不合格；390px 照本文最后一段的办法看。改了 `scripts/figlib.py` 或插图的样式，用 `scripts/figpreview.py` 单独看受影响的图。改动涉及公式（包括插图里的公式）时，Chrome 之外再用 Firefox 内核的浏览器看一遍：两种内核排 MathML 的差别很大，出现过 Chrome 里正常、Firefox 里上下标不缩小以致编号压住公式的情况。

无头 Chrome 的窗口最窄 500px，`--window-size=390,…` 截出的是按 500px 排版、右侧被裁掉的图。看 390px 要用能设置视口的浏览器工具，或者写一个只含 `<iframe src="specimen.html" width="390" height="844">` 的外层页面，对外层页面截图。
