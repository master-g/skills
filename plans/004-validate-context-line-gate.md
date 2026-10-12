# Plan 004: `--validate` 对上下文文件加 200 行门禁

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 547eeac..HEAD -- skills/bootstrap-claude/scripts/setup_context.py skills/bootstrap-claude/scripts/test_setup_context.py skills/bootstrap-claude/references/bootstrap.md`
> Plan 001–003 应已落地，这三个文件会有差异；对照时只看下面摘录的 `cmd_validate` 签名与开头、`main()` 的 argparse 段、`bootstrap.md` Step 3 段。

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: plans/002-import-pointer-compat.md（同样改 `cmd_validate`，排在其后避免冲突）
- **Category**: dx
- **Planned at**: commit `547eeac`, 2026-10-12

## Why this matters

Claude Code 官方 memory 文档写明：单个 CLAUDE.md 目标控制在 200 行内，超长会消耗上下文并降低遵循度，应把只对部分代码有效的指令移到路径作用域规则里。技能对 PROJECT_MEMORY.md 有 24 KB 的字节门禁，对上下文文件本身却没有任何体量检查，`--validate` 对一个 800 行的 CLAUDE.md 也会报 all PASS。Firefox 的根文件是 73 行，模板满填后约 60 行，200 行是宽裕的上限。本计划给 `--validate` 加一条行数检查，默认 200，可用 `--max-lines` 覆盖。

## Current state

- `skills/bootstrap-claude/scripts/setup_context.py` —— `cmd_validate(root, max_bytes)` 做只读校验；`main()` 的 argparse 已有 `--max-bytes`。
- `skills/bootstrap-claude/scripts/memory.py:28-29` —— 门槛常量的先例：

```python
DEFAULT_MAX_BYTES = 24000   # ~8k tokens of mixed zh/en; sisyphus was at 150k
DEFAULT_MAX_LINE = 300      # chars; median line in the worst files was 350+
```

`setup_context.py` 摘录（行号按 `547eeac`，Plan 001/002 之后会偏移，按符号找）：

```python
# :252-253
def cmd_validate(root: Path, max_bytes: int) -> int:
    """Read-only quality check. Returns the number of FAILs."""
...
# :274-275
    if truth is not None:
        text = truth.read_text(encoding="utf-8")
...
# :314-318
    ap.add_argument("--validate", action="store_true",
                    help="read-only quality check: section fill state, symlink "
                         "consistency, PROJECT_MEMORY.md size gate; exits 1 on any FAIL")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES,
                    help=f"PROJECT_MEMORY.md byte limit used by --validate (default {DEFAULT_MAX_BYTES})")
...
# :324
    if args.validate:
        sys.exit(1 if cmd_validate(root, args.max_bytes) else 0)
```

`bootstrap.md` Step 3（第 56-65 行）描述 `--validate` 检查什么：「reports each required section as 已填写 / 占位符 / 空, checks CLAUDE.md/AGENTS.md link consistency, and runs the PROJECT_MEMORY.md size gate」。

校验结果的格式是 `checks.append((ok: bool, message: str))`，PASS/FAIL 文案中文。

## Commands you will need

| Purpose      | Command                                                         | Expected on success      |
| ------------ | --------------------------------------------------------------- | ------------------------ |
| 脚本测试     | `python3 skills/bootstrap-claude/scripts/test_setup_context.py` | `test_setup_context: ok` |
| 文档链接检查 | `make check`                                                    | exit 0                   |

## Scope

**In scope**:

- `skills/bootstrap-claude/scripts/setup_context.py`
- `skills/bootstrap-claude/scripts/test_setup_context.py`
- `skills/bootstrap-claude/references/bootstrap.md`（仅 Step 3 一句）

**Out of scope**:

- `memory.py` —— 记忆文件门槛不动。
- 把行数检查加进非 `--validate` 的默认运行输出 —— 默认运行只报告自己做了什么。
- 统计 `@import` 进来的文件或子目录文件的行数 —— 只量真源文件本身。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `bootstrap-claude`。示例：`feat(bootstrap-claude): validate gates the context file at 200 lines`。
- 未经操作者指示不要提交、不要推送。

## Steps

### Step 1: 加常量与参数

在 `setup_context.py` 顶部常量区（`PLACEHOLDER = "_待填写_"` 附近）加：

```python
DEFAULT_MAX_LINES = 200  # Claude Code docs: keep each CLAUDE.md under ~200 lines; longer files lower adherence
```

argparse 加：

```python
    ap.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES,
                    help=f"context file line limit used by --validate (default {DEFAULT_MAX_LINES})")
```

`--validate` 的 help 文案改为 `"read-only quality check: section fill state, pointer consistency, context file line gate, PROJECT_MEMORY.md size gate; exits 1 on any FAIL"`。

调用处改为 `cmd_validate(root, args.max_bytes, args.max_lines)`，签名改为 `def cmd_validate(root: Path, max_bytes: int, max_lines: int = DEFAULT_MAX_LINES) -> int:`。

**Verify**: `python3 -m py_compile skills/bootstrap-claude/scripts/setup_context.py` → exit 0。

### Step 2: 加检查

在 `cmd_validate` 里 `text = truth.read_text(encoding="utf-8")` 之后、章节检查之前插入：

```python
        n_lines = len(text.splitlines())
        checks.append((n_lines <= max_lines,
                       f"{truth.name}: {n_lines} 行 (max {max_lines}；超长降低遵循度，模块专属内容移到子目录文件或 .claude/rules/)"))
```

**Verify**: 对任意已初始化目录跑 `--validate`，输出含一行 `PASS AGENTS.md: N 行 (max 200；…)`。

### Step 3: 测试

`test_setup_context.py` 末尾 `print(...)` 前追加：

```python
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # line gate: a ~290-line context file (250 filler + BASE + appended convention block)
    # FAILs validate at the default 200 and passes with --max-lines 400
    f.write_text(BASE + "".join(f"- filler {i}\n" for i in range(250)))
    run(d)
    v = run(d, "--validate"); assert "FAIL AGENTS.md:" in v and "行 (max 200" in v, v
    v = run(d, "--validate", "--max-lines", "400"); assert "PASS AGENTS.md:" in v, v
```

Plan 002 之后 AGENTS.md 是真源，所以直接写 AGENTS.md；`--max-lines 400` 留足余量，避免 PASS 分支贴着边界。

**Verify**: `python3 skills/bootstrap-claude/scripts/test_setup_context.py` → `test_setup_context: ok`。

### Step 4: 文档

`bootstrap.md` Step 3 的描述句改为：「It reports each required section as 已填写 / 占位符 / 空, checks CLAUDE.md/AGENTS.md pointer consistency, gates the context file at 200 lines (`--max-lines` to override; move module-specific material into nested files or `.claude/rules/`, see Nested instruction files), and runs the PROJECT_MEMORY.md size gate (`memory.py check`).」

**Verify**: `make check` → exit 0。

## Test plan

- 新用例（Step 3）：约 290 行文件默认 FAIL、`--max-lines 400` PASS。
- 现有用例全部通过（它们的文件都远小于 200 行，新增的 PASS 行不影响任何断言）。

## Done criteria

- [ ] `python3 skills/bootstrap-claude/scripts/test_setup_context.py` 打印 `test_setup_context: ok`
- [ ] `grep -n 'DEFAULT_MAX_LINES' skills/bootstrap-claude/scripts/setup_context.py` ≥ 3 处
- [ ] `python3 skills/bootstrap-claude/scripts/setup_context.py --help | grep -c 'max-lines'` → ≥ 1
- [ ] `make check` exit 0
- [ ] `git status --porcelain` 只列出 in-scope 三个文件（加 `plans/README.md`）
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- `cmd_validate` 不再接受 `max_bytes` 位置参数，或 `main()` 里没有 `--max-bytes`（说明结构被别的计划改了，先对照）。
- 现有用例在 Step 2 之后失败：新增的 PASS 行不该影响任何断言，若影响则停下汇报。

## Maintenance notes

- 门槛是行数不是字节：官方文档以行为单位给建议，且上下文文件是中英混排、行长差异大，字节门槛会误伤。
- 若将来支持 `.claude/CLAUDE.md` 或嵌套文件，行数应逐文件分别检查，不要加总。
- 已推迟：对 `@import` 链上文件求和。导入文件同样在启动时加载，理论上该算；等有真实超限案例再做。
