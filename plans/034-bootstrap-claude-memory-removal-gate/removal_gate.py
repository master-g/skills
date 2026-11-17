#!/usr/bin/env python3
"""Reference implementation for plan 034: account for every append-section entry
that disappears from PROJECT_MEMORY.md between a baseline and the current file.

Pure functions only; plan 034 Step 2 moves them into scripts/memory.py.
"""
import difflib
import re
from pathlib import Path

REPLACE_SECTIONS = ["上次会话", "下次运行", "Last Session", "Next Session"]
LEDGER_SECTIONS = ["上次会话", "Last Session"]
REWRITE_RATIO = 0.5
MIN_SHARED = 0.05
SHRINK_NOTE = 0.7
INSTRUCTION_NAMES = ("AGENTS.md", "CLAUDE.md")
ANCHOR_BREAK_RE = re.compile(r"[；;]|→|->")
MOVE_RE = re.compile(r"^\s*(?:-\s*)?移出[:：]\s*(.+?)\s*(?:→|->)\s*(.+?)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^-\s+")
DATE_PREFIX_RE = re.compile(r"^-\s+(?:\[\d{4}-\d\d-\d\d\]\s*)*")


def sections(text):
    out, cur = {}, None
    for line in text.split("\n"):
        m = HEADING_RE.match(line)
        if m:
            cur = m.group(2).strip() if len(m.group(1)) == 2 else None
            if cur is not None:
                out.setdefault(cur, [])
        elif cur is not None:
            out[cur].append(line)
    return out


def append_entries(text):
    entries = []
    for title, body in sections(text).items():
        if title in REPLACE_SECTIONS:
            continue
        cur = None
        for line in body:
            if BULLET_RE.match(line):
                if cur:
                    entries.append("\n".join(cur))
                cur = [line.rstrip()]
            elif cur is not None and line.strip() and not line.lstrip().startswith("<!--"):
                cur.append(line.rstrip())
        if cur:
            entries.append("\n".join(cur))
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
    secs = sections(text)
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
    """[(ok, message)] in the same shape memory.check_memory returns."""
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
