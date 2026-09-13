#!/usr/bin/env python3
"""Inspect, write and compact PROJECT_MEMORY.md.

Subcommands:
  check   <file> [--max-bytes N] [--max-line N]
          size gate: whole file <= max-bytes, no line longer than max-line chars,
          replace-sections (上次会话, 下次运行) hold exactly one dated block.
          Prints per-section bytes; exit 1 on any FAIL.
  add     <file> --section S --text T [--date D]
          append-sections (已验证的事实, 失败尝试): append a dated bullet at the end
          replace-sections (上次会话, 下次运行):   overwrite the section with one dated
          block; newlines in T become indented continuation lines.
  compact <file>
          replace-sections: keep only the newest dated block, drop the rest.
          append-sections are never auto-evicted — merge, or promote to docs/ and
          leave a one-line pointer (see references/maintain.md).

ponytail: bytes, not tokens — a byte cap can't be gamed by cramming lines the way
a line cap was; the per-line cap closes the other loophole.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

REPLACE_SECTIONS = ["上次会话", "下次运行", "Last Session", "Next Session"]
DEFAULT_MAX_BYTES = 24000   # ~8k tokens of mixed zh/en; sisyphus was at 150k
DEFAULT_MAX_LINE = 300      # chars; median line in the worst files was 350+
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^-\s+")
DATE_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2})\]")


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


DATED_BULLET_RE = re.compile(r"^-\s+\[\d{4}-\d{2}-\d{2}\]")


def section_entries(body_idxs, lines, dated_only=False):
    """Group a section body into entries (each top-level '- ' bullet + its
    continuation lines). With dated_only, only '- [YYYY-MM-DD]' bullets start an
    entry, so a block written as a date line plus sub-bullets counts as one.
    Returns list of line-index lists in file order."""
    entries, cur = [], None
    start = DATED_BULLET_RE if dated_only else BULLET_RE
    for idx in body_idxs:
        if start.match(lines[idx]):
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


def check_memory(text: str, max_bytes=DEFAULT_MAX_BYTES, max_line=DEFAULT_MAX_LINE):
    """Return [(ok, message)] — shared with setup_context.py --validate."""
    lines = text.split("\n")
    checks = []
    size = len(text.encode("utf-8"))
    checks.append((size <= max_bytes, f"总大小 {size} B (max {max_bytes})"))
    secs = parse_sections(lines)
    for s in secs:
        if s["level"] != 2:
            continue
        body = "\n".join(lines[i] for i in s["body"])
        checks.append((True, f"  {s['title']}: {len(body.encode('utf-8'))} B"))
        if s["title"] in REPLACE_SECTIONS:
            n = len(section_entries(s["body"], lines, dated_only=True))
            undated = len(section_entries(s["body"], lines)) - n
            if n == 0 and undated > 0:
                checks.append((False, f"  {s['title']}: 0 个带日期块（{undated} 条无日期 bullet），块首须为 - [YYYY-MM-DD]"))
            else:
                checks.append((n <= 1, f"  {s['title']}: {n} 条 (整节改写，须 ≤1)"))
    long = [(i + 1, len(l)) for i, l in enumerate(lines) if len(l) > max_line]
    if long:
        shown = ", ".join(f"L{i}:{n}" for i, n in long[:8]) + (" …" if len(long) > 8 else "")
        checks.append((False, f"{len(long)} 行超过 {max_line} 字符: {shown}"))
    else:
        checks.append((True, f"无超过 {max_line} 字符的行"))
    return checks


def print_checks(name, checks):
    fails = sum(1 for ok, _ in checks if not ok)
    print(f"check: {name}")
    for ok, msg in checks:
        print(f"  {'PASS' if ok else 'FAIL'} {msg}")
    print(f"result: {fails} FAIL" if fails else "result: all PASS")
    return fails


def cmd_check(args):
    path = Path(args.file)
    fails = print_checks(path.name, check_memory(path.read_text(encoding="utf-8"),
                                                 args.max_bytes, args.max_line))
    if fails:
        print("超限时：先把 上次会话／下次运行 压成一块，再合并同主题事实或搬入 docs/ 留一行指针。",
              file=sys.stderr)
    sys.exit(1 if fails else 0)


def entry_date(entry, lines):
    m = DATE_RE.search(lines[entry[0]])
    return m.group(1) if m else ""


def cmd_compact(args):
    path = Path(args.file)
    lines = read_lines(path)
    if lines and lines[-1] == "":
        lines.pop()
    removed = 0
    for title in REPLACE_SECTIONS:
        sec = find_section(parse_sections(lines), title)
        if not sec:
            continue
        ents = section_entries(sec["body"], lines, dated_only=True)
        if len(ents) <= 1:
            continue
        # newest by date; ties resolve to the later entry in file order
        keep = max(range(len(ents)), key=lambda k: (entry_date(ents[k], lines), k))
        kept_date = entry_date(ents[keep], lines)
        drop = [i for k, e in enumerate(ents) if k != keep for i in e]
        for i in sorted(drop, reverse=True):
            del lines[i]
        removed += len(ents) - 1
        print(f"{title}: kept {kept_date} block, dropped {len(ents) - 1}")
    write_lines(path, lines)
    if not removed:
        print(f"{path.name}: replace-sections already single-block, nothing to do")
    fails = print_checks(path.name, check_memory("\n".join(lines) + "\n"))
    if fails:
        print("追加节不自动淘汰：合并同主题条目，或搬入 docs/ 后只留一行指针。", file=sys.stderr)
        sys.exit(1)


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
    first, *rest = args.text.split("\n")
    block = [f"- [{date}] {first}"] + [("  " + r if r.strip() else "") for r in rest]
    if args.section in REPLACE_SECTIONS:
        # keep the HTML-comment hint, drop every previous entry
        keep = [i for i in sec["body"] if lines[i].strip().startswith("<!--")]
        for i in sorted(set(sec["body"]) - set(keep), reverse=True):
            del lines[i]
        sec = find_section(parse_sections(lines), args.section)  # indices shifted
        insert_at = (sec["body"][-1] + 1) if sec["body"] else (sec["hidx"] + 1)
        lines[insert_at:insert_at] = block
        after = insert_at + len(block)
        if after < len(lines) and lines[after].startswith("#"):
            lines.insert(after, "")
        write_lines(path, lines)
        print(f"replaced ## {args.section}: {block[0]}")
        return
    if rest:
        print("ERROR: append-sections take one line per entry (≤2 行时用一条长句，不用换行)",
              file=sys.stderr)
        sys.exit(1)
    insert_at = (sec["body"][-1] + 1) if sec["body"] else (sec["hidx"] + 1)
    while insert_at - 1 > sec["hidx"] and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, block[0])
    write_lines(path, lines)
    print(f"added to ## {args.section}: {block[0]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check")
    p_check.add_argument("file")
    p_check.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    p_check.add_argument("--max-line", type=int, default=DEFAULT_MAX_LINE)
    p_check.set_defaults(func=cmd_check)

    p_compact = sub.add_parser("compact")
    p_compact.add_argument("file")
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
