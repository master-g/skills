# Plan 013: tufte-reader 题图脚本按四本样例的反馈打磨：透明底、Commons 裁切、缩略图预览、帮助与文档措辞

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**：`git diff --stat 3b4c69d..HEAD -- skills/tufte-reader`
> 预期无输出（007–009 合入后 tufte-reader 没再变）。有输出就把「Current state」的摘录与现行代码逐段对照；对不上即为 STOP 条件。`references/plates.md` 允许维护者改过 50 条大意的措辞：文档改动由 `apply_docs.py` 按锚点完成，锚点找不到时它报 `AssertionError` 且不写任何文件，那才算漂移。

## Status

- **Priority**: P2
- **Effort**: S（四个脚本文件以成品提供，文档改动以脚本提供；执行者的工作是复制、应用、核对和联网实测）
- **Risk**: LOW（`plate.py` 的改动只加分支：透明底合成、本地裁切、成品纯色检查、帮助；Commons 与 IA 原有路径的行为不变，现有 50 个测试照常通过）
- **Depends on**: plans/007、008、009（均已 DONE 并合入 `3b4c69d`）
- **Category**: dx
- **Planned at**: commit `3b4c69d`, 2026-10-14

## Why this matters

007–009 合入后，advisor 让四个 sonnet worker 各按技能的「原创撰写」模式写了一本 3 章短读本并配题图（显微与观察、机械与流程、变化与提纯、天文与仪器）。四本都构建通过，选图也确实从主题出发、没有退回 Atalanta（只有炼金主题按寓意用了 3 幅）。但四个 worker 在同样的地方卡住：

- `plate.py` 遇到带透明通道的灰度 PNG（Commons 上不少裁切图是这种）会输出一张 3 KB 的纯灰图，退出码仍是 0；worker 只能换图绕过。
- `--region` 只对 IA 生效，Commons 上的整页扫描（Ramelli 的磨坊、锻坊等）裁不了，机械那本因此放弃了一章的题图。
- 搜图没有预览手段，worker 都是先取到临时目录再看；`find_plate.py` 按宽度排序把整页扫描排在前面，同一幅的 `.tif`/`.jpg` 重复出现。
- 两个脚本都不认 `-h`/`--help`，`-h` 被当作关键词或文件名。
- 「章首题图放在 `<h2>` 之后、第一个 `<section>` 的开头」三个 worker 都说没看懂放在 section 内还是外。
- 「系列」表对天文仪器、工序类主题覆盖薄，worker 靠大池子碰运气撞出了 Hevelius《天体机械》、Nova Reperta、Bosse，这三处值得补进表。
- SKILL.md 开头写「章末出处」，而 markup.md 说章与章之间不加出处，机械那本的 worker 为此困惑。

本计划把这些一次改掉。advisor 已在副本里实现并验证：57 个测试 OK；对 Commons 上 3282px 的 Ramelli 整页扫描用 `--region pct:12,8,70,55` 裁出 1000×981 的成品，101 KB；`find_plate.py --cat "Agostino Ramelli" --thumb` 拼出的总览图上整页扫描和裁切图一眼可辨；`make check`、prettier、图录核对（25 个分类）都通过。

### 维护者已确认的决定（不要改）

- 选图以主题为入口，风格由「系列」清单把关；许可白名单不变（公有领域、PDM、No restrictions、CC0、CC BY）；IA 仍只按 `IA_ITEMS` 白名单放行。本计划不碰这些。

## Current state

（`3b4c69d` 的状态。）

- `skills/tufte-reader/scripts/plate.py`：`shrink(raw, out_stem, width)` 用 `magick … -resize -colorspace gray -auto-level -level 15%,80% -colors 4` 压图，没有处理透明通道；`main()` 把 `--region` 只交给 `ia_source()`，Commons 路径忽略它；参数不对时打印 `__doc__` 返回 2，没有 `--help`。
- `skills/tufte-reader/scripts/find_plate.py`：`search()` 要求至少一个关键词；结果按宽度排序，不去重；没有缩略图。
- `skills/tufte-reader/tests/test_plate.py`：7 个测试；`tests/test_find_plate.py`：5 个测试；整个技能 50 个。
- `skills/tufte-reader/references/plates.md`「写法」一节：`- **章首题图**：放在该章 \`<h2>\` 之后、第一个 \`<section>\` 的开头。`；`references/markup.md`「## 题图」里有同一句；`SKILL.md` 第 10 行：`书的架构（扉页、目录、章、章末出处）`。
- 文档约定：Markdown 简体中文，章节按标题名引用，相对链接必须存在（`make check`）；格式由 prettier 决定。

**附件**（`plans/013-tufte-reader-plate-polish/`，都在副本里跑过）：

| 文件                 | 用途                                                                                                                                                                                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plate.py`           | 成品，覆盖 `skills/tufte-reader/scripts/plate.py`                                                                                                                                                                                                          |
| `find_plate.py`      | 成品，覆盖 `skills/tufte-reader/scripts/find_plate.py`                                                                                                                                                                                                     |
| `test_plate.py`      | 成品，覆盖 `skills/tufte-reader/tests/test_plate.py`（11 个测试，其中 1 个需要 ImageMagick，没有时自动跳过）                                                                                                                                               |
| `test_find_plate.py` | 成品，覆盖 `skills/tufte-reader/tests/test_find_plate.py`（8 个测试）                                                                                                                                                                                      |
| `apply_docs.py`      | 按锚点改 `plates.md`（选图、系列、取图、写法共 8 处，系列表加 3 行）、`markup.md`（1 句）、`SKILL.md`（1 句）。三个文件要么全改、要么全不改；advisor 在 `3b4c69d` 的副本上验证过结果与目标版本逐字节一致，锚点被改过的副本上报 `AssertionError` 且不写文件 |

改动内容：

- `plate.py`：`-h`/`--help` 打印说明、退出码 0，不联网。`shrink()` 先 `-background white -alpha remove -alpha off` 把透明底合成到白底；给了 `--region` 且来源是 Commons 时，按图源尺寸算出像素几何（新函数 `crop_geometry(w, h, region)`）用 `-crop … +repage` 裁；没有 magick 又要裁时报 ERROR、退出码 1。成品的标准差小于 0.02（透明底、空白页、裁错区域）时报 ERROR、删除成品、退出码 1。Commons 路径按裁切比例向 Commons 多要像素（`ceil(width × 100 / 区域宽%)`），裁完仍是 `--width` 宽。`<name>.json` 多记 `source_width`、`source_height`，裁过的记 `region`。`--region` 格式不对时统一退出码 2。IA 路径不变（IIIF 已在服务器端裁好，本地不再裁）。
- `find_plate.py`：`-h`/`--help`；只给 `--cat` 不给关键词时列出整个分类（查询串只有 `incategory:"…"`）；API 调用加 `iiurlwidth=320` 拿缩略图地址；结果按去掉扩展名的文件名去重，保留最宽的；`--thumb <目录>` 把列出的图各下载一张 320px 缩略图（`NN-<文件名>.jpg`，按表格顺序编号），有 magick 时拼成 `sheet.png`（每行 5 幅），拼图失败只警告。
- 文档：见 `apply_docs.py` 里的锚点对。要点：选图第 2 条加「选图前用 `--thumb` 看总览」，第 3 条改为「整页扫描只要画面完整就能用，`--region` 裁」；「系列」表加 Hevelius《Machina coelestis》、Nova Reperta、Abraham Bosse 三行，搜法段落写明只给 `--cat`、去重、`--thumb`、表外主题去大池子 `--deep`；「取图」写明 Commons 也能 `--region`、纯色成品的 ERROR、json 字段；章首题图位置改为「放在该章 `<h2>` 后面那个 `<section>` 的里面，作为它的第一个子元素」；SKILL.md「章末出处」改为「章末脚注、参考文献」。

## Commands you will need

| Purpose  | Command                                                                                              | Expected on success                                     |
| -------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 技能测试 | `python3 -m unittest discover -s skills/tufte-reader/tests`                                          | `Ran 57 tests`，末行 `OK`（没有 magick 时 `skipped=1`） |
| 文档门禁 | `make check`                                                                                         | `技能文档引用检查通过`，exit 0                          |
| 格式     | `npx prettier --check skills/tufte-reader/SKILL.md skills/tufte-reader/references/*.md`              | 通过                                                    |
| 图录核对 | `python3 -I plans/007-tufte-reader-plates/check_catalog.py skills/tufte-reader/references/plates.md` | `通过：文件 50 个，分类 25 个，0 处问题`                |

图录核对和 Step 3 需要联网；`plate.py` 的裁切和 `find_plate.py` 的总览图需要 ImageMagick 的 `magick`（本机已装）。`T=$(mktemp -d)`（fish：`set T (mktemp -d)`）。

## Scope

**In scope**：

- `skills/tufte-reader/scripts/plate.py`、`scripts/find_plate.py`（覆盖附件）
- `skills/tufte-reader/tests/test_plate.py`、`tests/test_find_plate.py`（覆盖附件）
- `skills/tufte-reader/references/plates.md`、`references/markup.md`、`SKILL.md`（由 `apply_docs.py` 改）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**：

- `build.py`、`tufte.css`、`specimen.html`、`dispatch.md`、`style.md`：题图的元素、样式、构建检查不变。
- `plate.py` 的许可白名单 `LICENSE_OK`、`IA_ITEMS`：政策由维护者定，本计划不碰。
- 给「系列」表加这三行之外的分类：每个都要核对存在和许可分布，另议。
- `make install`、提交、推送：由维护者决定。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `tufte-reader`。示例：`fix(tufte-reader): flatten alpha, crop Commons scans, preview thumbnails in plate scripts`。
- 未经操作者指示不要提交、不要推送。pre-commit 会跑 prettier 和 `make check`。

## Steps

### Step 1：覆盖脚本与测试

```sh
cp plans/013-tufte-reader-plate-polish/plate.py skills/tufte-reader/scripts/plate.py
cp plans/013-tufte-reader-plate-polish/find_plate.py skills/tufte-reader/scripts/find_plate.py
cp plans/013-tufte-reader-plate-polish/test_plate.py skills/tufte-reader/tests/test_plate.py
cp plans/013-tufte-reader-plate-polish/test_find_plate.py skills/tufte-reader/tests/test_find_plate.py
```

**Verify**：

- `python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 57 tests`，`OK`。
- `grep -c '"atalantafugiensh00maie": {' skills/tufte-reader/scripts/plate.py` → `1`；`grep -c "no restrictions" skills/tufte-reader/scripts/plate.py` → `1`（白名单没动）。

### Step 2：改文档

```sh
python3 -I plans/013-tufte-reader-plate-polish/apply_docs.py skills/tufte-reader
npx prettier --write skills/tufte-reader/SKILL.md skills/tufte-reader/references/plates.md skills/tufte-reader/references/markup.md
```

`apply_docs.py` 报 `AssertionError` 就按 STOP 处理，不要手工改。

**Verify**：

- `grep -c "Category:" skills/tufte-reader/references/plates.md` → `28`（原来 24：表里多 3 行，搜法段落多 1 行）。
- `grep -c "作为它的第一个子元素" skills/tufte-reader/references/plates.md skills/tufte-reader/references/markup.md` → 各 `1`。
- `grep -c "章末出处" skills/tufte-reader/SKILL.md` → `0`。
- `git diff skills/tufte-reader/references/plates.md | grep '^[-+]| [0-9]'` → 无输出（图录主表和高清版表没动）。
- `make check` → exit 0；prettier `--check` 三个文件通过。

### Step 3：联网实测（没网络时写「未运行」，不要标 DONE）

```sh
python3 skills/tufte-reader/scripts/find_plate.py --help | head -1; echo "rc=$?"
python3 skills/tufte-reader/scripts/find_plate.py --cat "Agostino Ramelli" --limit 12 --thumb "$T/cand"
python3 -I plans/007-tufte-reader-plates/check_catalog.py skills/tufte-reader/references/plates.md
cd "$T"
python3 <repo>/skills/tufte-reader/scripts/plate.py "File:Cut-away view of water-powered mill showing horizontal wheel with paddles, cog and shafts, and housing LCCN2006680147.tif" --region pct:12,8,70,55 -o figures/plates --name ramelli-mill; echo "rc=$?"
magick identify figures/plates/ramelli-mill.png
python3 -c "import json; d=json.load(open('figures/plates/ramelli-mill.json')); print(d['source_width'], d['source_height'], d['region'])"
```

（`<repo>` 换成仓库根目录的绝对路径。）

预期（advisor 2026-10-14 实测，Commons 的结果数会变，看形态）：

- 第一条打印 `find_plate.py 关键词… [--cat 分类] …`，`rc=0`。
- 第二条：`搜索  incategory:"Agostino Ramelli"`，结果约 10 个、可用约 7 个（已去重，`Sixteenth Century Cannon.jpg` 与 `Cannon2.jpg` 是不同文件名，仍各占一行），末尾一行 `缩略图  N 张 → …/cand/，总览 …/cand/sheet.png（按表格顺序，每行 5 幅）`。打开 `sheet.png`：每行 5 格，能看出哪些是整页扫描（带页眉和正文栏）、哪些是裁切图。
- 裁切取图：`取图 … ramelli-mill.png  约 100 KB  许可 Public domain`，`rc=0`；`magick identify` 报告 `PNG 1000x981`（高按裁切比例变化，宽是 1000）；json 打印 `3282 4096 pct:12,8,70,55`。打开成品：是磨坊的屋架与齿轮，顶上有 `FIGVRE CXV` 的花边标题，没有正文栏。
- 第三条（图录核对）：`通过：文件 50 个，分类 25 个，0 处问题`。

## Test plan

- `test_plate.py` 新增 4 个：`test_help_exits_zero_without_network`（`--help` 退出码 0、`--region bad` 退出码 2，都不联网）；`test_crop_geometry`（两组百分比到像素几何串）；`test_region_asks_commons_for_enough_pixels`（`--region` 宽 40% 时向 Commons 请求 2500px）；`test_shrink_flattens_alpha_and_rejects_blank`（透明底灰度 PNG 合成后不再是 `graya`、标准差大于 0.1；纯白页报 ERROR 且不留成品；`pct:0,0,50,50` 裁出 200×150；需要 magick，没有时跳过）。
- `test_find_plate.py` 新增 3 个：`test_help_and_category_only`（`--help` 退出码 0 不联网；只给 `--cat` 时查询串是 `incategory:"…"`，请求带 `iiurlwidth=320`）；`test_duplicates_keep_widest`（`.jpg`/`.tif` 同名只留 3000px 的那个）；`test_thumb_downloads_shown_rows`（只下载合格的三幅、按表格顺序编号 `01-a.jpg`…）。原 `test_usage_errors_do_not_touch_network` 的用例 `["--cat", "X"]` 改为 `["--deep"]`，因为只给分类现在是合法用法。
- 结果：`Ran 57 tests`，`OK`。

## Done criteria

- [ ] `python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 57 tests`，`OK`
- [ ] `make check` exit 0；prettier `--check` 对 SKILL.md 和 `references/*.md` 通过
- [ ] `grep -c "Category:" skills/tufte-reader/references/plates.md` → `28`；`grep -c "章末出处" skills/tufte-reader/SKILL.md` → `0`
- [ ] Step 3：`--help` 退出码 0；`--thumb` 产出 `sheet.png`；裁切取图 `rc=0` 且成品宽 1000；`check_catalog.py` 报 25 个分类通过（或明确写「未运行：无网络」）
- [ ] `git diff --stat` 只列出「Scope」里的 7 个技能文件（外加 `plans/README.md`）
- [ ] `plans/README.md` 中本计划的状态行已更新

## STOP conditions

- 漂移检查有输出，且摘录对不上。
- `apply_docs.py` 报 `AssertionError`。
- Step 1 测试数不是 57，或有失败（`skipped=1` 只在没有 magick 时出现，不算失败）。
- Step 3 裁切取图报 `ERROR 成品几乎是一片纯色`，或成品不是磨坊画面：说明 Commons 换了这个文件或缩略图档位变了，不要自己调百分比，汇报。
- `find_plate.py --cat` 不带关键词返回 `结果  0 个`：说明 CirrusSearch 对只有 `incategory:` 的查询行为变了，汇报。

## Maintenance notes

- **纯色检查的阈值**：成品标准差小于 0.02 判为纯色。真实版画压成 4 级灰度后标准差在 0.25–0.45；线条极少的小图可能接近阈值，误报时加 `--width` 不管用，要看是不是真的没画面。
- **Commons 裁切的像素来源**：脚本向 Commons 要 `width × 100 / 区域宽%` 像素宽的缩略图，上限是原图尺寸；原图不够大时成品会窄于 `--width`，这是预期，不是错误。
- **缩略图总览**：`sheet.png` 用 magick 的 `+append`/`-append` 拼，不用 `montage`（它要找字体）。每行 5 幅、按表格顺序，所以第 7 幅在第 2 行第 2 格。
- **样例**：四本样例读本和题图截图留在 advisor 的 scratchpad（`samples/`），没有放进仓库；要重现就用 SKILL.md 的「原创撰写」模式配题图写一本 3 章短读本。
- **审阅重点**：`shrink()` 里 `-alpha remove` 必须在 `-crop` 和 `-resize` 之前；IA 路径里 `region` 置 `None` 后不能再本地裁一次；`find_plate.py` 去重用去掉扩展名的小写文件名，`(cropped)` 之类后缀不同的视为不同文件（这是有意的）。
