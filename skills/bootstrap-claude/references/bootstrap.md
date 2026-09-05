# 初始化与兼容

本文中的 `<skill>` 指本技能根目录，所有 scripts/assets 路径均相对该目录。

## Mode 1 — Bootstrap

### Step 1: run the setup script

```bash
python3 <skill>/scripts/setup_context.py --dir <workspace>
```

It ensures the context file has all five required sections, creates
PROJECT_MEMORY.md, and reconciles the CLAUDE.md / AGENTS.md naming so both point
at one source of truth (see [Compatibility](#compatibility) below). It **never
overwrites** existing real content — it only appends missing sections and prints
exactly what it changed. Read that output so you know which file is the source of
truth and what's still a placeholder.

If it exits with a `CONFLICT` (both CLAUDE.md and AGENTS.md are independent real
files), don't force it — show the user both and ask which should win, then re-run
with `--resolve-conflict claude` or `--resolve-conflict agents`.

### Step 2: fill the sections with real facts

The script leaves `_待填写_` placeholders. An empty skeleton is nearly useless —
the value is in the content. Investigate the repo and replace the placeholders in
the **source-of-truth file** (the one the script reported — edit that, not the
symlink). Look for the evidence each section needs:

- **技术栈** — language/framework versions from `package.json`, `pyproject.toml`,
  `go.mod`, `Cargo.toml`, lockfiles, `.tool-versions`, Dockerfiles.
- **命令** — real scripts: `package.json` "scripts", `Makefile`, `justfile`, CI
  workflows, README. Prefer the exact command someone runs to build/test/lint.
- **代码风格** — linter/formatter configs (eslint, prettier, ruff, gofmt),
  `.editorconfig`, plus conventions you can see in the existing code.
- **禁止文件** — generated output, lockfiles, vendored deps, secrets, migration
  history, anything a `.gitignore` or build step owns. Files an agent must not hand-edit.
- **审查规则** — `CONTRIBUTING.md`, PR templates, `CODEOWNERS`, required CI checks,
  commit-message conventions.

If a section genuinely has no answer yet (e.g., no tests exist), say so explicitly
rather than leaving a bare placeholder — `- 暂无测试 (待补充)` tells the next session
something true. Silent placeholders read as "covered" when they aren't.

Don't invent commands you haven't verified. If unsure whether `npm test` works,
check that it's defined before writing it down.

The template also carries **启动流程** and **完成判定**. Read relevant context
and run checks proportional to the requested change. Existing unrelated baseline
failures are recorded, not automatically repaired. Preserve project-specific
policies; do not silently replace existing sections during bootstrap.

### Step 3: validate the result

```bash
python3 <skill>/scripts/setup_context.py --dir <workspace> --validate
```

Read-only. It reports each required section as 已填写 / 占位符 / 空, checks
CLAUDE.md/AGENTS.md link consistency, and checks PROJECT_MEMORY.md's length.
Fix every FAIL before calling the bootstrap done — a surviving placeholder
reads as "covered" when it isn't. Exit code 1 means at least one FAIL.

## Compatibility

Many tools read `AGENTS.md`; Claude Code reads `CLAUDE.md`. To serve both without
maintaining two copies, the skill keeps **one real file** and makes the other a
symlink to it. `setup_context.py` resolves this automatically:

| Situation                                        | Source of truth       | Other file                                            |
| ------------------------------------------------ | --------------------- | ----------------------------------------------------- |
| Neither exists                                   | `CLAUDE.md` (created) | `AGENTS.md` → symlink to CLAUDE.md                    |
| Only `CLAUDE.md` (real)                          | `CLAUDE.md`           | `AGENTS.md` → symlink to CLAUDE.md                    |
| Only `AGENTS.md` (real)                          | `AGENTS.md`           | `CLAUDE.md` → symlink to AGENTS.md                    |
| `AGENTS.md` real + `CLAUDE.md` already a symlink | `AGENTS.md`           | left as-is                                            |
| Both already point to the same file              | that file             | left as-is                                            |
| Both are independent real files                  | —                     | **CONFLICT** → ask the user, use `--resolve-conflict` |

The rule of thumb: **edit whichever file the script reports as the source of
truth.** Editing the symlink works too (it writes through), but knowing which is
real prevents confusion. PROJECT_MEMORY.md is always a single real file referenced
from the context file.
