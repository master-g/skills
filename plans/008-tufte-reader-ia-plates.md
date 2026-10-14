# Plan 008: plate.py 支持 Internet Archive 扫描本（IIIF 裁切），登记 Atalanta Fugiens 为首个条目并换成 1000px 高清版

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**：本计划在 007 之上打补丁。先确认 007 已经合入，且 `plate.py` 与 `test_plate.py` 在 007 之后没有改过：
> `cmp skills/tufte-reader/scripts/plate.py plans/007-tufte-reader-plates/plate.py && cmp skills/tufte-reader/tests/test_plate.py plans/007-tufte-reader-plates/test_plate.py && echo SAME`
> 预期输出 `SAME`。`references/plates.md` 允许维护者在 007 之后改过措辞（007 请维护者审阅 50 条中文大意）：图录的改动由 `apply_catalog.py` 按锚点完成，只动「取图」一节的几行、图录引言的一句和「高清版」表，不碰主表；锚点找不到时脚本报 `AssertionError` 且不写文件，那才算漂移。

## Status

- **Priority**: P2
- **Effort**: S（代码和数据都已备好：两个 `.py` 文件以补丁提供，图录改动以脚本提供；执行者的工作主要是应用和核对）
- **Risk**: LOW
- **Depends on**: plans/007-tufte-reader-plates.md（必须 DONE）
- **Category**: direction
- **Planned at**: commit `55a66e8`, 2026-10-14（007 尚未执行；补丁以 007 的附件为基准生成）

## Why this matters

007 的图录里，Atalanta Fugiens 是唯一有逐幅索引的系列，但主表用的是 Commons 上的单幅文件，宽度只有 580–650px（「系列」清单里的其他系列在 Commons 上多数有 1000px 以上的文件，不需要这一步）。题图在页面上约 480 CSS 像素宽，高分屏（Mac、手机）上需要约 1000 个物理像素才清楚。advisor 在 2 倍像素密度下截图，看到 600px 级别的图源排线发糊、出现马赛克（4 级灰度量化会加重这种块状感）；同样的位置换成 1000px 图源就清楚了。

更清晰、完整、未上色的版本在 Internet Archive：Getty 研究所扫描的 `atalantafugiensh00maie`，232 页，500ppi。Commons 上那 50 幅单图本来就是从这套扫描裁出来的。IA 支持 IIIF，服务器端可以按百分比区域裁出画面，再按要求的宽度返回，所以不需要本地裁切工具。advisor 已经算好 50 幅各自的叶号和区域：46 幅用 Commons 单图作模板自动匹配，4 幅目测定框；50 幅都逐一目视检查过。本计划把这些数据写进图录，并让 `plate.py` 支持这种来源。IA 来源是通用机制：以后「系列」里别的扫描本（Fludd、Kircher、Hooke 在 IA 上都有）按同一个白名单逐条登记，不用再改代码结构。

### 维护者已确认的决定（2026-10-14，不要改）

- **对 IA 放行这一个条目。** 007 的原则是「只从 Commons 取图」，因为 Commons 有机器可读的许可字段；IA 的元数据里没有许可字段。维护者同意在 `plate.py` 里用写死的白名单 `IA_ITEMS` 放行 `atalantafugiensh00maie`，并在白名单里写明依据：1618 年的原作早已进入公有领域；扫描是平面作品的忠实复制；Commons 上由同一扫描裁出的单图都标为 Public domain。白名单之外的 IA 条目一律退出码 3。
- **不用 Commons 上 Science History Institute 的整页翻拍本。** 它只传了约 30 幅，部分是手工上色的，页面有透视和弯曲。

### advisor 调研中顺带发现的问题（已在 007 修正，这里只作记录）

Commons 上名为 `Michael Maier Atalanta Fugiens Emblem 11.jpeg` 的文件画的其实是第 25 幅（日月二人斩龙）。007 的图录第 11 幅已改用 `File:Atalanta Fugiens 11 Latona.jpg`。

## Current state

（以下是 007 执行后的状态。）

- `skills/tufte-reader/scripts/plate.py`：只支持 Commons 来源。`main()` 把参数一律当作 `File:…`，调 `query()` 读许可，再经 `record()`、`shrink()`、`snippet()` 产出。`snippet()` 里图源名写死为 `Wikimedia Commons`。
- `skills/tufte-reader/tests/test_plate.py`：5 个离线测试，网络调用都用 `mock` 拦截。
- `skills/tufte-reader/references/plates.md`：「取图」一节只讲 Commons；「图录」有 50 行主表（Commons 单图）和一张 5 行的「高清版」表（Commons 上的高分辨率文件）。
- 整个技能的测试共 43 个。

**附件**（`plans/008-tufte-reader-ia-plates/`）：

| 文件               | 用途                                                                                                                                                                                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `008.patch`        | 对 `plate.py`、`test_plate.py` 的补丁（`git diff` 格式，带 index 行），以 007 附件为基准；advisor 已在 007 附件的副本上验证，打完与目标版本逐字节一致                                                                                                                                   |
| `apply_catalog.py` | 按锚点修改 `plates.md`：改写「取图」一节和图录引言一句，用内置的 50 行数据重写「高清版」表；主表不动。advisor 在三种输入上验证过：原样的 007 图录（结果与目标版本逐字节一致）、改过两处大意和主题的图录（改动保留、两个核对脚本通过）、锚点句被改过的图录（`AssertionError`，文件不变） |
| `check_ia.py`      | 联网核对「高清版」表：50 行都能取到，宽高比在 0.9–1.3，裁出的画面与 Commons 单图的相关系数不低于 0.6（第 11、12、25、45 幅只查宽高比）                                                                                                                                                  |
| `sheet.py`         | 联网取 50 幅 160px 小图，拼成一张 10×5 的总览图，用来目视核对裁切                                                                                                                                                                                                                       |

改动内容：

- `plate.py` 新增来源 `'ia:<条目>$<叶号>'`，必须同时给 `--region pct:x,y,w,h`。脚本先查 `IA_ITEMS` 白名单；条目不在白名单里退出码 3，参数格式不对退出码 2，这两种情况都不访问网络。图片地址是 `https://iiif.archive.org/iiif/<条目>$<叶号>/<区域>/<宽>,/0/default.jpg`。图注里的出处链接是阅读器页面 `https://archive.org/details/<条目>/page/n<叶号−1>/mode/1up`：IIIF 的叶号从 1 数，阅读器从 0 数，advisor 比对过两边的图片确认了这一点。图源名写成「Internet Archive（Getty Research Institute 扫描）」。Commons 来源的行为不变；顺带把下载失败也纳入报错，退出码 1。
- `test_plate.py` 新增 2 个测试：IA 地址、出处链接和图注的拼法；白名单外的条目、缺 `--region`、`--region` 格式不对、缺叶号四种情况的退出码，并确认都没有访问网络。
- `plates.md`（由 `apply_catalog.py` 修改）：「取图」一节改为默认用 IA 高清版，给出 IA 和 Commons 两种命令（IA 的来源参数要用单引号，否则 `$` 会被 shell 展开）；说明白名单机制；「高清版」表换成 50 行 IA 参数（幅 | 来源 | 区域），主表保留作退路和对照；末尾加一条登记别的 IA 扫描本的步骤。

## Commands you will need

| Purpose  | Command                                                                                              | Expected on success                                        |
| -------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 技能测试 | `python3 -m unittest discover -s skills/tufte-reader/tests`                                          | `Ran 45 tests`，末行 `OK`                                  |
| 文档门禁 | `make check`                                                                                         | `技能文档引用检查通过`，exit 0                             |
| 格式     | `npx prettier --check skills/tufte-reader/references/plates.md`                                      | 通过                                                       |
| IA 核对  | `python3 -I plans/008-tufte-reader-ia-plates/check_ia.py skills/tufte-reader/references/plates.md`   | 4 行 `SKIP …人工核对`，末行 `通过：高清版 50 行，0 处问题` |
| 图录核对 | `python3 -I plans/007-tufte-reader-plates/check_catalog.py skills/tufte-reader/references/plates.md` | `通过：文件 50 个，分类 22 个，0 处问题`                   |

后两条需要联网，`check_ia.py` 还需要 ImageMagick 的 `magick`。`T=$(mktemp -d)`（fish：`set T (mktemp -d)`）。

## Scope

**In scope**：

- `skills/tufte-reader/scripts/plate.py`
- `skills/tufte-reader/tests/test_plate.py`
- `skills/tufte-reader/references/plates.md`
- `plans/README.md`（只改本计划的状态行）

**Out of scope**：

- `build.py`、`tufte.css`、`specimen.html`、`SKILL.md`、`markup.md`、`dispatch.md`、`style.md`：题图的元素、样式、检查和文档写法 007 已经定好，本计划不改。specimen 的扉页图是 Commons 上第 42 幅的高清文件，已经清楚，不换。
- 给 `IA_ITEMS` 加别的条目：每个条目都需要维护者单独确认许可依据。
- `make install`、提交、推送：由维护者决定。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `tufte-reader`。示例：`feat(tufte-reader): fetch Atalanta Fugiens plates in high resolution from Internet Archive`。
- 未经操作者指示不要提交、不要推送。

## Steps

### Step 1：打补丁，改图录

```sh
git apply --check plans/008-tufte-reader-ia-plates/008.patch && git apply plans/008-tufte-reader-ia-plates/008.patch
python3 -I plans/008-tufte-reader-ia-plates/apply_catalog.py skills/tufte-reader/references/plates.md
npx prettier --write skills/tufte-reader/references/plates.md
```

`git apply --check` 失败，或 `apply_catalog.py` 报 `AssertionError`，都按 STOP 处理。不要手工合并；脚本失败时不会写文件，图录保持原样。

**Verify**：

- `git diff --stat` → 三个文件有变化：`plate.py`、`test_plate.py`、`plates.md`。
- `grep -c "ia:atalantafugiensh00maie" skills/tufte-reader/references/plates.md` → `51`（50 行表格，加「取图」里的示例 1 处）。
- `grep -n '"atalantafugiensh00maie": {' skills/tufte-reader/scripts/plate.py` → 1 行。
- `git diff skills/tufte-reader/references/plates.md | grep '^[-+]| [0-9]' | grep -v 'ia:atalantafugiensh00maie\|File:.*Emblema\|File:.*Emblem XLII\|File:.*Emblem XXVII'` → 无输出（主表的 50 行没有被改动；被删的只有原「高清版」表的 5 行）。

### Step 2：离线测试与格式

**Verify**：

- `python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 45 tests`，`OK`。
- `npx prettier --check skills/tufte-reader/references/plates.md` → 通过。
- `make check` → exit 0。

### Step 3：联网核对（没网络时写「未运行」，并按 STOP 处理：这一步是本计划的主要验收）

```sh
python3 -I plans/008-tufte-reader-ia-plates/check_ia.py skills/tufte-reader/references/plates.md
python3 -I plans/007-tufte-reader-plates/check_catalog.py skills/tufte-reader/references/plates.md
```

预期：第一条输出第 11、12、25、45 幅各一行 `SKIP`，末行 `通过：高清版 50 行，0 处问题`；第二条输出 `通过：文件 50 个，分类 22 个，0 处问题`。第二条从 007 时的 55 个文件减到 50 个，是因为原来 5 行的 Commons「高清版」表被换掉了。

再生成总览图，附在汇报里，由审阅者目视核对：

```sh
python3 -I plans/008-tufte-reader-ia-plates/sheet.py skills/tufte-reader/references/plates.md "$T/ia-sheet.png"
```

预期输出 `50 幅 → …/ia-sheet.png`。图上 10×5 排列，第 1 行是第 1–10 幅，依此类推。每一格应该是一幅完整的方形版画：带刻线边框，没有切掉人物，没有混进正文文字，也没有上色。

### Step 4：实际取一幅，再验证拒绝路径

```sh
cd "$T"
python3 <repo>/skills/tufte-reader/scripts/plate.py 'ia:atalantafugiensh00maie$185' --region pct:2.9,18.1,75.5,52.8 -o figures/plates --name atalanta-42; echo "rc=$?"
python3 <repo>/skills/tufte-reader/scripts/plate.py 'ia:someotherbook$12' --region pct:1,2,3,4 -o figures/plates; echo "rc=$?"
```

（`<repo>` 换成仓库根目录的绝对路径。）

预期：第一条输出 `取图 … atalanta-42.png  约 134 KB  许可 Public domain`，以及一段 `<figure class="plate" data-source="https://archive.org/details/atalantafugiensh00maie/page/n184/mode/1up" data-license="Public domain">`，图注里有「图源 …Internet Archive（Getty Research Institute 扫描）…，公有领域。」，`rc=0`。`magick identify figures/plates/atalanta-42.png` 报告宽 1000。第二条输出 `ERROR ia:someotherbook$12 不在 IA_ITEMS 白名单里…`，`rc=3`。

## Test plan

- 新增测试由补丁带入 `test_plate.py`：`test_ia_source_in_allowlist`（IIIF 地址、阅读器链接的叶号减 1、图注图源名、不带署名）和 `test_ia_rejects_unlisted_item_and_bad_args`（四种拒绝情况的退出码，以及都没有访问网络）。
- 联网部分由 `check_ia.py`、`check_catalog.py` 和 Step 4 覆盖，不进单元测试，因为单元测试要能离线跑。
- 结果：`Ran 45 tests`，`OK`。

## Done criteria

- [ ] `python3 -m unittest discover -s skills/tufte-reader/tests` → `Ran 45 tests`，`OK`
- [ ] `make check` exit 0；`npx prettier --check skills/tufte-reader/references/plates.md` 通过
- [ ] `check_ia.py` 末行 `通过：高清版 50 行，0 处问题`
- [ ] `check_catalog.py` 末行 `通过：文件 50 个，分类 22 个，0 处问题`
- [ ] Step 4 两条命令分别是 `rc=0`（PNG 宽 1000）和 `rc=3`
- [ ] 总览图 `ia-sheet.png` 附在汇报里
- [ ] `git status --porcelain` 只列出「Scope」里的文件
- [ ] `plans/README.md` 中本计划的状态行已更新

## STOP conditions

- 漂移检查没有输出 `SAME`，或者 007 还没合入。
- `git apply --check` 失败，或 `apply_catalog.py` 报 `AssertionError`。
- `check_ia.py` 有 FAIL 行，或者取不到 IIIF 图片（例如 HTTP 4xx/5xx、返回的是 HTML 而不是图片）。IA 改了 IIIF 的地址格式时也会出现这种情况，不要自己猜新地址。
- 总览图里有任何一格不是完整的版画（裁掉一部分、混进正文、取错页）。不要自己改区域数值，写出是第几幅、哪里不对。
- 联网核对无法运行。这一步是主要验收，汇报「未运行」并停下，不要标 DONE。

## Maintenance notes

- **区域数据怎么来的**：叶号按「第 N 幅在 IIIF 叶号 21 + 4(N−1)」排列，50 幅都落在这个规律上。46 幅的区域用 Commons 单图作模板，在 500px 宽的整页上由粗到细搜索得到（相关系数 0.81–0.97）；第 11、12、25、45 幅是目测或边框检测定的。所有区域四边各外扩 1 个百分点，把刻版边框包进来。重新生成的脚本没有放进仓库，需要时让 advisor 重跑。
- **IA 服务的依赖**：取图依赖 `iiif.archive.org` 的 IIIF Image API（区域写 `pct:`，尺寸写 `<宽>,`）。IA 改版导致取不到时，退路是图录主表的 Commons 单图（约 600px）。
- **白名单的扩充**：Fludd、Hooke 等其他系列在 IA 上也有扫描。以后要加，按 `IA_ITEMS` 上方注释的三条标准逐个确认，并请维护者认可依据；不要整批放行 IA 上的条目。
- **审阅重点**：`ia_source()` 里叶号减 1 的换算；白名单外的条目和参数错误都不能访问网络（测试里用 `mock` 断言）；图注里的图源名和链接。
