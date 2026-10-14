"""apply_catalog.py <skill>/references/plates.md —— 008 对图录的改动：「取图」改为默认用 IA 高清版，
图录引言改一句，「高清版」表换成 50 行 IA 参数。只按锚点改这三处，不碰主表（维护者可能改过大意与主题的措辞）。
任何一个锚点找不到就 assert 失败、不写文件：说明图录在 007 之后改过这几处，按计划的 STOP 处理。"""
import sys

# (幅, IIIF 叶号, 区域)：advisor 2026-10-14 算出并逐幅目视核对
ROWS = [
    (1, 21, "pct:3.7,12.6,73.9,53.0"),
    (2, 25, "pct:4.5,14.3,76.4,53.4"),
    (3, 29, "pct:7.7,14.4,75.8,51.7"),
    (4, 33, "pct:1.6,16.8,76.5,51.7"),
    (5, 37, "pct:3.1,16.9,80.6,50.6"),
    (6, 41, "pct:3.2,12.3,76.9,50.4"),
    (7, 45, "pct:5.1,10.8,77.3,51.5"),
    (8, 49, "pct:2.5,15.6,77.6,49.8"),
    (9, 53, "pct:3.5,15.1,73.6,53.1"),
    (10, 57, "pct:6.4,14.9,78.6,50.6"),
    (11, 61, "pct:7.3,12.9,74.9,53.3"),
    (12, 65, "pct:4.0,15.2,74.6,52.6"),
    (13, 69, "pct:5.5,17.6,73.9,51.1"),
    (14, 73, "pct:2.9,14.1,78.6,49.9"),
    (15, 77, "pct:5.6,12.8,75.0,48.5"),
    (16, 81, "pct:1.1,14.9,75.6,54.4"),
    (17, 85, "pct:5.7,16.0,74.2,53.5"),
    (18, 89, "pct:3.1,14.5,75.3,49.5"),
    (19, 93, "pct:2.9,12.6,76.4,50.6"),
    (20, 97, "pct:3.8,15.7,75.0,50.7"),
    (21, 101, "pct:5.2,15.8,74.5,53.6"),
    (22, 105, "pct:2.2,11.9,77.1,50.5"),
    (23, 109, "pct:1.7,13.9,78.2,50.4"),
    (24, 113, "pct:1.6,13.2,77.8,51.5"),
    (25, 117, "pct:4.0,16.0,78.2,50.2"),
    (26, 121, "pct:2.2,13.8,74.1,52.3"),
    (27, 125, "pct:4.4,15.2,74.2,52.9"),
    (28, 129, "pct:2.5,13.9,74.5,51.8"),
    (29, 133, "pct:3.7,13.7,73.9,51.7"),
    (30, 137, "pct:2.7,14.7,73.3,50.7"),
    (31, 141, "pct:1.4,15.6,78.2,51.6"),
    (32, 145, "pct:1.4,14.1,76.2,52.0"),
    (33, 149, "pct:5.5,12.8,74.7,53.0"),
    (34, 153, "pct:5.1,16.4,74.9,52.8"),
    (35, 157, "pct:6.4,17.1,76.9,51.6"),
    (36, 161, "pct:3.2,16.4,76.1,53.8"),
    (37, 165, "pct:3.5,15.2,74.8,53.9"),
    (38, 169, "pct:5.2,16.0,75.5,52.8"),
    (39, 173, "pct:6.2,15.2,75.5,53.0"),
    (40, 177, "pct:2.2,13.6,75.3,53.0"),
    (41, 181, "pct:7.3,17.3,73.4,52.7"),
    (42, 185, "pct:2.9,18.1,75.5,52.8"),
    (43, 189, "pct:3.9,14.3,73.7,52.5"),
    (44, 193, "pct:2.4,14.4,75.8,53.5"),
    (45, 197, "pct:7.7,14.8,75.0,53.0"),
    (46, 201, "pct:2.5,14.3,75.3,53.0"),
    (47, 205, "pct:7.1,14.4,74.9,53.5"),
    (48, 209, "pct:6.2,16.4,75.3,53.2"),
    (49, 213, "pct:7.7,13.8,74.8,53.5"),
    (50, 217, "pct:8.4,13.7,75.5,53.5"),
]

OLD_FETCH = """在页面所在的目录里运行：

```sh
python3 <skill-path>/scripts/plate.py "File:Michael Maier Atalanta Fugiens Emblem 42.jpeg" -o figures/plates --name atalanta-42
```

- 脚本从 Wikimedia Commons 读这个文件的许可字段，只接受公有领域、无已知版权限制（No restrictions，图书馆批量上传的古籍插图常这样标）、CC0 和 CC BY。其余许可（包括 CC BY-SA、NC、ND）或字段缺失时拒绝并以退出码 3 结束：换一幅图，不要绕过脚本手动下载。
"""
NEW_FETCH = """在页面所在的目录里运行。Atalanta Fugiens 用图录「高清版」表里的参数，从 Internet Archive 取 1000px 的高清版（shell 里用单引号，`$` 不能被展开）：

```sh
python3 <skill-path>/scripts/plate.py 'ia:atalantafugiensh00maie$185' --region pct:2.9,18.1,75.5,52.8 -o figures/plates --name atalanta-42
```

其他图从 Wikimedia Commons 取，写文件名：

```sh
python3 <skill-path>/scripts/plate.py "File:<Commons 上的文件名>" -o figures/plates --name <文件名>
```

- Commons 的图：脚本读这个文件的许可字段，只接受公有领域、无已知版权限制（No restrictions，图书馆批量上传的古籍插图常这样标）、CC0 和 CC BY。其余许可（包括 CC BY-SA、NC、ND）或字段缺失时拒绝并以退出码 3 结束：换一幅图，不要绕过脚本手动下载。
- Internet Archive 的图：IA 的元数据没有许可字段，脚本只放行 `plate.py` 里 `IA_ITEMS` 白名单登记过的条目，许可依据写在白名单里；目前只有 Atalanta Fugiens 的 Getty 扫描本，别的 IA 条目报退出码 3。`--region` 是画面在整页上的百分比位置，由 IIIF 服务器裁出来，不需要本地裁切工具。
- 要用 IA 上别的扫描本（「系列」里的 Fludd、Kircher、Hooke 等在 IA 上都有）：按 `plate.py` 里 `IA_ITEMS` 上方注释的三条标准确认原作与扫描都属公有领域，请维护者认可后加一条登记，并在 `tests/test_plate.py` 里加一行断言。
"""
OLD_600 = "- 图录里的单幅文件多数只有 600px 宽；扉页想要更清楚的，用「高清版」一栏的文件。\n"
NEW_600 = "- 图录主表里 Commons 的单幅文件只有约 600px 宽，在高分屏上发虚，只在 IA 取不到时作退路。\n"
OLD_INTRO = "下表的文件都在 Commons 的 `Category:Atalanta Fugiens` 里，取图前由 `plate.py` 检查许可。"
NEW_INTRO = "取图默认用「高清版」表的 IA 参数；主表的文件在 Commons 的 `Category:Atalanta Fugiens` 里，是约 600px 的单图，作退路和对照。"
HI_START = "**高清版**"

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
for old, new in ((OLD_FETCH, NEW_FETCH), (OLD_600, NEW_600), (OLD_INTRO, NEW_INTRO)):
    assert s.count(old) == 1, f"锚点找不到或不唯一：{old[:40]!r}"
    s = s.replace(old, new)
# 「高清版」表是图录的最后一部分，从它开始到文件末尾整体替换；它后面不该再有别的章节
assert s.count(HI_START) == 1 and "\n## " not in s[s.index(HI_START):], "「高清版」表的位置变了"
table = "\n".join(f"| {n} | `'ia:atalantafugiensh00maie${leaf}'` | `{region}` |" for n, leaf, region in ROWS)
hi = f"""**高清版**：Internet Archive 上 Getty 研究所的扫描本（`atalantafugiensh00maie`，500ppi，未上色），经 IIIF 按区域裁出画面，默认 1000px 宽，带刻版的边框。「来源」一列是 `plate.py` 的第一个参数，「区域」一列是 `--region` 的值。

| 幅 | 来源 | 区域 |
| --- | --- | --- |
{table}

"""
s = s[: s.index(HI_START)] + hi.rstrip("\n") + "\n"
open(path, "w", encoding="utf-8").write(s)
print(f"图录已更新：高清版 {len(ROWS)} 行。接着运行 npx prettier --write {path}")
