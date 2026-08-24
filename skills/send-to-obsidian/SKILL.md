---
name: send-to-obsidian
license: MIT
description: 抓取 URL、本地路径、目录或一段文本，摘要后存入 Obsidian 的 inbox，登记进台账，并盘点超过 7 天未处理的 entry 与未回收的外部产出。用户要求把链接或内容存进 obsidian / inbox 时使用。
---

# send-to-obsidian

把参数中的 URL、本地路径、目录或文本抓成 INBOX **entry**，写入 vault，登记台账，再盘点**过期 entry**（捕获日距今超过 7 天）。

参数即输入：`/send-to-obsidian <url | path | dir | 文本>`。参数为空时先向用户索取输入。

子命令：`/send-to-obsidian --sweep` 只做盘点，不写入（见第 6 节）。

**intake 只产登记档，不做蒸馏。** 摘要 entry 记录源路径，蒸馏是独立的后续动作，由人看过 entry 后发起。原件在 intake 时不动。

## 1. 定位 vault

运行 `obsidian eval code="app.vault.adapter.basePath"`，取当前 vault 路径存为 `$VAULT`。

命令失败时（Obsidian 未运行或 CLI 未安装），改读 `~/Library/Application Support/obsidian/obsidian.json` 的 `vaults` 字段取路径列表。

列表为空或多于一条时，把候选路径列给用户，等用户选定后再继续。

**完成标准**：`$VAULT` 已确定且目录存在。

## 2. 探测布局，确认 inbox 与台账

vault 有两种布局，探测而非假定——2026-08 的重构把顶层 `00 - INBOX/` 改成了 `inbox/`：

```bash
if [ -d "$VAULT/inbox" ]; then INBOX="inbox"; else INBOX="00 - INBOX"; fi
```

`$VAULT/$INBOX/` 不存在时创建它（两者都不存在时用 `inbox`，新布局是默认）。

`$VAULT/$INBOX/_inbox.md` 不存在时按下文[台账格式](#台账格式)创建它，其中 dataview 的 `FROM` 用探测到的 `$INBOX`。

**完成标准**：目录与台账文件均存在，`$INBOX` 已确定。

## 3. 查重

按输入类型查已有 entry：URL 输入用 `grep -rlF "<url>" "$VAULT/$INBOX/"`；路径或文本输入用标题 slug 匹配文件名。

命中时把已有 entry 的路径与捕获日展示给用户，问选哪一项：更新（保留原文件，重写摘要）、覆盖（整篇重写）、另存为新 entry、放弃。等用户回答后再继续。

**完成标准**：确认无重复，或用户已选定处理方式。

## 4. 抓取并写入 entry

按输入类型取内容：

| 输入 | 抓取方式 |
|---|---|
| URL | `autocli read <url>`（覆盖 x.com、知乎等登录态与 JS 页面）；失败时回退 WebFetch |
| 本地路径 | Read 工具 |
| **目录** | 按第 5 节的类型映射表逐文件处理 |
| 文本 | 直接使用参数文本 |

抓取失败时向用户报告失败原因，并问是否只存链接与标题。

按下文 [Entry 格式](#entry-格式) 写文件到 `$VAULT/$INBOX/`。摘要写 3–5 句，要点写 3–7 条，两者都基于抓到的正文。正文未抓到时，摘要处写「原文未抓取」。

`inbox/` **豁免全部必填 frontmatter 字段**——它的职责是零摩擦接住内容，质量门禁在出口而非入口。只保证 `source` 有值。

**完成标准**：文件已落盘，`source` 有值。

## 5. 目录输入的类型映射

teach 一类的工作区是一整个目录。逐文件按此表处理，**不是人工蒸馏清单，是 intake 的处理依据**：

| 文件 | intake 动作 | 最终去向（后续人工发起） |
|---|---|---|
| `MISSION.md` | 登记 entry | topic 的 `sections.yaml` 头部与 `_README` |
| `RESOURCES.md` | 登记 entry | `resources/` 单篇参考 |
| `GLOSSARY.md` | 跳过 | 留工作区；术语按二次出现门槛逐条抽取 |
| `NOTES.md` | 跳过 | 不入库 |
| `learning-records/*.md` | 跳过 | 不入库（面向下一次 teach，不面向重读） |
| `lessons/*.html` | 登记 entry，标记待蒸馏 | `topics/<topic>/` 词条加 `.quiz` 块 |
| `reference/*.html` | 登记 entry，标记待蒸馏 | 独立词条 |
| `assets/*` | 跳过 | 蒸馏时手工迁入 `site/public/assets/` |

标记待蒸馏 = entry 的「去向」段写 `- [ ] 蒸馏为 topics/<topic>/ 词条`。

## 6. 盘点

两部分，都在每次调用末尾做一次（`--sweep` 则只做这一节）。

### 6a. 过期 entry

```bash
cd "$VAULT/$INBOX" && cutoff=$(date -v-7d +%F) && ls *.md | awk -v c="$cutoff" '
  substr($0,1,1)=="_" {next}
  $0 ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}-/ { if (substr($0,1,10) < c) print substr($0,1,10), $0; next }
  { print "无日期前缀", $0 }'
```

把结果列成表给用户，每条给一个去向建议（迁入哪个顶层目录，或删除），依据是 entry 的 tags 与摘要。

### 6b. 未回收的外部产出

外部技能（effective-html / teach）产在自己的工作目录，不改它们的输出路径——技能会升级，路径强改要每次重打。改由这里盘点：

```bash
# 约定产出根与已 intake 清单取差集；已 intake 按 entry 的 source 字段记录
for root in ~/Downloads/htmls; do
  [ -d "$root" ] || continue
  find "$root" -maxdepth 2 \( -name '*.html' -o -name '*.md' \) -print
done | while read -r f; do
  grep -rqF "$f" "$VAULT/$INBOX/" || echo "未 intake: $f"
done
```

列出未 intake 项，问用户是否 intake。**漏报不写坏任何东西**——盘点只在实际常用的目录上做。

**完成标准**：每条过期 entry 都有一条去向建议；未回收清单已呈现。用户未表态时保持文件原样。

## Entry 格式

文件名 `YYYY-MM-DD-<topic-slug>.md`，日期取今天，slug 小写连字符英文或直接用中文标题。

```markdown
---
type: note
created: 2026-08-15
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
