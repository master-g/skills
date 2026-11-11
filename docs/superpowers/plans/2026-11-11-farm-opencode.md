# farm OpenCode Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a documented, configurable OpenCode V2 native-subagent backend to farm.

**Architecture:** Keep farm's six-step flow unchanged. Add an OpenCode backend reference that maps `subagent` startup, completion, final-response recovery, and `sessionID` follow-up, while `pairs` supplies an exact `provider/model[#variant]` reference.

**Tech Stack:** Markdown Agent Skill, Bash preflight, Python 3 standard-library tests, Prettier.

**Spec:** `docs/superpowers/specs/2026-11-11-farm-opencode-design.md`

## Global Constraints

- Follow OpenCode V2 behavior from the official configuration, agents, models, skills, and tools documentation.
- Do not add a hard-coded provider-specific default or silently fall back to a CLI worker.
- Preserve existing backends and farm's independent acceptance gates.
- Use simplified Chinese prose, English identifiers, title-based section links, and Conventional Commits with scope `farm`.

## Review Focus

- A CLI-shaped pair must never be passed as an OpenCode model; the OpenCode reference requires the `opencode:` worker prefix and a complete model reference.
- Missing or unavailable model configuration stops for user selection rather than changing backend.
- Concurrent workers use background calls and retain distinct session IDs; corrections continue the matching session.
- A worker's final response is recovery evidence only, not an acceptance result.
- The installed copy under `~/.claude/skills` must be refreshed after repository validation.

---

### Task 1: Add the OpenCode native worker backend

**Files:**

- Create: `skills/farm/references/opencode-worker.md`
- Modify: `skills/farm/SKILL.md`
- Modify: `skills/farm/pairs`

**Interfaces:**

- Consumes: Existing `preflight.sh` JSON `pairs` entries and OpenCode `subagent` tool.
- Produces: Worker pair values shaped as `opencode:provider/model[#variant]`, plus the four-action OpenCode backend contract.

- [ ] **Step 1: Document the current routing gap**

Confirm that `SKILL.md` has no OpenCode-specific native backend and `pairs` documents only `pi / claude / codex` worker values.

- [ ] **Step 2: Add the OpenCode backend reference**

Document configuration, model availability checks, single and pooled dispatch, background completion, final-response recovery, `sessionID` corrections, permission behavior, and unavailable usage statistics. Include tool-call examples using `general`, an absolute brief path, and the selected full model reference.

- [ ] **Step 3: Route OpenCode sessions to the new reference**

In `SKILL.md`「检测环境与能力」, route sessions with the `subagent` tool to `references/opencode-worker.md`. Preserve the existing Claude Code, App, generic-host, and CLI routes.

- [ ] **Step 4: Extend the pairs configuration documentation**

Explain the `opencode:` worker prefix and full `provider/model[#variant]` syntax. Add only commented examples, including an `opencode:*` entry; do not change active fallback pairs or `preflight.sh`.

- [ ] **Step 5: Verify pair preservation and existing tests**

Run a temporary `FARM_PAIRS` preflight containing `opencode:* = opencode:anthropic/claude-sonnet-5-5#high`, parse its JSON, and assert the worker string is unchanged. Run `python3 skills/farm/test_subagent.py`; expect `test_subagent: ok`.

- [ ] **Step 6: Validate documentation and formatting**

Run `npx prettier --write` on the changed Markdown files, then `make check`; expect both to succeed with valid relative links and title-based section references.

### Task 2: Install and commit the validated skill

**Files:**

- Modify locally: `~/.claude/skills/farm/` through the repository Makefile
- Commit: Task 1 files and this plan/spec

**Interfaces:**

- Consumes: Validated Task 1 working tree.
- Produces: An updated local farm installation and one commit on `main`.

- [ ] **Step 1: Inspect the final diff**

Run `git diff --check` and review `git diff`; confirm only the approved farm documents and plan/spec changed.

- [ ] **Step 2: Refresh the local installation**

Run `make install SKILL=farm SOURCE=.` so future OpenCode sessions load the updated skill rather than the stale copy.

- [ ] **Step 3: Commit without pushing**

Stage the approved files and commit as `feat(farm): add OpenCode native worker backend`. Confirm `git status --short` is clean; do not push.
