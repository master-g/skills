# 组件词表

组件外观由 `assets/show-me.css` 统一提供。写 markup 前读本文；**不要在单页里重做按钮、卡片、徽章或表格的外观**，否则主题、焦点状态和打印会分叉。

三条规则：

1. **语义 HTML 优先。** 自有 CSS 靠元素结构选中子元素（`.card > header > h2`），不是靠一串内部子类名。结构写错，样式就不生效。
2. **变体走 `data-` 属性**，不是 class：`.btn[data-variant]`、`.btn[data-size]`、`.badge[data-variant]`、`.alert[data-variant]`、`.card[data-size]`。
3. **没有 Tailwind 工具类。** 布局使用配方规定的结构类；少量页面级几何可以写在自己的 `<style>` 里，只能取 `var(--color-border)`、`var(--radius)` 等 token。

## 需要 JS 的组件只有两个

`tabs` 和 `dropdown-menu`（以及少用的 `popover` / `combobox` / `command` / `sidebar` / `drawer` / `chart`）。
`build.py` 检测到这些 class 时会自动内联保留的 basecoat JS。其余组件使用自有 CSS 和浏览器原生能力。
决定块和按节评论靠回复运行时，`<body data-reply>` 时才内联，见「决定块」。

---

## 按钮

```html
<button type="button" class="btn">主按钮</button>
<button type="button" class="btn" data-variant="secondary">次要</button>
<button type="button" class="btn" data-variant="outline">描边</button>
<button type="button" class="btn" data-variant="ghost">无框</button>
<button type="button" class="btn" data-variant="link">链接式</button>
<button type="button" class="btn" data-variant="destructive">危险</button>

<!-- 尺寸：xs / sm / (默认) / lg / icon / icon-xs / icon-sm / icon-lg -->
<button type="button" class="btn" data-size="sm">小按钮</button>
<button
  type="button"
  class="btn"
  data-variant="outline"
  data-size="icon"
  aria-label="设置"
>
  <i data-lucide="settings"></i>
</button>
```

图标写 `<i data-lucide="图标名"></i>`，`build.py` 会替换成内联 SVG。按钮内的图标尺寸由自有组件层统一管理，不要自己加尺寸。

**按钮组**（相邻按钮拼成一条）：

```html
<div class="button-group" role="group" aria-label="视图">
  <button type="button" class="btn" data-variant="outline">列表</button>
  <button type="button" class="btn" data-variant="outline">看板</button>
</div>
```

## 卡片

```html
<article class="card">
  <header>
    <h3>标题</h3>
    <p>一句话描述。</p>
    <div class="card-action">
      <span class="badge" data-variant="secondary">进行中</span>
    </div>
  </header>
  <section>
    <p>正文。</p>
  </section>
  <footer>
    <button type="button" class="btn" data-size="sm">操作</button>
  </footer>
</article>
```

`header` / `section` / `footer` 三段都可选 —— 内边距挂在 `.card` 自己身上，卡里直接写 `<p>` 也不会贴边。`header` 内的 `h2`/`h3`/`p` 自动拿到标题与描述样式；
`.card-action` 会靠右上角。紧凑版加 `data-size="sm"`。

**反色暗卡** `data-variant="ink"`：卡内墨纸互换，次要文字、边界、图表阶和按钮全部自动反过来，
深色主题下它就是那块亮卡。它花的是和 `--hero` 同一份强调预算：**一页只放一块**，给唯一的决定性数字或结论，
`build.py` 超过一块即 WARN。不要在暗卡里再叠 `data-tone`。

**行内反色高亮** `<span class="hl">`：墨底纸字，换行处每段各自闭合。给标题里的答案词、论点句里的关键词，
一个标题只圈一处；圈整句等于没圈。放在暗卡里会再反一次，自动成立。

## 大数

```html
<p class="stat-num">
  <strong>184<small>万条/日</small></strong>
</p>
<p class="stat-num">92.4<small>%</small></p>
<p class="stat-num">$1.24<small>M</small></p>
<p class="stat-num">−12.5<small>%</small></p>
```

数字是衬线大字（上限 2.75rem，低于首屏 h1），单位一律进 `<small>`：数字走拉丁字形可以收字距，
汉字量词、百分号、货币量级缩写都不能，所以分开处理。整串放大（`<strong>184 万条/日</strong>`）
会让单位和数字抢大小、还容易折行。货币符号跟数字同大小；负号用 U+2212 不用连字符；千分位写逗号；
没有单位就不写 `small`。指标带、卡片里的 KPI、暗卡里的决定性数字都用这一个类；
`<strong>` 可加可不加，字重由 `.stat-num` 定。

### 指标带

一排并列的大数用 `.metric-band`，所有配方都能用；每格一个块，大数加标签，可再跟一行注记：

```html
<div class="metric-band">
  <div>
    <p class="stat-num">1<small>s</small></p>
    <p>每集预加载的数据量</p>
  </div>
  <div>
    <p class="stat-num">720<small>p</small></p>
    <p>ABR 自动档上限</p>
  </div>
</div>
```

格内大数以外的 `<p>` 自动是小号次要色标签，标签写在大数上面还是下面都行。不要自造 `.stat-band` 一类的外壳，也不要写 `.xxx p { font-size }`：
这条选择器会连 `.stat-num`（它也是 `<p>`）一起压小。构建的渲染检查发现 `.stat-num` 小于 1.75rem 或正文小于 10px 时会报 ERROR。

## 徽章

```html
<span class="badge">默认</span>
<span class="badge" data-variant="secondary">次要</span>
<span class="badge" data-variant="outline">描边</span>
<span class="badge" data-variant="destructive">失败</span>
<span class="badge" data-variant="ghost">弱化</span>
```

状态语义靠变体表达：通过=默认或 secondary，失败=destructive，中性=outline。
一屏里的变体不超过三种，超过就读不出状态。
表达分类（模块名、领域、负责人）改用 `data-tone`，见下方「分类色」。

## 提示块

```html
<div class="alert">
  <i data-lucide="info"></i>
  <h4>标题</h4>
  <section>
    <p>说明文字，可以带 <code>chip</code> 和 <strong>强调</strong>。</p>
  </section>
</div>

<div class="alert" data-variant="destructive">
  <i data-lucide="triangle-alert"></i>
  <h4>回滚风险</h4>
  <section><p>迁移不可逆。</p></section>
</div>
```

图标是可选的第一个子元素。`.alert` 在「复制为 Markdown」里会导出成引用块。

**`.alert > section` 是 `display: grid`，每个子节点各占一行。**
正文必须包在 `<p>` 或 `<ul>` 里；直接写裸文本，句中的 `<code>`、`<strong>` 会各自被拆成独立一行。
`.item > section` 同理（flex 列），用 `<h4>` + `<p>` 两个子元素。`.card > section` 是普通流，无此限制。

## 表格

```html
<div class="table-container">
  <table class="table">
    <thead>
      <tr>
        <th>指标</th>
        <th>基线</th>
        <th>本次</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>P50 延迟</td>
        <td>120 ms</td>
        <td>96 ms</td>
      </tr>
    </tbody>
  </table>
</div>
```

`.table-container` 提供横向滚动，宽表必须套。数字按位对齐是骨架给的（`.table` 已开 `tabular-nums`），不用自己加。

单元格里的行内 `code`（键名、路径、函数名）不会在词中间断开。多列表格放 snake_case 键名或文件路径时，在每个 `_` 和 `/` 后插 `<wbr>`，例如 `<code>audio_<wbr>room_<wbr>enter_<wbr>hint</code>`：窄屏在这些位置断行，列宽只需容下最长的一段。没插 `<wbr>` 的标识符整个不拆开，表格放不下就横向滚动。

## 列表项（item）

用于「一行一条、带图标/元信息/右侧操作」的列表，比自己搭 flex 稳。

```html
<div class="item-group">
  <div class="item">
    <figure><i data-lucide="file-text"></i></figure>
    <section>
      <h4>auth/session.ts</h4>
      <p>+42 −8，重写会话续期逻辑</p>
    </section>
    <aside><span class="badge" data-variant="outline">已评审</span></aside>
  </div>
  <hr />
  <a class="item" href="#detail"> … </a>
</div>
```

`figure` 左侧图标、`section` 主体、`aside` 右侧。`<a class="item">` 是可点整行。
条目之间的 `<hr />` 由骨架画成整宽分隔线；不写 `hr` 时相邻条目也会自动加线，两种写法都行，不要给它补页面样式。

## 折叠（原生 details，无需 JS）

```html
<div class="accordion">
  <details>
    <summary>为什么放弃方案 B</summary>
    <p>展开后的内容。</p>
  </details>
  <details open>
    <summary>迁移步骤</summary>
    <p>…</p>
  </details>
</div>
```

展开指示是骨架画的：标题右侧收起时是 `+`、展开时是 `−`（`summary::after`）。`summary` 里只写文字，不另放 chevron 之类的图标，否则会和加减号同时出现。

## 标签页（需要 JS）

```html
<div class="tabs" id="tabs-approach">
  <nav role="tablist" aria-orientation="horizontal">
    <button
      type="button"
      role="tab"
      id="t1"
      aria-controls="p1"
      aria-selected="true"
      tabindex="0"
    >
      方案 A
    </button>
    <button
      type="button"
      role="tab"
      id="t2"
      aria-controls="p2"
      aria-selected="false"
      tabindex="-1"
    >
      方案 B
    </button>
  </nav>
  <div role="tabpanel" id="p1" aria-labelledby="t1" tabindex="-1">A 的内容</div>
  <div role="tabpanel" id="p2" aria-labelledby="t2" tabindex="-1" hidden>
    B 的内容
  </div>
</div>
```

id / `aria-controls` / `aria-labelledby` 必须对得上，否则 JS 接不上。默认选中项：`aria-selected="true"` +
`tabindex="0"`，其余 `aria-selected="false"` + `tabindex="-1"` + `hidden`。
`<nav role="tablist" data-variant="line">` 切换成下划线样式。

## 下拉菜单（需要 JS）

```html
<div class="dropdown-menu" id="dd-filter">
  <button
    type="button"
    id="dd-filter-trigger"
    class="btn"
    data-variant="outline"
    aria-haspopup="menu"
    aria-controls="dd-filter-menu"
    aria-expanded="false"
  >
    筛选<i data-lucide="chevron-down"></i>
  </button>
  <div id="dd-filter-popover" data-popover aria-hidden="true">
    <div role="menu" id="dd-filter-menu" aria-labelledby="dd-filter-trigger">
      <button type="button" role="menuitem">全部</button>
      <button type="button" role="menuitem">仅未决</button>
      <hr role="separator" />
      <button type="button" role="menuitem">
        导出<kbd class="kbd">⌘E</kbd>
      </button>
    </div>
  </div>
</div>
```

外层 `id` 是根，`-trigger` / `-popover` / `-menu` 三个 id 由它派生。

## 对话框（原生 dialog，无需 JS）

```html
<button
  type="button"
  class="btn"
  onclick="document.getElementById('dlg-detail').showModal()"
>
  详情
</button>

<dialog
  id="dlg-detail"
  class="dialog"
  aria-labelledby="dlg-detail-title"
  onclick="if (event.target === this) this.close()"
>
  <div>
    <header>
      <h2 id="dlg-detail-title">标题</h2>
      <p>描述。</p>
    </header>
    <section><p>正文。</p></section>
    <footer>
      <form method="dialog">
        <button class="btn" data-variant="outline">关闭</button>
      </form>
    </footer>
  </div>
</dialog>
```

`.dialog > div` 这层包裹不能省。破坏性确认用 `class="alert-dialog"`。

## 表单控件（全部纯 CSS）

```html
<div class="field">
  <label for="name">名称</label>
  <input type="text" id="name" placeholder="服务名" />
  <p>会出现在告警标题里。</p>
</div>

<div class="field">
  <label for="env">环境</label>
  <select id="env">
    <option>staging</option>
    <option>production</option>
  </select>
</div>

<div class="field">
  <label for="note">备注</label><textarea id="note" rows="3"></textarea>
</div>

<div class="field">
  <label><input type="checkbox" checked /> 发布前跑一次全量回归</label>
</div>
<div class="field">
  <label><input type="checkbox" role="switch" /> 灰度开关</label>
</div>
<div class="field">
  <label for="ratio">采样比例</label
  ><input type="range" id="ratio" min="0" max="100" value="20" />
</div>
```

`.field` 外的独立控件加 `class="input"` / `class="select"` / `class="textarea"` / `class="label"` 取同样外观。
一组字段外面套 `<fieldset class="fieldset"><legend>…</legend>` 分区。

**输入组**（带前后缀 / 内嵌按钮）：

```html
<div class="input-group">
  <i data-lucide="search"></i>
  <input type="search" placeholder="过滤…" />
  <kbd class="kbd" data-align="end">/</kbd>
</div>
```

## 决定块

**决定块**是页面上请读者拍板的一处：一个问题加 2 到 6 个选项，作者标出建议的选项。读者在页面上选，再用工具条上的回复按钮把所有决定和评论汇总成一段 Markdown（**回复**）贴回给 Agent。决定块只能放在开启了回复能力的页面上。

**开启回复能力**：在 `<body>` 上加 `data-reply`，例如 `<body data-recipe="approach-compare" data-reply>`。`build.py` 只在有这个标记时内联回复运行时（`assets/reply.js`），去掉标记重建就移除。开启后页面多出三样东西，都由运行时生成，作者不写标记：

- 正文每个顶层节（`#doc` 里的 `h1` / `h2`，组件容器里的标题不算，排除规则同目录）标题下一个「评论」按钮，点开是一个多行文本框，Esc 收起。
- 工具条上页面标题右端的回复按钮，显示「已作答决定数/决定总数 · 评论数」，点一下复制回复。
- 正文末尾一节：作答进度说明、「复制回复」和「清空作答」（点两次才清）。

```html
<fieldset class="decision" data-decision="queue">
  <legend>采用哪个任务队列方案？</legend>
  <label
    ><input type="radio" /> 方案甲：沿用 cron<small>不新增组件</small></label
  >
  <label
    ><input type="radio" data-suggested /> 方案乙：Redis 队列<small
      >重试内置，多运维一个 Redis</small
    ></label
  >
  <label><input type="radio" /> 方案丙：托管队列</label>
</fieldset>
```

- `fieldset.decision` 加 `data-decision="页内唯一的标识"`，问题写在 `<legend>`。
- 每个选项是一个 `<label>`：里面一个 `<input>`，后面是选项名，可选一句 `<small>` 说明。单选全用 `type="radio"`，多选全用 `type="checkbox"`，不加 `name`（运行时按标识分组），不隐藏原生控件。
- 建议项在 `<input>` 上写 `data-suggested`。单选恰好一个；多选零个或多个。运行时在建议项的选项名后加一个「建议」徽章，Markdown 导出写成「（建议）」，回复里的「建议是 …」也读这个属性。
- 所有选项一开始都不选中，不写 `checked`。读者的回复只该包含他真正做过的选择。
- 决定块放在它影响的那一节里，紧跟交代取舍的证据；不做选项预览（图、卡片）。

`build.py` 报 ERROR 的写法：页面没开启回复能力却有决定块；缺 `data-decision` 或标识重复；写了 `data-decision` 的 `<fieldset>` 漏了 `class="decision"`；选项不是 2 到 6 个；同一个决定块里两个选项重名（选项名是 `<label>` 里去掉 `<small>` 说明后的文字）；混用单选框和复选框；单选的建议项不是恰好一个。报错点名是哪个决定块，重名时还点名是哪个选项名。

### 回复

运行时暴露 `window.showMeReply()`，返回回复文本；工具条按钮、页尾按钮和 `build.py --snap`（写 `reply.md`）都调它。格式是契约：

```markdown
# 回复：<页面标题>

## 决定

- <问题>：<所选选项>（采纳建议）
- <问题>：<所选选项>（改选，建议是 <建议项>）
- <问题>：未作答（建议是 <建议项>）

## 评论

- 「<节标题>」
  > <读者原文，逐行加引用符号>
```

- 决定按页面顺序全部列出，包括未作答的。多选列出全部选中项，与建议不同时写「改选，建议是 A、C；加选 B；未选 C」；没有建议项的多选写「（没有建议项）」。
- 评论只列写了内容的节；没有评论时整节省略。两节标题相同时，从第二节起在标题后加序号写成「<节标题>（2）」「<节标题>（3）」，与状态里的键一致。页面没有决定块时省略「决定」一节；两样都没有时写一句「读者没有写评论。」

### 读者状态与初始状态

读者的选择和评论存在浏览器本地存储里，刷新或重新打开后还在。键含页面路径和决定块集合（标识、选项名）的签名：页面重做后决定块变了，旧作答作废。状态只有一种形状，决定按选项名、评论按节标题（同名的节用回复里那种带序号的写法）：

```json
{
  "decisions": { "queue": ["方案乙：Redis 队列"], "gates": [] },
  "comments": { "判据横向核对": "表格少了成本一列。" }
}
```

页面可以带一段同形的初始状态，写在 `<!--SHOW-ME:JS-->` 之前、`</main>` 之后：

```html
<script type="application/json" data-reply-state>
  { "decisions": { "queue": ["方案乙：Redis 队列"] } }
</script>
```

加载顺序：标记里的选中状态 → 初始状态 → 本地存储，后者只覆盖它记录了的决定块和节。重做页面时用它带入读者上一轮的作答（选项名和节标题照抄回复里的文字），读者不用把没变的决定再选一遍。读者原文里的 `<` 在 JSON 里一律写成转义 `\u003c`（`JSON.parse` 读回来仍是 `<`），否则原文里的 `</script>` 会提前结束这段脚本、截断页面；用 Python 生成时写 `json.dumps(state, ensure_ascii=False).replace("<", "\\u003c")`。构建器不改写这段数据，自检也不把里面的读者原文当成页面自己的脚本和写死的颜色。

「复制为 Markdown」导出决定块的问题和选项、标出建议项，不带读者的选择；评论入口、回复按钮和页尾一节都不进导出。打印保留决定块和当前选择，隐藏评论按钮和回复控件；写了内容的评论以文字随所在节印出。

## 代码块

```html
<pre><code class="language-go">func main() {
    fmt.Println("hi")
}</code></pre>
```

**语法高亮是自动的**，不用引任何东西：`build.py` 扫描页面里出现的 `language-*`，
只把用到的那几种语言的规则内联进去（分词器 1.7 KB + 每种语言 0.2–3 KB）。
着色在首绘前同步完成，不会闪一下再变色。

- 语言名写 `language-<名字>`，常用的都支持：`go` `rust` `ts` `js` `py` `bash` `json` `yaml` `kotlin`
  `toml` `sql` `html` `css` `xml` `md` `java` `c` `lua` `docker` `http` `ini` `make` `git`。
  别名会自动归一（`rust`→rs、`python`→py、`shell`/`sh`→bash、`tsx`→ts）。
  没有对应规则时 `build.py` 会 WARN 并让该块保持纯文本 —— 不要为此改语言名去凑。
- **`language-diff` 和 `language-text` 不着色**：前者归 `.d-add`/`.d-del` 管（见 `layouts.md`
  的「结构视图」），后者是调用树/文件树这类结构图，上语法色只会添乱。
- 行内 `<code>` 不着色，它是正文的一部分。
- 配色走 `--syn-comment` / `--syn-keyword` / `--syn-string` / `--syn-type` / `--syn-number`
  五个 token（骨架已给，两套主题各一组，在代码块底上实测 4.6:1 以上）。
  运算符和变量刻意不上色 —— 全上会花。想改配色就改这五个 token，不要去写 `.shj-syn-*` 规则。
- **换行 / 复制工具条是骨架给的**：每个 `pre > code` 右上角自动带「换行」「复制」两个按钮，hover 或键盘焦点进入时出现，
  触屏常显，打印隐藏，不进 Markdown 导出。页面不要自己再做复制按钮；不想让某块换行就别管它，默认关。

### 代码引用

页面里展示仓库里真实存在的代码时，推荐写**代码引用**：在代码块上写明文件路径和行号，内容留空，构建时由 `build.py` 从文件读进来。
伪代码、调用树、简化过的片段这类**示意代码**照旧手写，构建器不检查也不改动。

```html
<pre><code data-src="src/app.ts" data-lines="18-30"></code></pre>
```

- `data-src` 必填，写文件路径。`data-lines` 可选：`18-30` 引用一段（闭区间，从 1 起算），`18` 引用一行，不写引用整个文件。
- 路径按**运行构建命令的目录**解析，和图片按页面所在目录解析不同。在仓库根目录运行 `build.py`，路径就写读者熟悉的仓库相对路径。
  只能引用这个目录以内的文件：`../` 越界、绝对路径、`~/` 开头、`file:` 地址和指向目录外的符号链接都报 ERROR，报错里写出解析所用的目录。
- 构建器在代码块上方生成来源标注（`src/app.ts:18-30`，单行写 `src/app.ts:18`，整文件只写路径），代码带从文件实际行号开始的行号。
  行号不进「复制」和「复制为 Markdown」，读屏器不念，打印保留；导出的 Markdown 把来源标注写在代码围栏上方一行。
- 语言按扩展名推断，不用写 `language-*`；没有对应语法的扩展名按纯文本显示。推断错时显式写 `language-*`，显式的优先。
- 每次构建都按文件当前内容刷新。重建时文件找不到（换了分支、在别处构建），保留上次填进去的代码并给 WARN；第一次构建就找不到报 ERROR。
- 长度：超过 40 行给 WARN，超过 200 行报 ERROR。用 `data-lines` 只引用和论点有关的几行。
- 这些情况报 ERROR，代码块不填充：
  - 写法：只写了 `data-lines` 没写 `data-src`；`<code>` 不是直接放在 `<pre>` 里；写在 `language-diff` 上（diff 用「结构视图」手写，见 `layouts.md`）；
    代码块里手写了内容；`data-src` 是空的；`data-lines` 倒序、为 0 或不是数字。
  - 路径：越出运行构建命令的目录（见上面的路径规则）；文件找不到（只在第一次构建时报，重建时见上面的刷新规则）；指向的不是文件（比如目录）；文件读不了（权限不够）。
  - 密钥：路径（解析符号链接前后都算）的任何一层是存放密钥的目录（`.git`、`.ssh`、`.aws` 等，清单同「图片」），在这类目录里运行构建也一样；
    文件名是 `.env` 或 `.env.` 开头（`.env.example`、`.env.sample`、`.env.template`、`.env.dist` 这四个模板除外），或是 `.netrc`、`.npmrc`、`.pypirc`；
    文件名是 ssh-keygen 默认的私钥名 `id_rsa`、`id_dsa`、`id_ecdsa`、`id_ed25519`、`id_xmss`（及其带 `_sk` 的版本，`.pub` 公钥不算），或扩展名是 `.pem`、`.key`、`.p12`、`.pfx`；
    引用的几行看起来含私钥、令牌或带密码的地址。
  - 内容：文件是二进制（含 NUL 字节或不是 UTF-8）；行号超出文件末尾（报错写明文件有几行）；超过 200 行（见上面的长度规则）。
- `--check-only` 不读文件，没填充过的代码引用报 ERROR，去掉 `--check-only` 构建一遍即可。
  构建摘要里的「代码引用=N 处」是页面里代码引用的个数：带 `data-src` 的 `<code>` 都算，报错的和保留旧内容的也算。
- 成品里 `<code>` 上的 `data-src-start`、`data-src-lang` 和来源标注都归构建器所有，重建时整块重写，不要手改。

## 来源行与口径侧栏

```html
<p class="src">季度调研 · 100 个团队 · 多选，合计可超过 100</p>
```

`.src` 是脱离 figure 的来源行，与图的 `fig-src` 同一套 mono 小字：表格、指标带、引文下面都要交代来源与口径，
不要把口径塞进正文段落。侧栏 `.with-rail` / `.method-rail` 的结构见 layouts.md「报告节律」；
侧栏是卡片面色，不是第二套目录。

## 图片

截图用来呈现只能拍下来的东西：真实界面、报错弹窗、监控面板、设计稿。能画出来的示意（流程、结构、数据）照 `diagrams.md` 画 SVG、写 Mermaid，或照 `charts.md` 画数据图，它们跟随主题、能放大、导出时保留数据。

```html
<figure class="fig">
  <img src="shots/login-error.png" alt="登录页提交后弹出 500 错误" />
  <figcaption>改动前：提交后直接 500，没有可读的报错。</figcaption>
</figure>
```

- 写普通的 `<img src="路径" alt="说明">`。`build.py` 构建时把文件读进来，改写成页面内的 `data:` 地址，并在 `<img>` 上记下 `data-img-name="文件名"`，成品仍是一个文件，转发、离线都能看。
- 路径：相对路径按页面文件所在目录解析（和直接在浏览器里打开未构建的页面看到的是同一张）；绝对路径、`~/` 开头的路径和 `file://` 地址也可以。成品里只留文件名，不留目录。
- 格式：PNG、JPEG、GIF、WebP、AVIF、SVG，扩展名要和文件内容一致。单张上限 5 MB，大图先裁剪或压缩再放。
- 存放密钥和登录信息的目录（`.git`、`.ssh`、`.aws`、`.azure`、`.gnupg`、`.kube`、`.docker`、`.password-store`）里的文件不能内联，看起来含密钥或令牌的 SVG 也不能。截图先存到工作目录。
- `alt` 必填，写图里要读者看到的内容。纯装饰图写 `alt=""`。
- 有图注时放进 `<figure>`，图注用 `<figcaption>`，写成一句能独立成立的结论。图片宽度自动压到版心以内，高度随比例；打印时图和图注不跨页。
- 换图：把 `src` 改回文件路径再构建。已经是 `data:` 的图片构建时原样保留，重复构建结果不变。
- 本地资源只走 `<img src>` 这一种写法，路径后的 `?…`、`#…` 读文件时忽略。其他写法指向本地文件时 `build.py` 报 ERROR：图片类的 `srcset`、`<picture>` 的 `<source>`、`<video poster>`、`<input type="image">`、SVG 里的 `<image href>`、`<feImage href>` 和指向别的文件的 `<use href="x.svg#a">`、样式里的 `url()` 和 `image-set()`，改用 `<img src>`；非图片的 `<video>` / `<audio>`、`<track>`、`<iframe>`、`<object>`、`<embed>`、`<script src>`、会联网或加载内容的 `<link>`、样式里的 `@import`，页面必须自包含；`@font-face` 的 `src` 指向本地字体文件也是 ERROR，字体用骨架的 Google Fonts 或在字体栈里写 `local()` 兜底，把内容写进页面或删掉。`<a href>` 是链接不受限，`#id` 片段引用和 `data:` 地址也不算。上面任何一种写法（含 `<img src>`）指向 http(s) 或 `//` 开头的远程地址时同样报 ERROR，唯一放行的是骨架那几个指向 Google Fonts 的 `<link>`。
- 「复制为 Markdown」把图片导出成 `![alt](文件名)`，不带图片数据。

## 其余

```html
<span class="kbd">⌘K</span>
<!-- 键位 -->
<div class="progress"><span style="width:64%"></span></div>
<!-- 进度条 -->
<div class="skeleton" style="height:1rem"></div>
<!-- 骨架屏 -->
<nav class="breadcrumb">
  <ol>
    <li><a href="#a">仓库</a></li>
    <li aria-hidden="true"><i data-lucide="chevron-right"></i></li>
    <li><span aria-current="page">auth</span></li>
  </ol>
</nav>
<div class="avatar" data-size="sm"><span>MG</span></div>
<div class="empty">
  <!-- 空状态 -->
  <header>
    <figure><i data-lucide="inbox"></i></figure>
    <h3>还没有数据</h3>
    <p>连上数据源后这里会有内容。</p>
  </header>
</div>
```

## 设计 token

主题色全部是 CSS 变量。写自定义样式时用 token，不要写死颜色，写死的颜色在深色主题下不会跟着切换。当前方向是一墨一纸：所有灰都是墨在纸上的明度阶，深色只换两极，唯一彩色落点是 `--hero`。页面只消费下表的语义角色，不直接取原语（`--ink` / `--paper` / `--hero`）或明度阶（`--ink-*`），分层见 `visual-system.md`。

| token                                               | 用途                             |
| --------------------------------------------------- | -------------------------------- |
| `--color-background` / `--color-foreground`         | 页面底色 / 正文色                |
| `--color-card` / `--color-card-foreground`          | 抬升面 / 其上文字                |
| `--color-muted` / `--color-muted-foreground`        | 弱化底色 / 次要文字              |
| `--color-primary` / `--color-primary-foreground`    | 主强调（主按钮、进度条、焦点环） |
| `--color-secondary` / `--color-accent`              | 次要面 / 悬停面                  |
| `--color-destructive`                               | 危险、失败、删除                 |
| `--color-border` / `--color-input` / `--color-ring` | 描边 / 输入框边 / 焦点环         |
| `--chart-1` … `--chart-5`                           | 图表序列色：明度阶，1 最重       |
| `--chart-hero`                                      | 一张图里唯一的主角元素           |
| `--radius`                                          | 圆角基准                         |
| `--font-sans` / `--font-serif` / `--font-mono`      | 字体栈（骨架里已加中文回退）     |

图表色写 `var(--chart-1)`，**没有** `--color-chart-1` 这个名字。数据图的五件套外壳（`.fig` / `.fig-box` / `.fig-head` / `.fig-sub` / `.fig-src` / `figcaption`）、`.charts` 栅格与入场动画类在 `show-me.css`，契约见 `charts.md`「五件套外壳」。

## 公式

直接写 LaTeX，`build.py` 编译成 MathML 内联（Temml，零运行时）：

- 行内 `$E[W_k] = \min(c, b\cdot 2^k)/2$` 或 `\( … \)`。写线性形式；行内 `\frac` 会撑坏行高，`build.py` 发 WARN。
- 块级单独一行 `$$ … $$` 或 `\[ … \]`，直接放在 `section` 里，不包 `<p>`。堆叠分数、求和号只在这里用。
- `$5 和 $8` 这类价格不会被当成公式（开 `$` 后与闭 `$` 前不能有空白，闭 `$` 后不能紧跟数字）；要写字面 `$` 用 `\$`。
- 代码块、`<code>`、脚本和样式内部的 `$` 不会被碰。
- 编译需要本机有 `node`；没有时 `build.py` 报 ERROR，页面不能带着未编译的 `$…$` 交付。
- 「复制为 Markdown」把公式还原成 LaTeX 源。

## 字体

三个栈已经调好，**不要在页面里重写 `--font-*`**，也不要动骨架 `<head>` 里的字体 `<link>`。

| token          | 网络字体                   | 兜底                                                             |
| -------------- | -------------------------- | ---------------------------------------------------------------- |
| `--font-sans`  | IBM Plex Sans              | system-ui → PingFang SC / 微软雅黑                               |
| `--font-serif` | Newsreader + Noto Serif SC | Georgia → 思源宋体 → Songti SC                                   |
| `--font-mono`  | IBM Plex Mono              | ui-monospace → SF Mono → Menlo                                   |
| 公式（`math`） | 无网络字体                 | Latin Modern Math → STIX Two Math → Cambria Math → `math` 通用族 |

**这是本 skill 唯一放行的外部资源。** 骨架用 `media="print" onload="this.media='all'"`
异步加载 —— `fonts.googleapis.com` 在部分网络下不可达（**中国大陆整体不可达**），
同步 `<link>` 会把首屏卡在请求超时上。异步写法下首屏立刻用兜底字体渲染，字体取到了再换。
取不到时页面完全正常，只是落到系统字体。

**中西配平不靠技巧，靠少要一个字重。** 思源宋体的笔画比 Newsreader 细，同一
`font-weight` 下并排会显得虚。骨架向 Google 请求 Noto Serif SC 时**只要 500 和 700，
不要 400**：正文请求 400 时 CSS 的字体匹配会挑最近的可用面，于是落到 500，中文自动重一档。
`h3` 的 600 同理落到 700 —— 是真字重，不是合成粗体。

少要一个 600 是有意的：Google 把中文切成上百个 unicode-range 分片，每多一个字重就多约
31 KB 声明（三个字重 93 KB，两个 63 KB，均为压缩后）。

**中文标题不用负字距。** 骨架给 `h1` / 首屏 `h1` / `.fig-title` 的负字距（-0.01 ～ -0.035em）
和首屏 0.98 行高都是收紧拉丁字形用的；汉字满铺 em 框，负字距只会挤字，0.98 行高让多行标题上下相贴。
页面 `lang` 为中文（骨架默认 `zh-CN`）时 CSS 用 `:lang(zh)` 整体归正：标题字距 0.01em、首屏 h1 行高 1.2。
同页纯英文标题也随之放开，混排里拉丁与汉字的字距不能各调各的。切换 `lang` 到英文即恢复拉丁收紧值，
不要在页面里另写 `letter-spacing` 去补。中文大标题要压缩感时用更重的字重与 0.02 ～ 0.06em 正字距，汉字没有压缩字形。

**离线时的配平**由骨架的 `Han Serif Balanced` 接手：三个单值字重面（`500 500` /
`600 600` / `700 700`），`src` 全是 `local()`，装了思源宋体就生效。单值范围是必须的 ——
写成 `500 900` 浏览器会按请求字重去实例化可变轴，配平当场失效。

**家族名写错的表现不是报错，是变丑。** `"Source Han Serif SC"` 少写 `" VF"`，浏览器
不吭声，只是安静落到下一个字体，中文从此细一档 —— 直到有人觉得「怎么这么细」。
`build.py` 有三道闸：

- 字体栈和 `local()` 里的每个家族名，要么在它的 `KNOWN_FAMILIES` 名单里，
  要么页面自己有对应的 `@font-face`，否则 WARN。加新字体时连名单一起加。
- 每个 `--font-*` 栈必须以通用族（`serif` / `sans-serif` / `monospace`）收尾，否则 ERROR。
- 每个网络字体后面必须还有本地字体，否则 ERROR —— Google Fonts 取不到时那个位置就空了。

**骨架已经打开的排版细节**，页面不用重复写：

- `h1`–`h4` 是 `text-wrap: balance`（标题不留孤字），正文段落、列表、图注是 `text-wrap: pretty`。
- `main` 是 `hyphens: manual` —— 中英混排下 auto 会断在莫名其妙的位置。
- `.table` 是 `font-variant-numeric: tabular-nums`，表格里的数字按位对齐。
  自绘的统计数字要对齐时自己加这一条。
- `body` 开了 `optimizeLegibility` 与灰度抗锯齿。

## 单一视觉层

`show-me-html` 不再提供 `--style` 风格包。所有页面使用同一套 token、主题和组件状态；21 个配方通过几何、证据载体和交互方式区分。需要改变视觉方向时改 `assets/show-me.css` 与本文，不要在单页上叠一套主题。
