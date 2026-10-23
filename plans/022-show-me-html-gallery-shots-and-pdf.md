# Plan 022: show-me-html 的 gallery 截图改走 CDP 运行器，`build.py` 加 `--pdf`

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: 本计划要求计划 021 已合入。先确认：
>
> - `ls skills/show-me-html/scripts/render.mjs skills/show-me-html/scripts/cdp.mjs` 两个文件都在；
> - `grep -c 'def run_jobs' skills/show-me-html/scripts/build.py` → `1`；
> - `git diff --stat be84c43..HEAD -- skills/show-me-html/scripts skills/show-me-html/tests/test_build.py skills/show-me-html/SKILL.md` → 无输出。
>
> 前两条不满足就 STOP。第三条有输出时，对照下面「Current state」里的引文，引文找不到也是 STOP 条件。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。
>
> **派发前复核（advisor，2026-10-23，`be84c43`）**：021 已合入，「Current state」的引文与 HEAD 逐字一致，行号已按 `be84c43` 更新。有审阅者把初版计划原样套到副本上跑了一遍，初版自带的检查全部通过，但它复现出一处交付错误：`--pdf` 打出的 PDF 里，首屏以下的数据图是空白的。原因是 `charts.js` 只在图滚进视口时才画，而初版的测试页面和回归页面都没有数据图。另外几处问题：
>
> - 完成条件里「`chrome_proxy_args` 计数全为 0」做不到，因为 `cdp.mjs` 的注释里提到了它，而 `cdp.mjs` 不在初版的 Scope 里；
> - 没写在哪个检出目录里工作；
> - 回归步骤拿 Letter 纸的 PDF 去比 A4 的页数。
>
> 下面的代码块、测试和验证步骤都已改好。
>
> - 全量单元测试：执行前 `Ran 56 tests`，执行后 `Ran 58 tests`。

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW（gallery 截图只换传输方式，截图参数不变；`--pdf` 是新增参数）
- **Depends on**: `plans/021-show-me-html-cdp-runner.md`（已合入）
- **Category**: perf
- **Planned at**: commit `2f0e439`, 2026-10-22；`be84c43` 复核并修订

## Why this matters

show-me-html 的维护者改了图表运行时或图库之后，要跑 `python3 scripts/gallery.py --shots`。这个脚本把 59 张图拼成一页，先用无头 Chrome 跑一次探针，再给每张图在 light / dark 下各截一张。现在一共冷启动约 119 次 Chrome（4 个线程并行）。计划 021 已经给 `build.py` 做了单实例运行器 `run_jobs()`，背后是 `scripts/render.mjs`。审阅时把本计划 Step 2 的代码套上去实测：

- 118/118 张截图，探针问题 0 条，全程 34.7 秒；旧版 367.6 秒。
- 118 张 PNG 的尺寸与旧版完全一致；像素差异只在抗锯齿，占 0.3–1.4% 的像素。

维护者要求记下的另一个候选是「`build.py` 加 `--pdf`」，在运行器里只是一次 `Page.printToPDF`：

- show-me-html 的打印样式已经定为 A4（`@page { size: A4 }`），要传 `preferCSSPageSize: true` 才会用上它，否则 Chrome 按 Letter 出。
- 打印前要先把所有数据图画出来，否则首屏以下的图在 PDF 里是空白。
- 现在 `SKILL.md` 让用户自己用浏览器打印，本计划给一个一步到位的参数。

## Current state

技能目录是 `skills/show-me-html/`，下文路径都相对这个目录，行号按 `be84c43`。

### `scripts/gallery.py`

- import 区（`:12-22`）有 `import html as htmllib`（`:14`）和 `from concurrent.futures import ThreadPoolExecutor`（`:21`），这两个只在截图部分用到。`subprocess` 还用于 `git_label()` 和 `main()` 里调 `build.py`，要保留。
- `ERR_CAPTURE`（`:157`）和 `PROBE`（`:161`）两个字符串不动。`PROBE` 在 `load` 后等 3000ms，把结果写进 `<pre id="__probe">`。
- `chrome_run(chrome, *args)`（`:213-223`）用 `subprocess.run` 冷启动 Chrome，带 `--force-prefers-reduced-motion`，超时重试一次。
- `shots(page, out, index)`（`:226` 起）的前半段如下，到 `problems = [f"控制台报错：{e}" for e in data["errs"]]` 为止。后半段（拼 `index.md`）不动。

```python
def shots(page, out, index):
    build = runpy.run_path(str(BUILD))
    chrome, proxy = build["find_chrome"](), build["chrome_proxy_args"]()
    if not chrome:
        raise SystemExit("--shots 需要本机 Chrome/Chromium")
    html = page.read_text(encoding="utf-8")
    work = out / "shots"
    work.mkdir(exist_ok=True)
    themed = {}
    for theme in ("light", "dark"):
        themed[theme] = work / f"{theme}.html"
        themed[theme].write_text(html.replace(
            "<head>", f'<head><script>try{{localStorage.setItem("show-me-theme","{theme}")}}catch(e){{}}</script>', 1),
            encoding="utf-8")
    probe = work / "probe.html"
    probe.write_text(html.replace("<head>", "<head>" + ERR_CAPTURE, 1) + PROBE % (json.dumps(SHOT_W), PAD), encoding="utf-8")
    dom = chrome_run(chrome, *proxy, "--virtual-time-budget=8000", "--window-size=1000,900", "--dump-dom",
                     probe.as_uri() + "?only=*").stdout
    m = re.search(r'<pre id="__probe">(.*?)</pre>', dom, re.S)
    if not m:
        raise SystemExit("探针没返回结果（页面 JS 可能报错）：用浏览器打开 all-charts.html 看控制台")
    data = json.loads(htmllib.unescape(m.group(1)))
    figs = {f["id"]: f for f in data["figs"]}

    def shoot(job):
        fid, theme = job
        f = figs[fid]
        png = work / f"{fid}-{theme}.png"
        w = SHOT_W["wide" if f["wide"] else "half"]
        chrome_run(chrome, *proxy, "--force-device-scale-factor=2", "--virtual-time-budget=4000",
                   f"--window-size={w},{f['h'] + 2 * PAD}", f"--screenshot={png}",
                   themed[theme].as_uri() + f"?only={fid}")
        return png if png.exists() else None

    jobs = [(fid, t) for fid in figs for t in ("light", "dark")]
    with ThreadPoolExecutor(max_workers=4) as pool:
        made = dict(zip(jobs, pool.map(shoot, jobs)))

    problems = [f"控制台报错：{e}" for e in data["errs"]]
```

- 后半段用到的是 `figs`、`made[(fid, t)]`（值为 `None` 表示截图失败）、`jobs`、`themed`、`probe`。

### `scripts/build.py`

- `run_jobs(jobs)` 在一个 Chrome 里依次跑任务，返回 `(结果列表, 错误)`。没有 Chrome、node，或 node 早于 22 时返回 `(None, None)`。任务字段写在 `scripts/render.mjs` 文件头。
- `def chrome_proxy_args(env=None):`（`:1091`）是 020 加的，现在只剩 `gallery.py:228` 在调用。运行器里的代理由 `cdp.mjs` 的 `proxyArgs()` 处理，读的是同一组环境变量。
- `def shoot_sheets(page, theme="light", scale=2):` 在 `:989`。
- `main()` 里 `"--shot",` 参数在 `:1239`。
- `main()` 里 `    if args.shot:` 在 `:1318`，后面是 `    if args.open:  # 走到这里自检已通过：…`（`:1326`）。
- 文件开头文档字符串的用法有三行：

```text
    python3 build.py page.html                # 内联资产 + 自检
    python3 build.py page.html --check-only   # 只跑自检，不改文件
    python3 build.py page.html --open         # 自检通过后用系统默认浏览器打开
```

### `scripts/render.mjs`（021 新建）

- 文件头的任务字段说明里，`//   shot     路径：截当前视口` 之后是 `//   timeout  …`。结果说明是 `// stdout：与任务一一对应的 JSON 数组，每项 {value, slices: [{path, top, height}], shot, errors: [页面 JS 异常], error: "哪一步失败"}，`。
- `run(job)` 里 `ev` 的定义以 `    return r.result.value;` 和 `  };` 结束，下一行是 `  let step = "打开页面";`。
- `slices` 分支开头（`:125-131`）：

```js
    if (job.slices) {
      step = "切片截图";
      // 数据图滚入视口才画（charts.js 的 reveal），视口固定 900px 时首屏以外的图还没画
      await ev(
        "document.querySelectorAll('figure[data-chart] svg').forEach(function(s){ if (s._replay) s._replay(); }), 1"
      );
      await new Promise((r) => setTimeout(r, 300));
      const total = await ev("document.documentElement.scrollHeight");
```

- `shot` 分支（`:146-151`）是 `try` 里的最后一段，后面紧跟 `  } catch (e) {`。

### `scripts/cdp.mjs`

`:7` 是 `// 无头 Chrome 不读 HTTP(S)_PROXY 环境变量：配了代理就显式传，否则每次直连 Google Fonts。规则同 build.py 的 chrome_proxy_args`。

### `assets/charts.js`

数据图由 `reveal()` 在露出 20% 时才画，画之前 SVG 里只有 `<title>`/`<desc>`。每张图的 `svg._replay()` 能强制画出。reduced motion 下画的是末帧，不开 reduced motion 时，打印那一刻可能还是动画第一帧。

### `tests/test_build.py`

- 顶部 import 有 `hashlib, re, runpy, shutil, subprocess, sys, tempfile, time, unittest`，没有 `json`。
- `RENDERER = bool(FIND_CHROME() and shutil.which("node"))`。渲染测试的装饰器是 `@unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")`，现有 10 个。
- `test_chrome_proxy_args_follow_proxy_env`（`:397-407`）测 Python 版 `chrome_proxy_args`，没有装饰器。
- `test_render_check_flags_chart_text_below_font_floor`（`:410` 起）在首屏以外放一张图：先放一个 3000px 的空 `div`，再用 `showMeChart.reveal` + `showMeChart.txt` 画字。本计划的 PDF 测试照它的写法构造页面。
- `test_snap_narrows_to_one_theme_and_width`（`:285`）之后是 `test_render_check_warns_on_phone_overflow_only`。

### 其他

- `SKILL.md:78`：`成品页自带打印样式，用户要 PDF 时用浏览器打印它。`
- 关于 PDF 尺寸：Chrome 打出的 A4 PDF，`/MediaBox` 是 `[0 0 594.95996 841.91998]`；Letter 是 `[0 0 612 792]`。冻结场景探针 `probe_round.mjs` 打的 `_probe/*.pdf` 都是 Letter，因为它调 `printToPDF {}` 时没传 `preferCSSPageSize`，所以不能拿它们的页数和 A4 比。
- 本机装了 poppler（`pdftotext`、`pdftoppm`）。

## Commands you will need

以下命令都在你的 worktree 根目录运行。

| Purpose  | Command                                                                                                   | Expected on success |
| -------- | --------------------------------------------------------------------------------------------------------- | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`                                                | 末行 `OK`           |
| 语法检查 | `python3 -m py_compile skills/show-me-html/scripts/build.py skills/show-me-html/scripts/gallery.py`       | 无输出              |
| JS 语法  | `node --check skills/show-me-html/scripts/render.mjs && node --check skills/show-me-html/scripts/cdp.mjs` | 无输出              |
| 文档门禁 | `make check`                                                                                              | exit 0              |

测试不要用 pytest。

## Scope

**In scope**：

- `skills/show-me-html/scripts/gallery.py`
- `skills/show-me-html/scripts/render.mjs`
- `skills/show-me-html/scripts/build.py`
- `skills/show-me-html/scripts/cdp.mjs`（只改 `:7` 注释的后半句）
- `skills/show-me-html/tests/test_build.py`
- `skills/show-me-html/SKILL.md`（一行）
- `plans/README.md`（状态行）

**Out of scope**：

- gallery 的 `PROBE`、`ERR_CAPTURE`、`index.md` 的格式、截图尺寸与像素比：本计划只换传输方式。
- `--pdf` 的纸张、页边距、背景：由 `show-me.css` 的打印样式决定，本计划不加参数。`printBackground` 保持默认关，和浏览器打印的默认一致。
- 打印样式本身的问题（卡片跨页、看板列被裁、最小页面多出一张空白页）：那是计划 027。
- `probe_round.mjs` 打 Letter 纸 PDF：另记，本计划不改。
- `PROJECT_MEMORY.md`：由审阅者回写。

## Git workflow

- 你在派发时建好的独立 git worktree 里工作，分支已经建好，直接在上面提交。没有 worktree 时才 `git checkout -b advisor/022-show-me-html-gallery-shots-and-pdf main`。
- 主检出目录 `/Users/mg/github/skills` 停在 `main`，也就是改前版本，Step 2 的 STOP 兜底拿它做对照。不要在那里改文件、切分支或提交。那里已有的 `PROJECT_MEMORY.md`、`docs/research/…` 改动与本计划无关。
- 建议两个提交：`perf(show-me-html): gallery shots run in one headless Chrome`、`feat(show-me-html): build.py --pdf prints an A4 copy beside the page`。
- pre-commit 的 lint-staged 会用 prettier 重排提交里的 `.mjs` 和 Markdown，这是预期。提交后重跑 JS 语法检查。fresh worktree 没有 `node_modules`，钩子因此失败时在 worktree 里 `npm install` 一次再提交（之后 `git checkout package-lock.json`，它不进提交），不要用 `--no-verify`。
- 不要 push。

## Steps

### Step 1: 运行器支持 `pdf`，打印前先把数据图画全

1. `scripts/render.mjs` 文件头：
   - 在 `//   shot     路径：截当前视口` 那一行之后加一行：

     <!-- prettier-ignore -->
     ```js
     //   pdf      路径：先把数据图全部画出来，再按页面的 @page 尺寸打印成 PDF（show-me.css 定为 A4），无页眉页脚、不打背景
     ```

   - 结果说明那行 `每项 {value, slices: [{path, top, height}], shot, errors: …}` 里，在 `shot` 之后加 `, pdf`，变成 `每项 {value, slices: [{path, top, height}], shot, pdf, errors: [页面 JS 异常], error: "哪一步失败"}`。

2. 在 `run(job)` 里 `ev` 定义结束的 `  };` 之后、`  let step = "打开页面";` 之前，加：

   <!-- prettier-ignore -->
   ```js
     // 数据图滚入视口才画（charts.js 的 reveal）：截切片、打印前先把首屏以外的图也画出来
     const drawAll = async () => {
       await ev("document.querySelectorAll('figure[data-chart] svg').forEach(function(s){ if (s._replay) s._replay(); }), 1");
       await new Promise((r) => setTimeout(r, 300));
     };
   ```

3. `slices` 分支里，`step = "切片截图";` 下面那四句（注释 `// 数据图滚入视口才画…`、`await ev(` 到 `);` 的三行、`await new Promise((r) => setTimeout(r, 300));`），也就是「Current state」引文里 `step = "切片截图";` 和 `const total = …` 之间的部分，换成一行：

   <!-- prettier-ignore -->
   ```js
         await drawAll();
   ```

4. 在 `shot` 分支结束的 `    }` 之后、`  } catch (e) {` 之前加：

   <!-- prettier-ignore -->
   ```js
       if (job.pdf) {
         step = "打印 PDF";
         await drawAll();
         // 不传 preferCSSPageSize 时 Chrome 按 Letter 出，show-me.css 的 @page { size: A4 } 不生效
         const { data } = await S("Page.printToPDF", { preferCSSPageSize: true });
         writeFileSync(job.pdf, Buffer.from(data, "base64"));
         out.pdf = job.pdf;
       }
   ```

**Verify**:

- `node --check skills/show-me-html/scripts/render.mjs` 无输出。
- `grep -c '_replay' skills/show-me-html/scripts/render.mjs` → `1`（只剩 `drawAll` 里那一处）。
- `grep -c 'await drawAll()' skills/show-me-html/scripts/render.mjs` → `2`。
- 全量单元测试 → `OK`，`Ran 56 tests`。快照测试仍然通过，说明 `slices` 行为没变。

### Step 2: `gallery.py` 的截图改走运行器

1. 删掉 `chrome_run()` 整个函数（`:213-223`，连同它下面的两个空行）。
2. `shots()` 里，从 `def shots(page, out, index):` 到 `problems = [f"控制台报错：{e}" for e in data["errs"]]` **之前**的代码，整段替换为下面这段。`problems = …` 及之后的代码不动。

   ```python
   def shots(page, out, index):
       run_jobs = runpy.run_path(str(BUILD))["run_jobs"]
       html = page.read_text(encoding="utf-8")
       work = out / "shots"
       work.mkdir(exist_ok=True)
       themed = {}
       for theme in ("light", "dark"):
           themed[theme] = work / f"{theme}.html"
           themed[theme].write_text(html.replace(
               "<head>", f'<head><script>try{{localStorage.setItem("show-me-theme","{theme}")}}catch(e){{}}</script>', 1),
               encoding="utf-8")
       probe = work / "probe.html"
       probe.write_text(html.replace("<head>", "<head>" + ERR_CAPTURE, 1) + PROBE % (json.dumps(SHOT_W), PAD), encoding="utf-8")
       # 一个 Chrome 实例先跑探针、再依次截全部图（build.py 的 run_jobs → scripts/render.mjs）
       res, err = run_jobs([{"url": probe.as_uri() + "?only=*", "width": 1000, "reduced": True, "budget": 8000,
                             "eval": "(document.getElementById('__probe') || {}).textContent || ''"}])
       if res is None:
           raise SystemExit(f"--shots 跑不起来：{err}" if err else "--shots 需要本机 Chrome/Chromium 和 Node 22+")
       if not res[0].get("value"):
           why = res[0].get("error") or "；".join(res[0]["errors"][:2]) or "页面没写回结果"
           raise SystemExit(f"探针没返回结果（{why}）：用浏览器打开 all-charts.html 看控制台")
       data = json.loads(res[0]["value"])
       figs = {f["id"]: f for f in data["figs"]}

       jobs = [(fid, t) for fid in figs for t in ("light", "dark")]
       specs = [{"url": themed[t].as_uri() + f"?only={fid}", "width": SHOT_W["wide" if figs[fid]["wide"] else "half"],
                 "height": figs[fid]["h"] + 2 * PAD, "dpr": 2, "mobile": False, "reduced": True,
                 "shot": str(work / f"{fid}-{t}.png")} for fid, t in jobs]
       res, err = run_jobs(specs)
       if res is None:
           raise SystemExit(f"--shots 截图跑不起来：{err}" if err else "--shots 需要本机 Chrome/Chromium 和 Node 22+")
       made = {job: (Path(s["shot"]) if not r.get("error") else None) for job, s, r in zip(jobs, specs, res)}

   ```

   说明：
   - `textContent` 直接拿到原文，不再需要 `htmllib.unescape`。
   - 截图参数与原来一致：reduced motion、两倍像素、通栏 1000 / 半宽 500 宽、高度为探针量到的图高加两倍 `PAD`、虚拟时间 4000ms（运行器默认值）。

3. 删掉文件顶部不再用到的 `import html as htmllib` 和 `from concurrent.futures import ThreadPoolExecutor`。

**Verify**:

- 语法检查无输出。
- `grep -c 'chrome_run\|ThreadPoolExecutor\|htmllib\|--headless\|chrome_proxy_args' skills/show-me-html/scripts/gallery.py` → `0`。
- 完整跑一次（约 35 秒）：

  ```sh
  G=$(mktemp -d); echo "G=$G"
  /usr/bin/time -p python3 skills/show-me-html/scripts/gallery.py --shots --out "$G" 2>&1 | grep -E '超过 400 KB|自检通过|截图|问题|^real'
  ls "$G/shots"/*.png | wc -l
  ```

  预期：
  - 一行 `超过 400 KB` 的 WARN 和 `自检通过（1 个警告需逐条判断）。`；
  - `截图    118/118 张 → …`、`问题    0 条`、`real` 秒数；
  - `wc -l` 为 `118`。

  把 `real` 秒数写进汇报。参考值：审阅时实测 34.7 秒，旧版 367.6 秒。

- 打开 `"$G/shots/F3-light.png"`、`"$G/shots/G16-dark.png"`（`$G` 用上面 `echo` 出来的路径）看一眼：图完整，是末帧，深色主题正确。
- 如果 `问题` 不是 0 条：用主检出目录的旧版跑一次做对照，约 6 分钟。

  ```sh
  GO=$(mktemp -d); python3 /Users/mg/github/skills/skills/show-me-html/scripts/gallery.py --shots --out "$GO" | grep -E '截图|问题'
  diff <(sed -n '/## 探针发现的问题/,/^## /p' "$GO/shots/index.md") <(sed -n '/## 探针发现的问题/,/^## /p' "$G/shots/index.md")
  ```

  两边的问题列表相同就继续，不同就 STOP。

### Step 3: 删掉 Python 版代理参数，测试改测 `cdp.mjs`

1. `grep -rn chrome_proxy_args skills/show-me-html/scripts skills/show-me-html/tests`，预期只剩四处：
   - `build.py` 里的定义；
   - `cdp.mjs:7` 的注释；
   - `tests/test_build.py` 里的旧测试两行。

   除此之外还有别处，就 STOP。然后删掉 `build.py` 里的 `chrome_proxy_args()` 整个函数（从 `def chrome_proxy_args(env=None):` 到它的 `return args`，连同后面多出的空行，保持函数之间两个空行）。

2. `scripts/cdp.mjs:7` 注释末尾的 `规则同 build.py 的 chrome_proxy_args` 改为 `测试见 tests/test_build.py 的 test_cdp_proxy_args_follow_proxy_env`。
3. `tests/test_build.py`：
   - 文件顶部 import 区按字母序加 `import json`，放在 `import hashlib` 之后。
   - 把 `test_chrome_proxy_args_follow_proxy_env` 整个替换为下面的测试：同样的五组虚构值，改测 JS 版。

   ```python
       @unittest.skipUnless(shutil.which("node"), "需要 node")
       def test_cdp_proxy_args_follow_proxy_env(self):
           """Chrome 不读代理环境变量：有代理时传 --proxy-server，HTTPS 优先，NO_PROXY 转绕行列表，NO_PROXY=* 不走代理。"""
           cases = [{}, {"https_proxy": "http://127.0.0.1:7890/"},
                    {"HTTP_PROXY": "http://a.test:1", "HTTPS_PROXY": "http://b.test:2"},
                    {"ALL_PROXY": "socks5://127.0.0.1:7891", "NO_PROXY": "localhost, .corp.test"},
                    {"HTTPS_PROXY": "http://b.test:2", "no_proxy": "*"}]
           script = ("import(process.argv[1]).then(m => console.log(JSON.stringify("
                     "JSON.parse(process.argv[2]).map(e => m.proxyArgs(e)))))")
           out = subprocess.run(["node", "-e", script, (SKILL / "scripts" / "cdp.mjs").as_uri(), json.dumps(cases)],
                                capture_output=True, text=True, check=True).stdout
           self.assertEqual(json.loads(out), [
               [], ["--proxy-server=http://127.0.0.1:7890"], ["--proxy-server=http://b.test:2"],
               ["--proxy-server=socks5://127.0.0.1:7891", "--proxy-bypass-list=localhost;*.corp.test"], []])
   ```

**Verify**:

- `grep -rc 'chrome_proxy_args' skills/show-me-html/scripts skills/show-me-html/tests` → 每个文件都是 `0`。
- `node --check skills/show-me-html/scripts/cdp.mjs` 无输出。
- `python3 -m unittest skills.show-me-html.tests.test_build -k proxy` → `Ran 1 test`、`OK`。

### Step 4: `build.py --pdf`

1. `scripts/build.py`，在 `def shoot_sheets(` 之前加：

   ```python
   def print_pdf(page):
       """按页面的打印样式出 PDF（show-me.css 定为 A4），放在页面旁边、同名 .pdf。返回 (路径, 错误信息)。
       数据图先全部画出、reduced motion 下画末帧，再打印（render.mjs 的 pdf 任务）。"""
       out = page.with_suffix(".pdf")
       results, err = run_jobs([{"url": page.resolve().as_uri(), "reduced": True, "pdf": str(out)}])
       if results is None:
           return None, err or "找不到 Chrome/Chromium 或 Node 22+"
       if results[0].get("error"):
           return None, results[0]["error"]
       return out, None


   ```

2. `main()` 里，`--shot` 参数那个 `ap.add_argument(…)` 调用结束之后，加：

   ```python
       ap.add_argument("--pdf", action="store_true",
                       help="自检通过后按打印样式出一份 A4 PDF，放在页面旁边（同名 .pdf）")
   ```

   在 `    if args.shot:` 那一段之后、`    if args.open:` 之前加：

   ```python
       if args.pdf:
           out, err = print_pdf(args.page)
           print(f"已导出  {out}" if out else f"--pdf 未完成：{err}")

   ```

3. 文件开头文档字符串的用法里，`python3 build.py page.html --open` 那行之后加一行：

   ```text
       python3 build.py page.html --pdf          # 自检通过后出一份 A4 PDF
   ```

   注释的 `#` 与上面三行对齐。

4. 测试：在 `test_snap_narrows_to_one_theme_and_width` 之后（`test_render_check_warns_on_phone_overflow_only` 之前）加两个测试：

   ```python
       @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
       def test_pdf_prints_a4_beside_the_page(self):
           page = self.copy_fixture()
           result = run_build(page, "--pdf")
           self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
           self.assertIn("已导出", result.stdout)
           pdf = page.with_suffix(".pdf").read_bytes()
           self.assertTrue(pdf.startswith(b"%PDF"))
           box = re.search(rb"/MediaBox \[([^\]]*)\]", pdf)
           self.assertIsNotNone(box)
           self.assertRegex(box.group(1).decode(), r"^0 0 59[45]\.\d+ 84[12]\.\d+$")  # A4，不是 Letter 的 612 x 792

       @unittest.skipUnless(RENDERER and shutil.which("pdftotext"), "需要本机 Chrome/Chromium、node 和 pdftotext")
       def test_pdf_draws_charts_below_the_fold(self):
           """数据图滚入视口才画：--pdf 打印前要把首屏以外的图也画出来，不然 PDF 里是空框。"""
           def chart(cid, below):
               return ('<section>' + ('<div style="height: 3000px"></div>' if below else '')
                       + '<figure class="fig" data-chart="F1"><div class="fig-box">'
                       f'<svg id="{cid}" viewBox="0 0 400 320" role="img" aria-labelledby="{cid}-t {cid}-d">'
                       f'<title id="{cid}-t">t</title><desc id="{cid}-d">d</desc></svg></div></figure></section>')
           script = ('<script>["top", "fold"].forEach(function (id) { showMeChart.reveal(document.getElementById(id), (s) =>'
                     ' showMeChart.txt(s, { x: 20, y: 40, "font-size": 14 }, id === "top" ? "TOPLABEL" : "FOLDLABEL")); });</script>')
           page = self.copy_fixture()
           html = page.read_text(encoding="utf-8")
           html = html.replace("</main>", chart("top", False) + chart("fold", True) + "</main>").replace(
               "<!--SHOW-ME:JS-->", "<!--SHOW-ME:JS-->" + script)
           page.write_text(html, encoding="utf-8")
           result = run_build(page, "--pdf")
           self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
           text = subprocess.run(["pdftotext", str(page.with_suffix(".pdf")), "-"],
                                 capture_output=True, text=True, check=True).stdout
           self.assertIn("TOPLABEL", text)
           self.assertIn("FOLDLABEL", text)
   ```

**Verify**:

- 语法检查无输出。
- `python3 skills/show-me-html/scripts/build.py --help | grep -q -- '--pdf' && echo ok` → `ok`。
- `grep -c 'skipUnless(RENDERER' skills/show-me-html/tests/test_build.py` → `12`。
- 全量单元测试 → `OK`，`Ran 58 tests`，没有 skipped。
- 反证：临时删掉 `render.mjs` 的 `pdf` 分支里那行 `await drawAll();`，单跑 `python3 -m unittest skills.show-me-html.tests.test_build.BuildCliTests.test_pdf_draws_charts_below_the_fold`，应当失败（`FOLDLABEL` 找不到）。确认后改回去，再单跑一次，应当通过。

### Step 5: 文档

`SKILL.md:78` 的 `成品页自带打印样式，用户要 PDF 时用浏览器打印它。` 改为：

<!-- prettier-ignore -->
```markdown
成品页自带打印样式；用户要 PDF 时最后一次构建加 `--pdf`，页面旁边出一份同名 A4 PDF。
```

然后 `npx prettier --write skills/show-me-html/SKILL.md`。

**Verify**:

- `make check` → exit 0。
- `grep -c -- '--pdf' skills/show-me-html/SKILL.md` → `1`。

### Step 6: 回归

以下每段都在 worktree 根目录、各自的新 shell 里运行，变量在段内定义。

1. **冻结场景页出 PDF**：

   ```sh
   R=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-47a158d-021
   P=$(mktemp -d); echo "P=$P"; cp "$R/approach-compare.html" "$P/a.html"
   python3 skills/show-me-html/scripts/build.py "$P/a.html" --pdf | grep -E '已导出|未完成'
   python3 -c "import re,sys; d=open(sys.argv[1],'rb').read(); print(len(re.findall(rb'/Type\s*/Page[^s]', d)), set(re.findall(rb'/MediaBox \[[^]]*\]', d)))" "$P/a.pdf"
   ```

   **Verify**：打印 `已导出  …/a.pdf`；第二条命令打印页数和 `{b'/MediaBox [0 0 594.95996 841.91998]'}`。页数原样写进汇报，审阅时实测 2 页。不要拿 `$R/_probe/approach-compare.pdf` 比页数，那份是 Letter 纸。

2. **带数据图的长页面出 PDF**：

   ```sh
   G=$(mktemp -d); echo "G=$G"
   python3 skills/show-me-html/scripts/gallery.py --out "$G" > /dev/null
   python3 skills/show-me-html/scripts/build.py "$G/all-charts.html" --pdf | grep -E '已导出|未完成'
   pdftoppm -r 40 -f 4 -l 6 -png "$G/all-charts.pdf" "$G/p"; ls "$G"/p-*.png
   ```

   **Verify**：
   - 打印 `已导出`。
   - 打开三张 `p-*.png`（第 4–6 页，都在首屏以外）：数据图都已画出，有坐标轴、柱、线、点或扇区，不是只有标题和图注的空框；柱和线是画完的末帧，不是动画第一帧（比如柱全在底线上、线只画了一小段）。

3. **冻结场景轮次**：本计划改了 `build.py`，按 `MAINTENANCE.md` 要跑一轮。页面生成指引没变，所以复制上一轮的五页重建：

   ```sh
   PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-47a158d-021
   RND=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-022
   mkdir -p "$RND"
   for n in status-report approach-compare code-review concept-explainer triage-board; do
     cp "$PREV/$n.html" "$RND/" && python3 skills/show-me-html/scripts/build.py "$RND/$n.html" | grep -E '^(ERROR|WARN)|自检通过'
   done
   node skills/show-me-html/scripts/probe_round.mjs "$RND" "$PREV" | grep -E '^[a-z-]+: |probe\.json|截图：|Markdown 不同'
   ```

   **Verify**：
   - 五次构建都打印 `自检通过。`；五行 `<场景名>: 无问题`；`与上一轮对比：probe.json 相同`。
   - 截图应为 `30/30 张逐字节相同`。有不同就逐张打开看：只是抗锯齿噪声的，在汇报里列出文件名；版式或颜色有变化的，按 STOP 处理。
   - `scenarios/rounds/` 在 `.gitignore` 里，轮次目录不进提交。

## Test plan

- 替换：`test_chrome_proxy_args_follow_proxy_env` 换成 `test_cdp_proxy_args_follow_proxy_env`，同样五组输入，测 `cdp.mjs` 的 `proxyArgs()`。
- 新增：
  - `test_pdf_prints_a4_beside_the_page`：MediaBox 是 A4。
  - `test_pdf_draws_charts_below_the_fold`：首屏以下的图在 PDF 里有字。按 `test_render_check_flags_chart_text_below_font_floor` 的写法构造页面，要求做一次反证。
- 不改但必须通过：021 的快照测试。`slices` 分支改用 `drawAll()` 后行为不变。
- gallery 截图没有单元测试覆盖，靠 Step 2 的完整运行。PDF 里的图是不是末帧，靠 Step 6 第 2 小步人眼看。

## Done criteria

- [ ] 全量单元测试 `OK`，`Ran 58 tests`，没有 skipped（本机有 Chrome、node、pdftotext）
- [ ] Step 4 的反证做过：去掉 `pdf` 分支的 `drawAll()` 时 `test_pdf_draws_charts_below_the_fold` 失败，改回后通过
- [ ] `grep -c 'chrome_run\|ThreadPoolExecutor\|htmllib\|--headless' skills/show-me-html/scripts/gallery.py` → `0`
- [ ] `grep -rc 'chrome_proxy_args' skills/show-me-html/scripts skills/show-me-html/tests` 全是 `0`
- [ ] `gallery.py --shots` 截图 `118/118`，`问题    0 条`；汇报里写了 `real` 秒数
- [ ] Step 6：approach-compare 的 PDF 是 A4（页数写进汇报）；gallery PDF 第 4–6 页的图已画出、是末帧；轮次五页 `无问题`、`probe.json 相同`
- [ ] `make check` exit 0；在你的 worktree 里 `git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新（审阅者说明由他维护时跳过）

## STOP conditions

- 021 未合入（drift check），或「Current state」的引文找不到。
- `gallery.py --shots` 的截图张数少于 118，或者问题条数不是 0，且与旧版对照的问题列表不同。
- `--pdf` 出的 PDF 是 Letter（612 × 792）：说明 `preferCSSPageSize` 没生效，或者打印样式里的 `@page` 被改了。
- gallery PDF 首屏以外的数据图是空框，或停在动画第一帧。
- `chrome_proxy_args` 除了 Step 3 第 1 小步列出的四处之外还有别的出现。
- 你发现需要改 `show-me.css`、`charts.js` 或 `probe_round.mjs` 才能让本计划的测试通过。

## Maintenance notes

- 运行器的任务字段说明（`render.mjs` 文件头）新增 `pdf`，计划 025 的单页交互探针也会读这份说明。`drawAll()` 是切片和 PDF 共用的「先把数据图画全」，以后新增要截全页的任务也该先调它。
- 图库截图现在在一个 Chrome 里顺序执行，不重试。Chrome 崩一次，整批截图都会失败：`--shots` 会直接退出并打印运行器的错误，或者某张图记成「截图失败」。以后图型数量翻倍、耗时明显变长时，可以让 `render.mjs` 同时开几个页面并行。但要先确认 `Emulation.setVirtualTimePolicy` 在多个页面同时跑时互不影响。
- `chrome_run` 文档字符串里「别加 --user-data-dir」的说法随函数一起删掉。运行器在一个实例里跑完全部任务，字体只在第一页拉一次；等待由虚拟时间加真实超时保证。
- `gallery.py --shots` 现在需要 Node 22+，和 `build.py` 的渲染检查一样。
- `--pdf` 只在自检通过后执行，与 `--shot`、`--snap` 一样。PDF 不打 CSS 背景（`printBackground` 默认关），这和浏览器打印对话框的默认设置一致；`show-me.css` 里没有 `print-color-adjust`。以后想让提示框底色、徽章进 PDF，在打印样式里加 `print-color-adjust: exact`，不要改运行器。
- 最小夹具 `--pdf` 打出 2 页，第 2 页空白，可能与 `body { min-height: 100vh }` 有关，原因没有确认。这是打印样式的事，归计划 027。
