# 语法高亮 vendor

来源：[@speed-highlight/core](https://github.com/speed-highlight/core) v2.0.0，**CC0-1.0**（公有领域，无署名义务）。
许可证原文在 `LICENSE-speed-highlight.txt`。

选它的原因：输出纯 class（`shj-syn-*`）而不是写死颜色的 inline style，
所以配色能交给骨架的 `--syn-*` token，浅色/深色各一套。
分词器是同步的，着色在首绘前完成，不会闪一下再变色。

## 目录里是什么

- `languages/*.js` — 34 份语言规则，**上游原样**，未改动。每份是
  `var X = [...]; export {X as default};`，`build.py` 用正则把它转成
  `window.__SHJ_LANGS["名字"] = (function(){ ... })();` 拼进页面。
  语言之间会互相引用（`sub:"todo"`），`build.py` 跟着 `sub` 递归带上依赖。
- `core.js` — **打包产物**（1.7 KB）：上游的 `dist/tokenize.js` 加一段驱动代码，
  esbuild 打成 IIFE。它从 `window.__SHJ_LANGS` 读语言表，遍历
  `pre > code[class*="language-"]` 着色。

## 怎么升级

`languages/*.js` 直接从上游 `dist/languages/` 覆盖即可（删掉 `index.js`，它是唯一带
import 的文件，用不上）。`core.js` 需要重新打包：

```sh
npm i @speed-highlight/core esbuild
# 入口文件内容见下方
npx esbuild core-entry.js --bundle --format=iife --minify --outfile=core.js
```

`core-entry.js`：

```js
import { tokenizeWith } from '@speed-highlight/core/tokenize';

/* 语言表由 build.py 在本段之前拼进来：window.__SHJ_LANGS = { go: [...], ... } */
var LANGS = window.__SHJ_LANGS || {};
var ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;' };
function esc(s) { return s.replace(/[&<>]/g, function (c) { return ESC[c]; }); }

/* diff 由页面自己的 .d-add / .d-del 着色，text 是结构视图，两者都不碰 */
document.querySelectorAll('pre > code[class*="language-"]').forEach(function (code) {
  var m = code.className.match(/language-([\w+-]+)/);
  if (!m) return;
  var def = LANGS[m[1]];
  if (!def) return;
  var out = '';
  tokenizeWith(code.textContent, def, function (text, type) {
    out += type ? '<span class="shj-syn-' + type + '">' + esc(text) + '</span>' : esc(text);
  }, { languages: LANGS });
  code.innerHTML = out;
});
```

改完跑一遍 `build.py`，确认页面里代码块仍然着色、`language-diff` 仍然没被碰。

## 别改成 inline style

上游主入口（`@speed-highlight/core` 而不是 `/tokenize`）的 loader 用
`import(\`./languages/${lang}.js\`)`，打包工具会把 35 种语言全 glob 进来 —— 30 KB 而不是 2.9 KB。
走 `/tokenize` 子路径、自己注册语言表，是刻意的。
