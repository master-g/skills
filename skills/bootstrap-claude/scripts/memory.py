#!/usr/bin/env python3
"""Inspect, write and compact PROJECT_MEMORY.md.

Subcommands:
  check   <file> [--max-bytes N] [--max-line N] [--base REF] [--base-file PATH]
          size gate: whole file <= max-bytes, no line longer than max-line chars,
          replace-sections (上次会话, 下次运行) hold exactly one dated block.
          Then diffs append-section entries against the baseline (git REF, default
          HEAD, or --base-file): every entry gone and not rewritten needs a line
          "移出：<锚> → <去向>" in 上次会话. Prints per-section bytes; exit 1 on any FAIL.
  add     <file> --section S --text T [--date D]
          append-sections (已验证的事实, 失败尝试): append a dated bullet at the end
          replace-sections (上次会话, 下次运行):   overwrite the section with one dated
          block; newlines in T become indented continuation lines. Rewriting
          上次会话 keeps the 移出 lines that still account for an entry gone since HEAD.
  compact <file>
          replace-sections: keep only the newest dated block, drop the rest.
          append-sections are never auto-evicted — merge, or promote to docs/ and
          leave a one-line pointer (see references/maintain.md).

ponytail: bytes, not tokens — a byte cap can't be gamed by cramming lines the way
a line cap was; the per-line cap closes the other loophole.
"""
import argparse
import datetime
import difflib
import re
import subprocess
import sys
from pathlib import Path

REPLACE_SECTIONS = ["上次会话", "下次运行", "Last Session", "Next Session"]
LEDGER_SECTIONS = ["上次会话", "Last Session"]
DEFAULT_MAX_BYTES = 24000   # ~8k tokens of mixed zh/en; sisyphus was at 150k
DEFAULT_MAX_LINE = 300      # chars; median line in the worst files was 350+
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^-\s+")
DATE_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2})\]")
# 36 hand-labelled history pairs at similarity 0.5-0.7: 35 were the same entry rewritten
REWRITE_RATIO = 0.5
# confirmed promotions shared 7%-42% of keywords with AGENTS.md (rules get reworded); all 304 gone entries: median 0, p95 13%
MIN_SHARED = 0.05
SHRINK_NOTE = 0.7
INSTRUCTION_NAMES = ("AGENTS.md", "CLAUDE.md")
ANCHOR_BREAK_RE = re.compile(r"[；;]|→|->")
MOVE_RE = re.compile(r"^\s*(?:-\s*)?移出[:：]\s*(.+?)\s*(?:→|->)\s*(.+?)\s*$")
DATE_PREFIX_RE = re.compile(r"^-\s+(?:\[\d{4}-\d\d-\d\d\]\s*)*")
OVER_LIMIT_HINT = ("超限时：先把每次都要照做的规则晋升到 AGENTS.md，再把长条知识搬进 docs/、合并同主题条目、"
                   "作废过期条目；每条消失的条目在「上次会话」里写一行「移出：<条目开头> → <去向>」。")


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


def section_bodies(text):
    """{title: [body lines]} of the level-2 sections; a repeated title concatenates."""
    lines = text.split("\n")
    out = {}
    for s in parse_sections(lines):
        if s["level"] == 2:
            out.setdefault(s["title"], []).extend(lines[i] for i in s["body"])
    return out


def append_entries(text):
    entries = []
    for title, body in section_bodies(text).items():
        if title in REPLACE_SECTIONS:
            continue
        for idxs in section_entries(range(len(body)), body):
            head, *rest = (body[i] for i in idxs)
            rest = [l.rstrip() for l in rest if l.strip() and not l.lstrip().startswith("<!--")]
            entries.append("\n".join([head.rstrip()] + rest))
    return entries


def tokens(s):
    s = DATE_PREFIX_RE.sub("", s)
    out = set(re.findall(r"[A-Za-z_][A-Za-z0-9_./:\-]{3,}", s))
    cjk = re.sub(r"[^一-鿿]", "", s)
    out |= {cjk[i:i + 4] for i in range(0, max(0, len(cjk) - 3), 2)}
    return out


def shared(entry, text):
    tk = tokens(entry)
    return len(tk & tokens(text)) / len(tk) if tk else 0.0


def diff_entries(old_text, new_text, ratio=REWRITE_RATIO):
    """(rewritten [(old, new, similarity)], gone [old]) between two versions."""
    old, new = append_entries(old_text), append_entries(new_text)
    new_set, old_set = set(new), set(old)
    added = [e for e in new if e not in old_set]
    rewritten, gone = [], []
    for e in old:
        if e in new_set:
            continue
        best = max(added, key=lambda a: difflib.SequenceMatcher(None, e, a).ratio(), default=None)
        r = difflib.SequenceMatcher(None, e, best).ratio() if best else 0.0
        (rewritten.append((e, best, r)) if r >= ratio else gone.append(e))
    return rewritten, gone


def parse_moves(text):
    """[(anchor, destination)] from 移出 lines in the last-session block."""
    moves = []
    secs = section_bodies(text)
    for title in LEDGER_SECTIONS:
        for line in secs.get(title, []):
            m = MOVE_RE.match(line)
            if m:
                for anchor in re.split(r"[；;]", m.group(1)):
                    if anchor.strip():
                        moves.append((anchor.strip(), m.group(2)))
    return moves


def suggest_anchor(entry, others):
    """Shortest prefix of a separator-free segment that no other entry contains."""
    head = entry.split("\n")[0][2:]
    segments = [s.strip() for s in ANCHOR_BREAK_RE.split(head) if len(s.strip()) >= 8]
    for seg in segments:
        for n in range(min(28, len(seg)), len(seg) + 1, 4):
            if not any(seg[:n] in o for o in others):
                return seg[:n]
    return segments[0] if segments else head


def keep_moves(old_ledger_text, base_text, new_text):
    """移出 lines from a ledger about to be overwritten that still account for an
    entry gone since the baseline: an earlier session removed it and did not commit."""
    _, gone = diff_entries(base_text, new_text)
    kept = []
    for line in old_ledger_text.split("\n"):
        m = MOVE_RE.match(line)
        if m and any(a.strip() and a.strip() in g for a in re.split(r"[；;]", m.group(1)) for g in gone):
            kept.append(line.strip())
    return kept


def classify(dest, entry, new_text, root):
    """(ok, kind, message) for one destination string."""
    if dest.startswith("并入"):
        target = dest[2:].strip(" ：:「」")
        hits = [e for e in append_entries(new_text) if target and target in e]
        if len(hits) != 1:
            return False, "并入", f"并入的目标「{target}」对上 {len(hits)} 条现存条目，须正好 1 条"
        return True, "并入", "并入现存条目"
    if dest.startswith("作废"):
        reason = dest[2:].strip(" ：:（）()")
        if len(reason) < 4:
            return False, "作废", "作废要写原因（至少 4 个字）"
        return True, "作废", reason
    rel = re.split(r"[\s「]", dest, maxsplit=1)[0]
    path = Path(root) / rel
    if not path.is_file():
        return False, "搬出", f"去向文件不存在：{rel}"
    kind = "晋升" if (path.name in INSTRUCTION_NAMES or ".claude/rules" in rel) else "搬出"
    body = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"「(.+?)」", dest)
    if m and not any(h and m.group(1) in h.group(2) for h in map(HEADING_RE.match, body.split("\n"))):
        return False, kind, f"{rel} 里没有标题含「{m.group(1)}」的小节"
    got = shared(entry, body)
    if got < MIN_SHARED:
        return False, kind, f"{rel} 里找不到这条的关键词（{got:.0%}，须 ≥{MIN_SHARED:.0%}）：先把内容写进去"
    return True, kind, f"{rel}（关键词 {got:.0%}）"


def check_removed(old_text, new_text, root="."):
    """[(ok, message)] in the same shape check_memory returns."""
    rewritten, gone = diff_entries(old_text, new_text)
    checks = []
    for old, new, r in rewritten:
        if len(new) < SHRINK_NOTE * len(old):
            checks.append((True, f"改写后缩短 {1 - len(new) / len(old):.0%}：{suggest_anchor(old, [])}"))
    if not gone:
        checks.append((True, f"追加节无条目消失（改写 {len(rewritten)} 条）"))
        return checks
    moves = parse_moves(new_text)
    tally = {}
    for e in gone:
        mine = [(a, d) for a, d in moves if a in e and sum(a in g for g in gone) == 1]
        anchor = suggest_anchor(e, [g for g in gone if g is not e])
        if not mine:
            checks.append((False, f"消失的条目没有去向，在「上次会话」里补一行：\n      移出：{anchor} → <AGENTS.md | docs/… | 并入 <现存条目的开头> | 作废（原因）>"))
            continue
        ok, kind, msg = classify(mine[0][1], e, new_text, root)
        tally[kind] = tally.get(kind, 0) + ok
        checks.append((ok, f"{kind}：{anchor} → {msg}"))
    summary = "、".join(f"{k} {v}" for k, v in tally.items()) or "无"
    checks.append((True, f"消失 {len(gone)} 条，已交代：{summary}"))
    return checks


def git_out(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True)
    except OSError:
        return None
    return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None


def read_base(path: Path, ref="HEAD"):
    """The file as committed at ref, or None outside Git or when ref lacks it."""
    d = path.resolve().parent
    prefix = git_out(d, "rev-parse", "--show-prefix")
    if prefix is None:
        return None
    return git_out(d, "show", f"{ref}:{prefix.rstrip()}{path.name}")


def bad_ref(path: Path, ref):
    """True inside a Git repository where ref names no commit: a typo must not skip the gate."""
    d = path.resolve().parent
    return git_out(d, "rev-parse", "--show-prefix") is not None and \
        git_out(d, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}") is None


def repo_root(path: Path):
    d = path.resolve().parent
    top = git_out(d, "rev-parse", "--show-toplevel")
    return Path(top.rstrip("\n")) if top else d


def print_checks(name, checks):
    fails = sum(1 for ok, _ in checks if not ok)
    print(f"check: {name}")
    for ok, msg in checks:
        print(f"  {'PASS' if ok else 'FAIL'} {msg}")
    print(f"result: {fails} FAIL" if fails else "result: all PASS")
    return fails


def cmd_check(args):
    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    checks = check_memory(text, args.max_bytes, args.max_line)
    if args.base_file is not None:
        base = Path(args.base_file).read_text(encoding="utf-8")
    else:
        base = read_base(path, args.base)
    if base is None and args.base_file is None and args.base != "HEAD" and bad_ref(path, args.base):
        checks.append((False, f"--base {args.base} 不是这个仓库里的提交"))
    elif base is None:
        checks.append((True, "无基线，跳过条目去向检查"))
    else:
        checks += check_removed(base, text, repo_root(path))
    fails = print_checks(path.name, checks)
    if fails:
        print(OVER_LIMIT_HINT, file=sys.stderr)
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
        print(OVER_LIMIT_HINT, file=sys.stderr)
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
        kept = []
        base = read_base(path) if args.section in LEDGER_SECTIONS else None
        if base is not None:
            written = {l.strip() for l in args.text.split("\n")}
            old_ledger = "\n".join(lines[i] for i in sec["body"])
            kept = [l for l in keep_moves(old_ledger, base, "\n".join(lines)) if l not in written]
            block += ["  " + l for l in kept]
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
        if kept:
            print(f"kept {len(kept)} 条移出声明")
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
    p_check.add_argument("--base", default="HEAD")
    p_check.add_argument("--base-file", default=None)
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
