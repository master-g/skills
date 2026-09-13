#!/usr/bin/env python3
"""Fails if convention detection/upgrade in setup_context.py breaks. Run: python3 test_setup_context.py"""
import sys, tempfile, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import setup_context as sc

TPL = sc.template_convention()
assert TPL.rstrip("\n").endswith("-->"), "template convention must end with the marker"

def run(d, *flags):
    return subprocess.run([sys.executable, str(HERE / "setup_context.py"), "--dir", str(d), *flags],
                          capture_output=True, text=True).stdout

BASE = "# x\n\n## 技术栈\n- go\n\n## 命令\n- make\n\n## 代码风格\n- fmt\n\n## 禁止文件\n- dist\n\n## 审查规则\n- ci\n\n"

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # fresh dir -> created from template, marker present, validate convention latest
    out = run(d); assert "created CLAUDE.md from template" in out, out
    assert sc.convention_state((d / "CLAUDE.md").read_text())["state"] == "latest"

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "CLAUDE.md"
    # legacy diverged block: reported, untouched without flag; replaced (old text printed) with flag
    f.write_text(BASE + "## 项目记忆 (回写约定)\n跨会话信息记录在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。完成任务后回写。\n")
    out = run(d); assert "OUTDATED (legacy" in out and "完成任务后回写" in f.read_text(), out
    out = run(d, "--upgrade-convention"); t = f.read_text()
    assert "完成任务后回写" in out and "完成任务后回写" not in t and t.rstrip().endswith("-->") and "- go" in t, out
    assert sc.convention_state(t)["state"] == "latest"

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "CLAUDE.md"
    # marked but outdated block + custom text after marker -> auto upgrade, custom kept
    f.write_text(BASE + "## 项目记忆 (回写约定)\n旧正文\n<!-- bootstrap-claude convention v1 -->\n\n自定义补充段\n")
    out = run(d); t = f.read_text()
    assert "upgraded" in out and "旧正文" not in t and "自定义补充段" in t and "memory.py check" in t, out
    assert t.index("-->") < t.index("自定义补充段")

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "CLAUDE.md"
    # same text, no marker, custom trailing paragraph -> marker inserted before custom text (prefix rule)
    body = TPL.rstrip("\n").rsplit("\n", 1)[0]  # template without marker line
    f.write_text(BASE + body + "\n\n事实写回速查:\n- 决策 → ADR\n")
    out = run(d); t = f.read_text()
    assert "upgraded" in out and "-->\n\n事实写回速查" in t, out  # blank line before custom text kept
    assert sc.convention_state(t)["state"] == "latest"
    # second run: nothing changes
    before = t; out = run(d); assert "convention: latest" in out and f.read_text() == before, out

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "CLAUDE.md"
    # unmanaged: mentions memory file, no heading -> reported, file untouched
    f.write_text(BASE + "读 PROJECT_MEMORY.md 再开工。\n"); before = f.read_text()
    out = run(d); assert "unmanaged" in out and f.read_text() == before, out
    assert "FAIL 项目记忆" in run(d, "--validate")
print("test_setup_context: ok")
