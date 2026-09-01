# 组件词表

组件外观由 `assets/show-me.css` 统一提供。写 markup 前读本文；**不要在单页里重做按钮、卡片、徽章或表格的外观**，否则主题、焦点状态和打印会分叉。

三条规则：

1. **语义 HTML 优先。** 自有 CSS 靠元素结构选中子元素（`.card > header > h2`），不是靠一串内部子类名。结构写错，样式就不生效。
2. **变体走 `data-` 属性**，不是 class：`.btn[data-variant]`、`.btn[data-size]`、`.badge[data-variant]`、`.alert[data-variant]`、`.card[data-size]`。
3. **没有 Tailwind 工具类。** 布局使用配方规定的结构类；少量页面级几何可以写在自己的 `<style>` 里，只能取 `var(--color-border)`、`var(--radius)` 等 token。

## 需要 JS 的组件只有两个

`tabs` 和 `dropdown-menu`（以及少用的 `popover` / `combobox` / `command` / `sidebar` / `drawer` / `chart`）。
`build.py` 检测到这些 class 时会自动内联保留的 basecoat JS。其余组件使用自有 CSS 和浏览器原生能力。

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

`header` / `section` / `footer` 三段都可选。`header` 内的 `h2`/`h3`/`p` 自动拿到标题与描述样式；
`.card-action` 会靠右上角。紧凑版加 `data-size="sm"`。

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

## 折叠（原生 details，无需 JS）

```html
<div class="accordion">
  <details>
    <summary>为什么放弃方案 B<i data-lucide="chevron-down"></i></summary>
    <p>展开后的内容。</p>
  </details>
  <details open>
    <summary>迁移步骤<i data-lucide="chevron-down"></i></summary>
    <p>…</p>
  </details>
</div>
```

`summary` 里的最后一个 `<svg>` 会被自动旋转成展开指示。

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

## 代码块

```html
<pre><code class="language-go">func main() {
    fmt.Println("hi")
}</code></pre>
```

**语法高亮是自动的**，不用引任何东西：`build.py` 扫描页面里出现的 `language-*`，
只把用到的那几种语言的规则内联进去（分词器 1.7 KB + 每种语言 0.2–3 KB）。
着色在首绘前同步完成，不会闪一下再变色。

- 语言名写 `language-<名字>`，常用的都支持：`go` `rust` `ts` `js` `py` `bash` `json` `yaml`
  `toml` `sql` `html` `css` `xml` `md` `java` `c` `lua` `docker` `http` `ini` `make` `git`。
  别名会自动归一（`rust`→rs、`python`→py、`shell`/`sh`→bash、`tsx`→ts）。
  没有对应规则时 `build.py` 会 WARN 并让该块保持纯文本 —— 不要为此改语言名去凑。
- **`language-diff` 和 `language-text` 不着色**：前者归 `.d-add`/`.d-del` 管（见 `layouts.md`
  的「结构视图」），后者是调用树/文件树这类结构图，上语法色只会添乱。
- 行内 `<code>` 不着色，它是正文的一部分。
- 配色走 `--syn-comment` / `--syn-keyword` / `--syn-string` / `--syn-type` / `--syn-number`
  五个 token（骨架已给，两套主题各一组，在代码块底上实测 4.6:1 以上）。
  运算符和变量刻意不上色 —— 全上会花。想改配色就改这五个 token，不要去写 `.shj-syn-*` 规则。

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

主题色全部是 CSS 变量。写自定义样式时用 token，不要写死颜色，写死的颜色在深色主题下不会跟着切换。当前方向是暖灰纸面、深蓝墨色和钴蓝主强调；页面只消费语义角色，不依赖具体色值。

| token                                               | 用途                             |
| --------------------------------------------------- | -------------------------------- |
| `--color-background` / `--color-foreground`         | 页面底色 / 正文色                |
| `--color-card` / `--color-card-foreground`          | 抬升面 / 其上文字                |
| `--color-muted` / `--color-muted-foreground`        | 弱化底色 / 次要文字              |
| `--color-primary` / `--color-primary-foreground`    | 主强调（主按钮、进度条、焦点环） |
| `--color-secondary` / `--color-accent`              | 次要面 / 悬停面                  |
| `--color-destructive`                               | 危险、失败、删除                 |
| `--color-border` / `--color-input` / `--color-ring` | 描边 / 输入框边 / 焦点环         |
| `--chart-1` … `--chart-5`                           | 图表序列色，浅色与深色各一组     |
| `--radius`                                          | 圆角基准                         |
| `--font-sans` / `--font-serif` / `--font-mono`      | 字体栈（骨架里已加中文回退）     |

图表色写 `var(--chart-1)`，**没有** `--color-chart-1` 这个名字。

## 字体

三个栈已经调好，**不要在页面里重写 `--font-*`**，也不要动骨架 `<head>` 里的字体 `<link>`。

| token          | 网络字体                   | 兜底                               |
| -------------- | -------------------------- | ---------------------------------- |
| `--font-sans`  | IBM Plex Sans              | system-ui → PingFang SC / 微软雅黑 |
| `--font-serif` | Newsreader + Noto Serif SC | Georgia → 思源宋体 → Songti SC     |
| `--font-mono`  | IBM Plex Mono              | ui-monospace → SF Mono → Menlo     |

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

`show-me-html` 不再提供 `--style` 风格包。所有页面使用同一套 token、主题和组件状态；20 个配方通过几何、证据载体和交互方式区分。需要改变视觉方向时改 `assets/show-me.css` 与本文，不要在单页上叠一套主题。
