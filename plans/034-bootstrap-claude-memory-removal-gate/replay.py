#!/usr/bin/env python3
"""Replay removal_gate over a repository's PROJECT_MEMORY.md history.

Usage: python3 replay.py [--impl memory] <repo> [<repo> ...]

--impl names the module to test (default removal_gate, the reference in this
directory). After plan 034 Step 2, run with --impl memory and
PYTHONPATH=skills/bootstrap-claude/scripts to replay the shipped code.

History has no 移出 lines, so every disappearance fails by construction. The
replay shows three things: every real version parses, how many entries a commit
would have to account for, and (with --impl) that the shipped code prints the
same lines as the reference. It is not evidence that detection is correct.
"""
import importlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, errors="replace").stdout


def replay(repo, g):
    commits = git(repo, "log", "--format=%h", "--reverse", "--", "PROJECT_MEMORY.md").split()
    prev, quiet, loud, rewrites, sizes, wrong = None, 0, 0, 0, [], []
    for c in commits:
        cur = git(repo, "show", f"{c}:PROJECT_MEMORY.md")
        if prev is not None:
            rewritten, gone = g.diff_entries(prev, cur)
            failed = sum(1 for ok, _ in g.check_removed(prev, cur, repo) if not ok)
            rewrites += len(rewritten)
            if gone:
                loud += 1
                sizes.append(len(gone))
            else:
                quiet += 1
            if failed != len(gone):
                wrong.append(c)
        prev = cur
    sizes.sort()
    spread = f"中位 {sizes[len(sizes) // 2]}，最大 {sizes[-1]}" if sizes else "无"
    print(f"{Path(repo).resolve().name}: 无条目消失的提交 {quiet} 个全部 PASS，有条目消失的提交 {loud} 个全部 FAIL"
          f"（每次消失条数 {spread}），改写 {rewrites} 条不需要声明" if not wrong
          else f"{Path(repo).resolve().name}: 判定与预期不符的提交 {wrong}")
    return not wrong


if __name__ == "__main__":
    args = sys.argv[1:]
    impl = "removal_gate"
    if args[:1] == ["--impl"]:
        impl, args = args[1], args[2:]
    module = importlib.import_module(impl)
    sys.exit(0 if all([replay(r, module) for r in args]) else 1)
