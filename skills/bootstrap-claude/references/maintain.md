# 项目记忆维护

本文中的 `<skill>` 指本技能根目录。仅维护已选定的项目记忆，不因任务结束初始化整套上下文。

## Mode 2 — Maintain (write back after a task)

Use this mode when the user requests memory maintenance or an existing project
policy authorizes it. Update PROJECT_MEMORY.md with durable session findings. Add entries to
the right section — newest goes at the **bottom**, each line prefixed with today's
date so the compactor can age them out:

```bash
python3 <skill>/scripts/memory.py add <workspace>/PROJECT_MEMORY.md \
  --section "失败尝试" --text "试过用 X 做 Y,因为 Z 放弃,改用 W"
```

(`add` stamps today's date automatically; pass `--date YYYY-MM-DD` to override.
You can also just edit the file directly using the same `- [date] …` format.)

Where each kind of note goes:

- **已验证的事实** — a decision or constraint you _confirmed_ this session ("auth
  uses JWT in cookies, not headers"). Long-lived; survives compaction.
- **失败尝试** — a path that didn't work and _why_, so nobody re-walks it.
- **上次会话** — what this session actually did and where it stopped.
- **下次运行** — the plan / priorities for next time. Long-lived; survives compaction.

Write the _why_, not just the _what_ — "switched to esbuild (webpack OOM'd on the
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
