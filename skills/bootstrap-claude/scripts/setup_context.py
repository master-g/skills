#!/usr/bin/env python3
"""Bootstrap & reconcile a project's Claude context files.

Idempotent — safe to run on every invocation. It guarantees that:
  1. A single *source-of-truth* context file exists with every `## ` section
     of assets/CLAUDE.template.md (the template is the only place section text
     lives); the five REQUIRED_SECTIONS must be filled with real facts.
  2. CLAUDE.md is the one-line `@AGENTS.md` import so Claude Code reads the same
     content; no symlinks are created.
  3. PROJECT_MEMORY.md exists with its four sections.
  4. The 「项目记忆 (回写约定)」 block matches the template (the skill owns that text):
     missing -> appended; same text -> end marker added; bounded/prefixed block -> upgraded
     losslessly; a diverged legacy block -> reported, replaced only with --upgrade-convention.

Layout (AGENTS.md is always the source of truth; CLAUDE.md is the one-line `@AGENTS.md` import):
  - Neither exists / only a lone @AGENTS.md pointer      -> create AGENTS.md from template, write pointer
  - Only AGENTS.md (real)                                 -> write CLAUDE.md pointer
  - AGENTS.md real + CLAUDE.md pointer or symlink to it   -> truth = AGENTS.md; a symlink is replaced by the pointer
  - CLAUDE.md real, AGENTS.md missing or symlink to it    -> migrate: CLAUDE.md content moves to AGENTS.md, pointer written
  - Both are independent real files                       -> CONFLICT, refuse unless --resolve-conflict given

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
# Canonical section -> lowercase aliases. Matching is substring, case-insensitive,
# against any heading line. Chinese names are the template's; English names cover
# the common AGENTS.md vocabulary (see memory.py REPLACE_SECTIONS for the precedent).
SECTION_ALIASES = {
    "技术栈":  ["技术栈", "tech stack", "technology stack", "stack"],
    "命令":    ["命令", "commands", "scripts", "build and test", "build & test"],
    "代码风格": ["代码风格", "code style", "coding style", "style guide", "conventions"],
    "禁止文件": ["禁止文件", "do not edit", "protected files", "forbidden files", "never edit"],
    "审查规则": ["审查规则", "code review", "review rules", "reviewing", "pull request", "merge rules"],
}


def match_section(heading: str, canonical: str) -> bool:
    """Does this heading line name the canonical section (by any alias)?"""
    h = heading.lstrip("#").strip().lower()
    return any(a in h for a in SECTION_ALIASES[canonical])


PLACEHOLDER = "_待填写_"

MEMORY_LINK = "PROJECT_MEMORY.md"
CONV_HEADING_RE = re.compile(r"^##\s+.*(项目记忆|回写约定|project memory|writeback).*$", re.M | re.I)
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


def heading_present(text: str, canonical: str) -> bool:
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("#") and match_section(s, canonical):
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
    cu, au = resolve_pointer(claude, agents), ultimate(agents)

    if cu and au and cu != au:
        checks.append((False, "CLAUDE.md 与 AGENTS.md 指向不同内容 (CONFLICT)"))
        truth = None
    else:
        truth = au
        if truth is None:
            checks.append((False, "缺少上下文文件 — 先运行 bootstrap"))
        else:
            if cu != truth:
                checks.append((False, "CLAUDE.md 缺失或不是指向 AGENTS.md 的 @AGENTS.md 导入"))
            else:
                checks.append((True, "指向一致: 真实文件为 AGENTS.md，CLAUDE.md 为 @AGENTS.md 导入"))

    if truth is not None:
        text = truth.read_text(encoding="utf-8")
        bodies = section_bodies(text)
        for section in REQUIRED_SECTIONS:
            hit = next((t for t in bodies if match_section(t, section)), None)
            if hit is None:
                checks.append((False, f"{section}: 缺失"))
            else:
                state = section_state(bodies[hit])
                label = section if hit == section else f"{section} (匹配 ## {hit})"
                checks.append((state == "已填写", f"{label}: {state}"))
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
                    help="when both CLAUDE.md and AGENTS.md are independent real files, "
                         "pick whose content becomes AGENTS.md; the other is backed up to "
                         "*.bak and CLAUDE.md becomes the one-line @AGENTS.md import")
    ap.add_argument("--upgrade-convention", action="store_true",
                    help="replace a legacy (unmarked, diverged) 回写约定 block with the template "
                         "version; marked blocks upgrade automatically without this flag")
    ap.add_argument("--validate", action="store_true",
                    help="read-only quality check: section fill state, import-pointer "
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

    cu = resolve_pointer(claude, agents)
    au = ultimate(agents)

    if agents.is_symlink() and ultimate(agents) == ultimate(claude) and claude.is_file() and not claude.is_symlink():
        agents.unlink()
        au = None  # fall into the legacy-migration branch below

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

    ensure_claude_pointer(root, actions)
    ensure_sections(truth, project_name, actions)
    ensure_convention(truth, actions, args.upgrade_convention)
    ensure_memory(root, project_name, actions)

    print(f"source of truth: {truth.name}")
    for a in actions:
        print(f"  - {a}")


if __name__ == "__main__":
    main()
