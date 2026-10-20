# ondine vendor

来源：[ondine](https://github.com/wevm/ondine) v0.0.1（npm 包 `ondine`），MIT，许可证原文在 `../LICENSE-ondine.txt`。
Rust 写的 Mermaid 编译器，编成 wasm。`scripts/mermaid.mjs` 在构建时用 node 调用它，把 `<pre class="mermaid">`
编译成内联 SVG，页面不带任何运行时 JS。语法按 Mermaid 12.1，布局与外观是 ondine 自己的；
颜色、字体、线宽读 `--ondine-*` 变量，由 `tufte.css` 接到页面的 token 上。

- `Render.js` — 上游 `dist/Render.js` 原样（`create` 与 `RenderError`）。
- `internal/Wasm.js` — 上游 `dist/internal/Wasm.js` 原样。
- `internal/all.generated.wasm` — 上游 `dist/internal/all.generated.wasm` 原样：全部图型、按体积优化的那一份。
  `ondine/compiler` 默认加载的 `all.fast.generated.wasm` 快一些、体积是它的 2.5 倍，书的构建用不着。
- `package.json` — 只有上游 `package.json` 的 `"type": "module"` 一项，让 node 按 ES 模块加载上面两个 `.js`，
  不再向上找到仓库根的 `package.json` 并打印模块类型警告。

升级：用上游 `dist/` 的同名文件覆盖，跑 `tests/` 里的单元测试，再构建一次 `assets/specimen.html` 看 Mermaid 图。
