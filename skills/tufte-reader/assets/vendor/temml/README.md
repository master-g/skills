# Temml vendor

来源：[Temml](https://temml.org) v0.13.5，MIT，许可证原文在 `../LICENSE-temml.txt`。
LaTeX → MathML 编译器，`scripts/math.mjs` 在构建时用 node 调用它，产出的 MathML 内联进页面，
页面不带任何运行时 JS。

- `temml.cjs` — 上游 `dist/temml.cjs` 原样。
- `Temml-Local.css` — 上游 `dist/Temml-Local.css` 原样；`math.mjs` 注入页面前剥掉 `@font-face`
  （引用外链 woff2，违反离线约束）和 `math {}` 字体栈（由 `tufte.css` 统一给）。

升级：用上游 `dist/` 的同名文件覆盖，再构建一次 `assets/specimen.html` 确认公式正常。
