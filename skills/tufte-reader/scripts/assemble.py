#!/usr/bin/env python3
"""assemble.py 源目录 -o 页面.html [--only 片段名] [build.py 的参数]

把源目录里的片段拼成页面，填回图元库的图，再调 build.py 构建。页面每次从片段重新生成，
要改内容就改片段，不改页面。

源目录的布局：
  head.html        shell.html 从开头到 </header>：扉页、摘要、读本说明
  chNN.html        每章一个片段（一个完整的 <article class="chapter">），按文件名排序
  apx*.html        附录，排在各章之后；没有就不建
  refs.html        参考文献；没有就不建
  tail.html        shell.html 从 <!--TR:JS--> 到文件末尾
  figs.py          图元库的图，往 FIGS 里加条目；没有就不建
  chNN.figs.py     分章派发时每章自己的画图脚本，与 figs.py 在同一个进程里依次执行

--only ch03 只拼这一章，写到页面旁边的 <页面名>.ch03.check.html 再构建，供写这一章的人试构建；
只执行 figs.py 和这一章的画图脚本。核对完删掉这个文件。

其余以 -- 开头的参数（如 --open）原样交给 build.py，退出码也是它的。
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import build  # noqa: E402  —— 认识哪些参数由它定
from figlib import embed  # noqa: E402


def load_figs(paths):
    """依次执行画图脚本，收集各自的 FIGS。全书的图在同一个进程里画，图内 id 的前缀才各不相同。"""
    figs, owner, clashes = {}, {}, []
    for i, path in enumerate(paths):
        sys.path.insert(0, str(path.parent))
        spec = importlib.util.spec_from_file_location(f"_tr_figs_{i}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for key, fig in getattr(mod, "FIGS", {}).items():
            # 各脚本可能共用 figlib 的那个 FIGS：同一个键换了一幅图，才是后一个脚本覆盖了前一个的
            if key in figs and figs[key] is not fig:
                clashes.append(f"{key}（{owner[key]}、{path.name}）")
            owner.setdefault(key, path.name)
            figs[key] = fig
    if clashes:
        raise KeyError("图的键名重复：" + "；".join(clashes) + "。键名以章 id 开头")
    return figs


def main(argv):
    flags = [a for a in argv if a.startswith("--") and a != "--only"]
    rest = [a for a in argv if a not in flags]
    unknown = sorted(set(flags) - build.FLAGS)
    if unknown:
        print("ERROR 不认识的参数：" + "、".join(unknown))
        return 2
    opts = {}
    for key in ("-o", "--only"):
        if key in rest:
            at = rest.index(key)
            if at + 1 >= len(rest):
                print(f"ERROR {key} 后面缺参数")
                return 2
            opts[key] = rest[at + 1]
            del rest[at : at + 2]
    if len(rest) != 1 or "-o" not in opts:
        print(__doc__)
        return 2
    src, out = Path(rest[0]).resolve(), Path(opts["-o"]).resolve()
    if not src.is_dir():
        print(f"ERROR 源目录不存在：{src}")
        return 2

    chapters = sorted(src.glob("ch[0-9][0-9].html")) + sorted(src.glob("apx*.html"))
    only = opts.get("--only")
    if only:
        chapters = [p for p in chapters if p.stem == only]
        if not chapters:
            print(f"ERROR 源目录里没有 {only}.html")
            return 2
        out = out.with_name(f"{out.stem}.{only}.check.html")
    parts = [src / "head.html", *chapters, src / "refs.html", src / "tail.html"]
    missing = [p.name for p in parts if p.name in ("head.html", "tail.html") and not p.is_file()]
    if missing or not chapters:
        print("ERROR 源目录缺 " + "、".join(missing or ["chNN.html"]))
        return 2
    html = "".join(p.read_text(encoding="utf-8") for p in parts if p.is_file())

    fig_scripts = [p for p in [src / "figs.py", *sorted(src.glob("ch[0-9][0-9].figs.py")), *sorted(src.glob("apx*.figs.py"))]
                   if p.is_file() and (not only or p.name in ("figs.py", f"{only}.figs.py"))]
    try:
        page = embed(html, load_figs(fig_scripts))
    except KeyError as e:
        print(f"ERROR {e.args[0]}")
        return 1
    out.write_text(page, encoding="utf-8")
    print(f"拼接    片段 {len(chapters)} 个  →  {out}", flush=True)
    return subprocess.call([sys.executable, str(SCRIPTS / "build.py"), str(out), *flags])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
