#!/usr/bin/env python3
"""Smallest check that fails if memory.py's gate or replace logic breaks. Run: python3 test_memory.py"""
import sys, tempfile, argparse
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
print("test_memory: ok")
