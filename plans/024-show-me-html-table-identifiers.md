# Plan 024: show-me-html 表格里的长标识符不再被压成竖条（表格内 `code` 不在词中断开，文档教作者插 `<wbr>`）

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。索引 `plans/README.md` 由审阅者维护，你不要改它。
>
> **Drift check (run first)**: `git diff --stat 90fb8af..HEAD -- skills/show-me-html/assets/show-me.css skills/show-me-html/references/components.md`
> 计划 027（打印样式）先合入时 `show-me.css` 会出现在输出里，属于预期；只要下面「Current state」里引用的 CSS 和文档句子原样还在就继续。
>
> 本文件里的 css / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P2
- **Effort**: S（一条 CSS 规则、一段文档）
- **Risk**: LOW（只影响表格单元格里的行内 `code`）
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `2f0e439`, 2026-10-22；2026-10-23 维护者看过样张选定方案后，advisor 在 `90fb8af` 上改写

## Why this matters

show-me-html 的 `show-me.css` 给所有行内代码写了 `overflow-wrap: anywhere`。这条规则让 `code` 可以在任意字符处断行，所以它的最小内容宽度只有一个字符。表格是自动布局，列宽按最小内容宽度分配，于是多列表格里放 snake_case 键名或文件路径时，这一列会被挤到一两个字宽，标识符被压成竖条。2026-10-22 维护者的一页 status-report 报告做完后改了 7 轮，其中 4 轮在修这个。

2026-10-23 advisor 做了五页样张（同一张五列表格：键名、模块路径、英文原文、缺失语言、引用数），在 390px 手机视口下量了表格（容器宽 388px）：

| 样张                                      | 表格宽 | 键名列 / 模块列 | 效果                                       |
| ----------------------------------------- | ------ | --------------- | ------------------------------------------ |
| 现状                                      | 388    | 67 / 70         | 每行 4–5 个字符的竖条                      |
| 只在标识符的 `_`、`/` 后插 `<wbr>`        | 388    | 67 / 70         | 和现状一样：`anywhere` 仍允许在词中断开    |
| 表格里的 `code` 改成 `break-word`         | 994    | 361 / 408       | 标识符完整，整表横向滚动                   |
| `break-word` 加 `<wbr>`（**维护者选的**） | 444    | 98 / 120        | 在 `_`、`/` 处断开，只有最后一列需要拖一点 |

`<wbr>` 单独用没有效果：它只是多给一个断点，`anywhere` 本来就允许处处断。表格里的 `code` 改成 `break-word` 之后，`code` 的最小宽度变成「两个断点之间最长的那一段」，`<wbr>` 才起作用。作者忘了插 `<wbr>` 时，标识符不拆开，整表由 `.table-container` 横向滚动，仍然比竖条好认。

计划 012（2026-10-15）否决过「全局调整表格密度」，理由是四个冻结场景在 390px 下都不横滚。本计划只改表格里的 `code`，不含 `code` 的表格不受影响；冻结场景里唯一的表格（approach-compare）没有 `code`。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `90fb8af`，对不上时以引文为准。

- `assets/show-me.css:1729-1732`（规则本身，前面是 `.grid > *, main > * { min-width: 0; }`，后面是「页眉工具条」的注释）：

  ```css
  code,
  .kbd {
    overflow-wrap: anywhere;
  }
  ```

- `assets/show-me.css:499-505`（宽表的横向滚动容器）：

  ```css
  .table-container {
    width: 100%;
    overflow-x: auto;
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    background: var(--color-card);
  }
  ```

- `references/components.md:157-180`「表格」一节：一个三列表格示例，最后一句（`:180`）是 `` `.table-container` 提供横向滚动，宽表必须套。数字按位对齐是骨架给的（`.table` 已开 `tabular-nums`），不用自己加。``，下一节是「列表项（item）」。

- 运行器 `scripts/render.mjs`：`node scripts/render.mjs <jobs.json>`，jobs 里每个任务可带 `url`、`width`、`theme`、`eval`，stdout 是与任务一一对应的 JSON 数组，`eval` 的结果在 `value`。Chrome 路径用 `scripts/build.py` 里的 `find_chrome()` 取。Step 1 的脚本用它量表格。

- 测试夹具 `tests/fixtures/minimal-shell.html`：最小的合法页面，`</main>` 前可以追加 `<section>`。

## Commands you will need

| Purpose  | Command                                                    | Expected on success |
| -------- | ---------------------------------------------------------- | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build` | 末行 `OK`           |
| 文档门禁 | `make check`                                               | exit 0              |

## Scope

**In scope**：`skills/show-me-html/assets/show-me.css`（加一条规则）、`skills/show-me-html/references/components.md`（「表格」一节加一段）。样张放在临时目录，不进仓库。

**Out of scope**：

- 全局 `code, .kbd` 规则：正文段落里的长路径仍然需要能在任意处断行，否则窄屏整页溢出。只改表格里的。
- 表头、badge、正文格的折行规则：012 定过，不动。
- 构建时自动往标识符里插 `<wbr>`、加构建检查（量单元格里 `code` 的渲染宽度）：维护者没有选。
- 别的组件（列表项、卡片、来源行）里的 `code`。
- `plans/README.md`：审阅者维护。

## Git workflow

从本地 `main` 开分支 `advisor/024-show-me-html-table-identifiers`。提交一次，信息为 `fix(show-me-html): table identifiers break only at wbr and the table scrolls when they do not fit`。不要 push。

## Steps

### Step 1: 做样张并量改前的列宽

用 bash 跑，在仓库根目录：

```sh
S=$(mktemp -d); echo "$S"
cat > "$S/gen.py" <<'EOF'
import json, pathlib, re, subprocess, sys
sys.path.insert(0, "skills/show-me-html/scripts")
import build
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
for name, t in {"plain": table, "wbr": wbr}.items():
    (S / f"{name}.html").write_text(base.replace("</main>", t + "</main>"), encoding="utf-8")
ev = ("(()=>{const c=document.querySelector('.table-container'),t=c.querySelector('table');"
      "const w=[...t.rows[0].cells].map(x=>Math.round(x.getBoundingClientRect().width));"
      "return {container:c.clientWidth,table:Math.round(t.scrollWidth),key:w[0],module:w[1]}})()")
(S / "measure.json").write_text(json.dumps({"chrome": build.find_chrome(), "jobs": [
    {"url": (S / f"{n}.html").as_uri(), "width": 390, "theme": "light", "eval": ev} for n in ("plain", "wbr")]}))
print("ok")
EOF
python3 "$S/gen.py" "$S"
for n in plain wbr; do python3 skills/show-me-html/scripts/build.py "$S/$n.html" --snap "$S/before-$n" --snap-theme light --snap-width 390,1280 | grep -E '自检|ERROR'; done
node skills/show-me-html/scripts/render.mjs "$S/measure.json" | tee "$S/before.json"
```

**Verify**:

- 打印 `ok`，两次构建都打印 `自检通过。`。
- 最后一行是两项的 JSON 数组，`value` 大致是：`plain` 为 `{"container":388,"table":388,"key":67,"module":70}`，`wbr` 与 `plain` 相同（几像素以内的差别不算）。
- 看一眼 `$S/before-plain/light-390-01.png`：键名和路径每行只剩四五个字符。

### Step 2: 表格里的 `code` 不在词中断开

`skills/show-me-html/assets/show-me.css`：在 `code, .kbd { overflow-wrap: anywhere; }` 这条规则**之后**、「页眉工具条」注释之前，加：

<!-- prettier-ignore -->
```css
/* 表格里的标识符不在词中断开：anywhere 让 code 的最小宽度只剩一个字符，多列表格里 snake_case 键名和路径会被压成竖条。
   break-word 不降低最小宽度，列宽由 <wbr> 之间最长的一段决定（作者在 _ 和 / 后插 <wbr>，见 components.md「表格」）；
   没插 <wbr> 时整个标识符不拆开，放不下由 .table-container 横向滚动 */
.table code {
  overflow-wrap: break-word;
}
```

**Verify**: `grep -c '^\.table code {' skills/show-me-html/assets/show-me.css` → `1`。

### Step 3: 文档

`skills/show-me-html/references/components.md`「表格」一节最后那句（`` `.table-container` 提供横向滚动，宽表必须套。…不用自己加。``）之后空一行，另起一段：

<!-- prettier-ignore -->
```markdown
单元格里的行内 `code`（键名、路径、函数名）不会在词中间断开。多列表格放 snake_case 键名或文件路径时，在每个 `_` 和 `/` 后插 `<wbr>`，例如 `<code>audio_<wbr>room_<wbr>enter_<wbr>hint</code>`：窄屏在这些位置断行，列宽只需容下最长的一段。没插 `<wbr>` 的标识符整个不拆开，表格放不下就横向滚动。
```

然后 `npx prettier --write skills/show-me-html/assets/show-me.css skills/show-me-html/references/components.md`。

**Verify**: `git diff --stat` 只列出这两个文件；`grep -c '<wbr>' skills/show-me-html/references/components.md` 比改前多 1（改前用 `git show HEAD:skills/show-me-html/references/components.md | grep -c '<wbr>'` 看）。

### Step 4: 用样张确认改后的列宽

用 Step 1 的同一个 `$S`（新开了 shell 就把 Step 1 打印的路径赋回 `S`，不要再 `mktemp`，`before-*` 和 `before.json` 都在这个目录里）。样张页在 Step 1 已经被构建内联过旧 CSS，所以先用 `gen.py` 重新生成两页（它覆盖 `plain.html`、`wbr.html` 和 `measure.json`），再构建、量：

```sh
python3 "$S/gen.py" "$S"
for n in plain wbr; do python3 skills/show-me-html/scripts/build.py "$S/$n.html" --snap "$S/after-$n" --snap-theme light --snap-width 390,1280 | grep -E '自检|ERROR'; done
node skills/show-me-html/scripts/render.mjs "$S/measure.json" | tee "$S/after.json"
```

**Verify**:

- 两次构建都打印 `自检通过。`。
- `plain`：`table` 在 900 以上，`key` 在 300 以上（标识符不拆开，整表横向滚动）。
- `wbr`：`table` 在 480 以下，`key` 在 85–115，`module` 在 105–135（advisor 量到 444 / 98 / 120）。
- 看 `$S/after-wbr/light-390-01.png`：键名在 `_` 后断行（`audio_` / `room_` / `enter_` …），路径在 `/` 后断行，没有词中断开的地方；`$S/after-plain/light-1280-01.png` 与 `$S/before-plain/light-1280-01.png` 比，1280 下表格仍然不横滚。

### Step 5: 测试与门禁

```sh
python3 -m unittest skills.show-me-html.tests.test_build 2>&1 | tail -3
make check
```

**Verify**: 末行 `OK`，测试数与改前相同（本计划不加测试）；`make check` exit 0。

### Step 6: 冻结场景轮次

本计划改了 `show-me.css`，按 `MAINTENANCE.md` 要跑一轮。页面生成指引没变，复制上一轮的五页重建。上一轮在主检出里（`rounds/` 被 gitignore，worktree 里没有），用 bash 跑：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-b52953a-022
RND=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-024
mkdir -p "$RND"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$RND/" && python3 skills/show-me-html/scripts/build.py "$RND/$n.html" | grep -E '^(ERROR|WARN)|自检通过'
done
node skills/show-me-html/scripts/probe_round.mjs "$RND" "$PREV" | grep -E '^[a-z-]+: |probe\.json|截图：|Markdown 不同'
```

**Verify**:

- 五次构建都打印 `自检通过。`；五行 `<场景名>: 无问题`；`与上一轮对比：probe.json 相同`。
- 五个场景页的表格里都没有 `code`，截图应为 `30/30 张逐字节相同`。有不同就逐张打开看：只差几个像素的抗锯齿噪声（022 那轮 `concept-explainer-light-500` 就差 1 个像素），在汇报里列出文件名；版式有变化的，按 STOP 处理。
- `scenarios/rounds/` 在 `.gitignore` 里，轮次目录不进提交。

## Test plan

本计划不加单元测试：效果是视觉上的，靠 Step 1 和 Step 4 的样张列宽对照确认，冻结场景轮次兜底其他页面不受影响。

## Done criteria

- [ ] Step 4 的列宽落在预期范围内，`after.json` 和截图路径写进汇报
- [ ] 全量单元测试 `OK`，`make check` exit 0
- [ ] 冻结场景轮次 `probe.json` 相同，截图相同或只有抗锯齿噪声
- [ ] 分支上只有一个提交，只改了 `show-me.css` 和 `components.md`；样张和轮次目录没有进仓库

## STOP conditions

- Step 1 的 `plain` 量到的 `key` 在 150 以上：说明 `show-me.css` 已被别的改动修过，汇报 `before.json`，不要继续。
- Step 4 的 `wbr` 仍然在词中断开，或 `plain` 的 `key` 没有变宽：规则没生效（选择器被更具体的规则压过，或加错了位置），汇报 `after.json` 和截图。
- 冻结场景轮次里出现版式变化。
- 你发现需要改全局 `code, .kbd` 规则、表头或 badge 的规则才能达到预期。

## Maintenance notes

- 计划 012 记录的「四个场景在 390px 都不横滚」只对不含长标识符的表格成立；以后有人再提「表格太宽、要横拖」，先看是不是表格里的 `code` 没插 `<wbr>`。
- 正文里的 `code` 仍是 `anywhere`。如果以后要在段落里也保住标识符，要另外评估整页溢出风险，不能直接把全局规则改掉。
- 作者常忘插 `<wbr>` 的话，可以考虑让 `build.py` 在内联时自动给表格里的 `code` 插（`textContent` 不变，「复制为 Markdown」不受影响）；这次维护者没有选。
