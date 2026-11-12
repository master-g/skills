# 分章派发

每章由一个子 agent 写成**片段**（一个完整的 `<article class="chapter">`），主 agent 用 `scripts/assemble.py` 把片段拼成页面。子 agent 看不到主对话，它需要的东西全部写进交代里。

页面每次从片段重新生成：要改内容就改片段再拼接，不改页面，改在页面上的东西下次拼接就没了。

## 写好外壳

在工作区建源目录 `<页面名>.work/src/`，片段都放在这里：

- `head.html`：`assets/shell.html` 从开头到 `</header>`，写好扉页（含 `<title>`）。
- `tail.html`：`assets/shell.html` 从 `<!--TR:JS-->` 到文件末尾，原样存。
- `refs.html`：参考文献那个 `<section class="references">`；没有参考文献就不建。

shell.html 里的示例章不保留。派发之前这三个文件要写好：子 agent 的试构建会用到它们，`<title>` 还是骨架占位、或者引用链到的文献条目不在 `refs.html` 里，构建都报 ERROR。

## 切原文

把原文按章切开，存成工作区的 `source/chNN.*`（`NN` 是两位序号，从 `01` 起）。该章用到的图文件留在输出目录的 `figures/`。原创撰写没有原文可切，改为把该章要用的资料路径列进交代。

## 派发

一批派四个子 agent，一批全部返回后再派下一批。每个子 agent 的交代写全这几项：

- 任务：把这一章写成片段，存到源目录的 `chNN.html`；附录存成 `apxN.html`，拼接时排在各章之后。
- 处理方式：全文忠实翻译、整理或原创撰写，以及用户对这本读本的特别要求。
- 路径：该章原文（或资料）、`glossary.md`、`figures/`、源目录、页面的输出路径、`references/markup.md`、`references/style.md`、`scripts/`，都写绝对路径。
- 该章在结构清单里的那几行：章 `id`（按 [标记契约](markup.md) 的「章与节」取）、`chapter-number`、各类元素的条数；原创撰写再加图、表、式的编号区间。
- 画图：用图元库的图，画图代码写到源目录的 `chNN.figs.py`，只往 `FIGS` 里加条目，键名以章 `id` 开头；片段里留 `<!--FIG:键名-->`，占位符由拼接脚本填。流程图、时序图这类结构图直接在片段里写 Mermaid 源码（`references/markup.md` 的「Mermaid 图」），构建时编译，不经 `FIGS`。
- 完成标准：片段的段落、脚注、图、表、公式与该章原文一一对应；试构建 0 个 ERROR，统计与该章清单的每处差异都说得出原因。试构建只拼这一章：

  ```sh
  python3 <skill-path>/scripts/assemble.py <源目录> -o <页面路径> --only chNN
  ```

  它在页面旁边写出 `<页面名>.chNN.check.html` 并构建，核对完删掉这个文件。试构建里只有这一章，指向其他章的页内链接会报「页内链接指向不存在的 id」：这一条不用修，在返回里列出来。

- 返回：片段路径；构建统计与清单的差异及原因；`glossary.md` 之外自己新定的译名；试构建里留下的跨章链接；存疑之处（取不到的图、拿不准的译法）。

## 拼接

一批返回后先收术语：把各章新定的译名并进 `glossary.md`，同一术语出现两个译名时定下一个，在已有片段里统一替换，后面各批用更新后的术语表。

全部返回后：

1. 通读各章之间的指代（「见第 N 章」「如图 N」「式 (N)」），对不上的在片段里改正。
2. 用户要求配题图时，按 [题图](plates.md) 把章首题图放进对应的片段，扉页题图放进 `head.html`。题图由主 agent 统一放，子 agent 的交代里不提题图。
3. 拼接并构建：

   ```sh
   python3 <skill-path>/scripts/assemble.py <源目录> -o 页面.html
   ```

   它按文件名顺序拼 `head.html`、各章、附录、`refs.html`、`tail.html`，在同一个进程里执行各章的画图脚本并填回占位符（全书的图在一个进程里画完，图内 `id` 的前缀才各不相同），再调用 `build.py`。`--open`、`--by-chapter` 这些参数原样交给 `build.py`。

之后回到 SKILL.md 的「构建与核对」，拿构建输出的统计与全书合计对账；修 ERROR、改正文都在片段里做，再运行上面这条命令。
