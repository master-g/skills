# 目录输入与盘点

入口先定位 vault；目录输入读取“目录输入的类型映射”，`--sweep` 读取“盘点”。普通单条保存不读取本文件。

## 5. 目录输入的类型映射

teach 一类的工作区是一整个目录。逐文件按此表处理，**不是人工蒸馏清单，是 intake 的处理依据**：

| 文件                    | intake 动作            | 最终去向（后续人工发起）                  |
| ----------------------- | ---------------------- | ----------------------------------------- |
| `MISSION.md`            | 登记 entry             | topic 的 `sections.yaml` 头部与 `_README` |
| `RESOURCES.md`          | 登记 entry             | `resources/` 单篇参考                     |
| `GLOSSARY.md`           | 跳过                   | 留工作区；术语按二次出现门槛逐条抽取      |
| `NOTES.md`              | 跳过                   | 不入库                                    |
| `learning-records/*.md` | 跳过                   | 不入库（面向下一次 teach，不面向重读）    |
| `lessons/*.html`        | 登记 entry，标记待蒸馏 | `topics/<topic>/` 词条加 `.quiz` 块       |
| `reference/*.html`      | 登记 entry，标记待蒸馏 | 独立词条                                  |
| `assets/*`              | 跳过                   | 蒸馏时手工迁入 `site/public/assets/`      |

标记待蒸馏 = entry 的「去向」段写 `- [ ] 蒸馏为 topics/<topic>/ 词条`。

## 6. 盘点

仅在用户要求盘点或显式 `--sweep` 时执行；不写入、不删除。

### 6a. 过期 entry

```bash
cd "$VAULT/$INBOX" && cutoff=$(date -v-7d +%F) && ls *.md | awk -v c="$cutoff" '
  substr($0,1,1)=="_" {next}
  $0 ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}-/ { if (substr($0,1,10) < c) print substr($0,1,10), $0; next }
  { print "无日期前缀", $0 }'
```

把结果列成表给用户，每条给一个去向建议（迁入哪个顶层目录，或删除），依据是 entry 的 tags 与摘要。

### 6b. 未回收的外部产出

外部技能（show-me-html / teach）产在自己的工作目录，不改它们的输出路径——技能会升级，路径强改要每次重打。改由这里盘点：

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
