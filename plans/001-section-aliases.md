# Plan 001: 让 setup_context.py 用别名表识别英文章节标题

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 547eeac..HEAD -- skills/bootstrap-claude/scripts/setup_context.py skills/bootstrap-claude/scripts/test_setup_context.py`
> 如果任一文件在本计划写成之后有改动，先把下面「Current state」的摘录与现有代码逐段对照；不一致即视为 STOP。

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `547eeac`, 2026-10-12

## Why this matters

`setup_context.py` 负责把一个仓库的 CLAUDE.md / AGENTS.md 补齐到五个必填章节。它判断「章节是否已存在」时只认中文关键词（技术栈、命令、代码风格、禁止文件、审查规则）。拿一份英文 AGENTS.md（实测用 Firefox 仓库的 73 行 AGENTS.md）跑一遍，脚本把五个中文 `_待填写_` 章节全部追加到文件尾部，`--validate` 报 5 个 FAIL，而那份文件本来就有 `## Code Style` 和 `## Workflow`。同一仓库里的 `memory.py` 已经给改写类小节配了英文别名（`Last Session` / `Next Session`），`setup_context.py` 没有跟上。

另外 `--validate` 和 `ensure_sections` 用的是两套判定：前者要求标题与关键词**完全相等**（字典查 key），后者只要求**包含**关键词。一个写成 `## 技术栈与依赖` 的章节会被认为「已存在」却在校验时报「缺失」。本计划把两处统一到一个别名表和一个匹配函数。

## Current state

- `skills/bootstrap-claude/scripts/setup_context.py` —— 初始化与校验脚本，本计划唯一要改的源码文件。
- `skills/bootstrap-claude/scripts/test_setup_context.py` —— 用 `assert` 写的脚本式测试（不是 unittest.TestCase），直接运行即测试。
- `skills/bootstrap-claude/scripts/memory.py:27` —— 已有的英文别名先例：

```python
REPLACE_SECTIONS = ["上次会话", "下次运行", "Last Session", "Next Session"]
```

`setup_context.py` 现状摘录：

```python
# setup_context.py:35
REQUIRED_SECTIONS = ["技术栈", "命令", "代码风格", "禁止文件", "审查规则"]
...
# setup_context.py:39-40
CONV_HEADING_RE = re.compile(r"^##\s+.*(项目记忆|回写约定).*$", re.M)
...
# setup_context.py:57-63
def heading_present(text: str, keyword: str) -> bool:
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("#") and keyword in s:
            return True
    return False
...
# setup_context.py:86-90
def section_present(text: str, title: str) -> bool:
    """The memory-writeback section is identified by its link, others by heading keyword."""
    if MEMORY_LINK in title or "项目记忆" in title:
        return MEMORY_LINK in text
    return heading_present(text, title)
...
# setup_context.py:277-282  (inside cmd_validate; `bodies` comes from section_bodies(text), keyed by exact `## ` title)
        for section in REQUIRED_SECTIONS:
            if section not in bodies:
                checks.append((False, f"{section}: 缺失"))
            else:
                state = section_state(bodies[section])
                checks.append((state == "已填写", f"{section}: {state}"))
```

`ensure_sections`（189-211 行）遍历 `template_sections()` 返回的模板章节标题，用 `section_present(text, title)` 决定是否追加；模板标题就是中文的五个必填名加「项目记忆 (回写约定)」。

实测复现（只读，放在临时目录）：

```sh
mkdir -p /tmp/x && curl -sL https://raw.githubusercontent.com/mozilla-firefox/firefox/main/AGENTS.md -o /tmp/x/AGENTS.md
python3 skills/bootstrap-claude/scripts/setup_context.py --dir /tmp/x
#   - appended missing sections to AGENTS.md: 技术栈, 命令, 代码风格, 禁止文件, 审查规则
python3 skills/bootstrap-claude/scripts/setup_context.py --dir /tmp/x --validate
#   FAIL 代码风格: 占位符     ← 文件里本来就有 ## Code Style
```

仓库约定：Python 脚本无外部依赖、标准库 only；注释与报告文本中英混用，PASS/FAIL 文本是中文。测试风格见 `test_setup_context.py` 全文（58 行）：每个用例一个 `tempfile.TemporaryDirectory()` 块，用 `run(d, *flags)` 调脚本拿 stdout，再 `assert ... , out`。

## Commands you will need

| Purpose              | Command                                                                  | Expected on success                   |
| -------------------- | ------------------------------------------------------------------------ | ------------------------------------- |
| 脚本测试             | `python3 skills/bootstrap-claude/scripts/test_setup_context.py`          | 打印 `test_setup_context: ok`，exit 0 |
| 记忆脚本测试（回归） | `python3 skills/bootstrap-claude/scripts/test_memory.py`                 | 打印 `test_memory: ok`                |
| 文档链接检查         | `make check`                                                             | exit 0，无输出或仅 OK                 |
| 语法检查             | `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` | exit 0                                |

仓库未安装 pytest，不要用它。

## Scope

**In scope**（只能改这些文件）:

- `skills/bootstrap-claude/scripts/setup_context.py`
- `skills/bootstrap-claude/scripts/test_setup_context.py`

**Out of scope**（不要碰，即使看起来相关）:

- `skills/bootstrap-claude/assets/CLAUDE.template.md` —— 模板语言保持中文，这是用户的选择；本计划只加识别别名，不加英文模板。模板改动归 Plan 003。
- `skills/bootstrap-claude/scripts/memory.py` —— 它的别名已存在，不动。
- `skills/bootstrap-claude/references/*.md` —— 文档不需要因本计划改动。
- `skills/bootstrap-claude/evals/**` —— 现有 eval 期望不受影响。

## Git workflow

- 本仓库直接提交到 `main`，提交信息用 conventional commits，scope 写技能名。示例（来自 `git log`）：`fix(ad-astra): put the core algorithm on rung 1 and handle mid-course scope changes`。
- 本计划若提交，信息形如：`fix(bootstrap-claude): match required sections by alias table, unify ensure/validate detection`。
- 未经操作者指示不要提交、不要推送。pre-commit 会跑 `make check`。

## Steps

### Step 1: 引入别名表与统一匹配函数

在 `setup_context.py` 第 35 行附近，保留 `REQUIRED_SECTIONS`（它是规范名列表，其他地方按它遍历），在其后新增：

```python
# Canonical section -> lowercase aliases. Matching is substring, case-insensitive,
# against any heading line. Chinese names are the template's; English names cover
# the common AGENTS.md vocabulary (see memory.py REPLACE_SECTIONS for the precedent).
SECTION_ALIASES = {
    "技术栈":  ["技术栈", "tech stack", "technology stack", "stack"],
    "命令":    ["命令", "commands", "scripts", "build and test", "build & test"],
    "代码风格": ["代码风格", "code style", "coding style", "style guide", "conventions"],
    "禁止文件": ["禁止文件", "do not edit", "protected files", "forbidden files", "never edit"],
    "审查规则": ["审查规则", "code review", "review rules", "reviewing", "pull request", "merge rules"],
}


def match_section(heading: str, canonical: str) -> bool:
    """Does this heading line name the canonical section (by any alias)?"""
    h = heading.lstrip("#").strip().lower()
    return any(a in h for a in SECTION_ALIASES[canonical])
```

改写 `heading_present`，让它用 `match_section` 而不是裸子串：

```python
def heading_present(text: str, canonical: str) -> bool:
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("#") and match_section(s, canonical):
            return True
    return False
```

`section_present` 不用改（它仍调 `heading_present(text, title)`，title 就是模板里的规范名）。

把第 39 行的 `CONV_HEADING_RE` 扩成中英都认、忽略大小写：

```python
CONV_HEADING_RE = re.compile(r"^##\s+.*(项目记忆|回写约定|project memory|writeback).*$", re.M | re.I)
```

**Verify**: `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` → exit 0；`python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`（现有用例全是中文标题，必须仍通过）。

### Step 2: 让 `--validate` 用同一套匹配

在 `cmd_validate` 里（现 277-282 行），把「字典按 key 查」改成「在已解析的 `## ` 标题里找第一个匹配别名的」：

```python
        for section in REQUIRED_SECTIONS:
            hit = next((t for t in bodies if match_section(t, section)), None)
            if hit is None:
                checks.append((False, f"{section}: 缺失"))
            else:
                state = section_state(bodies[hit])
                label = section if hit == section else f"{section} (匹配 ## {hit})"
                checks.append((state == "已填写", f"{label}: {state}"))
```

`section_bodies` 只收 `## ` 级标题，与 `heading_present` 的「任意级别」略有差异；这是既有行为，本计划不改（见 Maintenance notes）。

**Verify**: `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

### Step 3: 补英文标题的测试用例

在 `test_setup_context.py` 末尾 `print("test_setup_context: ok")` 之前追加一个用例，仿照第 52-57 行的写法：

```python
BASE_EN = ("# x\n\n## Tech Stack\n- go\n\n## Commands\n- make\n\n## Code Style\n- fmt\n\n"
           "## Protected Files\n- dist\n\n## Code Review\n- ci\n\n")

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # English headings are recognised by alias: nothing appended except the convention block
    f.write_text(BASE_EN)
    out = run(d); t = f.read_text()
    assert "already has all required sections" in out, out
    assert "_待填写_" not in t and "## 技术栈" not in t, t
    v = run(d, "--validate")
    assert "缺失" not in v and "占位符" not in v, v
    assert "技术栈 (匹配 ## Tech Stack): 已填写" in v, v
```

注意：这个用例里只有 AGENTS.md，脚本会给 CLAUDE.md 建一个指向它的伙伴文件（本计划执行时还是 symlink，Plan 002 之后改为一行 `@AGENTS.md`），不要在断言里限制 CLAUDE.md 的形态。

**Verify**: `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

### Step 4: 用 Firefox 的真实文件做一次端到端确认

```sh
rm -rf /tmp/ff-check && mkdir -p /tmp/ff-check
curl -sL https://raw.githubusercontent.com/mozilla-firefox/firefox/main/AGENTS.md -o /tmp/ff-check/AGENTS.md
python3 skills/bootstrap-claude/scripts/setup_context.py --dir /tmp/ff-check
python3 skills/bootstrap-claude/scripts/setup_context.py --dir /tmp/ff-check --validate
```

Firefox 文件的 `## ` 标题是：`Tooling for Firefox work`、`Fixing review comments`、`Referring to code in bugs, reviews and commit messages`、`Code Style`、`Workflow`（另有一个 `# Global instructions` 一级标题）。按 Step 1 的别名表，只有 `Code Style` 命中（代码风格）；`Fixing review comments` 不含 `code review` / `review rules` / `reviewing` 任一别名，所以**不**命中审查规则——这是想要的，一节讲怎么修评论的标题并不陈述审查规则。

**Verify**: 第一条输出为 `appended missing sections to AGENTS.md: 技术栈, 命令, 禁止文件, 审查规则`（四节，不含代码风格）；第二条输出含 `PASS 代码风格 (匹配 ## Code Style): 已填写`，其余四节报 `占位符` FAIL。如果无法联网，跳过本步并在汇报里说明。

## Test plan

- 新增用例（Step 3）：英文五标题文件 → 不追加任何必填章节、validate 五节全 PASS 且标签显示匹配到的英文标题。
- 现有五个用例（中文标题、约定块的四种状态）全部保持通过，证明中文路径无回归。
- 验证命令：`python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

## Done criteria

全部满足：

- [ ] `python3 skills/bootstrap-claude/scripts/test_setup_context.py` 打印 `test_setup_context: ok`
- [ ] `python3 skills/bootstrap-claude/scripts/test_memory.py` 打印 `test_memory: ok`
- [ ] `grep -n "SECTION_ALIASES" skills/bootstrap-claude/scripts/setup_context.py` 至少 2 处命中（定义与 `match_section` 内的使用）
- [ ] `grep -n 'if section not in bodies' skills/bootstrap-claude/scripts/setup_context.py` 无命中
- [ ] `make check` exit 0
- [ ] `git status --porcelain` 只列出 in-scope 的两个文件（加上 `plans/README.md`）
- [ ] `plans/README.md` 本计划状态行已更新

## STOP conditions

遇到以下情况停下汇报：

- `setup_context.py` 第 35、39、57、86、277 行附近的代码与「Current state」摘录不一致。
- Step 1 之后现有测试失败，且不是因为你改动的匹配逻辑（说明别名表误伤了中文标题，例如 `"stack"` 这类短别名命中了不该命中的标题；此时不要继续放宽或收紧别名，汇报命中样本）。
- 发现修复需要改 `memory.py` 或模板。

## Maintenance notes

- 以后在模板里新增必填章节（Plan 003 会加两个），必须同时在 `SECTION_ALIASES` 加一条，否则 `match_section` 会 `KeyError`。可以考虑在 `template_sections()` 处加一个断言：模板的每个非约定章节都在别名表里。
- `heading_present` 认任意级别标题，`section_bodies`（供 validate）只认 `## `。本计划刻意没有统一这一点；若将来有人报「ensure 说存在、validate 说缺失」且标题是 `###`，解法是让 `section_bodies` 也认别名表而不是改 `heading_present`。
- 别名是子串匹配，所以刻意不收裸词 `"review"`（会把 Firefox 的 `## Fixing review comments` 误判为审查规则）和裸词 `"style"`。新增别名时先拿 Firefox 的六个标题过一遍，确认没有误命中。
- 已推迟：给英文仓库提供英文模板（`--lang en`）。本计划后英文仓库的**已有**章节能被识别，但**缺失**章节仍以中文追加。是否值得维护第二份模板由用户决定，见 `plans/README.md`。
