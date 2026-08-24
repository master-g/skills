---
name: bootstrap-claude
license: MIT
description: >-
  Bootstrap and maintain a project's Claude/AI-agent context files. Use this
  skill whenever the user wants to initialize or set up a workspace for Claude —
  creating or repairing CLAUDE.md (技术栈/命令/代码风格/禁止文件/审查规则) and
  PROJECT_MEMORY.md (已验证的事实/失败尝试/上次会话/下次运行) — even if they only
  say "set up this repo", "init CLAUDE.md", "bootstrap the project", "给这个项目加上下文",
  or "初始化 Claude 配置". ALSO use it at the END of a task to write progress back into
  PROJECT_MEMORY.md and keep it within 300–400 lines, and whenever an AGENTS.md /
  CLAUDE.md symlink needs to be created or reconciled. Trigger proactively when a
  workspace has no CLAUDE.md, or when the user mentions project memory, cross-session
  context, or recording what was done / what's next.
---

# bootstrap-claude

Give a project two files that let any Claude session pick up where the last one
left off:

- **CLAUDE.md** — the context an agent reads at the *start* of a session: how to
  build, test, and behave in this repo.
- **PROJECT_MEMORY.md** — what previous sessions *learned*: confirmed facts, dead
  ends, where things stopped, what's next.

The skill has two modes. They're not separate commands — read the situation and
do whichever fits (often both in one go).

| Mode | When | What you do |
| --- | --- | --- |
| **Bootstrap** | Files missing, or user asks to "set up / init" the project | Run `setup_context.py`, then fill the sections with real project facts |
| **Maintain** | Finishing a task, or user says "record what we did / update memory" | Append entries to PROJECT_MEMORY.md, then compact if it's grown too long |

`setup_context.py` is idempotent, so it's safe to run at the start of either mode.

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

The template also carries two boilerplate sections — **启动流程** (the fixed
session-start sequence) and **完成判定** (the checklist that gates any "done"
claim). They need no filling; leave them in place like the 项目记忆 section.

### Step 3: validate the result

```bash
python3 <skill>/scripts/setup_context.py --dir <workspace> --validate
```

Read-only. It reports each required section as 已填写 / 占位符 / 空, checks
CLAUDE.md/AGENTS.md link consistency, and checks PROJECT_MEMORY.md's length.
Fix every FAIL before calling the bootstrap done — a surviving placeholder
reads as "covered" when it isn't. Exit code 1 means at least one FAIL.

## Mode 2 — Maintain (write back after a task)

This is what makes the memory compound. After finishing a meaningful chunk of
work, update PROJECT_MEMORY.md so the next session starts informed. Add entries to
the right section — newest goes at the **bottom**, each line prefixed with today's
date so the compactor can age them out:

```bash
python3 <skill>/scripts/memory.py add <workspace>/PROJECT_MEMORY.md \
  --section "失败尝试" --text "试过用 X 做 Y,因为 Z 放弃,改用 W"
```

(`add` stamps today's date automatically; pass `--date YYYY-MM-DD` to override.
You can also just edit the file directly using the same `- [date] …` format.)

Where each kind of note goes:

- **已验证的事实** — a decision or constraint you *confirmed* this session ("auth
  uses JWT in cookies, not headers"). Long-lived; survives compaction.
- **失败尝试** — a path that didn't work and *why*, so nobody re-walks it.
- **上次会话** — what this session actually did and where it stopped.
- **下次运行** — the plan / priorities for next time. Long-lived; survives compaction.

Write the *why*, not just the *what* — "switched to esbuild (webpack OOM'd on the
CI runner)" is worth keeping; "changed bundler" isn't.

Two more rules for what goes in:

- **Exclude derivable content** — architecture, code structure, and anything
  re-derivable from the repo or git history doesn't belong in memory. It stales
  fast and crowds out what only sessions know.
- **上次会话 entries carry evidence** — record the branch/commit you stopped at
  and the verification command with its actual result ("make test 通过" /
  "npm test 失败于 X"), not just a prose summary of the work.

### Keep it under 300–400 lines

A memory file that grows forever stops being read. After adding entries, check the
length and compact if needed:

```bash
python3 <skill>/scripts/memory.py status  <workspace>/PROJECT_MEMORY.md
python3 <skill>/scripts/memory.py compact <workspace>/PROJECT_MEMORY.md
```

`compact` only acts when the file exceeds `--max` (default 400). It evicts the
oldest entries from the **non-protected** sections — **上次会话** first, then
**失败尝试** — until the file is back under `--target` (default 350). It **keeps**
**已验证的事实** and **下次运行** untouched, because confirmed facts and the forward
plan are the parts you can't reconstruct. Every evicted entry is printed, so
nothing disappears silently — if something evicted still matters, promote its
lesson into 已验证的事实 before it ages out.

If compaction can't get under the limit because the protected sections are
themselves huge, the script says so loudly. That's a signal to summarize
已验证的事实 by hand — collapse ten narrow facts into three general ones.

## Compatibility

Many tools read `AGENTS.md`; Claude Code reads `CLAUDE.md`. To serve both without
maintaining two copies, the skill keeps **one real file** and makes the other a
symlink to it. `setup_context.py` resolves this automatically:

| Situation | Source of truth | Other file |
| --- | --- | --- |
| Neither exists | `CLAUDE.md` (created) | `AGENTS.md` → symlink to CLAUDE.md |
| Only `CLAUDE.md` (real) | `CLAUDE.md` | `AGENTS.md` → symlink to CLAUDE.md |
| Only `AGENTS.md` (real) | `AGENTS.md` | `CLAUDE.md` → symlink to AGENTS.md |
| `AGENTS.md` real + `CLAUDE.md` already a symlink | `AGENTS.md` | left as-is |
| Both already point to the same file | that file | left as-is |
| Both are independent real files | — | **CONFLICT** → ask the user, use `--resolve-conflict` |

The rule of thumb: **edit whichever file the script reports as the source of
truth.** Editing the symlink works too (it writes through), but knowing which is
real prevents confusion. PROJECT_MEMORY.md is always a single real file referenced
from the context file.

## Wiring memory into CLAUDE.md

The bootstrap step writes a **项目记忆 (回写约定)** section into the context file.
That section is what makes future sessions self-maintain: it tells them to read
PROJECT_MEMORY.md at the start and write back at the end. Leave that section in
place — it's the contract that keeps the loop going.

## Files

- `scripts/setup_context.py` — idempotent bootstrap + CLAUDE.md/AGENTS.md reconciliation; `--validate` for the read-only quality check
- `scripts/memory.py` — `status` / `compact` / `add` for PROJECT_MEMORY.md
- `assets/CLAUDE.template.md`, `assets/PROJECT_MEMORY.template.md` — the skeletons
