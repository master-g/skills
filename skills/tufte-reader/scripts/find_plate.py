#!/usr/bin/env python3
"""find_plate.py 关键词… [--cat 分类] [--deep] [--min-width 1000] [--limit 20] [--all]

按主题词在 Wikimedia Commons 上找题图候选：一次调用取回搜索结果的尺寸和许可，只列出许可可用
（公有领域、无已知版权限制、CC0、CC BY）而且够宽的图。

  --cat 分类        限定在这个分类里搜，写分类名（带不带 Category: 都行）；加 --deep 连子分类一起搜
  --min-width 1000  图源的最小宽度。题图在页面上约 480 CSS 像素宽，高分屏需要 1000px 以上的图源
  --limit 20        最多看多少个搜索结果（上限 50）
  --all             把不合格的也列出来，并标明原因（许可、宽度、不是图片）

输出一张 Markdown 表，按宽度从大到小排；「文件」一列可以直接作 plate.py 的参数。
系列与分类名见 references/plates.md 的「系列」。
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plate  # noqa: E402  —— 复用许可白名单、API 地址和 User-Agent

IMAGE_MIMES = {"image/jpeg", "image/png", "image/tiff", "image/gif", "image/webp"}


def search(terms, cat=None, deep=False, limit=20):
    """关键词（加分类限定）→ (查询串, 结果列表)。结果按宽度从大到小排。"""
    q = " ".join(terms)
    if cat:
        cat = cat.removeprefix("Category:").replace("_", " ")
        q += f' {"deepcat" if deep else "incategory"}:"{cat}"'
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6",
              "gsrlimit": str(min(limit, 50)), "gsrsearch": q, "prop": "imageinfo",
              "iiprop": "size|url|mime|extmetadata", "iiextmetadatafilter": "LicenseShortName"}
    req = urllib.request.Request(plate.API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": plate.UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    rows = []
    for page in data.get("query", {}).get("pages", {}).values():
        info = page["imageinfo"][0]
        lic = plate.plain(info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", ""))
        rows.append({"title": page["title"], "width": info["width"], "height": info["height"],
                     "mime": info["mime"], "license": lic, "page": info["descriptionurl"]})
    rows.sort(key=lambda r: -r["width"])
    return q, rows


def verdict(row, min_width):
    """不合格的原因；合格时返回空串。"""
    if row["mime"] not in IMAGE_MIMES:
        return f"不是图片（{row['mime']}）"
    if plate.license_label(row["license"]) is None:
        return f"许可 {row['license'] or '缺失'}"
    if row["width"] < min_width:
        return f"只有 {row['width']}px"
    return ""


def main(argv):
    opts, flags, terms, it = {"--cat": None, "--min-width": "1000", "--limit": "20"}, {"--deep": False, "--all": False}, [], iter(argv)
    for a in it:
        if a in opts:
            opts[a] = next(it, None)
        elif a in flags:
            flags[a] = True
        else:
            terms.append(a)
    if not terms or not (opts["--min-width"] or "").isdigit() or not (opts["--limit"] or "").isdigit():
        print(__doc__)
        return 2
    min_width = int(opts["--min-width"])
    try:
        q, rows = search(terms, opts["--cat"], flags["--deep"], int(opts["--limit"]))
    except OSError as e:
        print(f"ERROR 搜索失败：{e}")
        return 1
    ok = [r for r in rows if not verdict(r, min_width)]
    shown = rows if flags["--all"] else ok
    print(f"搜索  {q}")
    print(f"结果  {len(rows)} 个，可用 {len(ok)} 个（许可可用且宽度不小于 {min_width}px）")
    if not shown:
        if rows:
            print("加 --all 看不合格的结果和原因；放宽 --min-width，或换关键词、换分类")
        return 0
    print()
    print("| 宽×高 | 许可 | 文件 | 页面 |")
    print("| --- | --- | --- | --- |")
    for r in shown:
        why = verdict(r, min_width)
        print(f"| {r['width']}×{r['height']} | {r['license']} | {r['title']}{' ✗ ' + why if why else ''} | {r['page']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
