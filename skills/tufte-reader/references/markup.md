# 标记契约

读本源码从 `assets/shell.html` 开始。本文件列出每种元素的写法；构建脚本负责的部分（边注开关、脚注归位、目录、图片内联、公式编译）作者不手写。完整示范见 `assets/specimen.html`。

源码可以用 prettier 之类的格式化工具排版：标签和行内公式被折成多行不影响构建。

下面的写法以翻译为准。原创撰写时提到「原文」的地方，按 [行文](style.md) 的「原创撰写」换成对应写法。

## 骨架

```html
<body>
  <button type="button" class="theme-toggle" aria-label="切换明暗主题"></button>
  <header class="titlepage">…</header>
  <article class="chapter" id="…">…</article>
  <!-- 每章一个 -->
  <section class="references" id="references">…</section>
  <!--TR:JS-->
</body>
```

- `<title>`：「中文标题 · 原文标题」；原创撰写写「书名 · 副标题」。`<html lang="zh-CN">`。
- `<!--TR:CSS-->` 与 `<!--TR:JS-->` 占位符保留到首次构建，构建后由内联资源替代，重跑时按 `data-tr` 标记刷新。
- 字体由构建处理：作者不写 `<link>`、`@font-face` 和 `font-family`。页面里唯一的外链是构建注入的字体样式表（jsDelivr），作者自己加的外链脚本或样式仍然报 ERROR。

## 扉页

```html
<header class="titlepage">
  <h1>中文标题</h1>
  <p class="subtitle">Original Title</p>
  <p class="byline">作者 著 · 单位 · 出处与年份</p>
  <div class="epigraph">
    <blockquote>
      <p>题记</p>
      <footer>出处</footer>
    </blockquote>
  </div>
  <p class="asterism">❧</p>
  <div class="abstract">
    <h2>摘要</h2>
    <p>…</p>
  </div>
  <p>读本说明：原文链接、许可、译法取舍（删节、未译部分、术语约定）。</p>
  <nav class="toc"></nav>
</header>
```

原创撰写时，`p.subtitle` 写副标题，`p.byline` 写「撰写者 · 年月」，读本说明的内容见 [行文](style.md) 的「原创撰写」。

题记只在原文有题记时使用。`<nav class="toc">` 留空，构建时从各章生成。

## 章与节

```html
<article class="chapter" id="attention">
  <h2><span class="chapter-number">3</span>模型架构</h2>
  <section>
    <p>…</p>
  </section>
  <section>
    <h3>3.1　编码器与解码器</h3>
    <p>…</p>
  </section>
</article>
```

- 章 `id` 用英文 kebab-case，取自原文标题。`chapter-number` 照原文编号：论文写 `1`、`2`，书写 `第 II 章`，附录写 `附录 A`，原文无编号的章写 `·`。原创撰写时 `id` 按章的主题自拟，编号从 `1` 起连续写。
- 标题只有两级：`h2` 是章，`h3` 是节。原文第三级及更深的标题，改成段首 `<span class="newthought">小标题，</span>`。构建遇到 h4–h6 报 ERROR。
- 每个 `h3` 连同其下段落放进一个 `<section>`；章首无小标题的段落也包进 `<section>`。
- 章与章之间不加署名页脚或导航：出处与许可写在扉页读本说明；某一章有删节、或整理模式下用到了哪些来源，写在该章第一段的译注旁注里。

## 注释分流

三种注释写法相同，都是插在正文句中的一个 span，构建补全开关：

| 内容                                        | 写法                                                            | 呈现                        |
| ------------------------------------------- | --------------------------------------------------------------- | --------------------------- |
| 原作者脚注                                  | `<span class="sidenote">…</span>`                               | 页边，数字编号，每章从 1 起 |
| 原作者脚注，超过约 150 字或含块级公式、列表 | `<span class="footnote">…</span>`                               | 章末，符号 \*†‡§‖¶          |
| 译注                                        | `<span class="marginnote"><span class="tn">译注</span>…</span>` | 页边，无编号                |
| 术语原文、人名原文、单位换算                | `<span class="marginnote">…</span>`                             | 页边，无编号                |

- 原创撰写没有「原作者」和「译者」之分：补充说明、旁证、题外话用 `sidenote`，太长或含块级内容的用 `footnote`，术语原文和某句话的来源用不带 `tn` 的 `marginnote`。不用「译注」标签。
- 开标签只写 `<span class="sidenote">` 这一种形式，不加别的属性或 class，否则构建认不出来，报 ERROR。
- 注释必须位于 `<p>`、`<li>`、`<figure>`、`<blockquote>` 内部，紧跟它所注释的词或句末标点。直接挂在 `<section>` 下时页边定位错位，构建报 ERROR。
- 注释内只放行内内容（文字、行内公式、`<em>`、`<code>`、`<a>`、小图 `<img>`）；块级内容用 `footnote`。
- 原文本身就是边注排版（LaTeX `\sidenote`、`\marginnote`）时，边注无论长短都留在页边，只有含块级公式或列表的才改成章末脚注。
- 同一段里多条旁注会在页边依次下推；一段超过三条时考虑把部分改成正文括注。

## 插图

```html
<figure>
  <span class="marginnote">图 1　图题。图注说明。</span>
  <img src="figures/fig1.png" alt="描述图的内容" />
</figure>

<figure class="fullwidth">…</figure>
<!-- 宽图：横跨正文栏与页边 -->

<p>
  …<span class="marginnote"
    ><img src="figures/small.png" alt="…" />图 2　小图放页边。</span
  >…
</p>

<figure class="fullwidth">
  <img src="figures/wide.png" alt="…" />
  <figcaption>图 3　通栏图的图注用 figcaption，放在图下。</figcaption>
</figure>
```

- 页边图（原文的 `marginfigure`）挂在它所属的正文段落开头，不要单独放进一个空 `<p>`：空段落没有高度，图会一直浮到下一章。
- 原文的 `figure*` 通栏图用 `figure.fullwidth`；原图宽度不到 1000px 的仍用普通 `figure`，放大会糊。
- 普通 figure 的图题放在 figure 内的 `marginnote` 里，写「图 N　」（全角空格）加译文图题；图中文字不改图，必要时在图注里对照翻译关键标签。
- `src` 写相对页面文件的本地路径，构建转成 data URI。外网图片先下载到本地，否则报 ERROR。
- 矢量示意图可以直接写内联 `<svg>`，给 `width` 和 `aria-label`，颜色用 `currentColor` 以跟随明暗主题。
- 内联 SVG 里的 `id`（`marker`、`linearGradient`、`clipPath` 等）在整个页面内必须唯一，带上图的编号作前缀：`<marker id="fig3-arrow">`。两幅图用了同一个 `id` 时，后一幅会引用到前一幅的定义，构建报 ERROR。
- 读本只用静态图，不写脚本，不加滑块、按钮这类交互控件。要表现一个过程，把各个状态画成并排的小图，每幅配一句说明，写法见下面的「分步图」。
- 宽图在手机上等比缩小后图内文字太小时，把 `<svg>` 或 `<img>` 包进 `<div class="scroll-x">`：窄屏下按原始宽度显示、横向滚动，宽屏不变。
- `<svg>` 内部不编译公式，`$…$` 会原样显示。图里的数学符号直接写 Unicode 字符（`x₁`、`Σ`），或者放到图注里。

## 分步图

把一个过程的各个状态画成并排的小图，每幅配一句说明。作者只画一幅 `<svg>`，标出每个部分在第几步出现；构建把每一步各画成一幅小图，成品是纯静态的，没有脚本和控件，屏幕和打印一样。什么时候用见 [行文](style.md) 的「分步图」。

```html
<figure class="steps">
  <span class="marginnote">图 4　图题。</span>
  <svg viewBox="0 0 240 120" width="240" role="img" aria-label="描述整个过程">
    <rect
      x="10"
      y="10"
      width="220"
      height="100"
      fill="none"
      stroke="currentColor"
    />
    <!-- 没有 data-step：每一步都有 -->
    <g data-step="1">…只在第 1 步…</g>
    <g data-step="2-">…从第 2 步起一直有…</g>
    <g data-step="2-3">…第 2、3 步…</g>
    <g data-step="3">…只在第 3 步…</g>
  </svg>
  <ol class="step-captions">
    <li>第 1 步的说明。</li>
    <li>第 2 步的说明，可以有行内公式 $x^2$。</li>
    <li>第 3 步的说明。</li>
  </ol>
</figure>
```

- **帧**：`<svg>` 里带 `data-step` 的元素。值写它出现在第几步：`3`、`3-5`、`3-`（从第 3 步到最后一步）、`1,4-6`。不带 `data-step` 的元素每一步都有。全部帧写在同一幅 `<svg>` 里，放在说明列表之前。
- **不变的部分只写一次**：坐标轴、外框、不变的方块不加 `data-step`；出现后不再消失的用 `3-`。
- **说明**：`<ol class="step-captions">` 的第 k 个 `<li>` 是第 k 步的说明，条数必须等于步数。步数是各帧里写出的最大编号，从 1 起连续，每一步至少有一个帧。
- **高亮当前步**用 `fill-opacity` 的深浅，颜色仍然只用 `currentColor`。图内的 `id` 照常带图号前缀，构建会给每幅小图再加后缀。
- **排版**：`<svg>` 的 `width` 决定小图多大。正文栏放得下两幅宽度为 `width` 四分之三的小图时并排成两列或更多，否则一列一幅；手机上总是一列。图里的字要在缩到四分之三时仍然看得清。
- 图题照普通插图写在 `marginnote` 里。统计里分步图同时计入「图」和「分步图」，「帧」是各分步图的步数之和。
- 构建检查：缺 `ol.step-captions`、没有帧、`data-step` 写法不对、编号不连续、说明条数与步数不等，都报 ERROR；`data-step` 写在 `figure.steps` 之外也报 ERROR。
- 展开之后源码里的那一幅 `<svg>` 和说明列表就没有了。要改帧，改展开前的源码再构建；已构建的页面里只能逐幅改小图。

## 表格

```html
<div class="table-wrapper">
  <table>
    <caption>
      表 1　表题
    </caption>
    <thead>
      <tr>
        <th>模型</th>
        <th class="num">BLEU</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Transformer</td>
        <td class="num">28.4</td>
      </tr>
    </tbody>
  </table>
</div>
```

三线表样式由 CSS 给出。数值列加 `class="num"` 右对齐。宽表加 `class="fullwidth"` 到 wrapper 上。

## 公式

- 行内 `$…$`，块级 `$$…$$` 单独成行、放在段落之间。构建时编译为 MathML，页面不带运行时 JS。
- 行内公式可以在源码里折行，内部的换行和缩进按一个空格处理。公式不能跨越标签：`$` 和 `$` 之间出现 `<` 就不算公式。
- 编号照原文：`$$…\tag{3}$$`。正文引用写「式 (3)」，不做交叉链接。
- 正文栏 33 个汉字宽，放得下约 55 个可见字符（去掉命令名与花括号后计数）。更长的单行块级公式，用 `\begin{aligned}…\end{aligned}` 在 `=` 或二元运算符前断行，对齐点写 `&{}+`（直接写 `&+` 会把加号排成一元运算符，间距变紧）；构建对未断行的长公式发 WARN。手机上仍放不下时横向滚动。
- 公式里的中文写进 `\text{}`；其余中文会让 `$…$` 不被识别为公式，构建报 ERROR 并给出上下文。
- 公式里的 `<` `>` `&` 按 HTML 写成 `&lt;` `&gt;` `&amp;`，编译前会还原。
- 可见字符超过约 25 个的行内公式，窄屏下自动变成可横向滚动的块；更长的考虑改成块级。
- Temml 与 LaTeX 的差异：`\hdots` 不支持，写 `\ldots`。`align` 环境拆成每行一个 `$$…\tag{n}$$`，或用 `aligned`。
- 公式中出现的 `$` 金额写 `\$`；正文里的美元金额保持 `$5` 这种「$ 后紧跟数字」的写法，不会被误识别。正文里要显示成对的美元符号（例如讲解 LaTeX 语法）时写 `&#36;`，或者放进 `<code>`。
- 行内公式紧挨全角标点（`$V$：`、`（$n$）`）时，构建把它们包进 `<span class="math-nobr">`，标点不会落到行首或行尾。作者不手写这个 span。
- 编译失败的公式会留下红字，构建报 ERROR：把出错的 `<span class="temml-error">` 或 `<math>` 整个换回改正后的 `$…$` 再构建。

## 代码

```html
<pre><code class="language-python">…</code></pre>
```

语言名见 `assets/vendor/shj/languages/`，常用别名（python、rust、shell 等）可直接写；运行输出写 `language-text`，不着色。代码与代码注释保持原文；需要解释时用正文或旁注。最长行超过 76 列的代码块，构建自动加 `fullwidth`，横跨正文栏与页边，并排在页边注之下。

代码多的材料（notebook、教程）不要手抄代码：写译文时放占位符，再用脚本从取到的原文按顺序原样填回，确保逐字一致、块数不漏。

## 引文、题记、分节

- 块引用：`<blockquote><p>…</p><footer>出处</footer></blockquote>`。
- 分节花 `<p class="asterism">❧</p>`：扉页固定一处；正文里只在原文有分节符（\* \* \* 之类）的位置使用。

## 习题与答案

```html
<section class="exercises">
  <h3>习题 1</h3>
  <ol>
    <li>…</li>
  </ol>
  <details class="answers">
    <summary>答案</summary>
    <ol>
      <li>…</li>
    </ol>
  </details>
</section>
```

## 参考文献与引用

```html
<p>……如文献 <a class="cite" href="#ref-vaswani2017">[12]</a> 所示。</p>

<section class="references" id="references">
  <h2>参考文献</h2>
  <ol>
    <li id="ref-vaswani2017">
      A. Vaswani et al. Attention Is All You Need. <em>NeurIPS</em>, 2017.
    </li>
  </ol>
</section>
```

- 引用标记保留原文格式（`[12]`、`(Vaswani et al., 2017)`），链到对应条目。原创撰写统一写「(Vaswani 等，2017)」，链到书末条目；条目按第一作者姓氏排序，只列正文引用过的文献。
- 参考文献条目保持原文，不翻译；按原文顺序排列，编号与原文一致。
- 没有参考文献的材料省略这一节。

## 构建负责的部分

作者不写：边注的 `label` + `checkbox`、章末 `section.footnotes`、目录内容、图片 data URI、公式外面的 `math-nobr` 与 `math-inline-long`、内联的 CSS 与脚本、字体的 `<link>`、分步图展开后的 `ol.step-frames`。已构建的页面可以直接编辑正文再重跑构建；新加的注释与脚注按同样写法插入即可。
