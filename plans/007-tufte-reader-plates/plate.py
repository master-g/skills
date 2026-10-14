#!/usr/bin/env python3
"""plate.py "File:…" [-o 目录] [--width 1000] [--name 文件名]

从 Wikimedia Commons 取一幅题图：读许可，下载缩略图，压成适合内联的灰度图，写出处记录，打印可直接粘贴的写法。
只接受公有领域、无已知版权限制（No restrictions）、CC0 和 CC BY；其余许可或许可字段缺失时拒绝，退出码 3，不下载。

输出（默认在当前目录）：
  <文件名>.png 或 .jpg   有 ImageMagick 的 magick 时缩成 4 级灰度 PNG；否则 macOS 用 sips 转 JPEG；都没有时保留原图
  <文件名>.json         出处、许可、作者、取图日期
  标准输出              <figure class="plate"> 写法，TODO-题图 处由作者改写

用法与选图见 references/plates.md。
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from html import escape, unescape
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia 要求 User-Agent 写明工具和联系方式，否则可能被限流或拒绝
UA = "tufte-reader-plate/1.0 (https://github.com/master-g/skills)"
FIELDS = "LicenseShortName|AttributionRequired|Artist|Credit|DateTimeOriginal|ObjectName"
SIZE_WARN = 300 * 1024
EXIT_LICENSE = 3

# 许可短名 → 图注里的写法。CC BY 不论版本号都接受；带 SA、NC、ND 的不接受。
# 「No restrictions」是机构声明「无已知版权限制」（Flickr Commons，多为 Internet Archive Book Images 的古籍插图），按公有领域处理
LICENSE_OK = re.compile(r"^(?:public domain|pdm(?:-owner)?|no restrictions|cc0(?: 1\.0)?|cc by(?: \d\.\d)?)$", re.I)


def license_label(short):
    """许可短名 → 图注写法；不接受时返回 None。"""
    s = " ".join((short or "").split())
    if not LICENSE_OK.match(s):
        return None
    low = s.lower()
    if low.startswith(("public domain", "pdm")):
        return "公有领域"
    if low == "no restrictions":
        return "无已知版权限制"
    return s.upper().replace("CC0 1.0", "CC0")


def plain(value):
    """extmetadata 的值常带 HTML 标签和实体，取纯文本。"""
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def query(title, width):
    params = {"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
              "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(width), "iiextmetadatafilter": FIELDS}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = next(iter(json.load(r)["query"]["pages"].values()))
    if "imageinfo" not in page:
        raise LookupError(f"Commons 上没有这个文件：{title}")
    return page["title"], page["imageinfo"][0]


def record(title, info):
    meta = {k: plain(v.get("value")) for k, v in info.get("extmetadata", {}).items()}
    return {
        "title": title,
        "page": info["descriptionurl"],
        "license": meta.get("LicenseShortName", ""),
        "attribution_required": meta.get("AttributionRequired", "").lower() == "true",
        "artist": meta.get("Artist", ""),
        "credit": meta.get("Credit", ""),
        "date": meta.get("DateTimeOriginal", ""),
        "fetched": datetime.date.today().isoformat(),
    }


def shrink(raw, out_stem, width):
    """缩到 width 宽（只缩不放），返回成品路径。"""
    magick, sips = shutil.which("magick"), shutil.which("sips")
    if magick:
        dst = out_stem.with_suffix(".png")
        # 扫描的纸色常偏灰：先拉伸色阶，把纸面推到近白，亮色主题的 multiply 才看不出方框；再量化成 4 级灰度
        subprocess.run([magick, str(raw), "-resize", f"{width}x>", "-colorspace", "gray", "-auto-level",
                        "-level", "15%,80%", "-colors", "4", str(dst)], check=True)
    elif sips:
        dst = out_stem.with_suffix(".jpg")
        subprocess.run([sips, "--resampleWidth", str(width), "-s", "format", "jpeg", "-s", "formatOptions", "50",
                        str(raw), "--out", str(dst)], check=True, capture_output=True)
    else:
        print("WARN  没有 magick 也没有 sips，保留下载的原图，没有压缩")
        return raw
    raw.unlink()
    return dst


def snippet(rec, src):
    lic = license_label(rec["license"])
    who = rec["artist"] or rec["credit"]
    # Artist 字段常是一串链接或机构说明，不能直接当署名；短而干净时才用，否则留给作者填
    if len(who) > 60 or "http" in who:
        who = "TODO-题图：署名"
    by = f"，署名：{escape(who)}" if rec["attribution_required"] else ""
    return (f'<figure class="plate" data-source="{escape(rec["page"])}" data-license="{escape(rec["license"])}">\n'
            f'  <span class="marginnote">题图　TODO-题图：出处（书名、页码或幅次）、图题或箴言的译文。'
            f'图源 <a href="{escape(rec["page"])}">Wikimedia Commons</a>，{lic}{by}。</span>\n'
            f'  <img src="{escape(src)}" alt="TODO-题图：画面描述" />\n'
            f"</figure>")


def main(argv):
    args, opts, it = [], {"-o": ".", "--width": "1000", "--name": None}, iter(argv)
    for a in it:
        if a in opts:
            opts[a] = next(it, None)
        else:
            args.append(a)
    if len(args) != 1 or not (opts["--width"] or "").isdigit():
        print(__doc__)
        return 2
    title = args[0] if args[0].startswith("File:") else "File:" + args[0]
    width = int(opts["--width"])
    try:
        title, info = query(title, width)
    except (LookupError, OSError) as e:
        print(f"ERROR {e}")
        return 1
    rec = record(title, info)
    if license_label(rec["license"]) is None:
        print(f"ERROR 许可「{rec['license'] or '缺失'}」不在可用范围（公有领域、无已知版权限制、CC0、CC BY）内，换一幅图：{rec['page']}")
        return EXIT_LICENSE

    out_dir = Path(opts["-o"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    name = opts["--name"] or re.sub(r"[^\w-]+", "-", Path(title[5:]).stem).strip("-").lower()
    url = info.get("thumburl") or info["url"]
    raw = out_dir / f"{name}.download{Path(urllib.parse.urlparse(url).path).suffix.lower() or '.jpg'}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw.write_bytes(r.read())
    img = shrink(raw, out_dir / name, width)
    rec["file"] = img.name
    (out_dir / f"{name}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    size = img.stat().st_size
    print(f"取图    {img}  {size // 1024} KB  许可 {rec['license']}")
    if size > SIZE_WARN:
        print(f"WARN  {size // 1024} KB 偏大：加 --width 800 重取")
    print(snippet(rec, os.path.relpath(img)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
