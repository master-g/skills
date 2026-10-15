"""apply_docs.py <skill 目录> —— 013 对文档的改动：plates.md 的选图、系列、取图、写法各一两句，markup.md 与 SKILL.md 各一句。
按锚点改，任何一个锚点找不到或不唯一就 assert 失败、不写文件（三个文件要么全改、要么全不改）。改完请运行 prettier。"""
import re
import sys
from pathlib import Path

skill = Path(sys.argv[1])
PLATES = [
    ("2. 按主题词找画面：先看「系列」表里哪些系列的主题对得上，到那几个分类里搜；炼金寓意类的主题也查「图录」的「适合的主题」一栏。搜法见「系列」一节末尾。寓意对不上就不配这一章，不要为了配图而牵强。",
     "2. 按主题词找画面：先看「系列」表里哪些系列的主题对得上，到那几个分类里搜；炼金寓意类的主题也查「图录」的「适合的主题」一栏。搜法见「系列」一节末尾；选图前用 `--thumb` 取缩略图总览看一眼，不要只凭文件名和尺寸挑。寓意对不上就不配这一章，不要为了配图而牵强。"),
    ("画面（线条清楚、未手工上色、不带大段正文文字；整页扫描要能裁出完整画面）。",
     "画面（线条清楚、未手工上色、不带大段正文文字）。整页扫描只要画面完整就能用：取图时给 `--region` 按百分比裁出画面，Commons 和 IA 的图都可以裁。"),
    ("搜图用 `scripts/find_plate.py`：关键词加 `--cat <分类>`（`--deep` 连子分类一起搜），一次取回尺寸和许可，只列出许可可用且宽度不小于 1000px 的图，按宽度从大到小排：",
     "搜图用 `scripts/find_plate.py`：关键词加 `--cat <分类>`（`--deep` 连子分类一起搜；只给 `--cat` 就列出整个分类），一次取回尺寸和许可，只列出许可可用且宽度不小于 1000px 的图，按宽度从大到小排，同一幅的 `.tif`/`.jpg` 重复只留最宽的。加 `--thumb <目录>` 把列出的图下载成缩略图并拼一张总览（按表格顺序，每行 5 幅），整页扫描、带正文的页面一眼能看出来："),
    ('python3 <skill-path>/scripts/find_plate.py dragon --cat "Musaeum Hermeticum"\npython3 <skill-path>/scripts/find_plate.py alchemist --cat "Engravings in the Wellcome Collection" --deep\n',
     'python3 <skill-path>/scripts/find_plate.py dragon --cat "Musaeum Hermeticum" --thumb /tmp/cand\npython3 <skill-path>/scripts/find_plate.py alchemist --cat "Engravings in the Wellcome Collection" --deep\npython3 <skill-path>/scripts/find_plate.py --cat "Agostino Ramelli" --thumb /tmp/cand\n'),
    ("没有合格结果时加 `--all` 看不合格的原因（许可、宽度、不是图片），再放宽 `--min-width`、换关键词或换分类。",
     "没有合格结果时加 `--all` 看不合格的原因（许可、宽度、不是图片），再放宽 `--min-width`、换关键词或换分类。「系列」表之外的主题（天文仪器、工序、航海……）到 Category:17th-century engravings 或 Category:Frontispieces 用 `--deep` 搜，关键词用英文或拉丁文。"),
    ("- Commons 的图：脚本读这个文件的许可字段，只接受公有领域、无已知版权限制（No restrictions，图书馆批量上传的古籍插图常这样标）、CC0 和 CC BY。其余许可（包括 CC BY-SA、NC、ND）或字段缺失时拒绝并以退出码 3 结束：换一幅图，不要绕过脚本手动下载。",
     "- Commons 的图：脚本读这个文件的许可字段，只接受公有领域、无已知版权限制（No restrictions，图书馆批量上传的古籍插图常这样标）、CC0 和 CC BY。其余许可（包括 CC BY-SA、NC、ND）或字段缺失时拒绝并以退出码 3 结束：换一幅图，不要绕过脚本手动下载。整页扫描加 `--region pct:x,y,w,h` 在本地裁出画面（需要 ImageMagick），百分比看缩略图估一次、取出来看成品再微调。"),
    ("- 图录主表里 Commons 的单幅文件只有约 600px 宽，在高分屏上发虚，只在 IA 取不到时作退路。",
     "- 图录主表里 Commons 的单幅文件只有约 600px 宽，在高分屏上发虚，只在 IA 取不到时作退路。\n- 成品几乎是一片纯色（透明底、空白页、裁错区域）时脚本报 ERROR 并删掉成品，退出码 1；`<name>.json` 里记有图源尺寸和裁切区域。"),
    ("- **章首题图**：放在该章 `<h2>` 之后、第一个 `<section>` 的开头。",
     "- **章首题图**：放在该章 `<h2>` 后面那个 `<section>` 的里面，作为它的第一个子元素（`<h2>` 和 `<section>` 之间不放，`<p>` 里也不放）。"),
]
# 系列表（铜版画）末尾加三行：锚在 Wellcome 那一行（prettier 会重排列宽，所以用正则只认行首）
ROWS = ("| Johannes Hevelius, _Machina coelestis_ | 1673 | Category:Machina Coelestis by Johannes Hevelius | 10 文件，公有领域，约 850px（偏小） | 观测、仪器操作、望远镜与象限仪 |\n"
        "| Stradanus 设计、Collaert 等刻, _Nova Reperta_（《新发现》） | 1590 年代 | Category:Nova Reperta | 38 文件，CC0 与公有领域为主，3500px | 发明与工艺：印刷、蒸馏、磁针、航海、火药 |\n"
        "| Abraham Bosse 的蚀刻 | 1630–1650 | Category:Abraham Bosse | 237 文件加 11 个子分类，CC0 为主，3500px | 作坊与工序、印刷、日常与职业 |\n")
MARKUP = [("- 扉页题图放在 `header.titlepage` 里、`p.byline` 之后；章首题图放在该章 `<h2>` 之后、第一个 `<section>` 的开头。",
           "- 扉页题图放在 `header.titlepage` 里、`p.byline` 之后；章首题图放在该章 `<h2>` 后面那个 `<section>` 的里面，作为它的第一个子元素。")]
SKILL = [("书的架构（扉页、目录、章、章末出处）", "书的架构（扉页、目录、章、章末脚注、参考文献）")]


def patched(path, pairs, row_after=None):
    s = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) == 1, f"{path.name}: 锚点找不到或不唯一：{old[:50]!r}"
        s = s.replace(old, new)
    if row_after:
        pat = r"^(\| Wellcome Collection 的版画 .*\n)"
        assert len(re.findall(pat, s, re.M)) == 1, f"{path.name}: 系列表里 Wellcome 那一行找不到"
        s = re.sub(pat, lambda m: m.group(1) + row_after, s, count=1, flags=re.M)
    return s


out = {
    skill / "references/plates.md": patched(skill / "references/plates.md", PLATES, ROWS),
    skill / "references/markup.md": patched(skill / "references/markup.md", MARKUP),
    skill / "SKILL.md": patched(skill / "SKILL.md", SKILL),
}
for path, text in out.items():
    path.write_text(text, encoding="utf-8")
print("文档已更新：plates.md、markup.md、SKILL.md。接着运行 npx prettier --write 这三个文件")
