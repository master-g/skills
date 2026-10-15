#!/usr/bin/env python3
"""plate.py 来源 [-o 目录] [--width 1000] [--name 文件名] [--region pct:x,y,w,h]

取一幅题图：确认许可，下载并压成适合内联的灰度图，写出处记录，打印可直接粘贴的写法。来源两种：

  "File:…"                     Wikimedia Commons 的文件。读它的许可字段，只接受公有领域、无已知版权限制（No restrictions）、CC0 和 CC BY
  'ia:<条目>$<叶号>'            Internet Archive 扫描本的一页，经 IIIF 在服务器端按 --region 裁出画面。
                               只接受 IA_ITEMS 白名单里的条目（IA 的元数据没有许可字段，许可依据写在白名单里）。
                               shell 里用单引号，否则 $<叶号> 会被展开

--region 对 Commons 的文件同样可用：整页扫描按百分比位置在本地裁出画面（需要 ImageMagick 的 magick），
脚本按裁切比例向 Commons 多要像素，成品仍是 --width 宽。-h / --help 打印本说明。

许可不合格、IA 条目不在白名单里时拒绝，退出码 3，不下载。成品几乎是一片纯色（透明底、空白页）时删掉成品，退出码 1。

输出（默认在当前目录）：
  <文件名>.png 或 .jpg   有 ImageMagick 的 magick 时缩成 4 级灰度 PNG；否则 macOS 用 sips 转 JPEG；都没有时保留原图
  <文件名>.json         出处、许可、作者、取图日期；Commons 的图还有图源尺寸，裁过的有 --region
  标准输出              <figure class="plate"> 写法，TODO-题图 处由作者改写

用法与选图见 references/plates.md。
"""
import datetime
import json
import math
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

# Internet Archive 的条目没有机器可读的许可字段，能用的条目逐个登记，写明依据。
# 加条目前先确认：原作已进入公有领域；扫描是平面作品的忠实复制；最好 Commons 上已有同一扫描的公有领域文件可作旁证
IA_ITEMS = {
    "atalantafugiensh00maie": {
        "license": "Public domain",
        "artist": "Matthäus Merian 刻，Michael Maier 著",
        "date": "1618",
        "credit": "Getty Research Institute 扫描",
        "basis": "1618 年出版的原作早已进入公有领域；扫描是平面作品的忠实复制；Commons 上由同一扫描裁出的 50 幅单图"
                 "（如 File:Michael Maier Atalanta Fugiens Emblem 42.jpeg）标为 Public domain",
    },
}
IA_RE = re.compile(r"^ia:([\w.-]+)\$(\d+)$")
REGION_RE = re.compile(r"^pct:\d+(?:\.\d+)?(?:,\d+(?:\.\d+)?){3}$")


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
        "site": "Wikimedia Commons",
        "page": info["descriptionurl"],
        "license": meta.get("LicenseShortName", ""),
        "attribution_required": meta.get("AttributionRequired", "").lower() == "true",
        "artist": meta.get("Artist", ""),
        "credit": meta.get("Credit", ""),
        "date": meta.get("DateTimeOriginal", ""),
        "fetched": datetime.date.today().isoformat(),
    }


def ia_source(spec, region, width):
    """'ia:<条目>$<叶号>' → (出处记录, IIIF 图片地址)；条目不在白名单里时返回 (None, None)。
    IIIF 的叶号从 1 数，阅读器页面的 n<叶号> 从 0 数，所以页面链接用叶号减 1。"""
    item, leaf = IA_RE.match(spec).groups()
    meta = IA_ITEMS.get(item)
    if meta is None:
        return None, None
    rec = {
        "title": spec,
        "site": f"Internet Archive（{meta['credit']}）",
        "page": f"https://archive.org/details/{item}/page/n{int(leaf) - 1}/mode/1up",
        "license": meta["license"],
        "attribution_required": False,
        "artist": meta["artist"],
        "credit": meta["credit"],
        "date": meta["date"],
        "region": region,
        "basis": meta["basis"],
        "fetched": datetime.date.today().isoformat(),
    }
    return rec, f"https://iiif.archive.org/iiif/{item}${leaf}/{region}/{width},/0/default.jpg"


def crop_geometry(w, h, region):
    """pct:x,y,w,h 在 w×h 像素的图上 → ImageMagick 的 -crop 几何串（像素）。"""
    x, y, cw, ch = (float(v) for v in region[4:].split(","))
    return f"{round(w * cw / 100)}x{round(h * ch / 100)}+{round(w * x / 100)}+{round(h * y / 100)}"


def shrink(raw, out_stem, width, region=None):
    """（按 region 裁切后）缩到 width 宽（只缩不放），返回成品路径；成品不可用时返回 None（已打印 ERROR）。"""
    magick, sips = shutil.which("magick"), shutil.which("sips")
    if magick:
        dst = out_stem.with_suffix(".png")
        # 透明底先合成到白底，否则灰度量化后是一片透明/纯灰
        cmd = [magick, str(raw), "-background", "white", "-alpha", "remove", "-alpha", "off"]
        if region:
            w, h = subprocess.run([magick, str(raw), "-format", "%w %h", "info:"], capture_output=True, text=True,
                                  check=True).stdout.split()
            cmd += ["-crop", crop_geometry(int(w), int(h), region), "+repage"]
        # 扫描的纸色常偏灰：先拉伸色阶，把纸面推到近白，亮色主题的 multiply 才看不出方框；再量化成 4 级灰度
        cmd += ["-resize", f"{width}x>", "-colorspace", "gray", "-auto-level", "-level", "15%,80%", "-colors", "4",
                str(dst)]
        subprocess.run(cmd, check=True)
        std = float(subprocess.run([magick, str(dst), "-format", "%[fx:standard_deviation]", "info:"],
                                   capture_output=True, text=True, check=True).stdout or 0)
        if std < 0.02:
            print(f"ERROR 成品几乎是一片纯色（标准差 {std:.3f}）：透明底、空白页或裁错了区域，已删除；换一幅图或改 --region")
            dst.unlink()
            raw.unlink()
            return None
    elif region:
        print("ERROR 裁切 Commons 的图需要 ImageMagick 的 magick；装上再取，或换一幅不用裁的图")
        raw.unlink()
        return None
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
    site = rec.get("site", "Wikimedia Commons")
    return (f'<figure class="plate" data-source="{escape(rec["page"])}" data-license="{escape(rec["license"])}">\n'
            f'  <span class="marginnote">题图　TODO-题图：出处（书名、页码或幅次）、图题或箴言的译文。'
            f'图源 <a href="{escape(rec["page"])}">{escape(site)}</a>，{lic}{by}。</span>\n'
            f'  <img src="{escape(src)}" alt="TODO-题图：画面描述" />\n'
            f"</figure>")


def main(argv):
    args, opts, it = [], {"-o": ".", "--width": "1000", "--name": None, "--region": None}, iter(argv)
    for a in it:
        if a in opts:
            opts[a] = next(it, None)
        else:
            args.append(a)
    if any(a in ("-h", "--help") for a in argv):
        print(__doc__)
        return 0
    if len(args) != 1 or not (opts["--width"] or "").isdigit():
        print(__doc__)
        return 2
    if opts["--region"] is not None and not REGION_RE.match(opts["--region"]):
        print(f"ERROR --region 写成 pct:x,y,w,h（画面在整页上的百分比位置）：{opts['--region']}")
        return 2
    width = int(opts["--width"])
    region = opts["--region"]

    if args[0].startswith("ia:"):
        if not IA_RE.match(args[0]):
            print(f"ERROR IA 来源写成 'ia:<条目>$<叶号>'（shell 里用单引号）：{args[0]}")
            return 2
        if not region:
            print("ERROR IA 来源要给 --region pct:x,y,w,h（画面在整页上的百分比位置，见 references/plates.md 的图录）")
            return 2
        rec, url = ia_source(args[0], region, width)
        region = None  # IIIF 已在服务器端裁好
        if rec is None:
            print(f"ERROR {args[0]} 不在 IA_ITEMS 白名单里：IA 的条目没有许可字段，登记前先确认原作与扫描都属公有领域")
            return EXIT_LICENSE
        title = args[0]
    else:
        title = args[0] if args[0].startswith("File:") else "File:" + args[0]
        # 要裁切时按比例多要像素，裁完仍有 width 宽；Commons 的缩略图不会超过原图尺寸
        ask = math.ceil(width * 100 / float(region.split(",")[2])) if region else width
        try:
            title, info = query(title, ask)
        except (LookupError, OSError) as e:
            print(f"ERROR {e}")
            return 1
        rec = record(title, info)
        rec["source_width"], rec["source_height"] = info.get("width"), info.get("height")
        if region:
            rec["region"] = region
        if license_label(rec["license"]) is None:
            print(f"ERROR 许可「{rec['license'] or '缺失'}」不在可用范围（公有领域、无已知版权限制、CC0、CC BY）内，换一幅图：{rec['page']}")
            return EXIT_LICENSE
        url = info.get("thumburl") or info["url"]

    out_dir = Path(opts["-o"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(title[5:]).stem if title.startswith("File:") else title[3:].replace("$", "-")
    name = opts["--name"] or re.sub(r"[^\w-]+", "-", stem).strip("-").lower()
    raw = out_dir / f"{name}.download{Path(urllib.parse.urlparse(url).path).suffix.lower() or '.jpg'}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw.write_bytes(r.read())
    except OSError as e:
        print(f"ERROR 下载失败：{e}")
        return 1
    img = shrink(raw, out_dir / name, width, region)
    if img is None:
        return 1
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
