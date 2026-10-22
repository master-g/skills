# Plan 022: show-me-html 的 gallery 截图改走 CDP 运行器，`build.py` 加 `--pdf`

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: 本计划要求计划 021 已合入。先确认：`ls skills/show-me-html/scripts/render.mjs skills/show-me-html/scripts/cdp.mjs` 两个文件都在，`grep -c 'def run_jobs' skills/show-me-html/scripts/build.py` → `1`。不满足就 STOP。
> 然后 `git diff --stat 2f0e439..HEAD -- skills/show-me-html/scripts/gallery.py`：020 给 `shots()` 加了 `proxy`，属于预期；别的改动对照下面「Current state」。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW（gallery 截图换传输方式，截图参数不变；`--pdf` 是新增参数）
- **Depends on**: `plans/021-show-me-html-cdp-runner.md`
- **Category**: perf
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 维护者改图表运行时或图库后要跑 `python3 scripts/gallery.py --shots`：它把 59 张图拼成一页，先用无头 Chrome 跑一次探针，再给每张图在 light / dark 下各截一张，现在是约 119 次冷启动 Chrome（4 个线程并行）。计划 021 已经给 `build.py` 做了单实例运行器 `run_jobs()`（背后是 `scripts/render.mjs`）。advisor 在 scratchpad 里把本计划 Step 2 的代码套上去实测：118/118 张截图、探针问题 0 条，全程 53 秒。

维护者还要求记下的候选「`build.py` 加 `--pdf`」在运行器里只是一次 `Page.printToPDF`。show-me-html 的打印样式已经定了 A4（`@page { size: A4 }`），传 `preferCSSPageSize: true` 才会用上它，否则 Chrome 按 Letter 出。现在 `SKILL.md` 让用户自己用浏览器打印，本计划给一个一步到位的参数。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。

- `scripts/gallery.py` 的截图部分（`2f0e439` 的 `:155-260`；020 改过 `shots()` 开头）：`ERR_CAPTURE` 和 `PROBE` 两个字符串不动；`chrome_run()` 用 `subprocess.run` 冷启动 Chrome（`--force-prefers-reduced-motion`，超时重试一次）；`shots()` 先写 `light.html` / `dark.html` / `probe.html` 三个文件，然后：

  ```python
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

  `shots()` 开头（020 之后）：

  ```python
      build = runpy.run_path(str(BUILD))
      chrome, proxy = build["find_chrome"](), build["chrome_proxy_args"]()
      if not chrome:
          raise SystemExit("--shots 需要本机 Chrome/Chromium")
  ```

  `htmllib`（`import html as htmllib`）和 `ThreadPoolExecutor` 只在这里用到；`subprocess` 还用于 `git_label()` 和 `main()` 里调 `build.py`。

- `scripts/build.py`（021 之后）：`run_jobs(jobs)` 在一个 Chrome 里依次跑任务，返回 `(结果列表, 错误)`，没有 Chrome 或 node 时返回 `(None, None)`。任务字段写在 `scripts/render.mjs` 文件头。`chrome_proxy_args()` 是 020 加的，021 之后只剩 `gallery.py` 在用；代理在运行器里由 `cdp.mjs` 的 `proxyArgs()` 处理（读同一组环境变量）。

- `scripts/render.mjs`（021 新建）的任务处理里，`if (job.shot) { … }` 是最后一段，之后是 `} catch (e) {`。

- `tests/test_build.py` 里 020 加的 `test_chrome_proxy_args_follow_proxy_env` 测的是 Python 版 `chrome_proxy_args`。文件顶部 import 了 `shutil`、`subprocess`，没有 `json`。021 之后渲染测试的装饰器是 `@unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")`。

- `SKILL.md`「使用边界与维护」第一行：`成品页自带打印样式，用户要 PDF 时用浏览器打印它。`

- Chrome 打出的 A4 PDF，`/MediaBox` 是 `[0 0 594.95996 841.91998]`（advisor 实测）；Letter 是 612 × 792。

## Commands you will need

| Purpose  | Command                                                                                             | Expected on success |
| -------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`                                          | 末行 `OK`           |
| 语法检查 | `python3 -m py_compile skills/show-me-html/scripts/build.py skills/show-me-html/scripts/gallery.py` | 无输出              |
| JS 语法  | `node --check skills/show-me-html/scripts/render.mjs`                                               | 无输出              |
| 图库截图 | `python3 skills/show-me-html/scripts/gallery.py --shots --out "$G"`                                 | 末行 `问题    0 条` |
| 文档门禁 | `make check`                                                                                        | exit 0              |

## Scope

**In scope**：`skills/show-me-html/scripts/gallery.py`、`scripts/render.mjs`、`scripts/build.py`、`tests/test_build.py`、`SKILL.md`（一行）、`plans/README.md`（状态行）。

**Out of scope**：

- gallery 的 `PROBE`、`ERR_CAPTURE`、`index.md` 的格式、截图尺寸与像素比：只换传输方式。
- `--pdf` 的纸张、页边距：由 `show-me.css` 的打印样式决定，本计划不加参数。
- 打印样式本身的问题（卡片跨页、看板列被裁）：那是计划 027。

## Git workflow

- 从本地 `main` 开分支 `advisor/022-show-me-html-gallery-shots-and-pdf`。
- 建议两个提交：`perf(show-me-html): gallery shots run in one headless Chrome`、`feat(show-me-html): build.py --pdf prints an A4 copy beside the page`。不要 push。

## Steps

### Step 1: 运行器支持 `pdf`

1. `scripts/render.mjs` 文件头的任务字段说明里，`shot` 那一行之后加一行：

   ```js
   //   pdf      路径：按页面的 @page 尺寸打印成 PDF（show-me.css 定为 A4），无页眉页脚
   ```

   结果说明那行 `每项 {value, slices: [{path, top, height}], shot, errors: …}` 里，`shot` 之后加 `, pdf`。

2. 在 `if (job.shot) { … }` 这一段之后（`} catch (e) {` 之前）加：

   <!-- prettier-ignore -->
   ```js
       if (job.pdf) {
         step = "打印 PDF";
         // 不传 preferCSSPageSize 时 Chrome 按 Letter 出，show-me.css 的 @page { size: A4 } 不生效
         const { data } = await S("Page.printToPDF", { preferCSSPageSize: true });
         writeFileSync(job.pdf, Buffer.from(data, "base64"));
         out.pdf = job.pdf;
       }
   ```

**Verify**: `node --check skills/show-me-html/scripts/render.mjs` 无输出。

### Step 2: `gallery.py` 的截图改走运行器

1. 删掉 `chrome_run()` 整个函数。
2. `shots()` 里，从函数开头到 `problems = [f"控制台报错：{e}" for e in data["errs"]]` **之前**的代码，替换为下面这段（`problems = …` 及之后的代码不动）：

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
           raise SystemExit(f"--shots 跑不起来：{err}" if err else "--shots 需要本机 Chrome/Chromium 和 node")
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
       made = {job: (Path(s["shot"]) if r and not r.get("error") else None)
               for job, s, r in zip(jobs, specs, res or [None] * len(jobs))}

   ```

   （`textContent` 直接拿到原文，不再需要 `htmllib.unescape`。截图参数与原来一致：reduced motion、两倍像素、通栏 1000 / 半宽 500 宽、高度为探针量到的图高加两倍 `PAD`、虚拟时间 4000ms。）

3. 删掉文件顶部不再用到的 `import html as htmllib` 和 `from concurrent.futures import ThreadPoolExecutor`。

**Verify**: 语法检查无输出；`grep -c 'chrome_run\|ThreadPoolExecutor\|htmllib\|--headless' skills/show-me-html/scripts/gallery.py` → `0`；

```sh
G=$(mktemp -d)
/usr/bin/time -p python3 skills/show-me-html/scripts/gallery.py --shots --out "$G" 2>&1 | tail -6
```

→ 截图行 `118/118 张`、末行 `问题    0 条`（018 合入后图库零问题；若不为 0，和合入前主检出目录的 `gallery.py --shots` 输出对比，相同就继续，不同就 STOP）；`real` 秒数写进汇报（advisor 实测 53 秒）。打开 `"$G/shots/F3-light.png"`、`"$G/shots/G16-dark.png"` 看一眼：图完整、是末帧、深色主题正确。

### Step 3: 删掉 Python 版代理参数，测试改测 `cdp.mjs`

1. `scripts/build.py`：`grep -rn chrome_proxy_args skills/show-me-html/scripts` 确认除了定义之外没有调用方，然后删掉 `chrome_proxy_args()` 函数。
2. `tests/test_build.py`：文件顶部 import 区按字母序加 `import json`；把 `test_chrome_proxy_args_follow_proxy_env` 整个替换为（同样的五组虚构值，改测 JS 版）：

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

**Verify**: `grep -c 'chrome_proxy_args' skills/show-me-html/scripts/build.py skills/show-me-html/scripts/gallery.py` → 两个文件都是 `0`；`python3 -m unittest skills.show-me-html.tests.test_build -k proxy` → `Ran 1 test`、`OK`。

### Step 4: `build.py --pdf`

1. `scripts/build.py`，在 `shoot_sheets()` 之前加：

   ```python
   def print_pdf(page):
       """按页面的打印样式出 PDF（show-me.css 定为 A4），放在页面旁边、同名 .pdf。返回 (路径, 错误信息)。"""
       out = page.with_suffix(".pdf")
       results, err = run_jobs([{"url": page.resolve().as_uri(), "pdf": str(out)}])
       if results is None:
           return None, err or "找不到 Chrome/Chromium 或 node"
       if results[0].get("error"):
           return None, results[0]["error"]
       return out, None
   ```

2. `main()` 里 `--shot` 参数之后加：

   ```python
       ap.add_argument("--pdf", action="store_true",
                       help="自检通过后按打印样式出一份 A4 PDF，放在页面旁边（同名 .pdf）")
   ```

   在 `if args.shot:` 那一段之后、`if args.open:` 之前加：

   ```python
       if args.pdf:
           out, err = print_pdf(args.page)
           print(f"已导出  {out}" if out else f"--pdf 未完成：{err}")
   ```

3. 文件开头文档字符串的用法里，`python3 build.py page.html --open` 那行之后加一行 `    python3 build.py page.html --pdf          # 自检通过后出一份 A4 PDF`（对齐方式照抄上面几行）。

4. 测试：在 `test_snap_narrows_to_one_theme_and_width` 之后加

   ```python
       @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
       def test_pdf_prints_a4_beside_the_page(self):
           page = self.copy_fixture()
           result = run_build(page, "--pdf")
           self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
           pdf = page.with_suffix(".pdf").read_bytes()
           self.assertTrue(pdf.startswith(b"%PDF"))
           self.assertRegex(pdf, rb"/MediaBox \[0 0 59[45]\.\d+ 84[12]\.\d+\]")  # A4，不是 Letter 的 612 x 792
   ```

**Verify**: 语法检查无输出；全量单元测试 → `OK`，测试数比执行前多 1；`python3 skills/show-me-html/scripts/build.py --help | grep -q -- '--pdf' && echo ok` → `ok`。

### Step 5: 文档

`SKILL.md`「使用边界与维护」第一行 `成品页自带打印样式，用户要 PDF 时用浏览器打印它。` 改为：

<!-- prettier-ignore -->
```markdown
成品页自带打印样式；用户要 PDF 时最后一次构建加 `--pdf`，页面旁边出一份同名 A4 PDF。
```

然后 `npx prettier --write skills/show-me-html/SKILL.md`。

**Verify**: `make check` → exit 0；`grep -c -- '--pdf' skills/show-me-html/SKILL.md` → `1`。

### Step 6: 回归

用最近一轮冻结场景的 approach-compare 出一份 PDF，确认是 A4、两页（当前打印样式下的页数；计划 027 合入后可能变化）：

```sh
R=$(ls -d /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/*/ | tail -1)
P=$(mktemp -d); cp "$R/approach-compare.html" "$P/a.html"
python3 skills/show-me-html/scripts/build.py "$P/a.html" --pdf | tail -2
python3 -c "import re,sys; d=open(sys.argv[1],'rb').read(); print(len(re.findall(rb'/Type\s*/Page[^s]', d)), set(re.findall(rb'/MediaBox \[[^]]*\]', d)))" "$P/a.pdf"
```

**Verify**: 打印 `已导出  …/a.pdf`；页数与 `$R/_probe/approach-compare.pdf` 的页数相同，MediaBox 是 `[0 0 594.95996 841.91998]`。

## Test plan

- 替换：`test_chrome_proxy_args_follow_proxy_env` → `test_cdp_proxy_args_follow_proxy_env`，同样五组输入，测 `cdp.mjs` 的 `proxyArgs()`。
- 新增：`test_pdf_prints_a4_beside_the_page`。
- gallery 没有单元测试覆盖截图，靠 Step 2 的完整运行。

## Done criteria

- [ ] 全量单元测试 `OK`，测试数比执行前多 1
- [ ] `grep -c 'chrome_run\|ThreadPoolExecutor\|htmllib\|--headless' skills/show-me-html/scripts/gallery.py` → `0`
- [ ] `grep -rc 'chrome_proxy_args' skills/show-me-html/scripts` 全是 `0`
- [ ] `gallery.py --shots` 截图 `118/118`，`问题` 条数与合入前相同
- [ ] Step 6 的 PDF 是 A4
- [ ] `make check` exit 0；`git status` 只显示 Scope 里的文件
- [ ] `plans/README.md` 本计划的状态行已更新

## STOP conditions

- 021 未合入（drift check）。
- `gallery.py --shots` 的截图张数少于 118，或问题条数与合入前不同。
- `--pdf` 出的 PDF 是 Letter（612 × 792）：说明 `preferCSSPageSize` 没生效或打印样式里的 `@page` 被改了。
- 发现 `chrome_proxy_args` 还有别的调用方。

## Maintenance notes

- 图库截图现在在一个 Chrome 里顺序执行。以后图型数量翻倍、耗时明显变长时，可以让 `render.mjs` 同时开几个页面并行，但要先确认 `Emulation.setVirtualTimePolicy` 在多个页面同时跑时互不影响。
- `chrome_run` 文档字符串里「别加 --user-data-dir」的说法随函数一起删掉：运行器每次用新配置，不再依赖字体缓存，等待由虚拟时间加真实超时保证。
- `--pdf` 只在自检通过后执行，与 `--shot`、`--snap` 一样。
