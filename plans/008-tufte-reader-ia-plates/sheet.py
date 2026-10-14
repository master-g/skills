"""sheet.py plates.md 输出.png —— 按图录「高清版」表取 50 幅的小图（160px），拼成一张总览图，给人目视核对裁切。
联网，只读仓库；需要 ImageMagick 的 magick。小图存在输出文件旁的 <输出名>.d/ 目录里。"""
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

UA = "tufte-reader-plate/1.0 (https://github.com/master-g/skills)"
text = open(sys.argv[1], encoding="utf-8").read()
out = Path(sys.argv[2]).resolve()
tmp = out.with_suffix(".d")
tmp.mkdir(parents=True, exist_ok=True)
rows = re.findall(r"^\|\s*(\d+)\s*\|\s*`'ia:([\w.-]+)\$(\d+)'`\s*\|\s*`(pct:[\d.,]+)`\s*\|", text, re.M)
files = []
for n, item, leaf, region in rows:
    f = tmp / f"{int(n):02d}.jpg"
    if not f.exists():
        req = urllib.request.Request(f"https://iiif.archive.org/iiif/{item}${leaf}/{region}/160,/0/default.jpg",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            f.write_bytes(r.read())
        time.sleep(0.3)
    files.append(str(f))
# 不用 montage（它要找字体，有的环境找不到）：每 10 幅横拼一行，再竖拼；第 1 行是第 1–10 幅，以此类推
cmd = ["magick"]
for i in range(0, len(files), 10):
    cmd += ["(", *files[i:i + 10], "-resize", "160x150", "-background", "white", "-gravity", "center",
            "-extent", "166x156", "+append", ")"]
subprocess.run(cmd + ["-append", str(out)], check=True)
print(f"{len(files)} 幅 → {out}")
