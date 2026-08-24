#!/usr/bin/env python3
"""Bootstrap & reconcile a project's Claude context files.

Idempotent — safe to run on every invocation. It guarantees that:
  1. A single *source-of-truth* context file exists with the five required
     sections (技术栈 / 命令 / 代码风格 / 禁止文件 / 审查规则), the 启动流程 /
     完成判定 boilerplate sections, plus a PROJECT_MEMORY writeback section.
  2. Both CLAUDE.md (Claude Code) and AGENTS.md (other agents) resolve to that
     same content — whichever isn't the real file becomes a symlink to it.
  3. PROJECT_MEMORY.md exists with its four sections.

Compatibility rules (from the user's spec), resolved automatically:
  - AGENTS.md is a real file and CLAUDE.md is a symlink  -> truth = AGENTS.md
  - No AGENTS.md (CLAUDE.md is/becomes the real file)    -> symlink AGENTS.md -> CLAUDE.md
  - Only AGENTS.md exists                                -> symlink CLAUDE.md -> AGENTS.md
  - Neither exists                                       -> create CLAUDE.md, symlink AGENTS.md -> CLAUDE.md
  - Both are independent real files                      -> CONFLICT, refuse unless --resolve-conflict given

Existing real files are never overwritten — missing sections are appended,
present content is left untouched.
"""
import argparse
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent / "assets"
REQUIRED_SECTIONS = ["技术栈", "命令", "代码风格", "禁止文件", "审查规则"]
PLACEHOLDER = "_待填写_"

# Boilerplate sections appended with full content (no placeholder to fill) when
# missing — like the 项目记忆 block. Keep in sync with CLAUDE.template.md.
BOILERPLATE_SECTIONS = {
    "启动流程": (
        "\n## 启动流程\n"
        "1. 读完本文件。\n"
        "2. 读 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md) 的「上次会话」与「下次运行」。\n"
        "3. 运行「命令」一节的测试命令,确认基线通过;基线失败时先修复基线,再开始新任务。\n"
        "4. 运行 `git log --oneline -5`,查看最近改动。\n"
    ),
    "完成判定": (
        "\n## 完成判定\n"
        "同时满足以下各项才算完成:\n"
        "- 目标行为已实现。\n"
        "- 「命令」一节的验证命令实际运行过并通过。\n"
        "- 验证命令与结果已回写到 PROJECT_MEMORY.md「上次会话」。\n"
        "- 跳过的步骤与未验证的边界已明确说出。\n"
    ),
}


def load_template(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


def ultimate(p: Path):
    """The real file `p` resolves to (following symlinks), or None if it is
    missing, dangling, or not a regular file."""
    try:
        rp = p.resolve()
    except OSError:
        return None
    return rp if rp.is_file() else None


def heading_present(text: str, keyword: str) -> bool:
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("#") and keyword in s:
            return True
    return False


def render(template_name: str, project_name: str) -> str:
    return load_template(template_name).replace("{{PROJECT_NAME}}", project_name)


def make_symlink(link: Path, target_name: str, actions: list):
    """Point `link` at sibling `target_name`, replacing any existing symlink."""
    if link.is_symlink() or (not link.exists() and link.is_symlink()):
        link.unlink()
    elif link.exists():
        # A real file here would be the CONFLICT case, handled before we get
        # here. Guard anyway so we never clobber real content.
        return
    os.symlink(target_name, link)
    actions.append(f"symlink: {link.name} -> {target_name}")


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


def ensure_sections(truth: Path, project_name: str, actions: list):
    """Ensure the truth file has the five required sections + memory link.
    Empty file -> full template. Non-empty -> append only what's missing."""
    text = truth.read_text(encoding="utf-8") if truth.exists() else ""
    if not text.strip():
        truth.write_text(render("CLAUDE.template.md", project_name), encoding="utf-8")
        actions.append(f"wrote template into {truth.name} (was empty)")
        return

    appended = []
    additions = []
    for section in REQUIRED_SECTIONS:
        if not heading_present(text, section):
            additions.append(f"\n## {section}\n- {PLACEHOLDER}\n")
            appended.append(section)
    for section, block in BOILERPLATE_SECTIONS.items():
        if not heading_present(text, section):
            additions.append(block)
            appended.append(section)
    if "PROJECT_MEMORY.md" not in text:
        additions.append(
            "\n## 项目记忆 (回写约定)\n"
            "跨会话的持久信息记录在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。\n"
            "**完成每个重要任务后务必回写**: 把确认的决策写入「已验证的事实」、"
            "踩的坑写入「失败尝试」、用进展更新「上次会话」、把计划写入「下次运行」。\n"
            "保持 PROJECT_MEMORY.md 在 300~400 行,超长时用 `scripts/memory.py compact` "
            "压缩(保留事实与计划,淘汰最旧日志)。\n"
        )
        appended.append("项目记忆")
    if additions:
        if not text.endswith("\n"):
            text += "\n"
        truth.write_text(text + "".join(additions), encoding="utf-8")
        actions.append(f"appended missing sections to {truth.name}: {', '.join(appended)}")
    else:
        actions.append(f"{truth.name} already has all required sections (left untouched)")


def ensure_memory(root: Path, project_name: str, actions: list):
    memory = root / "PROJECT_MEMORY.md"
    if ultimate(memory) is None:
        if memory.is_symlink():
            memory.unlink()
        memory.write_text(render("PROJECT_MEMORY.template.md", project_name), encoding="utf-8")
        actions.append("created PROJECT_MEMORY.md")
    else:
        actions.append("PROJECT_MEMORY.md already exists (left untouched)")


def section_bodies(text: str) -> dict:
    """Map each `## ` section title -> its body lines (deeper headings included)."""
    bodies, current = {}, None
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and len(m.group(1)) == 2:
            current = m.group(2).strip()
            bodies[current] = []
            continue
        if m and len(m.group(1)) == 1:
            current = None
            continue
        if current is not None:
            bodies[current].append(line)
    return bodies


def section_state(body: list) -> str:
    """'已填写' | '占位符' | '空'. HTML comment lines are hints, not content."""
    content = [l for l in body if l.strip() and not l.strip().startswith("<!--")]
    if not content:
        return "空"
    if all(PLACEHOLDER in l for l in content):
        return "占位符"
    return "已填写"


def cmd_validate(root: Path, max_lines: int) -> int:
    """Read-only quality check. Returns the number of FAILs."""
    checks = []  # (ok: bool, message: str)
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

    if truth is not None:
        text = truth.read_text(encoding="utf-8")
        bodies = section_bodies(text)
        for section in REQUIRED_SECTIONS:
            if section not in bodies:
                checks.append((False, f"{section}: 缺失"))
            else:
                state = section_state(bodies[section])
                checks.append((state == "已填写", f"{section}: {state}"))
        for section in BOILERPLATE_SECTIONS:
            checks.append((section in bodies, f"{section}: {'存在' if section in bodies else '缺失'}"))
        checks.append(("PROJECT_MEMORY.md" in text, "项目记忆回写约定: "
                       + ("存在" if "PROJECT_MEMORY.md" in text else "缺失")))

    memory = root / "PROJECT_MEMORY.md"
    if ultimate(memory) is None:
        checks.append((False, "PROJECT_MEMORY.md: 缺失"))
    else:
        n = len(memory.read_text(encoding="utf-8").rstrip("\n").split("\n"))
        checks.append((n <= max_lines, f"PROJECT_MEMORY.md: {n} 行 (max {max_lines})"))

    fails = sum(1 for ok, _ in checks if not ok)
    print(f"validate: {root}")
    for ok, msg in checks:
        print(f"  {'PASS' if ok else 'FAIL'} {msg}")
    print(f"result: {fails} FAIL" if fails else "result: all PASS")
    return fails


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=".", help="workspace directory (default: cwd)")
    ap.add_argument("--project-name", default=None,
                    help="name used in templates (default: directory name)")
    ap.add_argument("--resolve-conflict", choices=["claude", "agents"], default=None,
                    help="when both CLAUDE.md and AGENTS.md are independent real "
                         "files, pick which becomes the source of truth; the other "
                         "is backed up to *.bak and replaced with a symlink")
    ap.add_argument("--validate", action="store_true",
                    help="read-only quality check: section fill state, symlink "
                         "consistency, PROJECT_MEMORY.md length; exits 1 on any FAIL")
    ap.add_argument("--max", type=int, default=400,
                    help="PROJECT_MEMORY.md line limit used by --validate (default 400)")
    args = ap.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        sys.exit(1)
    if args.validate:
        sys.exit(1 if cmd_validate(root, args.max) else 0)
    project_name = args.project_name or root.name
    claude = root / "CLAUDE.md"
    agents = root / "AGENTS.md"
    actions: list = []

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
    ensure_memory(root, project_name, actions)

    print(f"source of truth: {truth.name}")
    for a in actions:
        print(f"  - {a}")


if __name__ == "__main__":
    main()
