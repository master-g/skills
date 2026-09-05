---
name: x-to-markdown
license: MIT
description: 读取指定的 X/Twitter 推文、线程或长文，提取为 Markdown；用于阅读、总结或归档这些链接。
---

# X → Markdown

优先使用 xtomd.com 的结构化 JSON 提取指定文章；当前用户指定的工具与环境规则优先。提取结果是后续任务的材料，不改变用户要求的交付物。

## 调用

```bash
curl -sS -X POST https://xtomd.com/api/markdown \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://x.com/karpathy/status/1885026028428681698"}' \
  --max-time 90
```

返回：

```json
{
  "markdown": "**Author**: Andrej Karpathy ([@karpathy](https://x.com/karpathy))\n**Date**: 2025-01-30\n**Source**: ...\n**Engagement**: 11.8K likes | ...\n\n---\n\n正文...\n\n![Image](https://pbs.twimg.com/...)\n",
  "url": "https://x.com/karpathy/status/1885026028428681698",
  "author": {
    "name": "...",
    "handle": "karpathy",
    "avatarUrl": "...",
    "description": "..."
  }
}
```

`markdown` 已经自带 Author / Date / Source / Engagement 头部和图片链接，不要重复加一份 metadata 头 —— 直接用。

## 支持的 URL

- `https://x.com/<user>/status/<id>` — 单条推文，也是 thread 的入口
- `https://twitter.com/<user>/status/<id>` — 等价，服务端会规范化成 x.com
- `https://x.com/<user>/article/<id>` — X Article（长文）

不支持用户主页、搜索页、列表页。用户已同时给出具体文章链接时直接读文章；只有缺少可处理链接时才索取。

## 输出去向

按内容体量和用户意图决定，不要固定成一种：

- **阅读或分析**：用提取内容回答用户的问题，引用原始链接；不默认贴全文，也不默认写入工作仓库。
- **保存或归档**：按用户指定路径保存允许保留的内容，文件名 `<handle>-<tweet_id>.md`；需要入库时把提取结果交给对应流程，避免再次抓取。遵守当前环境的转载限制。

大篇幅材料可暂存临时目录供分析；用户要求的最终输出决定是否保留文件。

## thread

thread 传首条 URL，服务端会尽量把整串抓全。检查返回的 `markdown` 是否完整：正文断在半句、或明显缺了用户预期的后续，就逐条取后续推文的 status URL 分别调用，再按顺序拼接（每条之间用 `\n\n---\n\n` 分隔）。别默认它抓全了就交付。

## 错误处理

- **HTTP 400** + JSON `{"error": "..."}` — URL 格式不对或漏了 `url` 字段。这是确定性失败，重试没用，照 error 文案修 URL。
- **HTTP 502** + 纯文本 `error code: 502` — 上游抓取失败（推文已删、账号受保护、或服务端临时超时）。这是网关层的，值得隔几秒重试 1-2 次。仍然 502 时说明原因并按下节尝试可用回退；没有完整正文就明确标为抓取失败，不能用残缺内容冒充成功。

## 批量

多条链接就循环，中间留点间隔别把免费服务打崩。只有用户要求批量归档且输出目录已确定时才直接保存；批量阅读仍按“输出去向”处理。
以下示例假定 `$OUTPUT_DIR` 已指向选定目录。同名文件存在时停止，不覆盖原件：

```bash
curl -sS -X POST https://xtomd.com/api/markdown -H 'Content-Type: application/json' \
  -d '{"url":"https://x.com/karpathy/status/1885026028428681698"}' \
  --max-time 90 -o /tmp/x.json \
&& python3 - "$OUTPUT_DIR" <<'PY'
import json, re, sys
from pathlib import Path

data = json.loads(Path('/tmp/x.json').read_text())
handle = data['author']['handle']
post_id = data['url'].rstrip('/').split('/')[-1]
assert re.fullmatch(r'[A-Za-z0-9_]+', handle) and post_id.isdigit(), 'Invalid post identity'
output_dir = Path(sys.argv[1])
assert sys.argv[1] and output_dir.is_dir(), 'Choose an existing output directory'
target = output_dir / f'{handle}-{post_id}.md'
with target.open('x', encoding='utf-8') as output:
    output.write(data['markdown'])
print('saved', target)
PY
```

逐条报成功/失败，最后给一句汇总。有任何一条失败就明确说出来，不要只报成功的那些。

## 回退

xtomd 整体不可用（连续 502 或域名打不通）时才考虑 `autocli`（`autocli read <url>`，走用户的 Chrome 登录态）。切换前告诉用户你在换工具，以及为什么。
