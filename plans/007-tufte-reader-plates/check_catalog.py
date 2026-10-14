"""check_catalog.py plates.md —— 核对图录：每个文件在 Commons 上存在、许可可用、箴言与 Commons 描述里的 OCR 文字对得上。
只读，访问网络。用法：python3 -I check_catalog.py <skill>/references/plates.md"""
import difflib
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "tufte-reader-plate/1.0 (https://github.com/master-g/skills)"
OK = re.compile(r"^(?:public domain|pdm(?:-owner)?|no restrictions|cc0(?: 1\.0)?|cc by(?: \d\.\d)?)$", re.I)


def norm(s):
    s = s.lower().replace("v", "u").replace("j", "i")
    return re.sub(r"[^a-z]", "", s)


def api(titles, extra):
    p = {"action": "query", "format": "json", "titles": "|".join(titles), **extra}
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p),
                                 headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=60))["query"]


text = open(sys.argv[1], encoding="utf-8").read()
rows = re.findall(r"^\|\s*(\d+)\s*\|\s*(File:[^|]+?)\s*\|(?:\s*([^|\n]+?)\s*\|)?", text, re.M)
cats = re.findall(r"\|\s*(Category:[^|]+?)\s*\|", text)
files = {f.strip(): (n, (m or "").strip()) for n, f, m in rows}
bad = 0
names = list(files)
for i in range(0, len(names), 50):
    q = api(names[i:i + 50], {"prop": "imageinfo", "iiprop": "extmetadata",
                              "iiextmetadatafilter": "LicenseShortName|ImageDescription"})
    norm_map = {x["to"]: x["from"] for x in q.get("normalized", [])}
    for page in q["pages"].values():
        title = norm_map.get(page["title"], page["title"])
        n, motto = files[title]
        if "imageinfo" not in page:
            print(f"FAIL 第 {n} 幅：文件不存在 {title}")
            bad += 1
            continue
        meta = page["imageinfo"][0]["extmetadata"]
        lic = meta.get("LicenseShortName", {}).get("value", "")
        if not OK.match(" ".join(lic.split())):
            print(f"FAIL 第 {n} 幅：许可 {lic or '缺失'}")
            bad += 1
        if not motto:
            continue
        desc = re.sub(r"<[^>]+>", " ", meta.get("ImageDescription", {}).get("value", ""))
        d, m = norm(desc), norm(motto)[:30]
        if len(d) < 40:
            print(f"SKIP 第 {n} 幅：Commons 描述里没有箴言，人工核对")
            continue
        best = max((difflib.SequenceMatcher(None, m, d[k:k + len(m)]).ratio() for k in range(0, len(d) - len(m) + 1)),
                   default=0)
        if best < 0.8:
            print(f"FAIL 第 {n} 幅：箴言与 Commons 描述不符（相似度 {best:.2f}）：{motto[:40]}")
            bad += 1
q = api(cats, {"prop": "categoryinfo"})
for page in q["pages"].values():
    files_n = page.get("categoryinfo", {}).get("files")
    if not files_n:
        print(f"FAIL 分类不存在或为空：{page['title']}")
        bad += 1
print(f"{'通过' if not bad else '失败'}：文件 {len(files)} 个，分类 {len(cats)} 个，{bad} 处问题")
sys.exit(1 if bad else 0)
