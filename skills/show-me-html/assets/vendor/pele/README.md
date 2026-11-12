# pele vendor

来源：[pele](https://github.com/obsidianmd/pele) v1.13.0（npm 包 `pele`），MIT，许可证原文在 `../LICENSE-pele.txt`。
JS 写的 Mermaid 渲染器，没有依赖。`scripts/mermaid.mjs` 在构建时用 node 调用它，把 `<pre class="mermaid">`
编译成内联 SVG，页面不带任何 Mermaid 运行时。语法按 Mermaid，布局与外观是 pele 自己的；
颜色、字体读 `--pele-*` 变量，由 `show-me.css` 接到页面的 token 上。

- `pele.mjs` — 上游 `dist/pele.js` 原样，单文件、没有 import，含全部图型。改成 `.mjs` 后缀，node 直接按 ES 模块加载。
  与 `skills/tufte-reader/assets/vendor/pele/pele.mjs` 是同一个文件；技能各自安装，所以各存一份。

升级步骤见技能根目录 `MAINTENANCE.md` 的「Vendor 升级」。
