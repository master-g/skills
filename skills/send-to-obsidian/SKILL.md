---
name: send-to-obsidian
license: MIT
description: 把链接、本地材料或文本保存到 Obsidian inbox；用户明确要求盘点时执行 --sweep。
---

# send-to-obsidian

把参数中的 URL、本地路径、目录或文本抓成 INBOX **entry**，写入 vault，供台账查询。盘点过期条目是单独的 `--sweep` 操作。

参数即输入：`/send-to-obsidian <url | path | dir | 文本>`。参数为空时先向用户索取输入。

子命令：`/send-to-obsidian --sweep` 定位 vault 与现有 inbox 后，只做盘点，不创建目录或台账；读取 [目录与盘点](references/directory-and-sweep.md) 的盘点部分。没有 inbox 时报告无条目。

**intake 只产登记档，不做蒸馏。** 摘要 entry 记录源路径，蒸馏是独立的后续动作，由人看过 entry 后发起。原件在 intake 时不动。

## 1. 定位 vault

运行 `obsidian eval code="app.vault.adapter.basePath"`，取当前 vault 路径存为 `$VAULT`。

命令失败时（Obsidian 未运行或 CLI 未安装），改读 `~/Library/Application Support/obsidian/obsidian.json` 的 `vaults` 字段取路径列表。

列表为空或多于一条时，把候选路径列给用户，等用户选定后再继续。

**完成标准**：`$VAULT` 已确定且目录存在。

## 2. 探测布局，确认 inbox 与台账

vault 有两种布局，探测而非假定——2026-08 的重构把顶层 `00 - INBOX/` 改成了 `inbox/`：

```bash
if [ -d "$VAULT/inbox" ]; then
  INBOX="inbox"
elif [ -d "$VAULT/00 - INBOX" ]; then
  INBOX="00 - INBOX"
else
  INBOX="inbox"
fi
```

`--sweep` 在探测到这里后直接进入盘点，不执行以下创建、查重或写入步骤。目录不存在时报告无条目并结束。

普通 intake 才在 `$VAULT/$INBOX/` 不存在时创建它（两者都不存在时用 `inbox`，新布局是默认）。

`$VAULT/$INBOX/_inbox.md` 不存在时按下文[台账格式](#台账格式)创建它，其中 dataview 的 `FROM` 用探测到的 `$INBOX`。

**完成标准**：目录与台账文件均存在，`$INBOX` 已确定。

## 3. 查重

按输入类型查已有 entry：URL 输入用 `grep -rlF "<url>" "$VAULT/$INBOX/"`；路径或文本输入用标题 slug 匹配文件名。

命中时把已有 entry 的路径与捕获日展示给用户，问选哪一项：更新（保留原文件，重写摘要）、覆盖（整篇重写）、另存为新 entry、放弃。等用户回答后再继续。

**完成标准**：确认无重复，或用户已选定处理方式。

## 4. 抓取并写入 entry

按输入类型取内容：

| 输入     | 抓取方式                                                                                                     |
| -------- | ------------------------------------------------------------------------------------------------------------ |
| URL      | 复用会话中已提取的正文；否则先用可用站点技能，X 用 x-to-markdown；再用通用正文提取或需要登录/JS 的浏览器工具 |
| 本地路径 | Read 工具                                                                                                    |
| **目录** | 按 [目录与盘点](references/directory-and-sweep.md) 的目录类型映射处理                                        |
| 文本     | 直接使用参数文本                                                                                             |

抓取失败时向用户报告失败原因，并问是否只存链接与标题。

按下文 [Entry 格式](#entry-格式) 写文件到 `$VAULT/$INBOX/`。摘要写 3–5 句，要点写 3–7 条，两者都基于抓到的正文。正文未抓到时，摘要处写「原文未抓取」。

`inbox/` **豁免全部必填 frontmatter 字段**——它的职责是零摩擦接住内容，质量门禁在出口而非入口。只保证 `source` 有值。

**完成标准**：回读已保存条目，`source` 正确，台账查询覆盖此目录。普通保存到此结束，不附带全库盘点。

## Entry 格式

文件名 `YYYY-MM-DD-<topic-slug>.md`，日期取今天，slug 小写连字符英文或直接用中文标题。

```markdown
---
title: <标题>
type: note
created: <今天>
source: <url | 本地路径 | text>
tags: [inbox, <topic>]
---

> [!info] 来源
> <url 或路径> · 捕获于 <日期>

## 摘要

<3–5 句>

## 要点

- <3–7 条>

## 去向

- [ ] 迁入 <建议的顶层目录>
```

正文不写 `# 一级标题`——新布局下标题由 frontmatter 的 `title` 承载，正文里的 h1 会与之重复。`source` 为文本输入时填 `text`。

## 台账格式

`$INBOX/_inbox.md`：

````markdown
---
type: moc
created: <今天>
area: [obsidian]
tags: [inbox, moc]
---

# INBOX 台账

```dataview
TABLE source AS 来源, created AS 捕获日, join(tags, ", ") AS 标签
FROM "<$INBOX 的值>"
WHERE file.name != "_inbox"
SORT created DESC
```
````
