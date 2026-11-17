#!/usr/bin/env python3
"""Grade one run of plan 034's two memory scenarios against the answer key.

Usage: python3 grade.py <triage|at-cap> <original project dir> <project dir after the run>

Both skill versions are graded by this one script, with removal_gate.py as the
fixed reference for what disappeared and what was accounted for.
Prints one line per criterion and a final JSON line; exit 1 when any criterion fails.
"""
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import removal_gate as g  # noqa: E402

KEY = json.loads((HERE / "answer-key.json").read_text(encoding="utf-8"))
MAX_BYTES, MAX_LINE, MAX_AGENTS_LINES = 24000, 300, 200
WORKFLOW = ("工作流与陷阱", "Workflow")


def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def workflow_section(agents_text):
    for title, body in g.sections(agents_text).items():
        if any(w in title for w in WORKFLOW):
            return "\n".join(body)
    return ""


def other_markdown(root):
    skip = {"AGENTS.md", "CLAUDE.md", "PROJECT_MEMORY.md"}
    return {str(p.relative_to(root)): read(p) for p in root.rglob("*.md")
            if p.name not in skip and ".git" not in p.parts}


def where(token, entries_text, agents, docs):
    if token in workflow_section(agents):
        return "AGENTS.md 工作流与陷阱"
    if token in agents:
        return "AGENTS.md 其他小节"
    if token in entries_text:
        return "记忆"
    for name, text in docs.items():
        if token in text:
            return name
    return "找不到"


def size_ok(memory):
    long_lines = [i + 1 for i, line in enumerate(memory.split("\n")) if len(line) > MAX_LINE]
    size = len(memory.encode("utf-8"))
    return size <= MAX_BYTES and not long_lines, f"{size} B，超长行 {len(long_lines)}"


def added_today(old, new):
    old_entries = set(g.append_entries(old))
    today = datetime.date.today().isoformat()
    return [e for e in g.append_entries(new) if e not in old_entries and today in e]


def grade_triage(old, new, agents, root):
    entries = "\n".join(g.append_entries(new))
    flow = workflow_section(agents)
    kept = [t for t in KEY["memory-triage"]["original"] if t in entries]
    gate = [m for ok, m in g.check_removed(old, new, root) if not ok]
    ok_size, size_note = size_ok(new)
    return [
        ("规则进了 AGENTS.md 工作流与陷阱", "db-reset" in flow, where("db-reset", entries, agents, {})),
        ("规则不在记忆的追加节", "db-reset" not in entries, ""),
        ("分页上限 500 记进了记忆", any("500" in e for e in added_today(old, new)), ""),
        ("不加缓存的决定在记忆里", "Redis" in entries, ""),
        ("决定没进 AGENTS.md 工作流与陷阱", "Redis" not in flow, "AGENTS.md 其他小节有" if "Redis" in agents else ""),
        ("原有 8 条都在", len(kept) == 8, f"{len(kept)}/8"),
        ("没有条目无去向地消失", not gate, f"{len(gate)} 条未交代"),
        ("体积和行宽在门槛内", ok_size, size_note),
    ]


def grade_at_cap(old, new, agents, root):
    key = KEY["memory-at-cap"]
    group_of = {t: "规则" for t in key["rule"]} | {t: "长事实" for t in key["long"]} \
        | {t: "过期" for t in key["stale"]} | {t: "成对" for pair in key["pairs"] for t in pair} \
        | {t: "保留" for t in key["keep"]}
    entries = "\n".join(g.append_entries(new))
    docs = other_markdown(root)
    rewritten, gone = g.diff_entries(old, new)
    moves = g.parse_moves(new)

    def group(entry):
        return next((grp for tok, grp in group_of.items() if tok in entry), "未知")

    void_wrong, undeclared, gone_by_group = [], 0, {}
    for e in gone:
        gone_by_group[group(e)] = gone_by_group.get(group(e), 0) + 1
        mine = [d for a, d in moves if a in e and sum(a in x for x in gone) == 1]
        if not mine:
            undeclared += 1
        elif mine[0].startswith("作废") and group(e) != "过期":
            void_wrong.append(group(e))
    gate = [m for ok, m in g.check_removed(old, new, root) if not ok]
    rule_at = [where(t, entries, agents, docs) for t in key["rule"]]
    keep_lost = [where(t, entries, agents, docs) for t in key["keep"] if t not in entries]
    long_at = [where(t, entries, agents, docs) for t in key["long"]]
    ok_size, size_note = size_ok(new)
    agents_lines = len(agents.split("\n"))
    spread = "、".join(f"{k} {v}" for k, v in sorted(gone_by_group.items())) or "无"
    return [
        ("体积和行宽在门槛内", ok_size, size_note),
        ("新事实记进了记忆", bool(added_today(old, new)), ""),
        ("3 条规则都在 AGENTS.md 工作流与陷阱", all(a == "AGENTS.md 工作流与陷阱" for a in rule_at), " / ".join(rule_at)),
        ("每条消失的条目都有去向", not gate, f"消失 {len(gone)}（{spread}），未声明 {undeclared}，核对失败 {len(gate)}，改写 {len(rewritten)}"),
        ("作废只出现在过期组", not void_wrong, "、".join(void_wrong)),
        ("保留组条目都在记忆里", not keep_lost, f"缺 {len(keep_lost)}：" + "、".join(sorted(set(keep_lost))) if keep_lost else ""),
        ("长事实没有找不到的", "找不到" not in long_at, " / ".join(sorted(set(long_at)))),
        ("AGENTS.md 不超过 200 行", agents_lines <= MAX_AGENTS_LINES, f"{agents_lines} 行"),
    ]


def main():
    kind, original, after = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    old, new = read(original / "PROJECT_MEMORY.md"), read(after / "PROJECT_MEMORY.md")
    agents = read(after / "AGENTS.md")
    rows = (grade_triage if kind == "triage" else grade_at_cap)(old, new, agents, after)
    for name, ok, note in rows:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f"（{note}）" if note else ""))
    print(json.dumps({"run": after.name, "results": [[n, ok, note] for n, ok, note in rows]}, ensure_ascii=False))
    sys.exit(0 if all(ok for _, ok, _ in rows) else 1)


if __name__ == "__main__":
    main()
