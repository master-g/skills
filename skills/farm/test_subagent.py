#!/usr/bin/env python3
"""Smallest check that fails if subagent.py misreads a transcript. Run: python3 test_subagent.py"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "subagent.py"


def assistant(msg_id, blocks, usage=None, model="claude-sonnet-5-5"):
    msg = {"id": msg_id, "model": model, "content": blocks,
           "usage": usage or {"input_tokens": 1, "cache_creation_input_tokens": 10,
                              "cache_read_input_tokens": 100, "output_tokens": 5}}
    return {"type": "assistant", "message": msg}


def tool(tid, name, **args):
    return {"type": "tool_use", "id": tid, "name": name, "input": args}


def run(config, agent, *args):
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config))
    p = subprocess.run([sys.executable, str(SCRIPT), agent, *args], env=env, capture_output=True, text=True)
    return p.returncode, (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr


with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    root = d / "proj"
    (root / "src").mkdir(parents=True)
    sub = d / "config" / "projects" / "-proj" / "sess-1" / "subagents"
    sub.mkdir(parents=True)

    def transcript(agent, entries):
        lines = [json.dumps(e) for e in entries]
        (sub / f"agent-{agent}.jsonl").write_text("\n".join(lines) + "\n{\"type\": \"assist", encoding="utf-8")

    transcript("good", [
        {"type": "user", "message": {"role": "user", "content": "读 brief"}},
        # 一条消息拆成两行,两行带同一份 usage:只算一次
        assistant("m1", [tool("t1", "Edit", file_path=str(root / "src/a.py"))]),
        assistant("m1", [tool("t2", "Write", file_path=str(root / ".farm/x-report.md"))]),
        assistant("m2", [tool("t3", "Bash", command="sed -i '' s/a/b/ src/b.py"),
                         tool("t4", "Bash", command="git status 2>&1 | tail -3"),
                         tool("t5", "Write", file_path=os.path.join(tempfile.gettempdir(), "scratch.py"))]),
        assistant("m3", [tool("t6", "Edit", file_path=str(root / "README.md"))]),
    ])
    code, out, err = run(d / "config", "good", "--root", str(root), "--allow", "src/", "--tool-uses", "6")
    assert code == 3, (code, err)                       # README.md 越界
    assert out["outside"] == ["README.md"], out["outside"]
    assert "src/a.py" in out["written"] and ".farm/x-report.md" in out["written"]
    assert out["tool_uses"] == 6 and out["bash_total"] == 2 and out["nested"] == 0
    assert out["bash_writes"] == ["sed -i '' s/a/b/ src/b.py"], out["bash_writes"]
    assert out["usage"] == {"input_tokens": 3, "cache_creation_input_tokens": 30,
                            "cache_read_input_tokens": 300, "output_tokens": 15}, out["usage"]
    assert out["model"] == "claude-sonnet-5-5"

    code, out, _ = run(d / "config", "good", "--root", str(root), "--allow", "src/", "--allow", "README.md")
    assert code == 0 and out["outside"] == [], (code, out)

    code, _, err = run(d / "config", "good", "--root", str(root), "--allow", "*", "--tool-uses", "7")
    assert code == 2 and "完成通知是 7 次" in err, (code, err)

    transcript("blank", [{"type": "user", "message": {"role": "user", "content": "hi"}},
                         assistant("m1", [{"type": "text", "text": "done"}])])
    code, _, err = run(d / "config", "blank", "--root", str(root))
    assert code == 2 and "一次工具调用都没读到" in err, (code, err)

    transcript("nested", [assistant("m1", [tool("t1", "Agent", prompt="x"),
                                           tool("t2", "Edit", file_path=str(root / "src/a.py"))])])
    code, _, err = run(d / "config", "nested", "--root", str(root), "--allow", "src/")
    assert code == 2 and "子代理" in err, (code, err)

    # --root 之外、又不在临时目录里的写入,--allow 怎么写都算越界
    elsewhere = os.path.realpath("/opt/farm-test/x.txt")
    transcript("abs", [assistant("m1", [tool("t1", "Write", file_path=elsewhere)])])
    code, out, _ = run(d / "config", "abs", "--root", str(root), "--allow", "*")
    assert code == 3 and out["outside"] == [elsewhere], (code, out)

    code, _, err = run(d / "config", "missing", "--root", str(root))
    assert code == 1 and "找到 0 个" in err, (code, err)

print("test_subagent: ok")
