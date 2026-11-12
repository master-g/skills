# Plan 033: tufte-reader 修脚注重建缺陷，收紧构建入口，统计按章并加段落数，新增拼接脚本

> **Executor instructions**: 按 Step 1 到 Step 5 的顺序执行，每一步跑完验证命令并确认预期结果后再进下一步。每一步是一个独立的提交，做完任何一步都可以停。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**：`git diff --stat 81a8f3e..HEAD -- skills/tufte-reader`
> 预期无输出。有输出就把「Current state」的摘录与现行代码逐段对照；对不上即为 STOP 条件。

## Status

- **Priority**: Step 1 是 P1，Step 2–4 是 P2，Step 5 是 P3
- **Effort**: M（Step 1、Step 4 的代码以附件提供并验证过；Step 2、Step 3 由执行者按规格实现）
- **Risk**: LOW–MEDIUM。Step 1、2、5 不改变正常构建的成品。Step 3 改「统计」行的文字。Step 4 改分章派发的工作区布局，是本计划里唯一改变做法的一步
- **Depends on**: 无
- **Category**: bug、dx
- **Planned at**: commit `81a8f3e`, 2026-11-12

## Why this matters

2026-11-12 维护者要求审计 tufte-reader。审计读了 `SKILL.md`、`dispatch.md`、`style.md`、`markup.md`、`plates.md` 的前四节和 `build.py` 全文，跑了全部测试和 specimen 构建，并用最小页面实测了几处构建行为。结果按优先级排列如下，每条都注明是实测还是推断。

1. **已归位的脚注里有列表时，重建会把新脚注插错位置，构建仍然通过（实测）。** 一章里已归位的脚注含 `<ol>`，之后在同一章再加一条脚注并重建，新脚注被插进前一条脚注的列表里，结果是 0 个 ERROR。`markup.md` 让含列表的注释走 `footnote`，也允许在已构建的页面上加脚注，两条路径都是文档认可的。
2. **标签没有闭合时构建抛 traceback（实测）。** 漏写 `</article>` 时 `element_end` 抛 `ValueError`，没有变成一行 ERROR。审计当时说会留下只编译了一半的页面，这个说法偏重：复核时补上标签重建，页面正常通过，所以后果只是报错难读。
3. **拼错的参数被忽略（实测）。** `--chek-only` 不报错，页面照常被改写。
4. **统计里没有段落数，也只有全书合计（读代码确认）。** `SKILL.md` 第 3 步和 `style.md` 都把「原文一段对应译文一段」当作结构核对的前提，而统计行没有段落这一项。结构清单是逐章的，统计对不上时要自己找是哪一章。
5. **分章派发的拼接每次由主代理现写（读文档推断，未见事故）。** `dispatch.md` 的「拼接」要求在同一个进程里执行各章的画图脚本、填占位符、按序拼章，`figlib.py` 只提供 `embed` 函数。维护者的 shelf 仓库六本书各有一份 14 行的 `src/assemble.py` 做同一件事，逐本复制。
6. **`SKILL.md` 的「修改本技能」两段是写给维护者的（读文档确认）。** 它们每次做读本都会加载。

### 维护者已确认的决定（不要改）

- 本计划处理的是缺陷和设计优化点，不做权限盘点（2026-11-12 确认）。
- 技能新增一个拼接脚本，分章派发改用 shelf 那套片段布局：`head.html`、`chNN.html`、`apx*.html`、`refs.html`、`tail.html`、画图脚本（2026-11-12 确认）。
- `build.py` 的就地构建保留，「逐章自己写」的单文件流程不变。
- 迁移 shelf 的六份 `assemble.py` 不在本计划内。

### 复核时自行定下的（维护者可改）

- 段落数只在原文能机械数出时列进结构清单（HTML 的 `<p>`、Markdown 的空行分段）。LaTeX 和 PDF 原文数不准，不要求列。在 shelf 的 financial-math 上试算，按 Step 3 的口径得到两章 53 和 38 段，片段里 `<p>` 开标签总数是 55 和 39，差的是列表和引文里的段落，口径可用。原文一侧能不能数准没有验证。
- 按章统计做成 `--by-chapter` 参数，不默认打印：十几章的书每次构建多十几行，多数时候用不上。
- 画图脚本支持两种写法并存：全书一份 `figs.py`（shelf 的写法），以及每章一份 `chNN.figs.py`（分章派发时各子 agent 各写各的文件，互不覆盖）。

## Current state

（`81a8f3e` 的状态。）

- `skills/tufte-reader/scripts/build.py:287-288`，脚注并入已有的章末列表：

  ```python
  if '<section class="footnotes">' in body:
      body = re.sub(r'(<section class="footnotes">.*?)(</ol>)', lambda mm: mm.group(1) + block + "\n" + mm.group(2), body, count=1, flags=re.S)
  ```

  非贪婪匹配停在第一个 `</ol>`，脚注里有嵌套列表时那是嵌套列表的闭合标签。

- `build.py:181-191`，`element_end(html, start, tag)` 做平衡扫描，找不到闭合时 `raise ValueError(f"<{tag}> 没有闭合")`。`chapters()`、`place_footnotes()`、`build_toc()`、`expand_steps()`、`step_frame()` 都调用它，`main()` 不捕获。
- `build.py:735-747`，`main()` 把所有以 `--` 开头的参数收进 `flags`，只查 `--check-only` 和 `--open`，别的不报错。没有 `-h` / `--help`。
- `build.py:565`，`Checker.stats` 是一个全书的字典，键依次是：章、小节(h3)、图、页边图、题图、表、代码块、边注、旁注、脚注、块级公式、行内公式、图内公式、分步图、帧。`main()` 把它打印成一行「统计」。
- `skills/tufte-reader/references/dispatch.md`：片段存 `<页面名>.work/chapters/NN-<章 id>.html`，画图代码存 `chapters/NN-<章 id>.figs.py`，原文切到 `source/NN-<章 id>.*`。子 agent 试构建要手工把页面复制成 `<页面名>.NN.check.html`、替换示例章、调 `embed`。「拼接」一节四步都由主 agent 手工做。
- `skills/tufte-reader/SKILL.md:72-78`，「修改本技能」一节三段。
- 测试：`python3 -m unittest discover -s skills/tufte-reader/tests` 输出 `Ran 68 tests`、`OK`，约 17 秒，其中 `test_figprobe.py` 占 15 秒。`make check` 输出 `技能文档引用检查通过（234 个文件）`。
- specimen 构建的统计行：`统计    章 3  小节(h3) 4  图 9  页边图 0  题图 1  表 1  代码块 1  边注 2  旁注 12  脚注 2  块级公式 3  行内公式 86  图内公式 6  分步图 1  帧 3`。
- shelf 的六份 `src/assemble.py` 调用已安装的 `~/.claude/skills/tufte-reader/scripts/build.py`，把自己的命令行参数原样传过去，实际只用 `--open`。shelf 里没有任何脚本解析「统计」行（已用 grep 核对）。

**附件**（`plans/033-tufte-reader-build-fixes-and-assemble/`）：

| 文件             | 用途                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `footnote.patch` | Step 1 的补丁：`build.py` 改 4 行，`tests/test_build.py` 加 1 个测试。先加测试时它失败（新脚注落在嵌套列表里），套上修复后通过。在副本上全量 `Ran 69 tests`、`OK`，specimen 成品与修复前逐字节相同                                                                                                                                                                                                        |
| `assemble.py`    | Step 4 的成品，复制到 `skills/tufte-reader/scripts/assemble.py`。在 shelf 六本书的副本上，它的成品与各书自己的 `src/assemble.py` 的成品逐字节相同（走的是全书一份 `figs.py`）。每章一份 `chNN.figs.py` 的路径另用两章、各一幅带箭头的图试过：整本拼接和 `--only ch02` 都是 0 个 ERROR，两幅图的箭头 `id` 分别是 `f1-arr`、`f2-arr`。没有试过的：没有 `refs.html` 的书、缺图时的报错，由 Step 4 的测试覆盖 |

## Commands you will need

| Purpose  | Command                                                                                                                         | Expected on success                  |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| 技能测试 | `python3 -m unittest discover -s skills/tufte-reader/tests`                                                                     | 末行 `OK`，`Ran N tests` 的 N 见各步 |
| 快速测试 | `python3 -m unittest discover -s skills/tufte-reader/tests -p 'test_build.py'`                                                  | 末行 `OK`，约 3 秒                   |
| 文档门禁 | `make check`                                                                                                                    | `技能文档引用检查通过`，exit 0       |
| 格式     | `npx prettier --check skills/tufte-reader/SKILL.md skills/tufte-reader/references/*.md`                                         | 通过                                 |
| 回归样张 | `T=$(mktemp -d); cp skills/tufte-reader/assets/specimen.html $T/s.html; python3 skills/tufte-reader/scripts/build.py $T/s.html` | 末行 `通过：0 个 ERROR，0 个 WARN`   |

构建需要 node。fish 里 `T=$(mktemp -d)` 写成 `set T (mktemp -d)`。

## Scope

**In scope**：

- `skills/tufte-reader/scripts/build.py`、新增 `scripts/assemble.py`
- `skills/tufte-reader/tests/test_build.py`、新增 `tests/test_assemble.py`
- `skills/tufte-reader/SKILL.md`、`references/dispatch.md`、`references/markup.md`（只改「图元库」的示例说明一处）、`references/plates.md`（只改「写法」最后一条）、新增 `references/maintaining.md`
- `AGENTS.md`（「命令」一节的测试那一行）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**：

- `math.mjs`、`mermaid.mjs`、`figlib.py`、`plate.py`、`find_plate.py`、`tufte.css`、`shell.html`、`shell.js`、`specimen.html`。
- `build.py` 里为重复构建服务的其他判断（已展开的边注、已内联的样式、已展开的分步图）：本计划只修脚注那一处。
- 把单文件流程也改成「片段为源」、删掉就地重建的代码：见 `plans/README.md` 本计划一节的 deferred。
- shelf 仓库的任何文件。
- `make install`、提交、推送：由维护者决定。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `tufte-reader`。每步一个提交，示例见各步。
- 未经操作者指示不要提交、不要推送。pre-commit 会跑 prettier 和 `make check`。

## Steps

### Step 1：修脚注重建（P1）

```sh
git apply plans/033-tufte-reader-build-fixes-and-assemble/footnote.patch
```

补丁把并入已有列表的那两行换成：找到 `section.footnotes` 里第一个 `<ol`，用 `element_end` 取它自己的闭合位置，把新条目插在那个 `</ol>` 之前。

**Verify**：

- `python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 69 tests`，`OK`。
- 回归样张构建通过；再构建一次，输出仍是 `新归位脚注 0 条` 且通过。
- 反向确认测试有效：`git stash push skills/tufte-reader/scripts/build.py` 后只跑快速测试，`test_footnote_added_after_one_holding_a_list` 失败；`git stash pop` 后通过。

提交示例：`fix(tufte-reader): append rebuilt footnotes after a footnote that holds a list`

### Step 2：标签没闭合报 ERROR，不认识的参数拒绝执行（P2）

改 `build.py` 的 `main()`：

- 认识的参数只有 `--open`、`--check-only`、`-h`、`--help`（Step 3 再加 `--by-chapter`）。出现别的以 `-` 开头的参数时，打印 `ERROR 不认识的参数：<参数>` 并返回 2，**在读写页面之前**返回。
- `-h` / `--help` 打印 `__doc__`，返回 0，不要求给页面路径。
- 合成阶段（`glue_math_punctuation` 到 `inline_assets` 那一段）抛出 `ValueError` 时，不写页面，把它记成一条 ERROR：`<原消息>，构建中止：补上闭合标签后重跑`，然后照常打印 ERROR 行和「失败：…」那一行，返回 1。未闭合的标签是作者会写出来的输入，在入口处报出来就是正确的处理，不需要在各个调用点分别防。
- 文件头的说明第一行改成 `build.py 页面.html [--open] [--check-only] [--by-chapter]`（`--by-chapter` 在 Step 3 才生效，两步分开提交时这一处放到 Step 3 改）。

在 `tests/test_build.py` 加三个测试（`run()` 目前不接受额外参数，按需要给它加一个 `args=()` 形参）：

- 去掉 `PAGE` 里第一章的 `</article>`：返回码 1，输出含 `没有闭合`，不含 `Traceback`。
- 传 `--chek-only`：返回码 2，输出含 `不认识的参数`，页面文件内容与运行前逐字节相同。
- 传 `--help`、不给页面：返回码 0，输出含 `build.py 页面.html`。

**Verify**：

- 全量测试 → `Ran 72 tests`，`OK`。
- 回归样张构建通过，成品与 Step 1 之后的成品逐字节相同（两次各建一份，`cmp`）。

提交示例：`fix(tufte-reader): report unclosed tags as ERROR and reject unknown build flags`

### Step 3：统计加段落数，`--by-chapter` 按章列出（P2）

改 `build.py` 的 `Checker`、`check()` 和 `main()`：

- 新增统计项「段落」，排在「章」之后。口径：`<article class="chapter">` 里没有 `class` 的 `<p>`，并且它到所在章之间的祖先里没有 `li`、`blockquote`、`figure`、`td`、`th`、`details`，也不在 `section.footnotes` 里。扉页、参考文献里的 `<p>` 不计。
- `Checker` 在全书合计之外，再按章 `id` 各记一份同样的计数（章内出现的元素记到所在章；章外的只进合计）。
- `--by-chapter`：在「统计」行之后，每章打印一行，行首两个空格加章 `id`，后面是除「章」以外的各项，格式与「统计」行相同。不带这个参数时输出只比现在多「段落」一项。

在 `tests/test_build.py` 加三个测试：

- 一章里有两个普通段落、一个 `<li><p>…</p></li>`、一个 `<blockquote><p>…</p></blockquote>`、一条含 `<p>` 的章末脚注：统计行含 `段落 2`（加上 `PAGE` 第二章固定的一段，全书是 `段落 3`，按实际夹具写断言）。
- `--by-chapter`：输出里有以 `  one` 和 `  two` 开头的两行，`one` 那行的「边注」数与只放在第一章的边注数相同。
- 不带 `--by-chapter` 时输出里没有以两个空格加章 `id` 开头的行。

改文档（改完跑 `npx prettier --write`）：

- `SKILL.md` 第 1 步「完成标准」那一段：在「逐章列出各级标题、图、表、块级公式、脚注各有多少条」后面加一句，原文的段落能机械数出时（HTML 的 `<p>`、Markdown 以空行分段）每章再列段落数，LaTeX 和 PDF 原文不列。
- `SKILL.md` 第 4 步：在「把构建输出的『统计』行和结构清单对照」之后加一句，对不上时加 `--by-chapter` 重跑，逐章找出差在哪里；在举例里加一条，「段落」不计列表、引文、图、表和章末脚注里的段落。
- `build.py` 文件头说明的第一行加上 `[--by-chapter]`。

**Verify**：

- 全量测试 → `Ran 75 tests`，`OK`。断言旧统计行整行文字的现有测试如果失败，把断言改成新的文字，并在汇报里列出改了哪几个。
- 回归样张：统计行以 `统计    章 3  段落 ` 开头，其余各项的数字与「Current state」里记的那一行相同；加 `--by-chapter` 时多出 3 行，三行里的「图」依次是 1、0、8，相加等于 9（计划时按章数过）。
- `make check` 通过；prettier 检查通过。

提交示例：`feat(tufte-reader): count paragraphs and print per-chapter stats with --by-chapter`

### Step 4：新增拼接脚本，分章派发改用片段布局（P2）

```sh
cp plans/033-tufte-reader-build-fixes-and-assemble/assemble.py skills/tufte-reader/scripts/assemble.py
```

脚本的用法是 `assemble.py 源目录 -o 页面.html [--only 片段名] [build.py 的参数]`，布局写在它的文件头里。它在一个进程里依次执行 `figs.py` 和各章的 `chNN.figs.py`，填回 `<!--FIG:名字-->`，写出页面，再调同目录的 `build.py`，退出码是 `build.py` 的。`--only ch03` 只拼这一章，写到页面旁边的 `<页面名>.ch03.check.html`。

新增 `tests/test_assemble.py`（用临时目录搭源目录，`head.html` 取 `shell.html` 到 `</header>` 并把 `<title>` 换掉，`tail.html` 取 `<!--TR:JS-->` 到末尾），五个测试：

- `head` + `ch01` + `ch02` + `tail`，加一份往 `FIGS` 里放一幅图的 `figs.py`：返回码 0，页面里两章按序出现，没有 `<!--FIG:` 残留。
- 有 `apx.html` 和 `refs.html` 时：附录排在 `ch02` 之后，参考文献排在附录之后、`<script data-tr="js">` 之前。
- 片段里有 `<!--FIG:nope-->` 而没有这幅图：返回码 1，输出含 `缺图：nope`，页面文件没有被创建。
- `--only ch02`：生成 `<页面名>.ch02.check.html`，其中只有第二章；原页面文件不存在或内容不变。
- `ch01.figs.py` 和 `ch02.figs.py` 各用 `figlib` 画一幅带箭头的图（`line(…, arrow=True)`）：页面构建通过，没有「重复的 id」这条 ERROR。

改写 `references/dispatch.md`，章节标题不变（「写好外壳」「切原文」「派发」「拼接」），内容换成：

- **写好外壳**：在工作区建 `<页面名>.work/src/`。把 `assets/shell.html` 从开头到 `</header>` 存成 `head.html` 并写好扉页（含 `<title>`），从 `<!--TR:JS-->` 到末尾存成 `tail.html`，参考文献写成 `refs.html`（没有就不建）。示例章不保留。
- **切原文**：存成工作区的 `source/chNN.*`，`NN` 是两位序号。
- **派发**：片段存 `src/chNN.html`，画图代码存 `src/chNN.figs.py`，只往 `FIGS` 里加条目，键名以章 `id` 开头。试构建改成一条命令：`python3 <skill-path>/scripts/assemble.py <src 的绝对路径> -o <页面的绝对路径> --only chNN`，核对完删掉 `<页面名>.chNN.check.html`。写明一条限制：试构建里只有这一章，指向其他章的页内链接会报「页内链接指向不存在的 id」，这一条不用修，在返回里列出来。交代里要给的路径、清单行、返回内容照旧。
- **拼接**：收术语的做法照旧。全部返回后运行 `python3 <skill-path>/scripts/assemble.py <src> -o 页面.html`，它完成原来的第 1、2 两步。通读各章之间的指代、放章首题图这两步保留，改的是 `src/` 里的片段。加一句：页面每次从片段重新生成，之后的修改都改片段再运行这条命令，不改页面。

同步六处：

- `SKILL.md` 第 3 步第一段（现在是「把 `assets/shell.html` 复制到输出路径……先写扉页和参考文献，再写各章」）：改成先定写法再动笔。逐章自己写时照原样复制到输出路径；分章派发时不在输出路径建页面，扉页、参考文献按 [分章派发](references/dispatch.md) 的「写好外壳」写进工作区的 `src/`，页面由 `assemble.py` 生成。
- `SKILL.md` 第 3 步题图那一段里的「分章派发时在拼接之后」：改成「分章派发时等各章片段返回后，放进 `src/` 里对应的片段，扉页题图放进 `head.html`」。
- `references/plates.md`「写法」最后一条（「分章派发时，子 agent 不放题图；主 agent 拼接完各章后统一放」）：改成「分章派发时，子 agent 不放题图；各章片段返回后由主 agent 统一放进 `src/` 里的片段，再运行 `assemble.py`。放进页面的题图下次拼接就没了」。
- `SKILL.md` 第 3 步「分章派发」那一条：片段放工作区的 `src/`，用 `assemble.py` 拼接。第 1 步「续写或修订已有读本时沿用原文件名」后面加一句：工作区里有 `src/` 的读本，改片段后运行 `assemble.py`。
- `SKILL.md` 第 4 步的命令块下加一行：分章派发的读本用 `assemble.py <src> -o 页面.html`，它拼接后会自己调用 `build.py`。
- `references/markup.md`「图元库」里 `page = embed(源码, FIGS)` 那个示例之后加一句：片段放在工作区 `src/` 时由 `assemble.py` 执行画图脚本并填回占位符，不用自己调 `embed`。

**Verify**：

- 全量测试 → `Ran 80 tests`，`OK`。
- `grep -nE 'chapters/|示例章|NN-<章 id>|拼接之后|拼接完各章后' skills/tufte-reader/SKILL.md skills/tufte-reader/references/*.md` → 无输出（旧布局的说法都已换掉）。
- `make check` 通过；prettier 检查通过。
- shelf 对照（本机有 `~/github/shelf` 时运行；没有就写「未运行」，不要标 DONE）。只在副本上做，不动 shelf 仓库：

  ```sh
  W=$(mktemp -d)
  for b in aesthetics-and-beauty financial-math how-llms-work how-rendering-works how-to-learn-mathematics kythera-zzz-shader; do
    rsync -a --exclude .work ~/github/shelf/books/$b $W/
    (cd $W/$b && python3 src/assemble.py >/dev/null)
    python3 skills/tufte-reader/scripts/assemble.py $W/$b/src -o $W/$b/mine.html >/dev/null
    cmp $W/$b/$b.html $W/$b/mine.html && echo "$b 相同"
  done
  ```

  预期六行「相同」。shelf 的脚本调用的是已安装的副本；仓库里的 `build.py` 经过 Step 2、3 之后成品仍应相同，因为这两步只改报错和统计输出。有一本不同就是 STOP 条件。

提交示例：`feat(tufte-reader): add assemble.py and move chapter dispatch to the fragment layout`

### Step 5：把「修改本技能」移出 SKILL.md，AGENTS.md 写明测试命令（P3）

- 新建 `skills/tufte-reader/references/maintaining.md`，标题 `# 维护`，把 `SKILL.md`「修改本技能」一节的三段原样搬过去，只把其中的「下一段」这类位置指代改成读得通的说法。
- `SKILL.md` 里那一节整节删掉，在文件末尾留一行：改这个技能的样式或脚本之前，先读 `[维护](references/maintaining.md)`。
- 仓库根 `AGENTS.md`「命令」一节「测试」那一行末尾加：tufte-reader 的测试在 `tests/` 目录，用 `python3 -m unittest discover -s skills/tufte-reader/tests`。

**Verify**：

- `grep -c "修改本技能" skills/tufte-reader/SKILL.md` → `0`；`grep -c "figprobe.py" skills/tufte-reader/references/maintaining.md` → `1`。
- `wc -l skills/tufte-reader/SKILL.md` 比这一步之前少 6 行左右。
- `make check` 通过；prettier 检查通过。

提交示例：`docs(tufte-reader): move maintenance notes out of SKILL.md`

## Test plan

- 每步的 Verify 就是该步的验收。全部做完后再跑一次全量测试（`Ran 80 tests`）、`make check`、回归样张构建。
- 回归样张的成品在 Step 1、2、3 前后应逐字节相同（Step 3 只改终端输出）。
- 浏览器里的样子本计划不改，不需要截图对比。

## Done criteria

- 五步各自的 Verify 全部通过，或明确写出哪一步没做、为什么。
- `python3 -m unittest discover -s skills/tufte-reader/tests` 末行 `OK`。
- `make check` 通过。
- shelf 对照六本全部相同，或写明「未运行」及原因。
- `plans/README.md` 里本计划的状态行已更新。

## STOP conditions

- Drift check 有输出，且「Current state」的摘录与现行代码对不上。
- `git apply` 报错：不要手工改，停下汇报。
- Step 2、3 之后回归样张的成品与之前不逐字节相同。
- Step 3 需要改的现有测试超过 3 个，或要改断言之外的测试逻辑。
- Step 4 的 shelf 对照有一本不同。
- 需要改 Scope 之外的文件才能通过验证。

## Maintenance notes

- 改完不会自动生效：`~/.claude/skills/tufte-reader` 是副本，要 `make install SKILL=tufte-reader SOURCE=.`，由维护者执行。shelf 的 `assemble.py` 调用的也是那份副本。
- Step 2 之后 `build.py` 拒绝不认识的参数。shelf 的脚本把自己的参数原样传给它，目前只用 `--open`；以后给 shelf 的脚本加参数时要记得这一点。
- shelf 六本书要不要改成调用技能的 `assemble.py`，由维护者另行决定。改的话每本的 `src/assemble.py` 可以缩成一行调用，`figs.py` 不用动。
- shelf 六本书已入库的成品与现在重建的成品不相同（计划时在副本上比对过），原因没有查，推测是成品生成之后技能又改过。这与本计划无关，只是做 shelf 对照时不要拿已入库的成品当基准。
- 试构建时跨章链接报 ERROR 这条限制，分章派发原来的做法里就有，本计划没有消除它。
