# pele vendor

来源：[pele](https://github.com/obsidianmd/pele) v1.13.0（npm 包 `pele`），MIT，许可证原文在 `../LICENSE-pele.txt`。
JS 写的 Mermaid 渲染器，没有依赖。`scripts/mermaid.mjs` 在构建时用 node 调用它，把 `<pre class="mermaid">`
编译成内联 SVG，页面不带任何运行时 JS。语法按 Mermaid 12.1，布局与外观是 pele 自己的；
颜色、字体读 `--pele-*` 变量，由 `tufte.css` 接到页面的 token 上。

- `pele.mjs` — 上游 `dist/pele.js` 原样，单文件、没有 import，含全部图型。改成 `.mjs` 后缀，node 直接按 ES 模块加载，
  不会向上找到仓库根的 `package.json` 并打印模块类型警告。

升级：用上游 `dist/pele.js` 覆盖 `pele.mjs`，跑 `tests/` 里的单元测试，再构建一次 `assets/specimen.html` 看 Mermaid 图。
