#!/usr/bin/env python3
"""Inspect and compact PROJECT_MEMORY.md.

Subcommands:
  status  <file>                 report total + per-section line counts, flag if over --max
  compact <file>                 evict oldest entries from non-protected sections until
                                 <= --target, printing every removed entry (never silent)
  add     <file> --section S --text T [--date D]
                                 append a timestamped bullet to the end of section S

Protected sections (kept through compaction): 已验证的事实, 下次运行
Evictable sections (oldest first):           上次会话, then 失败尝试
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

PROTECTED = ["已验证的事实", "下次运行"]
EVICT_PRIORITY = ["上次会话", "失败尝试"]  # evicted in this order, oldest entry first
DEFAULT_MAX = 400
DEFAULT_TARGET = 350
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^-\s+")


def read_lines(path: Path):
    return path.read_text(encoding="utf-8").split("\n")


def write_lines(path: Path, lines):
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def parse_sections(lines):
    """List of {title, level, hidx, body:[absolute line idx]} for each heading."""
    secs = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            secs.append({"title": m.group(2).strip(), "level": len(m.group(1)),
                         "hidx": i, "body": []})
        elif secs:
            secs[-1]["body"].append(i)
    return secs


def section_entries(body_idxs, lines):
    """Group a section body into entries (each top-level '- ' bullet + its
    continuation lines). Returns list of line-index lists, file order = oldest first."""
    entries, cur = [], None
    for idx in body_idxs:
        if BULLET_RE.match(lines[idx]):
            if cur:
                entries.append(cur)
            cur = [idx]
        elif cur is not None:
            cur.append(idx)
    if cur:
        entries.append(cur)
    return entries


def find_section(secs, title):
    for s in secs:
        if s["level"] == 2 and s["title"] == title:
            return s
    return None


def cmd_status(args):
    path = Path(args.file)
    lines = read_lines(path)
    total = len([l for l in lines if True])
    # Trailing empty from split on final newline shouldn't inflate; count real lines.
    real_total = len(path.read_text(encoding="utf-8").rstrip("\n").split("\n"))
    secs = parse_sections(lines)
    print(f"{path.name}: {real_total} lines (max {args.max}, target {args.target})")
    for s in secs:
        if s["level"] != 2:
            continue
        n_entries = len(section_entries(s["body"], lines))
        tag = ""
        if s["title"] in PROTECTED:
            tag = " [protected]"
        elif s["title"] in EVICT_PRIORITY:
            tag = " [evictable]"
        print(f"  ## {s['title']}: {len(s['body'])} lines, {n_entries} entries{tag}")
    if real_total > args.max:
        print(f"OVER LIMIT by {real_total - args.max} lines — run: memory.py compact {path}")
    else:
        print("within limit")


def cmd_compact(args):
    path = Path(args.file)
    lines = read_lines(path)
    # drop a single trailing empty element from the final newline for honest counts
    if lines and lines[-1] == "":
        lines.pop()

    def count():
        return len(lines)

    if count() <= args.max:
        print(f"{path.name}: {count()} lines — under max {args.max}, nothing to do")
        return

    removed = []
    while count() > args.target:
        secs = parse_sections(lines)
        victim = None
        for title in EVICT_PRIORITY:
            sec = find_section(secs, title)
            if not sec:
                continue
            ents = section_entries(sec["body"], lines)
            if ents:
                victim = (title, ents[0])
                break
        if victim is None:
            break
        title, ent = victim
        removed.append((title, [lines[i] for i in ent]))
        for i in sorted(ent, reverse=True):
            del lines[i]

    write_lines(path, lines)

    if not removed:
        print(f"WARNING: {path.name} is {count()} lines (> max {args.max}) but all evictable "
              f"sections are empty. Protected sections (已验证的事实 / 下次运行) are too large — "
              f"summarize them by hand.", file=sys.stderr)
        return

    print(f"{path.name}: compacted to {count()} lines (target {args.target}). "
          f"Evicted {len(removed)} entr{'y' if len(removed)==1 else 'ies'}:")
    for title, block in removed:
        first = BULLET_RE.sub("", block[0].strip()) if block else ""
        print(f"  - [{title}] {first}")
    if count() > args.max:
        print(f"WARNING: still {count()} lines (> max {args.max}); protected sections dominate.",
              file=sys.stderr)


def cmd_add(args):
    path = Path(args.file)
    lines = read_lines(path)
    if lines and lines[-1] == "":
        lines.pop()
    secs = parse_sections(lines)
    sec = find_section(secs, args.section)
    if sec is None:
        print(f"ERROR: section '## {args.section}' not found in {path.name}", file=sys.stderr)
        sys.exit(1)
    date = args.date or datetime.date.today().isoformat()
    bullet = f"- [{date}] {args.text}"
    # insert after the last line of this section's body
    insert_at = (sec["body"][-1] + 1) if sec["body"] else (sec["hidx"] + 1)
    # skip back over trailing blank lines inside the section so the bullet sits
    # right under existing content
    while insert_at - 1 > sec["hidx"] and insert_at - 1 < len(lines) and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, bullet)
    write_lines(path, lines)
    print(f"added to ## {args.section}: {bullet}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("file")
    p_status.add_argument("--max", type=int, default=DEFAULT_MAX)
    p_status.add_argument("--target", type=int, default=DEFAULT_TARGET)
    p_status.set_defaults(func=cmd_status)

    p_compact = sub.add_parser("compact")
    p_compact.add_argument("file")
    p_compact.add_argument("--max", type=int, default=DEFAULT_MAX)
    p_compact.add_argument("--target", type=int, default=DEFAULT_TARGET)
    p_compact.set_defaults(func=cmd_compact)

    p_add = sub.add_parser("add")
    p_add.add_argument("file")
    p_add.add_argument("--section", required=True)
    p_add.add_argument("--text", required=True)
    p_add.add_argument("--date", default=None)
    p_add.set_defaults(func=cmd_add)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
