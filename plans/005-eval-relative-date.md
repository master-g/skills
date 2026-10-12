# Plan 005: eval 3 的「今天」不再写死为 2026-06-18

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 547eeac..HEAD -- skills/bootstrap-claude/evals/evals.json`
> Plan 002/003 会改 eval 2 与 eval 4 的条目；只对照 id 为 3 的条目。若 id 3 已无 `2026-06-18`，本计划已被独立完成，标记 DONE 并汇报。

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none（与 002/003 改同一文件的不同条目，任何顺序都行）
- **Category**: tests
- **Planned at**: commit `547eeac`, 2026-10-12

## Why this matters

`evals/evals.json` 的 eval 3（`writeback`）要求新写入的记忆条目「带今天的日期 2026-06-18」。eval 由 agent 在运行当天执行，`memory.py add` 自动写当天日期，所以除 2026-06-18 那一天外，这条 eval 永远判失败，评审也无法区分「日期格式错」和「日期不是那个写死的值」。改成相对表述即可。

## Current state

- `skills/bootstrap-claude/evals/evals.json` —— 四个 eval 的 JSON；id 3 在第 37-50 行。

摘录：

```json
// evals.json:42 (expected_output, 节选)
"... Entries are dated with today's date (2026-06-18) in the - [YYYY-MM-DD] format and appended without destroying the existing entries. ..."
// evals.json:47 (expectations[2])
"The new entry carries today's date 2026-06-18",
```

`memory.py add` 的日期来源（`scripts/memory.py`，`add` 子命令）：默认 `datetime.date.today()`，`--date` 可覆盖。`references/maintain.md` 第 36 行也写明「`add` 自动加当天日期」。

## Commands you will need

| Purpose        | Command                                                                                    | Expected on success |
| -------------- | ------------------------------------------------------------------------------------------ | ------------------- |
| JSON 合法性    | `python3 -I -c "import json; json.load(open('skills/bootstrap-claude/evals/evals.json'))"` | 无输出，exit 0      |
| 写死日期已清除 | `grep -c '2026-06-18' skills/bootstrap-claude/evals/evals.json`                            | `0`                 |

## Scope

**In scope**:

- `skills/bootstrap-claude/evals/evals.json`（仅 id 为 3 的条目）

**Out of scope**:

- `evals/files/py-lib/PROJECT_MEMORY.md` 夹具里已有条目的日期 —— 那是历史数据，不是「今天」。
- 其他三个 eval。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `bootstrap-claude`。示例：`fix(bootstrap-claude): eval 3 expects the run date, not a hard-coded 2026-06-18`。
- 未经操作者指示不要提交、不要推送。

## Steps

### Step 1: 改两处文字

id 3 条目：

- `expected_output` 中 `today's date (2026-06-18)` 改为 `the date the eval is run (today's date)`。
- `expectations` 中 `"The new entry carries today's date 2026-06-18"` 改为 `"The new entry carries the date the eval was run (today's date) in [YYYY-MM-DD] form — not a stale, invented, or copied date"`。

**Verify**: `python3 -I -c "import json; json.load(open('skills/bootstrap-claude/evals/evals.json'))"` → exit 0；`grep -c '2026-06-18' skills/bootstrap-claude/evals/evals.json` → `0`。

## Test plan

- 没有自动化测试覆盖 evals.json；验证即 JSON 合法 + 写死日期为 0 处。

## Done criteria

- [ ] `grep -c '2026-06-18' skills/bootstrap-claude/evals/evals.json` → `0`
- [ ] JSON 可被 `json.load` 解析
- [ ] `git status --porcelain` 只列出 `skills/bootstrap-claude/evals/evals.json`（加 `plans/README.md`）
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- id 3 条目的文字与摘录不一致且不含 `2026-06-18`（已被别人修过）。

## Maintenance notes

- 以后写 eval 期望时，凡涉及「今天」「当前分支」「本机路径」一律用相对表述；评审 agent 在运行时解析。
