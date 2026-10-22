# Plan 024: show-me-html 表格里的长标识符不再被压成竖条（先出样张，维护者选定后实现）

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。本计划在 Step 2 之后**必须停下**，把样张交给维护者选择；`plans/README.md` 里记下选择之后，才执行 Step 3 的对应分支。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 2f0e439..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/references/components.md`
> 计划 018（改 token 与骨架样式）、027（打印样式）先合入时 `show-me.css` 会出现在输出里，属于预期；只要下面「Current state」里引用的两段 CSS 原样还在就继续。
>
> 本文件里的 css / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P2
- **Effort**: S（样张三页；实现是一条 CSS 规则或一段文档）
- **Risk**: LOW（只影响表格单元格里的行内 `code`）
- **Depends on**: none。计划 021 合入后可以直接拍 390px 的样张；没合入时用 500px，见 Step 2。
- **Category**: bug
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 的 `show-me.css` 给所有行内代码写了 `overflow-wrap: anywhere`。这条规则让 `code` 可以在任意字符处断行，所以它的最小内容宽度只有一个字符。表格是自动布局，列宽按最小内容宽度分配，于是多列表格里放 snake_case 键名或文件路径时，这一列会被挤到一两个字宽，标识符被压成竖条。2026-10-22 维护者的一页 status-report 报告做完后改了 7 轮，其中 4 轮在修这个：给键名和模块路径插 `<wbr>`、给标识符列设最小宽度、给长英文列设最大宽度。

advisor 用下面 Step 1 的样张表格在 scratchpad 里复现了：390px 下基线版的键名和路径每行只剩两三个字符；只给表格里的 `code` 改用 `overflow-wrap: break-word` 后，每个标识符占一行，整张表比容器宽，由 `.table-container` 横向滚动。

计划 012（2026-10-15）否决过「全局调整表格密度」，理由是四个冻结场景在 390px 下都不横滚，改了只换来观感变化。这里是更窄的一种情形：多列表格加长标识符。改 CSS 会让这类表格在手机上改为横向滚动，等于在这一情形下改变 012 的取舍，所以由维护者看过样张再定。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `2f0e439`，对不上时以引文为准。

- `assets/show-me.css:1318-1321`（规则本身）：

  ```css
  code,
  .kbd {
    overflow-wrap: anywhere;
  }
  ```

- `assets/show-me.css:493-499`（宽表的横向滚动容器）：

  ```css
  .table-container {
    width: 100%;
    overflow-x: auto;
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    background: var(--color-card);
  }
  ```

  `.table th` 已有 `word-break: keep-all`，表格里的 `.badge` 有 `white-space: nowrap`（`:512-524`），注释写着「放不下时整表横向滚动，正文格照常折行」。

- `references/components.md:157-180`「表格」一节：一个三列表格示例，之后一句 `` `.table-container` 提供横向滚动，宽表必须套。数字按位对齐是骨架给的（`.table` 已开 `tabular-nums`），不用自己加。``

- 构建与快照：`python3 scripts/build.py 页面.html --snap 目录` 自检通过后截图并打印每张 PNG 的路径。计划 021 合入后有 `--snap-theme`、`--snap-width` 两个参数；没合入时固定拍 light/dark × 500/1280。用 `python3 scripts/build.py --help | grep -c snap-width` 判断（`1` 表示已合入）。

- 测试夹具 `tests/fixtures/minimal-shell.html`：最小的合法页面，`</main>` 前可以追加 `<section>`。

## Commands you will need

| Purpose  | Command                                                    | Expected on success |
| -------- | ---------------------------------------------------------- | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build` | 末行 `OK`           |
| 文档门禁 | `make check`                                               | exit 0              |

## Scope

**In scope**：`skills/show-me-html/assets/show-me.css`（仅分支 B）、`skills/show-me-html/references/components.md`、`plans/README.md`。样张放在临时目录，不进仓库。

**Out of scope**：

- 全局 `code, .kbd` 规则：正文段落里的长路径仍然需要能在任意处断行，否则窄屏整页溢出。只改表格里的。
- 表头、badge、正文格的折行规则：012 定过，不动。
- 加构建检查（量单元格里 `code` 的渲染宽度）：维护者没有选这条。

## Git workflow

从本地 `main` 开分支 `advisor/024-show-me-html-table-identifiers`。样张阶段不提交。实现后的提交例如 `fix(show-me-html): table identifiers keep their width and the table scrolls`（分支 B）或 `docs(show-me-html): break long identifiers in tables with wbr`（分支 A）。不要 push。

## Steps

### Step 1: 做三页样张

```sh
S=$(mktemp -d); echo "$S"
python3 - "$S" <<'EOF'
import pathlib, re, sys
S = pathlib.Path(sys.argv[1])
base = pathlib.Path("skills/show-me-html/tests/fixtures/minimal-shell.html").read_text(encoding="utf-8")
row = lambda k, m, en, langs, n: (f"<tr><td><code>{k}</code></td><td><code>{m}</code></td>"
                                  f"<td>{en}</td><td>{langs}</td><td>{n}</td></tr>")
table = ("<section><h2>缺失最多的文案键</h2><div class=\"table-container\"><table class=\"table\">"
         "<thead><tr><th>键名</th><th>模块</th><th>英文原文</th><th>缺失语言</th><th>引用</th></tr></thead><tbody>"
         + row("audio_room_enter_failed_timeout_hint", "feature/audio-room/src/main/res/values/strings.xml",
               "The room is taking longer than usual to respond. Please check your network and try again.", "ar、tr、id、vi", 135)
         + row("wallet_recharge_first_purchase_bonus_desc", "feature/wallet/src/main/res/values/strings.xml",
               "Get a bonus on your first recharge, valid for seven days after purchase.", "ar、pt", 48)
         + row("profile_edit_nickname_length_exceeded", "feature/profile/src/main/res/values/strings.xml",
               "Nickname is too long.", "es", 12)
         + "</tbody></table></div></section>")
wbr = re.sub(r"<code>(.*?)</code>",
             lambda m: "<code>" + m.group(1).replace("_", "_<wbr>").replace("/", "/<wbr>") + "</code>", table)
variants = {
    "a-base": (table, ""),
    "b-break-word": (table, "<style>.table code { overflow-wrap: break-word; }</style>"),
    "c-wbr": (wbr, ""),
}
for name, (t, style) in variants.items():
    (S / f"{name}.html").write_text(base.replace("</main>", t + "</main>").replace("</head>", style + "</head>"),
                                    encoding="utf-8")
print("ok")
EOF
```

三页分别是：现状；分支 B（只在表格里把 `code` 改成 `break-word`，样张里用页内 `<style>` 模拟）；分支 A（不改 CSS，只在标识符的 `_` 和 `/` 后插 `<wbr>`，这是维护者那页最后的修法之一）。

**Verify**: 打印 `ok`；`ls "$S"` 列出三个 `.html`。

### Step 2: 构建并截图，然后停下交给维护者

```sh
if python3 skills/show-me-html/scripts/build.py --help | grep -q snap-width; then W="--snap-theme light --snap-width 390,1280"; else W=""; fi
for v in a-base b-break-word c-wbr; do
  python3 skills/show-me-html/scripts/build.py "$S/$v.html" --snap "$S/snap-$v" $W | grep -E '自检|ERROR'
done
ls "$S"/snap-*/
```

**Verify**: 三次都打印 `自检通过。`；每个 `snap-*` 目录里有 1280 宽和窄屏（390，或 021 未合入时的 500）的 light 截图。自己先看一遍：`a-base` 的窄屏截图里键名和路径应被压成两三个字宽的竖条（advisor 复现结果）；`b-break-word` 每个标识符一行、表格需要横向滚动；`c-wbr` 在 `_` 和 `/` 处断行。

然后**停下**，向维护者汇报：三页 HTML 的路径、每页 1280 和窄屏截图的路径，以及下面这张对照：

| 样张         | 改动                                                                | 窄屏                       | 代价                                                                           |
| ------------ | ------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------ |
| a-base       | 无                                                                  | 标识符压成竖条             | 现状                                                                           |
| b-break-word | `show-me.css` 一条规则：`.table code { overflow-wrap: break-word }` | 标识符不拆开，整表横向滚动 | 这类表格在手机上要横向拖动；012 的「四个场景都不横滚」在长标识符表格上不再成立 |
| c-wbr        | 只改文档：页面作者在标识符里插 `<wbr>`                              | 在 `_`、`/` 处断行，不横滚 | 每个页面都要记得插；忘了就回到 a                                               |

请维护者选 B、A，或都不做。把选择和日期写进 `plans/README.md` 本计划所在节的「Decisions recorded」，状态行改为 `BLOCKED（等维护者看样张）` 直到有选择。

### Step 3（维护者选 B）: 表格里的标识符不拆字

1. `assets/show-me.css`：在 `code, .kbd { overflow-wrap: anywhere; }` 这条规则**之后**加：

   <!-- prettier-ignore -->
   ```css
   /* 表格里的标识符不拆字：anywhere 让 code 的最小宽度只剩一个字符，多列表格里 snake_case 键名和路径会被压成竖条。
      break-word 只在一整行都放不下时才断，列宽至少容下最长的标识符；整表放不下时由 .table-container 横向滚动 */
   .table code {
     overflow-wrap: break-word;
   }
   ```

2. `references/components.md`「表格」一节最后那句之后另起一段：

   <!-- prettier-ignore -->
   ```markdown
   表格里的行内 `code`（键名、路径、函数名）不会被拆开：列宽至少容下最长的标识符，多列表格在窄屏上因此会横向滚动，这是有意的。标识符长到一个单元格装不下（例如很深的文件路径）时，在 `/` 后插 `<wbr>` 给浏览器断点。
   ```

3. `npx prettier --write skills/show-me-html/assets/show-me.css skills/show-me-html/references/components.md`

**Verify**: 用 Step 1 的 `a-base.html` 再构建一次并截图：窄屏截图里标识符不再是竖条（与 `b-break-word` 一致）；全量单元测试 → `OK`；`make check` → exit 0；冻结场景轮次（按 `skills/show-me-html/scenarios/README.md`，目录后缀 `-024`）五页 `自检通过`、探针五行 `无问题`，截图与上一轮对比若有差异，逐张确认只出现在含 `code` 的表格里。

### Step 3（维护者选 A）: 只写进文档

`references/components.md`「表格」一节最后那句之后另起一段：

<!-- prettier-ignore -->
```markdown
骨架让行内 `code` 能在任意字符处断行（正文里的长路径才不会撑破窄屏），代价是表格自动布局时 `code` 列会被挤到一两个字宽。多列表格放 snake_case 键名或文件路径时，在 `_` 和 `/` 后插 `<wbr>`：窄屏在这些位置断行，标识符仍然认得出来。
```

然后 `npx prettier --write skills/show-me-html/references/components.md`。

**Verify**: `make check` → exit 0；`grep -c '<wbr>' skills/show-me-html/references/components.md` 比改前多 1。

### Step 3（维护者选都不做）

`plans/README.md` 本计划状态改为 `REJECTED（<日期> 维护者看过样张选不改：<一句理由>）`，不改其他文件。

## Test plan

本计划不加单元测试：效果是视觉上的，靠 Step 2 的样张和 Step 3 的复拍确认；分支 B 另有冻结场景轮次兜底。

## Done criteria

- [ ] 样张三页与截图已交给维护者，`plans/README.md` 记下了选择
- [ ] 按所选分支完成 Step 3，对应的 Verify 全部满足
- [ ] `git status` 只显示 Scope 里的文件；样张没有进仓库
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- Step 2 结束（必停，等维护者选择）。
- `a-base` 的窄屏截图里标识符**没有**被压成竖条：说明 `show-me.css` 已被别的改动修过，汇报截图，不要继续。
- 分支 B 的冻结场景轮次里，不含 `code` 的表格或别的组件截图出现变化。

## Maintenance notes

- 选 B 之后，计划 012 记录的「四个场景在 390px 都不横滚」只对不含长标识符的表格成立；以后有人再提「表格太宽」，先看是不是这条规则在起作用。
- 正文里的 `code` 仍是 `anywhere`。如果以后要在段落里也保住标识符，要另外评估整页溢出风险，不能直接把全局规则改掉。
