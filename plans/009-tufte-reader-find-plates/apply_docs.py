"""apply_docs.py <skill>/references/plates.md —— 009 对图录的改动：「系列」一节末尾的手工 curl 搜法换成 find_plate.py 的用法。
按锚点改这一段，别处不动；锚点找不到就 assert 失败、不写文件。"""
import sys

START = "搜图用 Commons 的搜索 API："
END = "搜分类，不要猜。\n"
NEW = """搜图用 `scripts/find_plate.py`：关键词加 `--cat <分类>`（`--deep` 连子分类一起搜），一次取回尺寸和许可，只列出许可可用且宽度不小于 1000px 的图，按宽度从大到小排：

```sh
python3 <skill-path>/scripts/find_plate.py dragon --cat "Musaeum Hermeticum"
python3 <skill-path>/scripts/find_plate.py alchemist --cat "Engravings in the Wellcome Collection" --deep
```

没有合格结果时加 `--all` 看不合格的原因（许可、宽度、不是图片），再放宽 `--min-width`、换关键词或换分类。「文件」一列直接作 `plate.py` 的参数。分类名不确定时，用 Commons 的搜索 API `list=search&srnamespace=14&srsearch=<关键词>` 搜分类，不要猜。
"""
path = sys.argv[1]
s = open(path, encoding="utf-8").read()
assert s.count(START) == 1 and s.count(END) == 1 and s.index(START) < s.index(END), "「系列」里的搜法段落找不到或不唯一"
s = s[: s.index(START)] + NEW + s[s.index(END) + len(END):]
open(path, "w", encoding="utf-8").write(s)
print(f"图录已更新：搜法换成 find_plate.py。接着运行 npx prettier --write {path}")
