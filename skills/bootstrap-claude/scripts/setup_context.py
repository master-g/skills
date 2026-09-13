#!/usr/bin/env python3
"""Bootstrap & reconcile a project's Claude context files.

Idempotent — safe to run on every invocation. It guarantees that:
  1. A single *source-of-truth* context file exists with every `## ` section
     of assets/CLAUDE.template.md (the template is the only place section text
     lives); the five REQUIRED_SECTIONS must be filled with real facts.
  2. Both CLAUDE.md (Claude Code) and AGENTS.md (other agents) resolve to that
     same content — whichever isn't the real file becomes a symlink to it.
  3. PROJECT_MEMORY.md exists with its four sections.
  4. The 「项目记忆 (回写约定)」 block matches the template (the skill owns that text):
     missing -> appended; same text -> end marker added; bounded/prefixed block -> upgraded
     losslessly; a diverged legacy block -> reported, replaced only with --upgrade-convention.

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
sys.path.insert(0, str(SCRIPT_DIR))
from memory import check_memory, DEFAULT_MAX_BYTES  # noqa: E402
ASSETS = SCRIPT_DIR.parent / "assets"
REQUIRED_SECTIONS = ["技术栈", "命令", "代码风格", "禁止文件", "审查规则"]
PLACEHOLDER = "_待填写_"

MEMORY_LINK = "PROJECT_MEMORY.md"
CONV_HEADING_RE = re.compile(r"^##\s+.*(项目记忆|回写约定).*$", re.M)
CONV_MARKER_RE = re.compile(r"^<!-- bootstrap-claude convention v\d+ -->[ \t]*$", re.M)


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


def template_sections() -> dict:
    """Ordered {title: block} for every `## ` section of CLAUDE.template.md.
    The template is the single source of truth for section text."""
    blocks, title, buf = {}, None, []
    for line in load_template("CLAUDE.template.md").splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            if title:
                blocks[title] = "\n".join(buf).rstrip("\n") + "\n"
            title, buf = m.group(1).strip(), [line]
        elif title:
            buf.append(line)
    if title:
        blocks[title] = "\n".join(buf).rstrip("\n") + "\n"
    return blocks


def section_present(text: str, title: str) -> bool:
    """The memory-writeback section is identified by its link, others by heading keyword."""
    if MEMORY_LINK in title or "项目记忆" in title:
        return MEMORY_LINK in text
    return heading_present(text, title)


def template_convention() -> str:
    """The skill-owned writeback block: heading line through the end marker."""
    for title, block in template_sections().items():
        if "项目记忆" in title or "回写约定" in title:
            return block
    raise RuntimeError("CLAUDE.template.md has no 项目记忆 section")


def _norm_body(block: str) -> str:
    lines = block.split("\n")[1:]  # drop heading; marker lines are boundary, not content
    lines = [l.rstrip() for l in lines if not CONV_MARKER_RE.match(l)]
    return "\n".join(lines).strip("\n")


def convention_state(text: str) -> dict:
    """{state, start, end, marked}. state in
    missing   - no memory link and no heading: append the block
    unmanaged - memory link present but no writeback heading: report only
    latest    - body equals the template
    outdated  - body differs; marked=True means the block is bounded by the end
                marker (lossless auto-upgrade), else legacy (whole section)"""
    m = CONV_HEADING_RE.search(text)
    if not m:
        return {"state": "unmanaged" if MEMORY_LINK in text else "missing"}
    start = m.start()
    after = text[m.end():]
    mk = CONV_MARKER_RE.search(after)
    nh = re.search(r"^## ", after, re.M)
    if mk and (not nh or mk.start() < nh.start()):
        end, marked = m.end() + mk.end(), True
    else:
        end, marked = (m.end() + nh.start()) if nh else len(text), False
    old = text[start:end]
    tpl = template_convention()
    state = "latest" if _norm_body(old) == _norm_body(tpl) else "outdated"
    return {"state": state, "start": start, "end": end, "marked": marked, "old": old}


def ensure_convention(truth: Path, actions: list, upgrade: bool):
    """Keep the writeback block current. Marked or template-prefixed blocks upgrade
    losslessly (custom text after the block survives); a legacy block that diverged
    is replaced only with --upgrade-convention, and the old text is printed."""
    text = truth.read_text(encoding="utf-8")
    st = convention_state(text)
    tpl = template_convention()
    if st["state"] == "missing":
        text = text.rstrip("\n") + "\n\n" + tpl
        truth.write_text(text, encoding="utf-8")
        actions.append(f"convention: appended to {truth.name}")
        return
    if st["state"] == "unmanaged":
        actions.append(f"convention: unmanaged — {truth.name} mentions {MEMORY_LINK} but has no "
                       "「项目记忆 (回写约定)」 heading; add the template block by hand if wanted")
        return
    if st["state"] == "latest":
        if st["marked"]:
            actions.append("convention: latest")
            return
        # same text, no marker yet: insert the marker so future upgrades are bounded
        new = text[:st["start"]] + tpl.rstrip("\n") + "\n" + text[st["end"]:]
        truth.write_text(new, encoding="utf-8")
        actions.append("convention: latest (end marker added)")
        return
    old_body, tpl_body = _norm_body(st["old"]), _norm_body(tpl)
    if st["marked"] or old_body.startswith(tpl_body):
        # bounded, or an old template copy with custom text appended after it
        rem = "" if st["marked"] else old_body[len(tpl_body):].strip("\n")
        custom = ("\n" + rem + "\n") if rem else ""  # one blank line, then the project's own text
        new = text[:st["start"]] + tpl.rstrip("\n") + "\n" + custom + text[st["end"]:]
        truth.write_text(new, encoding="utf-8")
        actions.append("convention: upgraded (custom text after the block preserved)")
        return
    if not upgrade:
        actions.append("convention: OUTDATED (legacy block, not marked) — read the section, then "
                       "re-run with --upgrade-convention; the old text is printed on replacement")
        return
    new = text[:st["start"]] + tpl + text[st["end"]:]
    truth.write_text(new, encoding="utf-8")
    actions.append("convention: upgraded (legacy block replaced; old text below — re-add any "
                   "custom lines AFTER the end marker)\n" + st["old"].rstrip("\n"))


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

    appended, additions = [], []
    for title, block in template_sections().items():
        if "项目记忆" in title or "回写约定" in title:
            continue  # owned by ensure_convention
        if not section_present(text, title):
            additions.append("\n" + block)
            appended.append(title)
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


def cmd_validate(root: Path, max_bytes: int) -> int:
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
        st = convention_state(text)
        label = st["state"] + ("" if st["state"] != "outdated" else (" (marked)" if st["marked"] else " (legacy)"))
        checks.append((st["state"] == "latest", f"项目记忆 (回写约定): {label}"))

    memory = root / "PROJECT_MEMORY.md"
    if ultimate(memory) is None:
        checks.append((False, "PROJECT_MEMORY.md: 缺失"))
    else:
        for ok, msg in check_memory(memory.read_text(encoding="utf-8"), max_bytes):
            checks.append((ok, f"PROJECT_MEMORY.md: {msg.strip()}"))

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
    ap.add_argument("--upgrade-convention", action="store_true",
                    help="replace a legacy (unmarked, diverged) 回写约定 block with the template "
                         "version; marked blocks upgrade automatically without this flag")
    ap.add_argument("--validate", action="store_true",
                    help="read-only quality check: section fill state, symlink "
                         "consistency, PROJECT_MEMORY.md size gate; exits 1 on any FAIL")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES,
                    help=f"PROJECT_MEMORY.md byte limit used by --validate (default {DEFAULT_MAX_BYTES})")
    args = ap.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        sys.exit(1)
    if args.validate:
        sys.exit(1 if cmd_validate(root, args.max_bytes) else 0)
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
    ensure_convention(truth, actions, args.upgrade_convention)
    ensure_memory(root, project_name, actions)

    print(f"source of truth: {truth.name}")
    for a in actions:
        print(f"  - {a}")


if __name__ == "__main__":
    main()
