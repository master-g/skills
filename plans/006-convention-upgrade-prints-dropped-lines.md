# Plan 006: 约定块自动升级时打印被丢弃的块内旧行，新章节插在约定块之前

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 90ecd48..HEAD -- skills/bootstrap-claude/scripts/setup_context.py skills/bootstrap-claude/scripts/test_setup_context.py skills/bootstrap-claude/references/bootstrap.md skills/bootstrap-claude/SKILL.md`
> 预期无输出（四个文件自计划写成后没变）。有输出就把下面「Current state」的摘录与现行代码逐段对照；对不上即为 STOP 条件。

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none（001–005 已全部合入 main）
- **Category**: bug
- **Planned at**: commit `90ecd48`, 2026-10-12

## Why this matters

`setup_context.py` 每次运行都会把「项目记忆 (回写约定)」一节和模板比对；带 `<!-- bootstrap-claude convention vN -->` 结束标记的块在模板升级后会被**整块替换**，脚本只保留标记**之后**的文字。写在块**内部**（标记之前）的项目自定义行会被静默删掉，而输出却说 `convention: upgraded (custom text after the block preserved)`，也不像 legacy 路径那样打印旧文。

2026-10-12 在 DopaManga 仓库从 v2 升到 v3 时就丢了块内三处项目自定义内容：单独一行 `@PROJECT_MEMORY.md` 导入（该项目把记忆文件导入每次会话的唯一通道），以及改写进两句模板正文里的说明和「按 PR 合并后的状态写，合并后不为补记状态另开 PR」规则。操作者是从 `git diff` 里偶然发现的。本计划让升级路径把旧块里不属于新模板的行打印出来并提示补回标记之后，文案改为准确表述；同时让新追加的必填章节插在约定块之前而不是文件末尾（003 升级后 DopaManga 的 agent 不得不手工把「导航」「工作流与陷阱」挪回正文顺序）；顺手把两处过期的「five REQUIRED_SECTIONS」改成 seven。

## Current state

相关文件：

- `skills/bootstrap-claude/scripts/setup_context.py`（442 行）—— 脚本本体。`ensure_convention` 在第 176–215 行，`ensure_sections` 在第 240–261 行，模块 docstring 第 1–25 行。
- `skills/bootstrap-claude/scripts/test_setup_context.py`（120 行）—— 脚本式 assert 测试，不是 unittest；每个用例是一个 `with tempfile.TemporaryDirectory()` 块，结尾 `print("test_setup_context: ok")`。
- `skills/bootstrap-claude/references/bootstrap.md` 第 20–25 行 —— 面向 agent 的约定块处理说明。
- `skills/bootstrap-claude/SKILL.md` 第 19 行 —— 入口处对 `convention:` 各状态的处理指引。
- `skills/bootstrap-claude/assets/CLAUDE.template.md` 第 51–64 行 —— 约定块模板，以 `<!-- bootstrap-claude convention v3 -->` 结尾。**本计划不改它**（改正文就要升 v4，让所有项目再升级一次）。

### `ensure_convention` 现状（`setup_context.py:176-215`）

```python
def ensure_convention(truth: Path, actions: list, upgrade: bool):
    """Keep the writeback block current. Marked or template-prefixed blocks upgrade
    losslessly (custom text after the block survives); a legacy block that diverged
    is replaced only with --upgrade-convention, and the old text is printed."""
    text = truth.read_text(encoding="utf-8")
    st = convention_state(text)
    tpl = template_convention()
    ...
    old_body, tpl_body = _norm_body(st["old"]), _norm_body(tpl)
    if st["marked"] or old_body.startswith(tpl_body):
        # bounded, or an old template copy with custom text appended after it
        rem = "" if st["marked"] else old_body[len(tpl_body):].strip("\n")
        custom = ("\n" + rem + "\n") if rem else ""  # one blank line, then the project's own text
        new = text[:st["start"]] + tpl.rstrip("\n") + "\n" + custom + text[st["end"]:]
        truth.write_text(new, encoding="utf-8")
        actions.append("convention: upgraded (custom text after the block preserved)")
        return
    if not upgrade:
        actions.append("convention: OUTDATED (legacy block, not marked) — read the section, then "
                       "re-run with --upgrade-convention; the old text is printed on replacement")
        return
    new = text[:st["start"]] + tpl + text[st["end"]:]
    truth.write_text(new, encoding="utf-8")
    actions.append("convention: upgraded (legacy block replaced; old text below — re-add any "
                   "custom lines AFTER the end marker)\n" + st["old"].rstrip("\n"))
```

要点：

- `st["marked"]` 为 True 时 `st["old"]` 是从标题到结束标记（含）的整段；`st["end"]` 在标记之后，所以 `text[st["end"]:]` 就是「标记之后的文字」，一直被保留。**丢的是 `old_body` 里不在 `tpl_body` 里的行**。
- `st["marked"]` 为 False 但 `old_body.startswith(tpl_body)`（prefix 路径）：块正文等于当前模板正文加尾随自定义段，`rem` 把尾随段切出来放到新标记之后，不丢任何行。
- `_norm_body`（第 146–149 行）去掉标题行和标记行，各行 `rstrip()`，整体 `strip("\n")`；用它比较两边正文。
- `convention_state`（第 152–173 行）返回 `{"state", "start", "end", "marked", "old"}`。
- legacy 路径的多行 action 直接拼在字符串里，`main()` 用 `print(f"  - {a}")` 打印，续行不缩进（`setup_context.py:438-440`）。

### `ensure_sections` 现状（`setup_context.py:240-261`）

```python
def ensure_sections(truth: Path, project_name: str, actions: list):
    """Ensure the truth file has the five required sections + memory link.
    Empty file -> full template. Non-empty -> append only what's missing."""
    text = truth.read_text(encoding="utf-8") if truth.exists() else ""
    ...
    appended, additions = [], []
    for title, block in template_sections().items():
        if "项目记忆" in title or "回写约定" in title:
            continue  # owned by ensure_convention
        if not section_present(text, title):
            additions.append("\n" + block)
            appended.append(title)
    if additions:
        if not text.endswith("\n"):
            text += "\n"
        truth.write_text(text + "".join(additions), encoding="utf-8")
        actions.append(f"appended missing sections to {truth.name}: {', '.join(appended)}")
    else:
        actions.append(f"{truth.name} already has all required sections (left untouched)")
```

`template_sections()` 返回的每个 `block` 以 `## 标题` 行开头、以单个 `\n` 结尾（第 114–128 行）。`main()` 的调用顺序是 `ensure_claude_pointer → ensure_sections → ensure_convention → ensure_memory`（第 432–435 行），所以 `ensure_sections` 运行时约定块可能已存在（旧项目）也可能还没有（新文件）。约定块标题用 `CONV_HEADING_RE`（第 60 行）定位：

```python
CONV_HEADING_RE = re.compile(r"^##\s+.*(项目记忆|回写约定|project memory|writeback).*$", re.M | re.I)
CONV_MARKER_RE = re.compile(r"^<!-- bootstrap-claude convention v\d+ -->[ \t]*$", re.M)
```

### 过期措辞

- `setup_context.py:7`：`the five REQUIRED_SECTIONS must be filled with real facts.`
- `setup_context.py:241`：`"""Ensure the truth file has the five required sections + memory link.`
- `REQUIRED_SECTIONS`（第 35 行）实际有七项：`["技术栈", "导航", "命令", "工作流与陷阱", "代码风格", "禁止文件", "审查规则"]`。

### 现有测试中会受影响的用例

`test_setup_context.py:34-40`（marked 旧块 + 标记后自定义段）：

```python
    f.write_text(BASE + "## 项目记忆 (回写约定)\n旧正文\n<!-- bootstrap-claude convention v1 -->\n\n自定义补充段\n")
    out = run(d); t = f.read_text()
    assert "upgraded" in out and "旧正文" not in t and "自定义补充段" in t and "memory.py check" in t, out
    assert t.index("-->") < t.index("自定义补充段")
```

改动后 `旧正文` 会出现在 `out` 里（被打印），但断言只检查它不在文件 `t` 里，仍然通过。第 42–51 行的 prefix 用例断言 `"upgraded" in out`，新文案必须仍含 `upgraded`。

### 文档现状

`bootstrap.md:20-25`：

```
「项目记忆 (回写约定)」一节的文字归本技能所有，以节末 `<!-- bootstrap-claude convention vN -->`
标记为边界。脚本每次运行都把它和 `assets/CLAUDE.template.md` 比对并按状态处理：缺失就追加；
文字相同但无标记就补标记；有标记或以模板正文开头的块直接升级，标记之后的项目自定义行保留；
无标记且已分叉的旧块只报告 `OUTDATED (legacy)`，加 `--upgrade-convention` 才替换并打印旧文，
被替换掉的自定义行由你补回标记之后；`unmanaged`（只提到 PROJECT_MEMORY 而无该节标题）不改。
升级模板时改正文并把标记版本号加一。
```

`SKILL.md:19`：

```
- 已初始化：看 `convention:` 一行。`latest` 不动；`upgraded` / `end marker added` 已自动升级到最新回写约定；`OUTDATED (legacy …)` 先读该节，再加 `--upgrade-convention` 重跑并把打印出的自定义行补回结束标记之后；`unmanaged` 说明项目自写了约定，只报告不改。
```

仓库约定（`AGENTS.md`）：Python 只用标准库；报告文本中英混用；技能文档间按标题名引用章节，不按编号；`make check` 查链接与编号引用；pre-commit 跑 prettier + `make check`。

## Commands you will need

| Purpose    | Command                                                                  | Expected on success               |
| ---------- | ------------------------------------------------------------------------ | --------------------------------- |
| 语法检查   | `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` | 无输出，exit 0                    |
| 脚本测试   | `python3 skills/bootstrap-claude/scripts/test_setup_context.py`          | 最后一行 `test_setup_context: ok` |
| 文档门禁   | `make check`                                                             | exit 0                            |
| 端到端复现 | 见 Step 5                                                                | 输出含被丢弃的两行                |

## Scope

**In scope**（只改这些文件）：

- `skills/bootstrap-claude/scripts/setup_context.py`
- `skills/bootstrap-claude/scripts/test_setup_context.py`
- `skills/bootstrap-claude/references/bootstrap.md`（仅第 20–25 行那一段）
- `skills/bootstrap-claude/SKILL.md`（仅第 19 行）

**Out of scope**（不要碰）：

- `skills/bootstrap-claude/assets/CLAUDE.template.md` —— 改正文就要升 v4，让所有项目再升级一次；本计划不改模板。
- `memory.py`、`test_memory.py`、`evals/` —— 与本缺陷无关。
- 把被丢弃的行**自动**搬到标记之后 —— 旧模板的过期行也会被搬进去变成噪音；本计划只打印，由人决定补回哪些。
- legacy 路径（`--upgrade-convention`）的行为与文案 —— 已经打印旧文，不动。
- `/Users/mg/github/DopaManga` 等其他仓库 —— 它们自己查 diff。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `bootstrap-claude`。示例：`fix(bootstrap-claude): print in-block lines dropped by convention upgrade, insert new sections before the block`。
- 未经操作者指示不要提交、不要推送。

## Steps

### Step 1: 升级路径打印被丢弃的旧行并改文案

把 `ensure_convention` 里 `if st["marked"] or old_body.startswith(tpl_body):` 分支改成下面的形状（其余分支不动）：

```python
    old_body, tpl_body = _norm_body(st["old"]), _norm_body(tpl)
    if st["marked"] or old_body.startswith(tpl_body):
        # bounded, or an old template copy with custom text appended after it
        rem = "" if st["marked"] else old_body[len(tpl_body):].strip("\n")
        custom = ("\n" + rem + "\n") if rem else ""  # one blank line, then the project's own text
        new = text[:st["start"]] + tpl.rstrip("\n") + "\n" + custom + text[st["end"]:]
        truth.write_text(new, encoding="utf-8")
        tpl_lines = set(tpl_body.splitlines())
        dropped = [l for l in old_body.splitlines() if l.strip() and l not in tpl_lines]
        if st["marked"] and dropped:
            actions.append("convention: upgraded (marked block replaced; text after the end marker kept). "
                           "These old in-block lines are not in the new template — re-add any that are "
                           "your own AFTER the end marker:\n" + "\n".join("    " + l for l in dropped))
        elif st["marked"]:
            actions.append("convention: upgraded (marked block replaced; text after the end marker kept)")
        else:
            actions.append("convention: upgraded (end marker inserted; custom text after the template kept)")
        return
```

说明：`dropped` 里会混进旧模板版本里措辞已变的行（例如 v2 的 `memory.py check` 那行），这是预期，文案已说明「补回属于你自己的」。prefix 路径（`marked` 为 False）没有丢行，不打印。

同时把函数 docstring 第二句改为：`Marked blocks are replaced and any in-block lines missing from the new template are printed; template-prefixed blocks get the end marker inserted before their trailing custom text; a legacy block that diverged is replaced only with --upgrade-convention, and the old text is printed.`

**Verify**: `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` → exit 0；`python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`（现有用例全部仍过）。

### Step 2: 新用例 —— 块内自定义行被打印

在 `test_setup_context.py` 第 41 行（marked 用例块之后、prefix 用例块之前）插入：

```python
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # project-custom lines INSIDE a marked block (before the marker) are dropped on upgrade,
    # but printed so the operator can re-add them; lines that match the template are not printed
    tpl_first = TPL.split("\n")[2]  # first body line of the template, identical in old and new
    f.write_text(BASE + "## 项目记忆 (回写约定)\n\n" + tpl_first + "\n\n@PROJECT_MEMORY.md\n\n"
                 "回写按 PR 合并后的状态写。\n<!-- bootstrap-claude convention v2 -->\n\n标记后的段落\n")
    out = run(d); t = f.read_text()
    assert "upgraded" in out and "AFTER the end marker" in out, out
    assert "@PROJECT_MEMORY.md" in out and "回写按 PR 合并后的状态写。" in out, out
    assert out.count(tpl_first) == 0, out  # template-identical line is not reported as dropped
    assert "@PROJECT_MEMORY.md" not in t and "标记后的段落" in t and sc.convention_state(t)["state"] == "latest"
```

先用 `python3 -c "import sys; sys.path.insert(0,'skills/bootstrap-claude/scripts'); import setup_context as sc; print(repr(sc.template_convention().split(chr(10))[2]))"` 确认 `TPL.split("\n")[2]` 是 `跨会话的持久信息记录在 …` 那一行（索引 0 是标题，1 是空行）；若不是，改索引使其取到模板的第一条正文行。

**Verify**: `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

### Step 3: 缺失章节插在约定块之前

把 `ensure_sections` 里 `if additions:` 分支改为：

```python
    if additions:
        m = CONV_HEADING_RE.search(text)
        if m:
            # keep the writeback block last: new sections go before it, not after it
            head = text[:m.start()].rstrip("\n") + "\n"
            text = head + "".join(additions) + "\n" + text[m.start():]
        else:
            if not text.endswith("\n"):
                text += "\n"
            text += "".join(additions)
        truth.write_text(text, encoding="utf-8")
        actions.append(f"appended missing sections to {truth.name}: {', '.join(appended)}")
```

action 文案保持 `appended missing sections to …`（evals 与文档引用了它）。

在 `test_setup_context.py` 的 Step 2 用例之后再插入：

```python
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # a missing required section is inserted BEFORE the convention block, which stays last
    f.write_text(BASE.replace("## 导航\n- src/\n\n", "") + TPL + "\n标记后的段落\n")
    out = run(d); t = f.read_text()
    assert "appended missing sections" in out and "导航" in out, out
    assert t.index("## 导航") < t.index("## 项目记忆 (回写约定)") and "\n\n## 项目记忆" in t, t
    assert t.rstrip().endswith("标记后的段落") and sc.convention_state(t)["state"] == "latest"
```

**Verify**: `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

### Step 4: docstring five → seven，文档措辞

- `setup_context.py:7` 的 `the five REQUIRED_SECTIONS` → `the seven REQUIRED_SECTIONS`；`setup_context.py:241` 的 `the five required sections` → `the seven required sections`。
- 模块 docstring 第 13–14 行（第 4 点）改为：`missing -> appended; same text -> end marker added; marked block -> replaced, in-block lines missing from the new template printed; template-prefixed block -> end marker inserted before its trailing custom text; a diverged legacy block -> reported, replaced only with --upgrade-convention.`
- `bootstrap.md:22` 的 `有标记或以模板正文开头的块直接升级，标记之后的项目自定义行保留；` 改为 `有标记的块整块替换，块内不属于新模板的旧行打印出来由你补回标记之后，标记之后的文字保留；以模板正文开头的块补标记并保留尾随的自定义段；`。并在第 25 行 `升级模板时改正文并把标记版本号加一。` 之前加一句：`项目自定义内容一律写在结束标记之后，写在块内的会在下次升级时被替换。`
- `SKILL.md:19` 的 `` `upgraded` / `end marker added` 已自动升级到最新回写约定； `` 改为 `` `upgraded` / `end marker added` 已自动升级到最新回写约定，输出里列出的旧行若是项目自己写的，补回结束标记之后； ``。

**Verify**: `grep -c 'five' skills/bootstrap-claude/scripts/setup_context.py` → `0`；`make check` → exit 0。

### Step 5: 端到端复现 DopaManga 场景（只读副本）

```bash
T=$(mktemp -d); cp /Users/mg/github/DopaManga/PROJECT_MEMORY.md "$T/"
git -C /Users/mg/github/DopaManga show HEAD:AGENTS.md > "$T/AGENTS.md"
python3 skills/bootstrap-claude/scripts/setup_context.py --dir "$T"
```

DopaManga 的 `HEAD:AGENTS.md`（在 HEAD 里 CLAUDE.md 还是指向它的 symlink，所以取 AGENTS.md）是 v2 块的真实文件：块内第一句被改写并多了一行 `@PROJECT_MEMORY.md` 导入，「收尾顺序」那句里嵌了「按 PR 合并后的状态写，合并后不为补记状态另开 PR」。工作区里的未提交版已经是 v3，所以必须取 HEAD。若 `git show` 报错或内容里没有 `convention v2` 标记（该仓库 HEAD 变了），改用 Step 2 的合成样例跑一遍即可，并在汇报中说明。

**Verify**: 输出含 `convention: upgraded (marked block replaced` 且下面列出 `@PROJECT_MEMORY.md` 和含 `按 PR 合并后的状态写` 的那一行（另有两三行 v2 模板旧措辞一起被列出，属预期噪音）；`$T/AGENTS.md` 里 `## 导航`、`## 工作流与陷阱` 出现在 `## 项目记忆 (回写约定)` 之前。跑完 `rm -rf "$T"`。

## Test plan

- 新用例 1（Step 2）：marked v2 块内含两条自定义行 + 一条与模板相同的行 → 两条自定义行出现在输出、模板行不出现、文件里自定义行已不在、标记后段落保留、状态 latest。
- 新用例 2（Step 3）：缺「导航」且已有约定块 + 标记后段落 → 「导航」插在约定块之前，约定块仍在最后，标记后段落仍在文件末尾。
- 现有用例全部不改、全部通过；特别关注第 34–51 行的 marked 与 prefix 用例。
- 结构模式：照第 34–40 行的用例写，一个 `with tempfile.TemporaryDirectory()` 块一个场景。

## Done criteria

- [ ] `python3 skills/bootstrap-claude/scripts/test_setup_context.py` 最后一行 `test_setup_context: ok`
- [ ] `python3 skills/bootstrap-claude/scripts/test_memory.py` 最后一行 `test_memory: ok`（确认没误伤）
- [ ] `grep -c 'custom text after the block preserved' skills/bootstrap-claude/scripts/setup_context.py` → `0`
- [ ] `grep -c 'five' skills/bootstrap-claude/scripts/setup_context.py` → `0`
- [ ] `make check` exit 0
- [ ] Step 5 的端到端输出列出了 `@PROJECT_MEMORY.md` 那一行
- [ ] `git status --porcelain` 只列出 in-scope 四个文件（加 `plans/README.md`）
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- Drift check 有输出且摘录对不上现行代码。
- `convention_state` 返回的字典没有 `old` 键或 `marked` 键（结构被改过）。
- Step 1 之后现有的 marked / prefix 用例（第 34–51 行）失败：说明新文案或新逻辑改变了保留行为，停下汇报而不是改旧断言。
- Step 3 之后任何现有用例失败：插入位置逻辑影响了别的场景，停下汇报。
- 发现需要改 `CLAUDE.template.md` 才能满足某条验证。

## Maintenance notes

- 以后升模板（v4+）时，`dropped` 列表会把旧版措辞的模板行也打出来，这是可接受的噪音；如果噪音太多，再考虑保留一份旧模板正文做精确比对。
- 已推迟：在模板约定块里加一行「自定义内容写在标记之后」的 HTML 提示。它会改正文、触发 v4 升级；等下次真要改正文时一起加。
- 已推迟：把 `dropped` 自动搬到标记之后。原因见 Out of scope。
- 审查时重点看：Step 1 的 `tpl_lines` 用的是 `_norm_body` 之后的行（已 `rstrip`），`dropped` 的比较两边口径一致；Step 3 插入后约定块标题前恰好一个空行（prettier 不会碰脚本生成的文件，格式由脚本自己保证）。
- 其他已升级到 v3 的仓库（本仓库 `skills` 自己的 AGENTS.md 是 003 之后新生成的，不受影响）请各自 `git diff AGENTS.md` 核对一次。
