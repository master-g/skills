# 初始化与兼容

本文中的 `<skill>` 指本技能根目录，所有 scripts/assets 路径均相对该目录。

## Mode 1 — Bootstrap

### Step 1: run the setup script

```bash
python3 <skill>/scripts/setup_context.py --dir <workspace>
```

It ensures the context file has the five required sections and the memory
writeback section from `assets/CLAUDE.template.md`, creates PROJECT_MEMORY.md, and makes AGENTS.md the single source of truth and CLAUDE.md a one-line
`@AGENTS.md` import (migrating a legacy CLAUDE.md-as-real-file layout automatically; see [Compatibility](#compatibility) below). It **never
overwrites** existing real content — it only appends missing sections and prints
exactly what it changed. Read that output so you know which file is the source of
truth and what's still a placeholder.

「项目记忆 (回写约定)」一节的文字归本技能所有，以节末 `<!-- bootstrap-claude convention vN -->`
标记为边界。脚本每次运行都把它和 `assets/CLAUDE.template.md` 比对并按状态处理：缺失就追加；
文字相同但无标记就补标记；有标记或以模板正文开头的块直接升级，标记之后的项目自定义行保留；
无标记且已分叉的旧块只报告 `OUTDATED (legacy)`，加 `--upgrade-convention` 才替换并打印旧文，
被替换掉的自定义行由你补回标记之后；`unmanaged`（只提到 PROJECT_MEMORY 而无该节标题）不改。
升级模板时改正文并把标记版本号加一。

If it exits with a `CONFLICT` (both CLAUDE.md and AGENTS.md are independent real
files with content), the script refuses to guess. Show the user both, ask whose
content should become AGENTS.md, then re-run with `--resolve-conflict claude` or
`--resolve-conflict agents` (the other is backed up as `.bak`, and CLAUDE.md becomes
the one-line import).

### Step 2: fill the sections with real facts

The script leaves `_待填写_` placeholders. An empty skeleton is nearly useless —
the value is in the content. Investigate the repo and replace the placeholders in
the **source-of-truth file** (always `AGENTS.md`; editing the `@AGENTS.md` pointer in
CLAUDE.md does nothing useful). Look for the evidence each section needs:

- **技术栈** — language/framework versions from `package.json`, `pyproject.toml`,
  `go.mod`, `Cargo.toml`, lockfiles, `.tool-versions`, Dockerfiles.
- **导航** — top-level directory layout; the docs maintainers say to read first
  (`ARCHITECTURE.md`, `docs/` entry points, `CONTRIBUTING.md`); existing nested
  instruction files (`find . -name AGENTS.md -o -name CLAUDE.md -not -path './node_modules/*'`);
  any repo-specific search/index tool. A small single-package repo gets one line.
- **命令** — real scripts: `package.json` "scripts", `Makefile`, `justfile`, CI
  workflows, README. Prefer the exact command someone runs to build/test/lint.
- **工作流与陷阱** — CI config for slow steps and build/test variants; `CONTRIBUTING.md`
  and PR templates for approval gates (what needs a human before it runs: push, publish,
  paid CI, production config); scripts that touch shared state. Every entry carries its
  reason — a rule without a reason reads as arbitrary and gets skipped. New repos
  legitimately start with only the approval-gate line; the rest accrues from incidents
  (see 项目记忆维护 → 晋升).
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

### Step 3: validate the result

```bash
python3 <skill>/scripts/setup_context.py --dir <workspace> --validate
```

Read-only. It reports each required section as 已填写 / 占位符 / 空, checks
that CLAUDE.md is the `@AGENTS.md` import of AGENTS.md, and runs the PROJECT_MEMORY.md size gate (`memory.py check`).
Fix every FAIL before calling the bootstrap done — a surviving placeholder
reads as "covered" when it isn't. Exit code 1 means at least one FAIL.

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

### Nested instruction files

Claude Code loads a subdirectory's `CLAUDE.md` / `AGENTS.md` on demand when it reads or
edits a file in that directory, and `.claude/rules/*.md` with a `paths:` frontmatter does
the same by glob. Use them for module-specific commands and gotchas in large repos so the
root stays under 200 lines. List in the root 「导航」 section which directories carry their
own file, and open each child file with one line saying the root still applies
(`../AGENTS.md 仍然适用`). Do **not** run `setup_context.py --dir <subdir>` to make one —
it would lay down a full root skeleton plus a second PROJECT_MEMORY.md. Write the child
file by hand.
