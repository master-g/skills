# Plan 009: tufte-reader 加搜图脚本 find_plate.py，按主题词在 Commons 分类里找许可可用的高清题图

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**：本计划依赖 007 新建的 `scripts/plate.py` 和 `references/plates.md`。先确认 007 已合入，且这两处锚点还在：
>
> ```sh
> grep -c "^LICENSE_OK = re.compile\|^def license_label\|^def plain\|^API = \|^UA = " skills/tufte-reader/scripts/plate.py
> grep -c "^搜图用 Commons 的搜索 API：" skills/tufte-reader/references/plates.md
> ```
>
> 预期两行依次输出 `5` 和 `1`。008 执行与否都不影响本计划：008 改的是「取图」一节和「高清版」表，本计划只改「系列」末尾的一段。

## Status

- **Priority**: P2
- **Effort**: S（脚本、测试、文档改写脚本都已备好并在副本上跑过；执行者的工作是复制、应用和核对）
- **Risk**: LOW
- **Depends on**: plans/007-tufte-reader-plates.md（必须 DONE）。plans/008-tufte-reader-ia-plates.md 可先可后，建议在它之后执行，下面的测试数按这个顺序写
- **Category**: direction
- **Planned at**: commit `55a66e8`, 2026-10-14（007、008 尚未执行；附件以 007 的附件为基准）

## Why this matters

007 的图录把选图定为「以主题为入口」：从章节主题提关键词，到「系列」清单划定的 Commons 分类里找画面，风格由清单把关。但 007 给的搜法是一条手工拼的 `curl`，返回原始 JSON，写读本的 agent 要自己拆尺寸和许可字段，实际上会退回到只用 Atalanta Fugiens 那张现成的图录，选图又被局限回一本书。

本计划把那次 API 调用包成 `scripts/find_plate.py`：关键词加分类限定，一次取回搜索结果的尺寸和许可，用 `plate.py` 同一套许可白名单过滤，只列出宽度够的候选，按宽度排序，「文件」一列可以直接作 `plate.py` 的参数。advisor 联网实测：`dragon --cat "Musaeum Hermeticum"` 返回 3 幅公有领域、1400–2000px 的图；`alchemist --cat "Engravings in the Wellcome Collection"` 返回 5 幅 CC BY 4.0、3000px 以上的图；`telescope --cat "Emblem books" --deep` 返回 1 幅。

### 维护者已确认的决定（2026-10-14，不要改）

- **选图以主题为入口，不限于 Atalanta Fugiens**：风格由「系列」清单把关（同一时代、同一技法），Atalanta 图录是其中一个有逐幅索引的系列。
- **许可**：公有领域、PDM、无已知版权限制（Commons 的「No restrictions」）、CC0、CC BY（署名）。本脚本复用 `plate.py` 的 `license_label()`，不另写一份白名单。

## Current state

（以下是 007 执行后的状态；008 执行与否不影响这些位置。）

- `skills/tufte-reader/scripts/plate.py`：取图脚本。本计划复用它顶部的这几个名字，位置在文件前 55 行：
  - `plate.py:26`：`API = "https://commons.wikimedia.org/w/api.php"`
  - `plate.py:28`：`UA = "tufte-reader-plate/1.0 (https://github.com/master-g/skills)"`
  - `plate.py:35`：`LICENSE_OK = re.compile(r"^(?:public domain|pdm(?:-owner)?|no restrictions|cc0(?: 1\.0)?|cc by(?: \d\.\d)?)$", re.I)`
  - `plate.py:38`：`def license_label(short):` —— 许可短名 → 图注写法，不接受时返回 `None`
  - `plate.py:51`：`def plain(value):` —— 去掉 extmetadata 值里的 HTML 标签和实体
- `skills/tufte-reader/references/plates.md`「系列」一节的末尾有一段手工搜法，以这句开头（`plates.md:53`）：

  ```
  搜图用 Commons 的搜索 API：关键词加 `incategory:"<分类>"`（或 `deepcat:"<分类>"` 连子分类一起搜），一次返回尺寸和许可：
  ```

  后面是一个 `curl` 代码块，再接一段以「搜分类，不要猜。」结尾的说明（`plates.md:60`）。本计划用 `apply_docs.py` 把从开头那句到「搜分类，不要猜。」的整段换成脚本用法；它后面的「Science History Institute、Wellcome Collection……」那段不动。

- `skills/tufte-reader/tests/test_plate.py`：离线测试的写法样板——`sys.path.insert(0, …/scripts)` 后 `import plate`，网络调用用 `unittest.mock` 拦截。新测试照这个结构写（附件已写好）。
- 测试总数：007 执行后 43 个，008 执行后 45 个。本计划加 5 个。
- 文档约定：Markdown 简体中文，章节按标题名引用，相对链接必须存在，`make check` 检查这两条；格式由 prettier 决定。

**附件**（`plans/009-tufte-reader-find-plates/`）：

| 文件                 | 用途                                                                                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `find_plate.py`      | 成品，复制到 `skills/tufte-reader/scripts/find_plate.py`                                                                                                                 |
| `test_find_plate.py` | 成品，复制到 `skills/tufte-reader/tests/test_find_plate.py`（离线，5 个测试）                                                                                            |
| `apply_docs.py`      | 按锚点改 `plates.md`：把「系列」末尾的 curl 搜法换成脚本用法。advisor 在 007 版和 008 版两种图录上验证过，改完 prettier 通过；锚点找不到时报 `AssertionError` 且不写文件 |

`find_plate.py` 做的事：把关键词和 `--cat` 拼成 CirrusSearch 查询（`关键词 incategory:"分类"`，`--deep` 时用 `deepcat:`），调 `generator=search&gsrnamespace=6&prop=imageinfo&iiprop=size|url|mime|extmetadata`，一次拿到每个结果的宽高、MIME、许可短名和文件页面。用 `plate.license_label()` 判许可，MIME 不是位图（PDF、DjVu）或宽度小于 `--min-width`（默认 1000）的不列出；`--all` 时全部列出并标明原因。参数错误（没有关键词、`--min-width`/`--limit` 不是数字）退出码 2，不访问网络；搜索失败退出码 1。`gsrlimit` 上限 50，脚本把更大的 `--limit` 截到 50。

## Commands you will need

| Purpose  | Command                                                                               | Expected on success                                   |
| -------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| 技能测试 | `python3 -m unittest discover -s skills/tufte-reader/tests`                           | 末行 `OK`；008 已执行时 `Ran 50 tests`，否则 `Ran 48` |
| 文档门禁 | `make check`                                                                          | `技能文档引用检查通过`，exit 0                        |
| 格式     | `npx prettier --check skills/tufte-reader/references/plates.md`                       | 通过                                                  |
| 搜图实测 | `python3 skills/tufte-reader/scripts/find_plate.py dragon --cat "Musaeum Hermeticum"` | 见 Step 3                                             |

测试用 `python3 -m unittest`，仓库里没装 pytest。

## Scope

**In scope**：

- `skills/tufte-reader/scripts/find_plate.py`（新建，复制附件）
- `skills/tufte-reader/tests/test_find_plate.py`（新建，复制附件）
- `skills/tufte-reader/references/plates.md`（只改「系列」末尾一段，由 `apply_docs.py` 完成）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**：

- `skills/tufte-reader/scripts/plate.py`、`tests/test_plate.py`：008 的漂移检查用 `cmp` 把它们钉在 007 附件的字节上，本计划只 import、不改。搜图逻辑全部放在新文件里。
- `build.py`、`tufte.css`、`specimen.html`、`SKILL.md`、`markup.md`、`dispatch.md`、`style.md`：题图的元素、样式、检查和写法 007 已经定好。SKILL.md 已经指向 `references/plates.md`，不需要再提脚本名。
- `plates.md` 的「选图」「取图」「写法」「图录」各节和「系列」的两张表：不动。
- 给「系列」加新分类：每个分类都要用 `check_catalog.py` 核对存在、再探测许可分布，另起计划。
- `make install`、提交、推送：由维护者决定。

## Git workflow

- 直接提交到 `main`，conventional commits，scope `tufte-reader`。示例：`feat(tufte-reader): add find_plate.py to search Commons categories for usable plates`。
- 未经操作者指示不要提交、不要推送。pre-commit 会跑 prettier 和 `make check`。

## Steps

### Step 1：加入脚本和测试

```sh
cp plans/009-tufte-reader-find-plates/find_plate.py skills/tufte-reader/scripts/find_plate.py
cp plans/009-tufte-reader-find-plates/test_find_plate.py skills/tufte-reader/tests/test_find_plate.py
```

**Verify**：`python3 -m unittest discover -s skills/tufte-reader/tests` → 末行 `OK`；`Ran 50 tests`（008 已执行）或 `Ran 48 tests`（008 未执行）。

### Step 2：改图录里的搜法

```sh
python3 -I plans/009-tufte-reader-find-plates/apply_docs.py skills/tufte-reader/references/plates.md
npx prettier --write skills/tufte-reader/references/plates.md
```

`apply_docs.py` 报 `AssertionError` 就按 STOP 处理，不要手工改。

**Verify**：

- `grep -c "find_plate.py" skills/tufte-reader/references/plates.md` → `3`。
- `grep -c "curl" skills/tufte-reader/references/plates.md` → `0`。
- `git diff --stat skills/tufte-reader/references/plates.md` → 只有这一个文件，改动在「系列」一节末尾；`git diff skills/tufte-reader/references/plates.md | grep '^[-+]|'` → 无输出（两张表没动）。
- `npx prettier --check skills/tufte-reader/references/plates.md` → 通过；`make check` → exit 0。

### Step 3：联网实测（没网络时写「未运行」，不要标 DONE）

```sh
python3 skills/tufte-reader/scripts/find_plate.py dragon --cat "Musaeum Hermeticum"
python3 skills/tufte-reader/scripts/find_plate.py alchemist --cat "Engravings in the Wellcome Collection" --limit 5
python3 skills/tufte-reader/scripts/find_plate.py telescope --cat "Emblem books" --deep --all --limit 6; echo "rc=$?"
python3 skills/tufte-reader/scripts/find_plate.py; echo "rc=$?"
```

预期（advisor 2026-10-14 实测，结果数会随 Commons 的上传变化，看形态不看具体数字）：

- 第一条：第一行 `搜索  dragon incategory:"Musaeum Hermeticum"`，第二行 `结果  N 个，可用 M 个（许可可用且宽度不小于 1000px）`，然后一张 4 列的 Markdown 表，许可一列全是 `Public domain`，宽度从大到小（实测 3 幅：2056、1725、1423px）。
- 第二条：许可一列全是 `CC BY 4.0`，宽度 3000px 上下。
- 第三条：表里可能有带 `✗` 的行并标明原因；`rc=0`。
- 第四条：打印用法（第一行 `find_plate.py 关键词…`），`rc=2`。

## Test plan

- 新增测试在附件 `test_find_plate.py`，5 个，全部离线（`mock.patch("urllib.request.urlopen")`）：
  - `test_query_has_terms_and_category`：查询串是 `关键词 incategory:"分类"`，`Category:` 前缀和下划线被规整；`--deep` 用 `deepcat:`；`--limit 99` 截到 50；用的是 `plate.UA`。
  - `test_filters_license_width_and_mime`：6 个假结果里，公有领域 2000px、No restrictions 1500px、CC BY 1200px（TIFF）通过；CC BY-SA、600px、PDF 不列出；按宽度降序。
  - `test_all_lists_rejects_with_reasons`：`--all` 时三种不合格各带原因。
  - `test_no_results_hint`：没有合格结果时给提示、不打表头。
  - `test_usage_errors_do_not_touch_network`：四种参数错误都退出码 2，`urlopen` 没被调用。
- 联网行为由 Step 3 覆盖，不进单元测试。
- 结果：`Ran 50 tests`（或 48），`OK`。

## Done criteria

- [ ] `python3 -m unittest discover -s skills/tufte-reader/tests` → `OK`，测试数比执行前多 5
- [ ] `make check` exit 0；`npx prettier --check skills/tufte-reader/references/plates.md` 通过
- [ ] `grep -c "find_plate.py" skills/tufte-reader/references/plates.md` → `3`；`grep -c curl …/plates.md` → `0`
- [ ] Step 3 的四条命令形态符合预期（或明确写「未运行：无网络」）
- [ ] `cmp skills/tufte-reader/scripts/plate.py plans/007-tufte-reader-plates/plate.py`（008 未执行时）或 `git diff --stat -- skills/tufte-reader/scripts/plate.py` 为空（008 已执行时）：`plate.py` 没被改
- [ ] `git status --porcelain` 只列出「Scope」里的文件
- [ ] `plans/README.md` 中本计划的状态行已更新

## STOP conditions

- 漂移检查的两条 grep 不是 `5` 和 `1`，或 007 还没合入。
- `apply_docs.py` 报 `AssertionError`。
- Step 1 的测试有失败：`import plate` 失败说明 007 的 `plate.py` 不在 `scripts/` 里；`license_label` 相关断言失败说明 007 的许可白名单和本计划假设的不一样（应含 `no restrictions`）。两种都是 007 的状态和计划不符，汇报，不要改 `plate.py`。
- Step 3 第一条命令返回 `ERROR 搜索失败` 以外的异常（例如 JSON 解析错误）：说明 Commons API 的返回结构变了，不要自己猜新结构。
- 发现需要改「Out of scope」里的任何文件。

## Maintenance notes

- **搜索的边界**：CirrusSearch 按文件名、描述和分类文字匹配，关键词用英文或拉丁文比中文命中率高；`gsrlimit` 对普通请求上限 50，想多看就换关键词或分类，不要翻页。`deepcat:` 会递归子分类，Commons 对子分类数量有限制（约几百个），超大分类树可能返回空，这时退回 `incategory:` 或换更具体的子分类。
- **许可字段**：脚本只认 `LicenseShortName`。「No restrictions」已按维护者决定放行；其他写法（如 `Copyrighted free use`）和多许可模板（短名可能是 `CC BY-SA 4.0` 而同时标了 PD）一律按不合格列出，用 `--all` 可以看到。要放宽时改 `plate.py` 的 `LICENSE_OK`（它是唯一的白名单），并同步 `plans/007-tufte-reader-plates/check_catalog.py`。
- **和图录的关系**：「系列」表里的分类名是脚本 `--cat` 的输入。给表加分类时用 `check_catalog.py` 核对存在，再用本脚本探一下许可分布和宽度，写进「规模与许可」一列。
- **审阅重点**：`search()` 的查询串拼法（`incategory:"…"` 要带引号，分类名下划线换成空格）；`verdict()` 的三条判定顺序；参数错误不访问网络（测试里用 `mock` 断言）。
