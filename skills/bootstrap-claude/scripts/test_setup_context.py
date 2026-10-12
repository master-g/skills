#!/usr/bin/env python3
"""Fails if convention detection/upgrade in setup_context.py breaks. Run: python3 test_setup_context.py"""
import os, sys, tempfile, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import setup_context as sc

TPL = sc.template_convention()
assert TPL.rstrip("\n").endswith("-->"), "template convention must end with the marker"

def run(d, *flags):
    return subprocess.run([sys.executable, str(HERE / "setup_context.py"), "--dir", str(d), *flags],
                          capture_output=True, text=True).stdout

BASE = "# x\n\n## 技术栈\n- go\n\n## 导航\n- src/\n\n## 命令\n- make\n\n## 工作流与陷阱\n- push 前先问\n\n## 代码风格\n- fmt\n\n## 禁止文件\n- dist\n\n## 审查规则\n- ci\n\n"

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # fresh dir -> created from template, marker present, validate convention latest
    out = run(d); assert "created AGENTS.md from template" in out, out
    assert sc.convention_state((d / "AGENTS.md").read_text())["state"] == "latest"
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n"

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # legacy diverged block: reported, untouched without flag; replaced (old text printed) with flag
    f.write_text(BASE + "## 项目记忆 (回写约定)\n跨会话信息记录在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。完成任务后回写。\n")
    out = run(d); assert "OUTDATED (legacy" in out and "完成任务后回写" in f.read_text(), out
    out = run(d, "--upgrade-convention"); t = f.read_text()
    assert "完成任务后回写" in out and "完成任务后回写" not in t and t.rstrip().endswith("-->") and "- go" in t, out
    assert sc.convention_state(t)["state"] == "latest"

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # marked but outdated block + custom text after marker -> auto upgrade, custom kept
    f.write_text(BASE + "## 项目记忆 (回写约定)\n旧正文\n<!-- bootstrap-claude convention v1 -->\n\n自定义补充段\n")
    out = run(d); t = f.read_text()
    assert "upgraded" in out and "旧正文" not in t and "自定义补充段" in t and "memory.py check" in t, out
    assert t.index("-->") < t.index("自定义补充段")

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # same text, no marker, custom trailing paragraph -> marker inserted before custom text (prefix rule)
    body = TPL.rstrip("\n").rsplit("\n", 1)[0]  # template without marker line
    f.write_text(BASE + body + "\n\n事实写回速查:\n- 决策 → ADR\n")
    out = run(d); t = f.read_text()
    assert "upgraded" in out and "-->\n\n事实写回速查" in t, out  # blank line before custom text kept
    assert sc.convention_state(t)["state"] == "latest"
    # second run: nothing changes
    before = t; out = run(d); assert "convention: latest" in out and f.read_text() == before, out

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # unmanaged: mentions memory file, no heading -> reported, file untouched
    f.write_text(BASE + "读 PROJECT_MEMORY.md 再开工。\n"); before = f.read_text()
    out = run(d); assert "unmanaged" in out and f.read_text() == before, out
    assert "FAIL 项目记忆" in run(d, "--validate")
BASE_EN = ("# x\n\n## Tech Stack\n- go\n\n## Repo Map\n- src/\n\n## Commands\n- make\n\n## Workflow\n- ask before push\n\n## Code Style\n- fmt\n\n"
           "## Protected Files\n- dist\n\n## Code Review\n- ci\n\n")

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp); f = d / "AGENTS.md"
    # English headings are recognised by alias: nothing appended except the convention block
    f.write_text(BASE_EN)
    out = run(d); t = f.read_text()
    assert "already has all required sections" in out, out
    assert "_待填写_" not in t and "## 技术栈" not in t, t
    v = run(d, "--validate")
    assert "缺失" not in v and "占位符" not in v, v
    assert "技术栈 (匹配 ## Tech Stack): 已填写" in v, v

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # Firefox layout: AGENTS.md real + CLAUDE.md is the one-line import -> no CONFLICT, nothing rewritten
    (d / "AGENTS.md").write_text(BASE); (d / "CLAUDE.md").write_text("@AGENTS.md\n")
    r = subprocess.run([sys.executable, str(HERE / "setup_context.py"), "--dir", str(d)],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "source of truth: AGENTS.md" in r.stdout, r.stdout + r.stderr
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n" and "pointer:" not in r.stdout
    assert "指向一致" in run(d, "--validate")

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # legacy layout: CLAUDE.md real + AGENTS.md symlink -> migrated, no symlink left anywhere
    (d / "CLAUDE.md").write_text(BASE); os.symlink("CLAUDE.md", d / "AGENTS.md")
    out = run(d)
    assert "migrated: CLAUDE.md content moved to AGENTS.md" in out, out
    a, c = d / "AGENTS.md", d / "CLAUDE.md"
    assert a.is_file() and not a.is_symlink() and "- go" in a.read_text()
    assert c.is_file() and not c.is_symlink() and c.read_text() == "@AGENTS.md\n"
    before = (a.read_text(), c.read_text()); run(d); assert (a.read_text(), c.read_text()) == before  # idempotent

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # lone pointer: CLAUDE.md = @AGENTS.md, no AGENTS.md -> AGENTS.md created, pointer untouched
    (d / "CLAUDE.md").write_text("@AGENTS.md\n")
    out = run(d)
    assert "created AGENTS.md from template" in out, out
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n" and (d / "AGENTS.md").is_file()

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # conflict: two real files -> exit 2 without flag; --resolve-conflict claude moves CLAUDE.md content into AGENTS.md
    (d / "CLAUDE.md").write_text(BASE); (d / "AGENTS.md").write_text("# other\n")
    r = subprocess.run([sys.executable, str(HERE / "setup_context.py"), "--dir", str(d)],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "CONFLICT" in r.stderr, r.stderr
    out = run(d, "--resolve-conflict", "claude")
    assert (d / "AGENTS.md.bak").read_text() == "# other\n" and "- go" in (d / "AGENTS.md").read_text(), out
    assert (d / "CLAUDE.md").read_text() == "@AGENTS.md\n"
print("test_setup_context: ok")
