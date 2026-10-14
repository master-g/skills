import base64, sys
from pathlib import Path
spec, png = Path(sys.argv[1]), Path(sys.argv[2])
uri = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()
block = f'''      <figure
        class="plate"
        data-source="https://commons.wikimedia.org/wiki/File:M.Maier._Atalanta_Fugiens._1618._Emblem_XLII.JPG"
        data-license="Public domain"
      >
        <span class="marginnote"
          >题图　《逃离的阿塔兰忒》（<em>Atalanta Fugiens</em>）第 42 幅：『行于化学者，当以自然为向导，理性为手杖，经验为眼镜，阅读为明灯。』Matthäus
          Merian 刻，1618。图源
          <a
            href="https://commons.wikimedia.org/wiki/File:M.Maier._Atalanta_Fugiens._1618._Emblem_XLII.JPG"
            >Wikimedia Commons</a
          >，公有领域。</span
        >
        <img
          src="{uri}"
          alt="自然女神手持花枝与果实在前行走，戴眼镜、拄杖、提灯的老者循她的足迹跟在后面"
        />
      </figure>
'''
s = spec.read_text(encoding="utf-8")
anchor = '      <p class="byline">Silvanus P. Thompson 著 · 1910 年初版，1914 年修订</p>\n'
assert s.count(anchor) == 1
spec.write_text(s.replace(anchor, anchor + block), encoding="utf-8")
