"""measure_plate.py 页面.html —— 量题图在 1280/390 宽、明暗主题下的渲染宽度与样式。"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
url = Path(sys.argv[1]).resolve().as_uri()
JS = """() => [...document.querySelectorAll('figure.plate img')].map(i => {
  const s = getComputedStyle(i), host = i.closest('header.titlepage, article.chapter');
  return [Math.round(i.getBoundingClientRect().width), Math.round(host.getBoundingClientRect().width), s.mixBlendMode, s.filter, s.backgroundColor];
})"""
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    for w in (1280, 390):
        for scheme in ("light", "dark"):
            pg = b.new_page(viewport={"width": w, "height": 900}, color_scheme=scheme)
            pg.goto(url, wait_until="domcontentloaded"); pg.wait_for_timeout(800)
            print(w, scheme, pg.evaluate(JS))
            pg.close()
    b.close()
