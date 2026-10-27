"""从 Claude Code 会话转录（.jsonl）里抽出一段时间内的工具调用耗时。

用法：
  python3 -I session_timeline.py <session.jsonl> <开始 UTC ISO> <结束 UTC ISO> [timeline.tsv]

输出：阶段总时长、工具耗时合计、残差（总时长 − 工具耗时，近似模型生成与思考时间）、
按类别汇总的工具耗时，以及 ≥10s 的单次调用。给了第四个参数时把逐条事件写成 TSV。
工具耗时 = tool_result 的时间戳 − 发出 tool_use 那条 assistant 记录的时间戳。
类别按工具名与命令文本粗分，规则见 category()。
"""

import collections
import json
import sys
from datetime import datetime


def ts(r):
    return datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))


def category(name, inp):
    text = json.dumps(inp, ensure_ascii=False)
    if name == "Read" and ".png" in text:
        return "读截图"
    if name == "Write":
        return "写页面/脚本"
    if "--snap" in text:
        return "构建+快照"
    if "build.py" in text:
        return "构建（无快照）"
    if "magick" in text or "sips" in text:
        return "切分截图"
    if "ego-browser" in text or name == "Skill":
        return "浏览器验证"
    return "读文档/查样式/其他"


def main():
    path, start, end = sys.argv[1:4]
    tsv = sys.argv[4] if len(sys.argv) > 4 else None
    start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
    calls, results, usage, events = {}, {}, {}, []
    last = start
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if r.get("type") not in ("assistant", "user") or "timestamp" not in r:
            continue
        t = ts(r)
        if not start <= t < end:
            continue
        m = r["message"]
        content = m.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        if r["type"] == "assistant":
            usage[m["id"]] = m.get("usage", {})
            last = max(last, t)
        for b in content:
            if b.get("type") == "tool_use":
                inp = b["input"]
                desc = inp.get("description") or inp.get("file_path") or inp.get("skill") or ""
                calls[b["id"]] = (t, b["name"], desc, category(b["name"], inp))
                events.append((t, "tool_use", b["name"], desc))
            elif b.get("type") == "tool_result":
                results[b["tool_use_id"]] = t
                events.append((t, "tool_result", "", b["tool_use_id"]))
    agg = collections.defaultdict(lambda: [0, 0.0])
    long_calls = []
    for k, (t, name, desc, cat) in calls.items():
        dur = (results.get(k, t) - t).total_seconds()
        agg[cat][0] += 1
        agg[cat][1] += dur
        if dur >= 10:
            long_calls.append((t, dur, cat, desc))
    total = (last - start).total_seconds()
    tool = sum(v[1] for v in agg.values())
    print(f"阶段 {total:.0f}s · 工具 {tool:.0f}s · 残差（近似模型时间）{total - tool:.0f}s")
    for cat, (n, s) in sorted(agg.items(), key=lambda x: -x[1][1]):
        print(f"{cat}\t{n} 次\t{s:.0f}s")
    out = sum(u.get("output_tokens", 0) for u in usage.values())
    read = sum(u.get("cache_read_input_tokens", 0) for u in usage.values())
    print(f"assistant 消息 {len(usage)} 条 · 输出 {out} tokens · 缓存读 {read} tokens")
    for t, dur, cat, desc in sorted(long_calls):
        print(f"{t:%H:%M:%S}\t{dur:.0f}s\t{cat}\t{desc}")
    if tsv:
        with open(tsv, "w", encoding="utf-8") as f:
            for t, kind, name, desc in sorted(events):
                f.write(f"{t:%H:%M:%S}\t{kind}\t{name}\t{desc}\n")


if __name__ == "__main__":
    main()
