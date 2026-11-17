#!/usr/bin/env python3
"""Run: python3 test_removal_gate.py. Plan 034 Step 2 ports these cases into test_memory.py."""
import tempfile
from pathlib import Path

import removal_gate as g

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


def fails(checks):
    return [m for ok, m in checks if not ok]


def drop(text, needle):
    return "\n".join(l for l in text.split("\n") if needle not in l)


def ledger(text, *lines):
    return text.replace("main；make test 通过", "main；make test 通过\n" + "\n".join("  " + l for l in lines))


with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    (root / "AGENTS.md").write_text("## 工作流与陷阱\n\n- 部署前先跑 `make smoke`：回滚脚本靠它写出的版本号\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "staging.md").write_text("# staging\n\n无关内容\n", encoding="utf-8")

    assert not fails(g.check_removed(OLD, OLD, root)), "unchanged file passes"

    rewritten = OLD.replace("见 docs/adr/0007）", "见 docs/adr/0007）；vite 也试过，同样 OOM")
    assert not fails(g.check_removed(OLD, rewritten, root)), "same-topic rewrite needs no ledger line"

    gone = drop(OLD, "make smoke")
    f = fails(g.check_removed(OLD, gone, root))
    assert len(f) == 1 and "移出：[2026-01-01] 部署前必须先跑" in f[0], f

    ok = ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「工作流与陷阱」")
    checks = g.check_removed(OLD, ok, root)
    assert not fails(checks) and any("晋升" in m for _, m in checks), checks

    assert "没有标题含" in fails(g.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「代码风格」"), root))[0]
    assert "不存在" in fails(g.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → docs/nope.md"), root))[0]
    assert "找不到这条的关键词" in fails(g.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → docs/staging.md"), root))[0]
    assert "作废要写原因" in fails(g.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → 作废"), root))[0]
    assert not fails(g.check_removed(OLD, ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → 作废（部署改走平台，smoke 已并入流水线）"), root))

    merged = drop(OLD, "生产 Redis").replace("和生产不同", "和生产不同；Redis 也落后一个大版本")
    assert fails(g.check_removed(OLD, merged, root)), "a merge below the rewrite ratio must be declared"
    assert not fails(g.check_removed(OLD, ledger(merged, "移出：生产 Redis 是 7.0 → 并入 staging 的缓存键带租户前缀"), root))
    assert "须正好 1 条" in fails(g.check_removed(OLD, ledger(merged, "移出：生产 Redis 是 7.0 → 并入 [2026-01-0"), root))[0]

    ambiguous = ledger(drop(drop(OLD, "生产 Redis"), "缓存键"), "移出：[2026-01-03] → 作废（staging 环境已下线）")
    assert len(fails(g.check_removed(OLD, ambiguous, root))) == 2, "an anchor matching two gone entries accounts for neither"

    grouped = ledger(drop(drop(OLD, "生产 Redis"), "缓存键"), "移出：生产 Redis 是 7.0；staging 的缓存键 → 作废（staging 环境已下线）")
    assert not fails(g.check_removed(OLD, grouped, root)), "one line may carry several anchors"

    stale = ledger(OLD, "移出：早就不在的条目 → 作废（上一次会话留下的行）")
    assert not fails(g.check_removed(OLD, stale, root)), "a ledger line that matches nothing is ignored"

    tricky = OLD.replace("- [2026-01-04] 试过把 lockfile", "- [2026-01-04] 缓存；试过把 lockfile 放进层缓存 -> 失败；另试过把 lockfile")
    hint = fails(g.check_removed(tricky, drop(tricky, "lockfile"), root))[0]
    anchor = hint.split("移出：")[1].split(" → ")[0]
    assert not g.ANCHOR_BREAK_RE.search(anchor), anchor
    pasted = ledger(drop(tricky, "lockfile"), f"移出：{anchor} → 作废（CI 换了带层缓存的 runner）")
    assert not fails(g.check_removed(tricky, pasted, root)), "the suggested line parses back to the same entry"

    uncommitted = ledger(gone, "移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「工作流与陷阱」", "移出：早就不在的条目 → 作废（更早的会话）")
    last = "\n".join(g.sections(uncommitted)["上次会话"])
    assert g.keep_moves(last, OLD, uncommitted) == ["移出：[2026-01-01] 部署前必须先跑 → AGENTS.md「工作流与陷阱」"], "only lines for entries still gone survive a rewrite"

print("test_removal_gate: ok")
