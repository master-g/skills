#!/usr/bin/env python3
"""Smallest check that fails if memory.py's gate or replace logic breaks. Run: python3 test_memory.py"""
import sys, tempfile, argparse, subprocess, io, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory as m

BASE = """# 项目记忆 — t

## 已验证的事实

- [2026-01-01] 事实 A

## 失败尝试

## 上次会话

<!-- hint -->
- [2026-08-06] 旧块
- [2026-09-03] 新块（不在末尾）
- [2026-08-19] 更旧块

## 下次运行

- [2026-01-01] 下一步
"""

def fails(checks): return [msg for ok, msg in checks if not ok]

# check: replace-section with 3 entries fails; fixed file passes
assert any("上次会话: 3 条" in f for f in fails(m.check_memory(BASE)))
assert any("总大小" in f for f in fails(m.check_memory("x" * 30000)))
assert any("超过 300 字符" in f for f in fails(m.check_memory("## a\n" + "y" * 301)))
assert not fails(m.check_memory("## 上次会话\n- [2026-01-01] ok\n"))
assert any("0 个带日期块" in f for f in fails(m.check_memory("## 上次会话\n- undated a\n- undated b\n")))

with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "PROJECT_MEMORY.md"; f.write_text(BASE, encoding="utf-8")
    # compact keeps newest by date even when it is not last in file; append sections untouched
    m.cmd_compact(argparse.Namespace(file=str(f)))
    t = f.read_text(encoding="utf-8")
    assert "新块" in t and "旧块" not in t and "更旧块" not in t and "事实 A" in t, t
    assert not fails(m.check_memory(t))
    # add to replace-section: multi-line text becomes one block with indented continuation
    m.cmd_add(argparse.Namespace(file=str(f), section="上次会话", text="第一行\n第二行", date="2026-09-13"))
    t = f.read_text(encoding="utf-8")
    assert "- [2026-09-13] 第一行\n  第二行\n" in t and "新块" not in t and "<!-- hint -->" in t, t
    assert not fails(m.check_memory(t))
    # add to append-section keeps existing entries, rejects multi-line
    m.cmd_add(argparse.Namespace(file=str(f), section="失败尝试", text="试过 X，因 Y 放弃", date="2026-09-13"))
    t = f.read_text(encoding="utf-8")
    assert "事实 A" in t and "- [2026-09-13] 试过 X" in t
    try:
        m.cmd_add(argparse.Namespace(file=str(f), section="失败尝试", text="a\nb", date=None)); raise AssertionError("multi-line append accepted")
    except SystemExit: pass

OLD = """# 项目记忆 — t

## 已验证的事实

- [2026-01-01] 部署前必须先跑 `make smoke`，否则回滚脚本读不到版本号
- [2026-01-02] 换到 esbuild（webpack 在 CI runner 上 OOM，见 docs/adr/0007）
- [2026-01-03] staging 的缓存键带租户前缀 `t:<id>:`，和生产不同
- [2026-01-03] 生产 Redis 是 7.0，staging 落后一个大版本，Lua 脚本的行为有差异

## 失败尝试

- [2026-01-04] 试过把 lockfile 放进 Docker 层缓存，CI 的 runner 不保留层，放弃

## 上次会话

- [2026-01-05] main；make test 通过

## 下次运行

- [2026-01-05] 无
"""

def drop(text, needle): return "\n".join(l for l in text.split("\n") if needle not in l)
def ledger(text, *lines): return text.replace("main；make test 通过", "main；make test 通过\n" + "\n".join("  " + l for l in lines))
def git(d, *a): subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)

def check_exit(f, base="HEAD"):
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            m.cmd_check(argparse.Namespace(file=str(f), max_bytes=m.DEFAULT_MAX_BYTES, max_line=m.DEFAULT_MAX_LINE, base=base, base_file=None))
    except SystemExit as e:
        return e.code, out.getvalue()

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    (root / "AGENTS.md").write_text("## 工作流与陷阱\n\n- 部署前先跑 `make smoke`：回滚脚本靠它写出的版本号\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "staging.md").write_text("# staging\n\n无关内容\n", encoding="utf-8")

    assert not fails(m.check_removed(OLD, OLD, root)), "unchanged file passes"

    rewritten = OLD.replace("见 docs/adr/0007）", "见 docs/adr/0007）；vite 也试过，同样 OOM")
    assert not fails(m.check_removed(OLD, rewritten, root)), "same-topic rewrite needs no ledger line"

    gone = drop(OLD, "make smoke")
    f = fails(m.check_removed(OLD, gone, root))
    assert len(f) == 1 and "移出：[2026-01-01] 部署前必须先跑" in f[0], f

    ok = ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「工作流与陷阱」")
    checks = m.check_removed(OLD, ok, root)
    assert not fails(checks) and any("晋升" in msg for _, msg in checks), checks

    assert "没有标题含" in fails(m.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「代码风格」"), root))[0]
    assert "不存在" in fails(m.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → docs/nope.md"), root))[0]
    assert "找不到这条的关键词" in fails(m.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → docs/staging.md"), root))[0]
    assert "作废要写原因" in fails(m.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → 作废"), root))[0]
    assert not fails(m.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → 作废（部署改走平台，smoke 已并入流水线）"), root))

    merged = drop(OLD, "生产 Redis").replace("和生产不同", "和生产不同；Redis 也落后一个大版本")
    assert fails(m.check_removed(OLD, merged, root)), "a merge below the rewrite ratio must be declared"
    assert not fails(m.check_removed(OLD, ledger(merged, "移出：生产 Redis 是 7.0 → 并入 staging 的缓存键带租户前缀"), root))
    assert "须正好 1 条" in fails(m.check_removed(OLD, ledger(merged, "移出：生产 Redis 是 7.0 → 并入 [2026-01-0"), root))[0]

    ambiguous = ledger(drop(drop(OLD, "生产 Redis"), "缓存键"), "移出：[2026-01-03] → 作废（staging 环境已下线）")
    assert len(fails(m.check_removed(OLD, ambiguous, root))) == 2, "an anchor matching two gone entries accounts for neither"

    grouped = ledger(drop(drop(OLD, "生产 Redis"), "缓存键"), "移出：生产 Redis 是 7.0；staging 的缓存键 → 作废（staging 环境已下线）")
    assert not fails(m.check_removed(OLD, grouped, root)), "one line may carry several anchors"

    stale = ledger(OLD, "移出：早就不在的条目 → 作废（上一次会话留下的行）")
    assert not fails(m.check_removed(OLD, stale, root)), "a ledger line that matches nothing is ignored"

    tricky = OLD.replace("- [2026-01-04] 试过把 lockfile", "- [2026-01-04] 缓存；试过把 lockfile 放进层缓存 -> 失败；另试过把 lockfile")
    hint = fails(m.check_removed(tricky, drop(tricky, "lockfile"), root))[0]
    anchor = hint.split("移出：")[1].split(" → ")[0]
    assert not m.ANCHOR_BREAK_RE.search(anchor), anchor
    pasted = ledger(drop(tricky, "lockfile"), f"移出：{anchor} → 作废（CI 换了带层缓存的 runner）")
    assert not fails(m.check_removed(tricky, pasted, root)), "the suggested line parses back to the same entry"

    uncommitted = ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「工作流与陷阱」", "移出：早就不在的条目 → 作废（更早的会话）")
    last = "\n".join(m.section_bodies(uncommitted)["上次会话"])
    assert m.keep_moves(last, OLD, uncommitted) == ["移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「工作流与陷阱」"], "only lines for entries still gone survive a rewrite"

with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "PROJECT_MEMORY.md"; f.write_text(OLD, encoding="utf-8")
    code, out = check_exit(f)
    assert code == 0 and "无基线，跳过条目去向检查" in out, out

with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "PROJECT_MEMORY.md"; f.write_text(OLD, encoding="utf-8")
    git(d, "init", "-q"); git(d, "add", "-A")
    git(d, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "baseline")
    f.write_text(drop(OLD, "make smoke"), encoding="utf-8")
    code, out = check_exit(f)
    assert code == 1 and "消失的条目没有去向" in out, out
    move = "移出：[2026-01-01] 部署前必须先跑 → 作废（部署改走平台，smoke 已并入流水线）"
    f.write_text(ledger(drop(OLD, "make smoke"), move), encoding="utf-8")
    assert check_exit(f)[0] == 0, "a declared removal passes against HEAD"
    m.cmd_add(argparse.Namespace(file=str(f), section="上次会话", text="main；第二次会话", date="2026-01-06"))
    t = f.read_text(encoding="utf-8")
    assert "- [2026-01-06] main；第二次会话\n  " + move in t, "rewriting 上次会话 keeps an uncommitted 移出 line"
    assert check_exit(f)[0] == 0, "the kept line still accounts for the entry"
    m.cmd_add(argparse.Namespace(file=str(f), section="上次会话", text="main；第三次会话\n" + move, date="2026-01-07"))
    assert f.read_text(encoding="utf-8").count(move) == 1, "a 移出 line already in the new text is not repeated"
    code, out = check_exit(f, base="no-such-ref")
    assert code == 1 and "不是这个仓库里的提交" in out, "a mistyped --base fails instead of skipping the gate"
print("test_memory: ok")
