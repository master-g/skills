#!/usr/bin/env python3
"""find_plate.py 关键词… [--cat 分类] [--deep] [--min-width 1000] [--limit 20] [--all] [--thumb 目录]

按主题词在 Wikimedia Commons 上找题图候选：一次调用取回搜索结果的尺寸和许可，只列出许可可用
（公有领域、无已知版权限制、CC0、CC BY）而且够宽的图。

  --cat 分类        限定在这个分类里搜，写分类名（带不带 Category: 都行）；加 --deep 连子分类一起搜
  --min-width 1000  图源的最小宽度。题图在页面上约 480 CSS 像素宽，高分屏需要 1000px 以上的图源
  --limit 20        最多看多少个搜索结果（上限 50）
  --all             把不合格的也列出来，并标明原因（许可、宽度、不是图片）
  --thumb 目录      把列出的图各下载一张 320px 缩略图到目录里，有 ImageMagick 时再拼成 sheet.png（按表格顺序，每行 5 幅），
                    用来目视挑图；整页扫描、带正文的页面在这里一眼能看出来

只给 --cat 不给关键词时列出整个分类。同一幅图的 .tif/.jpg 等重复文件只保留最宽的一个。
输出一张 Markdown 表，按宽度从大到小排；「文件」一列可以直接作 plate.py 的参数。-h / --help 打印本说明。
系列与分类名见 references/plates.md 的「系列」。
"""
import json
import re
import shutil
import subprocess
import sys
import time
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
        q = (q + " " if q else "") + f'{"deepcat" if deep else "incategory"}:"{cat}"'
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6",
              "gsrlimit": str(min(limit, 50)), "gsrsearch": q, "prop": "imageinfo",
              "iiprop": "size|url|mime|extmetadata", "iiextmetadatafilter": "LicenseShortName", "iiurlwidth": "320"}
    req = urllib.request.Request(plate.API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": plate.UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    rows = []
    for page in data.get("query", {}).get("pages", {}).values():
        info = page["imageinfo"][0]
        lic = plate.plain(info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", ""))
        rows.append({"title": page["title"], "width": info["width"], "height": info["height"],
                     "mime": info["mime"], "license": lic, "page": info["descriptionurl"],
                     "thumb": info.get("thumburl")})
    rows.sort(key=lambda r: -r["width"])
    # 同一幅图常有 .tif 和 .jpg 两份：按去掉扩展名的文件名去重，保留最宽的
    seen, unique = set(), []
    for r in rows:
        key = re.sub(r"\.[a-z0-9]+$", "", r["title"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return q, unique


def thumbs(rows, out_dir):
    """下载各行的缩略图；有 magick 时拼成 sheet.png。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for i, r in enumerate(rows, 1):
        if not r["thumb"]:
            continue
        f = out_dir / f"{i:02d}-{re.sub(r'[^\w-]+', '-', Path(r['title'][5:]).stem).strip('-')[:60].lower()}.jpg"
        req = urllib.request.Request(r["thumb"], headers={"User-Agent": plate.UA})
        with urllib.request.urlopen(req, timeout=60) as resp:
            f.write_bytes(resp.read())
        files.append(str(f))
        time.sleep(0.2)
    magick = shutil.which("magick")
    if magick and files:
        cmd = [magick]
        for k in range(0, len(files), 5):
            cmd += ["(", *files[k:k + 5], "-resize", "240x240", "-background", "white", "-gravity", "center",
                    "-extent", "246x246", "-bordercolor", "gray60", "-border", "1", "+append", ")"]
        try:
            subprocess.run(cmd + ["-append", str(out_dir / "sheet.png")], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"缩略图  {len(files)} 张 → {out_dir}/（拼总览图失败，逐张看）")
            return
        print(f"缩略图  {len(files)} 张 → {out_dir}/，总览 {out_dir / 'sheet.png'}（按表格顺序，每行 5 幅）")
    else:
        print(f"缩略图  {len(files)} 张 → {out_dir}/（没有 magick，不拼总览图）")


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
    opts, flags, terms, it = {"--cat": None, "--min-width": "1000", "--limit": "20", "--thumb": None}, {"--deep": False, "--all": False}, [], iter(argv)
    if any(a in ("-h", "--help") for a in argv):
        print(__doc__)
        return 0
    for a in it:
        if a in opts:
            opts[a] = next(it, None)
        elif a in flags:
            flags[a] = True
        else:
            terms.append(a)
    if not (terms or opts["--cat"]) or not (opts["--min-width"] or "").isdigit() or not (opts["--limit"] or "").isdigit():
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
    if opts["--thumb"]:
        try:
            thumbs(shown, opts["--thumb"])
        except OSError as e:
            print(f"WARN  缩略图下载失败：{e}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
