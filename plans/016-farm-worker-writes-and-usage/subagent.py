#!/usr/bin/env python3
"""Read a Claude Code subagent transcript for farm's gate: files it wrote, token usage.

  python3 subagent.py <agent-id> [--root DIR] [--allow PATTERN]... [--tool-uses N]

Finds ${CLAUDE_CONFIG_DIR:-~/.claude}/projects/*/*/subagents/agent-<agent-id>.jsonl and
prints one JSON object:
  transcript   path of the transcript read
  model        model id of the first assistant message
  tool_uses    tool calls read (unique tool_use ids)
  written      files passed to Edit / Write / NotebookEdit, relative to --root when inside it
  outside      written files no --allow pattern matches; .farm/ and the system temp
               directories are always allowed, other paths outside --root never are
  bash_writes  Bash commands that look like they write files: review by hand
  bash_total   Bash calls in all
  nested       Agent calls: files written by those subagents are not in this transcript
  usage        input / cache_creation_input / cache_read_input / output tokens, summed
               once per assistant message id

The transcript format is Claude Code's internal one. When nothing is read the check
fails instead of passing; --tool-uses (the completion notice's <tool_uses>) catches a
partial read.

Exit: 0 ok | 1 transcript not found or ambiguous | 2 read incomplete (no tool calls,
count differs from --tool-uses, or nested Agent calls) | 3 written files outside --allow
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import sys
import tempfile
from pathlib import Path

WRITE_TOOLS = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}
USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
# 粗筛,只决定哪些命令列给 orchestrator 人工看;漏网的由集成门禁的 git status 兜底
BASH_WRITE_RE = re.compile(
    r"(?<![0-9&>])>{1,2}(?!\s*/dev/null)(?!&)"
    r"|\btee\b|\bsed\b[^|;&]*\s-i|\bperl\s+-\w*i"
    r"|\b(?:mv|cp|rm|mkdir|touch|ln|patch|truncate)\s"
    r"|\bgit\s+(?:checkout|restore|reset|apply|stash|clean|mv|rm|am|cherry-pick|merge|rebase)\b"
    r"|--write\b|\b(?:npm|pnpm|yarn|bun)\s+(?:install|add|i)\b|<<"
)


def find_transcript(agent_id):
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return sorted(glob.glob(os.path.join(base, "projects", "*", "*", "subagents", f"agent-{agent_id}.jsonl")))


TEMP_DIRS = sorted({os.path.realpath(d) for d in (tempfile.gettempdir(), "/tmp", "/var/tmp")})


def allowed(path, patterns):
    if os.path.isabs(path):  # --root 之外:只放行临时目录
        return any(path.startswith(t + "/") for t in TEMP_DIRS)
    for pat in [".farm/"] + patterns:
        stem = pat.rstrip("/")
        if path == stem or path.startswith(stem + "/") or fnmatch.fnmatchcase(path, pat):
            return True
    return False


def relative(path, root):
    real = os.path.realpath(path)
    try:
        rel = os.path.relpath(real, root)
    except ValueError:
        return real
    return real if rel.startswith("..") else rel


def read(transcript, root, patterns):
    tool_ids, written, bash, nested, usage, model = set(), [], [], 0, {}, None
    for line in Path(transcript).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue  # 写到一半的末行
        msg = entry.get("message")
        if entry.get("type") != "assistant" or not isinstance(msg, dict):
            continue
        model = model or msg.get("model")
        if msg.get("id") and isinstance(msg.get("usage"), dict):
            usage[msg["id"]] = msg["usage"]  # 同一条消息拆成多行时,每行带同一份 usage
        for block in msg.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("id") in tool_ids:
                continue
            tool_ids.add(block.get("id"))
            name, args = block.get("name"), block.get("input") or {}
            if name in WRITE_TOOLS and args.get(WRITE_TOOLS[name]):
                written.append(relative(args[WRITE_TOOLS[name]], root))
            elif name == "Bash":
                bash.append(str(args.get("command", "")))
            elif name == "Agent":
                nested += 1
    written = sorted(set(written))
    return {
        "transcript": transcript,
        "model": model,
        "tool_uses": len(tool_ids),
        "written": written,
        "outside": [p for p in written if not allowed(p, patterns)],
        "bash_writes": [c[:200] for c in bash if BASH_WRITE_RE.search(c)],
        "bash_total": len(bash),
        "nested": nested,
        "usage": {k: sum(u.get(k) or 0 for u in usage.values()) for k in USAGE_KEYS},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent_id")
    ap.add_argument("--root", default=".", help="project root; written paths are made relative to it")
    ap.add_argument("--allow", action="append", default=[], help="path, directory or glob relative to --root")
    ap.add_argument("--tool-uses", type=int, help="<tool_uses> from the completion notice")
    args = ap.parse_args()

    found = find_transcript(args.agent_id)
    if len(found) != 1:
        print(f"ERROR: agent-{args.agent_id}.jsonl 找到 {len(found)} 个: {found}", file=sys.stderr)
        sys.exit(1)
    result = read(found[0], os.path.realpath(args.root), args.allow)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    problems = []
    if result["tool_uses"] == 0:
        problems.append("一次工具调用都没读到,转录格式可能变了")
    if args.tool_uses is not None and result["tool_uses"] != args.tool_uses:
        problems.append(f"读到 {result['tool_uses']} 次工具调用,完成通知是 {args.tool_uses} 次")
    if result["nested"]:
        problems.append(f"worker 派了 {result['nested']} 个子代理,它们改的文件不在这份转录里")
    if problems:
        print("FAIL 核对不完整: " + "; ".join(problems), file=sys.stderr)
        sys.exit(2)
    if result["outside"]:
        print(f"FAIL 越界写入 {len(result['outside'])} 个文件", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
