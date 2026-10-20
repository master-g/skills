# X 链接

适用于以下三种链接；X 的用户主页、搜索页、列表页按普通 URL 处理。

- `https://x.com/<user>/status/<id>`：单条推文，也是 thread 的入口
- `https://twitter.com/<user>/status/<id>`：同上，服务端会规范化成 x.com
- `https://x.com/<user>/article/<id>`：X Article（长文）

## 抓取

```bash
curl -sS -X POST https://xtomd.com/api/markdown \
  -H 'Content-Type: application/json' \
  -d '{"url":"<用户给的链接>"}' \
  --max-time 90
```

返回 JSON 的 `markdown` 以 Author / Date / Source / Engagement 头部开始，正文和图片链接在第一个 `---` 之后；`author.name` 是作者名。写 entry 时：

- `title` 写成「<作者名>：<帖子主题>」，主题从正文概括。
- 摘要和要点基于 `---` 之后的正文。
- `source` 填用户给的链接，与查重时搜索的字符串一致。

## thread 完整性

thread 传首条链接，服务端会尽量抓全整串。正文断在半句、或缺了明显的后续时，逐条取后续推文的 status 链接分别调用，按顺序拼接（每条之间用 `---` 分隔），拼全后再写摘要。

## 错误与回退

- HTTP 400 + JSON `{"error": "..."}`：链接格式不对，按 error 文案修正链接后再调用。
- HTTP 502 + 纯文本 `error code: 502`：上游抓取失败（推文已删、账号受保护或服务端超时），隔几秒重试 1–2 次。

xtomd 仍不可用时，先告诉用户要换工具及原因，再依次尝试：

1. `autocli` 可用时运行 `autocli read <url>`，它走用户 Chrome 的登录态；
2. 需要登录的浏览器工具，打开链接读取正文。

都拿不到完整正文时按抓取失败处理，残缺内容只作失败说明的依据。
