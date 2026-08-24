---
name: x-to-markdown
description: 用 xtomd.com 免费 API 把 X/Twitter 的推文、thread、长文（X Article）抓成干净 markdown。只要用户给出 x.com 或 twitter.com 的链接，或者说"把这条推文转成 markdown / 存下来 / 归档 / 存进 Obsidian / 帮我读一下这条 X"、"convert this tweet/thread/X article to markdown"、"archive this thread"、"read this x.com link"，就用这个 skill —— 即使用户没提 markdown 或 xtomd。抓 X/Twitter 内容时优先于 autocli、ego-browser、WebFetch、jina-reader，因为那些工具在 X 上要么被登录墙挡住、要么拿到的是带 UI 噪音的残缺正文。
---

# X → Markdown

xtomd.com 是抓 X/Twitter 内容的首选：免费、免 auth、返回结构化 JSON。X 的正文对未登录抓取器基本不可见，所以别拿 WebFetch 或通用浏览器工具去试 —— 直接打这个 API。

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
  "author": { "name": "...", "handle": "karpathy", "avatarUrl": "...", "description": "..." }
}
```

`markdown` 已经自带 Author / Date / Source / Engagement 头部和图片链接，不要重复加一份 metadata 头 —— 直接用。

## 支持的 URL

- `https://x.com/<user>/status/<id>` — 单条推文，也是 thread 的入口
- `https://twitter.com/<user>/status/<id>` — 等价，服务端会规范化成 x.com
- `https://x.com/<user>/article/<id>` — X Article（长文）

不支持用户主页（`x.com/karpathy`）、搜索页、列表页。用户给这类链接时先说明这一点，再问要哪条具体推文 —— 别猜一条抓。

## 输出去向

按内容体量和用户意图决定，不要固定成一种：

- **直接贴在回复里** — 单条短推文，或用户只是想"看看这条说了什么"。抓完把 `markdown` 原文贴出来即可。
- **落盘成文件** — 长文、thread、批量，或用户提到保存 / 归档 / Obsidian / Notion / 第二大脑 / 之后要引用。用 Write 工具存，文件名 `<handle>-<tweet_id>.md`（如 `karpathy-1885026028428681698.md`），默认落在当前目录，用户指定路径就用他的。存完报路径 + 头几行预览，不要把全文再贴一遍。

拿不准就落盘并给预览 —— 用户想看全文时再贴，比反过来省事。

## thread

thread 传首条 URL，服务端会尽量把整串抓全。检查返回的 `markdown` 是否完整：正文断在半句、或明显缺了用户预期的后续，就逐条取后续推文的 status URL 分别调用，再按顺序拼接（每条之间用 `\n\n---\n\n` 分隔）。别默认它抓全了就交付。

## 错误处理

- **HTTP 400** + JSON `{"error": "..."}` — URL 格式不对或漏了 `url` 字段。这是确定性失败，重试没用，照 error 文案修 URL。
- **HTTP 502** + 纯文本 `error code: 502` — 上游抓取失败（推文已删、账号受保护、或服务端临时超时）。这是网关层的，值得隔几秒重试 1-2 次。仍然 502 就停手，告诉用户抓不到并说明可能原因 —— 别静默降级去用别的工具抓个残缺版本冒充成功。

## 批量

多条链接就循环，中间留点间隔别把免费服务打崩。想跳过 context 直接落盘（长文或量大时值得）：

```bash
curl -sS -X POST https://xtomd.com/api/markdown -H 'Content-Type: application/json' \
  -d '{"url":"https://x.com/karpathy/status/1885026028428681698"}' \
  --max-time 90 -o /tmp/x.json \
&& python3 -c "import json;d=json.load(open('/tmp/x.json'));f=d['author']['handle']+'-'+d['url'].rstrip('/').split('/')[-1]+'.md';open(f,'w').write(d['markdown']);print('saved',f)"
```

逐条报成功/失败，最后给一句汇总。有任何一条失败就明确说出来，不要只报成功的那些。

## 回退

xtomd 整体不可用（连续 502 或域名打不通）时才考虑 `autocli`（`autocli read <url>`，走用户的 Chrome 登录态）。切换前告诉用户你在换工具，以及为什么。
