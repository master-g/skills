"""check_ia.py plates.md —— 核对图录「高清版」表：每行的 IIIF 裁切能取到，裁出的画面与 Commons 上同一幅的单幅文件一致。
联网，只读；需要 ImageMagick 的 magick 解码图片。用法：python3 -I check_ia.py <skill>/references/plates.md

一致性用相关系数衡量：两张图都缩成 24×24 灰度后的皮尔逊相关。同一幅画面实测 0.69–0.97，不同画面最高 0.54（advisor 在 50×48 对上测得），阈值取 0.6。
第 11、12、25 幅在 Commons 上只有整页扫描，第 45 幅画面留白多、相关系数不稳；这四幅只检查宽高比，打印「人工核对」。"""
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

UA = "tufte-reader-plate/1.0 (https://github.com/master-g/skills)"
NO_REF = {11, 12, 25, 45}
MIN_SCORE = 0.6


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    time.sleep(0.3)
    return data


def gray(data):
    """图片字节 → 24×24 灰度的去均值单位向量，外加原图宽高比。"""
    px = subprocess.run(["magick", "-", "-colorspace", "gray", "-resize", "24x24!", "-depth", "8", "gray:-"],
                        input=data, capture_output=True, check=True).stdout
    size = subprocess.run(["magick", "-", "-format", "%w %h", "info:"], input=data, capture_output=True,
                          check=True).stdout.split()
    v = list(px)
    m = sum(v) / len(v)
    v = [x - m for x in v]
    s = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / s for x in v], int(size[0]) / int(size[1])


def commons_thumb(title):
    p = {"action": "query", "format": "json", "titles": title, "prop": "imageinfo", "iiprop": "url",
         "iiurlwidth": "300"}
    q = json.loads(fetch("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)))
    page = next(iter(q["query"]["pages"].values()))
    return page["imageinfo"][0]["thumburl"]


if not shutil.which("magick"):
    sys.exit("需要 ImageMagick 的 magick")
text = open(sys.argv[1], encoding="utf-8").read()
singles = {int(n): f.strip() for n, f in re.findall(r"^\|\s*(\d+)\s*\|\s*(File:[^|]+?)\s*\|", text, re.M)}
rows = re.findall(r"^\|\s*(\d+)\s*\|\s*`'ia:(atalantafugiensh00maie)\$(\d+)'`\s*\|\s*`(pct:[\d.,]+)`\s*\|", text, re.M)
bad = 0
for n, item, leaf, region in rows:
    n = int(n)
    try:
        crop, ar = gray(fetch(f"https://iiif.archive.org/iiif/{item}${leaf}/{region}/300,/0/default.jpg"))
    except Exception as e:  # noqa: BLE001 —— 网络或解码失败都算这一行不通过
        print(f"FAIL 第 {n} 幅：取不到裁切图（{e}）")
        bad += 1
        continue
    if not 0.9 <= ar <= 1.3:
        print(f"FAIL 第 {n} 幅：宽高比 {ar:.2f}，画面应接近方形（0.9–1.3）")
        bad += 1
        continue
    if n in NO_REF:
        print(f"SKIP 第 {n} 幅：没有可靠参照，宽高比 {ar:.2f}，人工核对")
        continue
    ref, _ = gray(fetch(commons_thumb(singles[n])))
    score = sum(a * b for a, b in zip(crop, ref))
    if score < MIN_SCORE:
        print(f"FAIL 第 {n} 幅：与 {singles[n]} 的相关系数 {score:.2f} < {MIN_SCORE}")
        bad += 1
print(f"{'通过' if not bad else '失败'}：高清版 {len(rows)} 行，{bad} 处问题")
sys.exit(1 if bad or len(rows) != 50 else 0)
