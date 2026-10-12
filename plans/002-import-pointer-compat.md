# Plan 002: AGENTS.md 为真源，CLAUDE.md 只写一行 `@AGENTS.md`，不再使用 symlink

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 547eeac..HEAD -- skills/bootstrap-claude/scripts/setup_context.py skills/bootstrap-claude/scripts/test_setup_context.py skills/bootstrap-claude/references/bootstrap.md skills/bootstrap-claude/evals/evals.json skills/bootstrap-claude/SKILL.md skills/bootstrap-claude/assets/CLAUDE.template.md skills/bootstrap-claude/assets/PROJECT_MEMORY.template.md`
> Plan 001 应已落地（它改了 `setup_context.py` 的章节匹配与测试文件），所以这两个文件会有差异；对照时只看本计划「Current state」摘录的段落（`ultimate`、`ensure_partner_symlinks`、`cmd_validate` 开头、`main()` 的真源判定、argparse 的 `--resolve-conflict`），这些段 Plan 001 不碰。其他文件有差异即 STOP。

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED（改默认布局并迁移已有项目的文件名；用户已于 2026-10-12 明确拍板：「AGENTS.md first, add an import in CLAUDE.md, no longer using symlink」）
- **Depends on**: plans/001-section-aliases.md（同一文件，先落地避免冲突）
- **Category**: bug + migration
- **Planned at**: commit `547eeac`, 2026-10-12

## Why this matters

Claude Code 官方文档（`https://code.claude.com/docs/en/memory`，「AGENTS.md」与「Share one file with other coding tools」两节）给出的「一份内容、所有工具都读」写法是：AGENTS.md 为真实文件，CLAUDE.md 只含一行 `@AGENTS.md` 导入。Firefox 仓库正是这个布局。而本技能现在的做法相反：新项目以 CLAUDE.md 为真实文件、AGENTS.md 为 symlink；遇到 Firefox 布局时把 `@AGENTS.md` 指针文件当成独立的真实文件，报 **CONFLICT** 退出码 2（实测），唯一出路是把其中一个改名 `.bak` 再做 symlink。

symlink 还有独立的问题：未开启 `core.symlinks` 的 Windows 检出会把 symlink 落成一个内容为 `AGENTS.md` 四个字的普通文本文件，两边都坏；其他工具读到的 AGENTS.md 标题还是「Claude 项目上下文」。导入指针是普通文本文件，供应商中立。Claude Code ≥ 2.1.277 在没有 CLAUDE.md 时也能直接读 AGENTS.md，但文档注明某些会话里不行，所以 CLAUDE.md 导入行仍要保留。

用户的决定：**AGENTS.md 是唯一真源；CLAUDE.md 永远只是一行 `@AGENTS.md`；脚本不再创建任何 symlink，遇到旧布局（CLAUDE.md 为真实文件、AGENTS.md 为 symlink）自动迁移。**

## Current state

- `skills/bootstrap-claude/scripts/setup_context.py` —— 主要改动点。
- `skills/bootstrap-claude/scripts/test_setup_context.py` —— 脚本式测试；现有用例都把 BASE 写进 `CLAUDE.md` 再读 `CLAUDE.md`，迁移后要改读 `AGENTS.md`。
- `skills/bootstrap-claude/references/bootstrap.md` —— 「Compatibility」一节的兼容表，整节重写。
- `skills/bootstrap-claude/SKILL.md:18` —— 入口文案含 `created CLAUDE.md from template`。
- `skills/bootstrap-claude/assets/CLAUDE.template.md:1-4` —— 标题「Claude 项目上下文」；文件名保持不变（见 Out of scope）。
- `skills/bootstrap-claude/assets/PROJECT_MEMORY.template.md:3` —— `回写约定见 [CLAUDE.md](./CLAUDE.md)`。
- `skills/bootstrap-claude/evals/evals.json` —— eval 1/2/4 的期望写了 CLAUDE.md 为真源或 symlink。

`setup_context.py` 现状摘录（行号按 `547eeac`）：

```python
# :47-54
def ultimate(p: Path):
    """The real file `p` resolves to (following symlinks), or None if it is
    missing, dangling, or not a regular file."""
    try:
        rp = p.resolve()
    except OSError:
        return None
    return rp if rp.is_file() else None
...
# :175-186
def ensure_partner_symlinks(root: Path, truth: Path, actions: list):
    """Make whichever of CLAUDE.md / AGENTS.md is not the truth file a symlink
    pointing at the truth file's name."""
    for name in ("CLAUDE.md", "AGENTS.md"):
        p = root / name
        if ultimate(p) == truth:
            continue  # already correct (it *is* the truth, or links to it)
        if p.is_symlink() or not p.exists():
            if p.is_symlink():
                p.unlink()
            os.symlink(truth.name, p)
            actions.append(f"symlink: {name} -> {truth.name}")
...
# :255-272  (cmd_validate 开头)
    claude, agents = root / "CLAUDE.md", root / "AGENTS.md"
    cu, au = ultimate(claude), ultimate(agents)

    if cu and au and cu != au:
        checks.append((False, "CLAUDE.md 与 AGENTS.md 指向不同内容 (CONFLICT)"))
        truth = None
    else:
        truth = cu or au
        if truth is None:
            checks.append((False, "缺少上下文文件 — 先运行 bootstrap"))
        else:
            bad = [name for name, resolved in (("CLAUDE.md", cu), ("AGENTS.md", au))
                   if resolved != truth]
            if bad:
                for name in bad:
                    checks.append((False, f"{name} 缺失或未指向 {truth.name}"))
            else:
                checks.append((True, f"symlink 一致: 真实文件为 {truth.name}"))
...
# :307-310
    ap.add_argument("--resolve-conflict", choices=["claude", "agents"], default=None,
                    help="when both CLAUDE.md and AGENTS.md are independent real "
                         "files, pick which becomes the source of truth; the other "
                         "is backed up to *.bak and replaced with a symlink")
...
# :332-369  (main)
    cu = ultimate(claude)
    au = ultimate(agents)

    if cu and au and cu == au:
        truth = cu
    elif cu and au and cu != au:
        if not args.resolve_conflict:
            print(
                "CONFLICT: CLAUDE.md and AGENTS.md are independent real files with "
                "different content.\n"
                f"  CLAUDE.md -> {cu}\n  AGENTS.md -> {au}\n"
                "Refusing to guess. Re-run with --resolve-conflict claude|agents to pick "
                "the source of truth (the other is backed up to *.bak and symlinked).",
                file=sys.stderr,
            )
            sys.exit(2)
        keep, drop = (claude, agents) if args.resolve_conflict == "claude" else (agents, claude)
        bak = drop.with_suffix(drop.suffix + ".bak")
        os.replace(drop, bak)
        actions.append(f"CONFLICT resolved: backed up {drop.name} -> {bak.name}")
        truth = ultimate(keep)
    elif cu and not au:
        truth = cu
    elif au and not cu:
        truth = au
    else:
        # Neither has real content. Clean up any dangling symlinks and init fresh.
        for p in (claude, agents):
            if p.is_symlink():
                p.unlink()
        claude.write_text(render("CLAUDE.template.md", project_name), encoding="utf-8")
        actions.append("created CLAUDE.md from template")
        truth = ultimate(claude)

    ensure_partner_symlinks(root, truth, actions)
    ensure_sections(truth, project_name, actions)
    ensure_convention(truth, actions, args.upgrade_convention)
    ensure_memory(root, project_name, actions)
```

模块 docstring 第 15-20 行列了五条 symlink 措辞的兼容规则。

`test_setup_context.py` 现状：第 12-14 行 `run(d, *flags)` 只返回 stdout；第 21-22 行断言 `"created CLAUDE.md from template"` 并读 `d / "CLAUDE.md"`；第 25、34、42、53 行都是 `f = d / "CLAUDE.md"`，之后往 `f` 写 BASE 再读 `f`。

`bootstrap.md:67-85` 的 Compatibility 表（六行，全是 symlink 措辞），以及第 35-36 行「edit that, not the symlink」、第 27-29 行的 CONFLICT 说明。

`evals.json` 相关期望：eval 1 `"CLAUDE.md exists in the project and is a regular file (the source of truth)"`、`"AGENTS.md exists and is a symlink pointing at CLAUDE.md"`、expected_output 开头 "CLAUDE.md (real) + AGENTS.md (symlink)"；eval 2 prompt "(and CLAUDE.md is just a symlink to it)"、expectations `"CLAUDE.md is still a symlink pointing at AGENTS.md"`、`"...not duplicated into the CLAUDE.md symlink as a separate file"`（夹具 `evals/files/go-svc/` 实际只有 AGENTS.md，没有 CLAUDE.md）；eval 3 `"CLAUDE.md (or the source-of-truth context file) 命令 section..."`；eval 4 `"CLAUDE.md's 「项目记忆 (回写约定)」 section now ends with..."`（夹具 `evals/files/py-lib/` 的真实文件是 CLAUDE.md，会被迁移）。

Claude Code 对导入的解析规则（来自官方文档）：`@path` 要在反引号和代码块之外；相对路径相对于所在文件。指针文件写 `@AGENTS.md\n` 一行即可。

## Commands you will need

| Purpose           | Command                                                                                    | Expected on success      |
| ----------------- | ------------------------------------------------------------------------------------------ | ------------------------ |
| 脚本测试          | `python3 skills/bootstrap-claude/scripts/test_setup_context.py`                            | `test_setup_context: ok` |
| 记忆脚本测试      | `python3 skills/bootstrap-claude/scripts/test_memory.py`                                   | `test_memory: ok`        |
| 文档链接检查      | `make check`                                                                               | exit 0                   |
| evals.json 合法性 | `python3 -I -c "import json; json.load(open('skills/bootstrap-claude/evals/evals.json'))"` | exit 0                   |

## Scope

**In scope**:

- `skills/bootstrap-claude/scripts/setup_context.py`
- `skills/bootstrap-claude/scripts/test_setup_context.py`
- `skills/bootstrap-claude/references/bootstrap.md`（Compatibility 整节；Step 2 第 35-36 行一句；第 27-29 行 CONFLICT 说明）
- `skills/bootstrap-claude/SKILL.md`（仅第 18 行）
- `skills/bootstrap-claude/assets/CLAUDE.template.md`（仅第 1-4 行标题与引言；不碰任何 `## ` 章节）
- `skills/bootstrap-claude/assets/PROJECT_MEMORY.template.md`（仅第 3 行链接）
- `skills/bootstrap-claude/evals/evals.json`（仅与真源 / symlink 相关的措辞）

**Out of scope**:

- 把 `assets/CLAUDE.template.md` 改名为 `AGENTS.template.md` —— 牵连脚本、测试、文档多处引用，收益只是文件名；记为推迟。
- 模板的 `## ` 章节正文与结束标记 —— 归 Plan 003；本计划改的标题行在第一个 `## ` 之前，不影响 `convention_state` 的比对。
- `evals/files/**` 夹具内容。
- 任何 Windows 专用逻辑。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `bootstrap-claude`。示例：`feat(bootstrap-claude): AGENTS.md is the source of truth, CLAUDE.md is a one-line @AGENTS.md import; migrate symlink layouts`。
- 未经操作者指示不要提交、不要推送。

## Steps

### Step 1: 加「指针解析」函数

在 `ultimate()` 之后新增：

```python
IMPORT_RE = re.compile(r"^@(?:\./)?AGENTS\.md\s*$")
POINTER_TEXT = "@AGENTS.md\n"


def is_import_pointer(p: Path) -> bool:
    """True if `p` is a regular (non-symlink) file whose only non-blank,
    non-comment content is the single line `@AGENTS.md` — Claude Code's
    documented way to read AGENTS.md through CLAUDE.md."""
    if p.is_symlink() or not p.is_file():
        return False
    lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines()]
    lines = [l for l in lines if l and not l.startswith("<!--")]
    return len(lines) == 1 and bool(IMPORT_RE.match(lines[0]))


def resolve_pointer(p: Path, agents: Path):
    """The real content file `p` stands for: an `@AGENTS.md` import resolves to
    `agents`, a symlink is followed, a regular file is itself. None if missing,
    dangling, or not a regular file."""
    if is_import_pointer(p):
        return ultimate(agents)
    return ultimate(p)
```

只认单行、只认 `AGENTS.md`，避免把任何含 `@AGENTS.md` 字样的真实 CLAUDE.md 误判为指针。

**Verify**: `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` → exit 0。

### Step 2: 重写 `main()` 的真源判定：AGENTS.md 永远是真源

把第 332-364 行（从 `cu = ultimate(claude)` 到 `truth = ultimate(claude)`）替换为：

```python
    cu = resolve_pointer(claude, agents)
    au = ultimate(agents)

    if cu and au and cu != au:
        # Two independent real files. Refuse to guess.
        if not args.resolve_conflict:
            print(
                "CONFLICT: CLAUDE.md and AGENTS.md are independent real files with "
                "different content.\n"
                f"  CLAUDE.md -> {cu}\n  AGENTS.md -> {au}\n"
                "Refusing to guess. Re-run with --resolve-conflict claude|agents to pick "
                "whose content becomes AGENTS.md (the other is backed up to *.bak; "
                "CLAUDE.md becomes the one-line @AGENTS.md import).",
                file=sys.stderr,
            )
            sys.exit(2)
        if args.resolve_conflict == "claude":
            bak = agents.with_suffix(agents.suffix + ".bak")
            os.replace(agents, bak)
            os.replace(claude, agents)
            actions.append(f"CONFLICT resolved: backed up AGENTS.md -> {bak.name}; "
                           "CLAUDE.md content moved to AGENTS.md")
        else:
            bak = claude.with_suffix(claude.suffix + ".bak")
            os.replace(claude, bak)
            actions.append(f"CONFLICT resolved: backed up CLAUDE.md -> {bak.name}")
    elif cu and not au:
        # Legacy layout: CLAUDE.md holds the content (AGENTS.md missing or a symlink to it).
        if agents.is_symlink():
            agents.unlink()
        os.replace(claude, agents)
        actions.append("migrated: CLAUDE.md content moved to AGENTS.md (AGENTS.md is the source of truth)")
    elif not au:
        # Nothing real anywhere (fresh dir, dangling symlinks, or a lone @AGENTS.md pointer).
        if agents.is_symlink():
            agents.unlink()
        agents.write_text(render("CLAUDE.template.md", project_name), encoding="utf-8")
        actions.append("created AGENTS.md from template")
    truth = ultimate(agents)
```

要点：

- `cu and au and cu == au`（CLAUDE.md 已是指针或 symlink）与 `au and not cu`（只有 AGENTS.md）都不需要动作，直接 `truth = ultimate(agents)`。
- 旧布局 `CLAUDE.md` 真实 + `AGENTS.md` symlink → `cu` 是 CLAUDE.md 的 resolve 结果、`au` 是 symlink 的 resolve 结果，两者**相等**，落到第一个分支之外 → 不迁移。所以第一个判断前要先处理这一情形。把下面这段放在 `if cu and au and cu != au:` **之前**：

```python
    if agents.is_symlink() and ultimate(agents) == ultimate(claude) and claude.is_file() and not claude.is_symlink():
        agents.unlink()
        au = None  # fall into the legacy-migration branch below
```

- 一个孤立的 `@AGENTS.md` 指针（AGENTS.md 缺失）：`cu` 为 None、`au` 为 None → 进第三个分支，从模板创建 AGENTS.md，指针文件**不被覆盖**。

然后把第 366 行 `ensure_partner_symlinks(root, truth, actions)` 改为 `ensure_claude_pointer(root, actions)`（Step 3 定义）。

**Verify**: `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` → exit 0。

### Step 3: `ensure_claude_pointer` 替代 `ensure_partner_symlinks`

删除 `ensure_partner_symlinks`，新增：

```python
def ensure_claude_pointer(root: Path, actions: list):
    """CLAUDE.md is always the one-line `@AGENTS.md` import: a plain text file
    (survives Windows checkouts without core.symlinks) that Claude Code expands at
    launch. A legacy symlink is replaced; a correct pointer is left alone."""
    claude = root / "CLAUDE.md"
    if is_import_pointer(claude):
        return
    if claude.is_symlink():
        claude.unlink()
        claude.write_text(POINTER_TEXT, encoding="utf-8")
        actions.append("pointer: CLAUDE.md symlink replaced with @AGENTS.md import")
        return
    if not claude.exists():
        claude.write_text(POINTER_TEXT, encoding="utf-8")
        actions.append("pointer: CLAUDE.md -> @AGENTS.md")
        return
    # A regular CLAUDE.md with content can only reach here if main() left it (it never should).
    actions.append("WARNING: CLAUDE.md is a regular file with content and was left untouched")
```

**Verify**: `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` → exit 0。

### Step 4: `cmd_validate`、docstring、argparse 文案

- `cmd_validate` 第 256 行改为 `cu, au = resolve_pointer(claude, agents), ultimate(agents)`。
- 第 262 行 `truth = cu or au` 改为 `truth = au`（AGENTS.md 缺失即报 `缺少上下文文件 — 先运行 bootstrap`，哪怕 CLAUDE.md 有内容，因为那是未迁移的旧布局）。
- 第 266-272 行的一致性检查改为：

```python
            if cu != truth:
                checks.append((False, "CLAUDE.md 缺失或不是指向 AGENTS.md 的 @AGENTS.md 导入"))
            else:
                checks.append((True, "指向一致: 真实文件为 AGENTS.md，CLAUDE.md 为 @AGENTS.md 导入"))
```

- `--resolve-conflict` help 改为 `"when both CLAUDE.md and AGENTS.md are independent real files, pick whose content becomes AGENTS.md; the other is backed up to *.bak and CLAUDE.md becomes the one-line @AGENTS.md import"`。
- 模块 docstring 第 15-20 行改为：

```
Layout (AGENTS.md is always the source of truth; CLAUDE.md is the one-line `@AGENTS.md` import):
  - Neither exists / only a lone @AGENTS.md pointer      -> create AGENTS.md from template, write pointer
  - Only AGENTS.md (real)                                 -> write CLAUDE.md pointer
  - AGENTS.md real + CLAUDE.md pointer or symlink to it   -> truth = AGENTS.md; a symlink is replaced by the pointer
  - CLAUDE.md real, AGENTS.md missing or symlink to it    -> migrate: CLAUDE.md content moves to AGENTS.md, pointer written
  - Both are independent real files                       -> CONFLICT, refuse unless --resolve-conflict given
```

第 2 条保证也改为 "2. CLAUDE.md is the one-line `@AGENTS.md` import so Claude Code reads the same content; no symlinks are created."

**Verify**: `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` → exit 0。

### Step 5: 迁移现有测试并补用例

`test_setup_context.py`：

1. 第 21-22 行改为：

```python
    out = run(d); assert "created AGENTS.md from template" in out, out
    assert sc.convention_state((d / "AGENTS.md").read_text())["state"] == "latest"
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n"
```

2. 第 25、34、42、53 行的 `f = d / "CLAUDE.md"` 全部改为 `f = d / "AGENTS.md"`（这些用例测的是约定块状态机，与布局无关；放进 AGENTS.md 后脚本不再迁移）。Plan 001 加的英文用例已经写 AGENTS.md，不动。

3. 在 `print(...)` 前追加四个用例。`run()` 只返回 stdout，CONFLICT 走 stderr 和退出码，所以第一个用 `subprocess.run`：

```python
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # Firefox layout: AGENTS.md real + CLAUDE.md is the one-line import -> no CONFLICT, nothing rewritten
    (d / "AGENTS.md").write_text(BASE); (d / "CLAUDE.md").write_text("@AGENTS.md\n")
    r = subprocess.run([sys.executable, str(HERE / "setup_context.py"), "--dir", str(d)],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "source of truth: AGENTS.md" in r.stdout, r.stdout + r.stderr
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n" and "pointer:" not in r.stdout
    assert "指向一致" in run(d, "--validate")

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # legacy layout: CLAUDE.md real + AGENTS.md symlink -> migrated, no symlink left anywhere
    (d / "CLAUDE.md").write_text(BASE); os.symlink("CLAUDE.md", d / "AGENTS.md")
    out = run(d)
    assert "migrated: CLAUDE.md content moved to AGENTS.md" in out, out
    a, c = d / "AGENTS.md", d / "CLAUDE.md"
    assert a.is_file() and not a.is_symlink() and "- go" in a.read_text()
    assert c.is_file() and not c.is_symlink() and c.read_text() == "@AGENTS.md\n"
    before = (a.read_text(), c.read_text()); run(d); assert (a.read_text(), c.read_text()) == before  # idempotent

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # lone pointer: CLAUDE.md = @AGENTS.md, no AGENTS.md -> AGENTS.md created, pointer untouched
    (d / "CLAUDE.md").write_text("@AGENTS.md\n")
    out = run(d)
    assert "created AGENTS.md from template" in out, out
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n" and (d / "AGENTS.md").is_file()

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # conflict: two real files -> exit 2 without flag; --resolve-conflict claude moves CLAUDE.md content into AGENTS.md
    (d / "CLAUDE.md").write_text(BASE); (d / "AGENTS.md").write_text("# other\n")
    r = subprocess.run([sys.executable, str(HERE / "setup_context.py"), "--dir", str(d)],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "CONFLICT" in r.stderr, r.stderr
    out = run(d, "--resolve-conflict", "claude")
    assert (d / "AGENTS.md.bak").read_text() == "# other\n" and "- go" in (d / "AGENTS.md").read_text(), out
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n"
```

文件顶部需要 `import os`（第 3 行 `import sys, tempfile, subprocess` 加上 `os`）。

**Verify**: `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

### Step 6: 文档与模板文案

`references/bootstrap.md`：

- 第 13-18 行 Step 1 的说明里 "reconciles the CLAUDE.md / AGENTS.md naming so both point at one source of truth" 改为 "makes AGENTS.md the single source of truth and CLAUDE.md a one-line `@AGENTS.md` import (migrating a legacy CLAUDE.md-as-real-file layout automatically)"。
- 第 27-29 行 CONFLICT 说明改为：两个都是有内容的真实文件时脚本拒绝猜；给用户看两份内容，问哪份该成为 AGENTS.md，再用 `--resolve-conflict claude|agents` 重跑（另一份备份为 `.bak`，CLAUDE.md 变成一行导入）。
- 第 35-36 行 "(the one the script reported — edit that, not the symlink)" 改为 "(always `AGENTS.md`; editing the `@AGENTS.md` pointer in CLAUDE.md does nothing useful)"。
- 第 67-85 行 Compatibility 整节替换为：

```markdown
## Compatibility

Many tools read `AGENTS.md`; Claude Code reads `CLAUDE.md`, and expands `@path` imports
in it. The skill therefore keeps **one real file, `AGENTS.md`**, and makes `CLAUDE.md`
a one-line import `@AGENTS.md` — the layout the Claude Code docs recommend and the one
Firefox uses. A plain text pointer (unlike a symlink) survives Windows checkouts without
`core.symlinks`, and the file other agents read carries no Claude-specific framing.
`setup_context.py` resolves every layout automatically and never creates symlinks:

| Situation                                                | Result                                                                       |
| -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Neither exists, or only a lone `@AGENTS.md` pointer      | `AGENTS.md` created from the template; `CLAUDE.md` = `@AGENTS.md`            |
| Only `AGENTS.md` (real)                                  | left as-is; `CLAUDE.md` = `@AGENTS.md` written                               |
| `AGENTS.md` real + `CLAUDE.md` already `@AGENTS.md`      | left as-is                                                                   |
| `AGENTS.md` real + `CLAUDE.md` a symlink to it           | symlink replaced by the `@AGENTS.md` pointer                                 |
| `CLAUDE.md` real, `AGENTS.md` missing or a symlink to it | **migrated**: content moves to `AGENTS.md`, `CLAUDE.md` becomes `@AGENTS.md` |
| Both are independent real files                          | **CONFLICT** → ask the user, re-run with `--resolve-conflict claude\|agents` |

Always edit `AGENTS.md`. PROJECT_MEMORY.md is a single real file referenced from it.
Claude Code ≥ 2.1.277 can also read `AGENTS.md` with no `CLAUDE.md` at all, but the docs
note some sessions cannot, so the pointer stays.
```

`SKILL.md:18`：`created CLAUDE.md from template` 改为 `created AGENTS.md from template`，同一行开头的「新目录」后补「（或迁移输出 `migrated:`）」。

`assets/CLAUDE.template.md` 第 1-4 行改为：

```markdown
# {{PROJECT_NAME}} — 项目上下文

> 项目指令与常用命令，供 AI 编码代理按任务需要查阅；Claude Code 经 CLAUDE.md 的 `@AGENTS.md` 导入读到同一份内容。
> 跨会话记忆见 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。
```

`assets/PROJECT_MEMORY.template.md` 第 3 行：`回写约定见 [CLAUDE.md](./CLAUDE.md)` 改为 `回写约定见 [AGENTS.md](./AGENTS.md)`。

**Verify**: `make check` → exit 0；`grep -rn 'symlink' skills/bootstrap-claude/SKILL.md skills/bootstrap-claude/references/` → 只剩 Compatibility 表里描述「替换 / 迁移」symlink 的行；`python3 skills/bootstrap-claude/scripts/test_setup_context.py` → ok（模板标题改动不影响约定块比对）。

### Step 7: 同步 eval 期望

`evals.json`：

- eval 1：`expected_output` 开头 "CLAUDE.md (real) + AGENTS.md (symlink) + PROJECT_MEMORY.md created" 改为 "AGENTS.md (real, source of truth) + CLAUDE.md (one line: `@AGENTS.md`) + PROJECT_MEMORY.md created"；expectations 前两条改为 `"AGENTS.md exists in the project and is a regular file (the source of truth)"`、`"CLAUDE.md exists, is a regular file (not a symlink), and its only content is the line '@AGENTS.md'"`；其余条目里的 "CLAUDE.md" 改为 "AGENTS.md"（`"CLAUDE.md contains all five headings"`、`"CLAUDE.md links to PROJECT_MEMORY.md..."`）。
- eval 2：prompt "(and CLAUDE.md is just a symlink to it)" 改为 "(we never added a CLAUDE.md)"；`expected_output` 中 "CLAUDE.md stays a symlink to AGENTS.md" 改为 "CLAUDE.md is created as the one-line `@AGENTS.md` import"；expectations `"CLAUDE.md is still a symlink pointing at AGENTS.md"` 改为 `"CLAUDE.md exists as a regular file whose only content is '@AGENTS.md' — not a symlink, not a copy"`；最后一条 "...into the CLAUDE.md symlink as a separate file" 改为 "...into CLAUDE.md as a separate copy"。
- eval 3：`"CLAUDE.md (or the source-of-truth context file) 命令 section..."` 改为 `"AGENTS.md (the source-of-truth context file, migrated from the fixture's CLAUDE.md) 命令 section..."`。
- eval 4：`expected_output` 末尾补 "The fixture's CLAUDE.md is migrated: its content now lives in AGENTS.md and CLAUDE.md is the one-line `@AGENTS.md` import."；expectations 里 `"CLAUDE.md's 「项目记忆 (回写约定)」 section..."` 改为 `"AGENTS.md's 「项目记忆 (回写约定)」 section..."`，并新增 `"CLAUDE.md is now a regular file containing only '@AGENTS.md'; no symlink exists"`。

**Verify**: `python3 -I -c "import json; json.load(open('skills/bootstrap-claude/evals/evals.json'))"` → exit 0；`grep -c 'symlink' skills/bootstrap-claude/evals/evals.json` → `0`。

## Test plan

- 迁移后的现有用例：约定块四态 + 新目录创建，证明状态机与新布局无回归。
- 新用例 ×4（Step 5）：Firefox 布局零动作且不报 CONFLICT；旧 symlink 布局迁移且幂等；孤立指针不被覆盖；CONFLICT 退出 2 且 `--resolve-conflict claude` 的内容落到 AGENTS.md。
- 验证：`python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

## Done criteria

- [ ] `python3 skills/bootstrap-claude/scripts/test_setup_context.py` 打印 `test_setup_context: ok`
- [ ] `python3 skills/bootstrap-claude/scripts/test_memory.py` 打印 `test_memory: ok`
- [ ] `grep -n 'os.symlink' skills/bootstrap-claude/scripts/setup_context.py` 无命中
- [ ] `grep -n 'ensure_partner_symlinks\|symlink 一致' skills/bootstrap-claude/scripts/setup_context.py` 无命中
- [ ] 空目录跑脚本：输出含 `created AGENTS.md from template` 与 `pointer: CLAUDE.md -> @AGENTS.md`，`cat CLAUDE.md` 为 `@AGENTS.md`
- [ ] Firefox 布局（任意 AGENTS.md + 内容为 `@AGENTS.md` 的 CLAUDE.md）跑脚本：exit 0，`source of truth: AGENTS.md`，CLAUDE.md 内容不变
- [ ] `grep -c 'symlink' skills/bootstrap-claude/evals/evals.json` → `0`
- [ ] `make check` exit 0
- [ ] `git status --porcelain` 只列出 in-scope 七个文件（加 `plans/README.md`）
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- `ultimate`、`ensure_partner_symlinks`、`cmd_validate` 开头、`main()` 真源判定、argparse 五段与摘录不一致。
- Plan 001 尚未落地（`grep -n SECTION_ALIASES setup_context.py` 无命中）。
- 迁移分支需要删除或覆盖任何**有内容**的真实文件才能通过某个用例：停下汇报。本计划允许的文件操作只有：改名 CLAUDE.md→AGENTS.md、把被淘汰的一方改名为 `.bak`、删除 symlink、写入指针文件、从模板创建缺失的 AGENTS.md。
- 发现需要把 `is_import_pointer` 放宽到多行或任意路径：停下汇报，不要放宽。

## Maintenance notes

- 审阅重点一：`is_import_pointer` 的判定是否足够窄（单行、只认 `AGENTS.md`）。放宽它会让含 `@AGENTS.md` 字样的真实 CLAUDE.md 被当成指针而丢失真源地位。
- 审阅重点二：迁移分支只做 `os.replace`，不写入、不覆盖；旧 symlink 布局里 `AGENTS.md` symlink 先 unlink 再 rename，顺序不能反（否则 `os.replace` 会写穿 symlink）。
- 已初始化的旧项目下次运行脚本会自动迁移并打印 `migrated:`；这是一次性的文件改名，由 Git 记录。SKILL.md 的入口文案已提示这一输出。
- 已推迟：把 `assets/CLAUDE.template.md` 改名为 `AGENTS.template.md`。
- 已推迟：识别 `.claude/CLAUDE.md` 这一合法位置。
- Claude Code 在 `claude-md-and-agents-md` 模式下会跳过已通过导入读过的 AGENTS.md，不会读两遍。
