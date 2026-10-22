# Plan 020: show-me-html 的无头 Chrome 走环境变量里的代理，并修正两处会引发返工的文档

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 2f0e439..HEAD -- skills/show-me-html/scripts/build.py skills/show-me-html/scripts/gallery.py skills/show-me-html/scripts/probe_round.mjs skills/show-me-html/tests/test_build.py skills/show-me-html/references/components.md skills/show-me-html/references/layouts.md`
> 输出为空才继续。有输出时，逐条对照下面「Current state」里的摘录；对不上就是 STOP 条件。
>
> 本文件里的 js / markdown 代码块前都有 `<!-- prettier-ignore -->`，内容就是要粘贴的原样，不要按 prettier 的风格改写。

## Status

- **Priority**: P1
- **Effort**: S（一个 Python 函数、一个 JS 常量、五处调用、一个测试、两段文档）
- **Risk**: LOW（没配代理的环境行为不变；配了代理的环境里，Chrome 访问外网改走代理）
- **Depends on**: none。维护者定的顺序是 020 → 018 → 019 → 021，本计划最先执行。
- **Category**: perf
- **Planned at**: commit `2f0e439`, 2026-10-22

## Why this matters

show-me-html 的 `build.py` 在每次构建时用无头 Chrome 渲染页面做检查（渲染检查、`--snap` 快照、`--shot` 截图），`gallery.py --shots` 和 `probe_round.mjs` 也一样。页面骨架会从 Google Fonts 加载字体。Chrome 不读 `HTTP_PROXY` / `HTTPS_PROXY` 这类环境变量，只认系统代理或 `--proxy-server` 参数。维护者本机的代理只配在环境变量里、系统代理是关的，所以每次启动 Chrome 都直连 Google Fonts。

2026-10-22 维护者本机实测（一页 389 KB 的 status-report 页面，带检查脚本的一次 `--dump-dom`）：默认 16.7～18.7 秒；加 `--proxy-server=<环境变量里的代理>` 后 5.3～7.3 秒。同一页面的普通构建 18～34 秒，`--snap` 120 秒，一次 32 分钟的会话里有 20 分钟在等 Chrome。本计划让所有启动 Chrome 的地方在环境变量里有代理时把它传给 Chrome，字体照常加载，只是走代理。维护者决定默认开启，不加开关。

同一份调查还发现两处文档会让写页面的 agent 返工，顺带修掉：

- `references/components.md` 的折叠示例让在 `summary` 里放 `chevron-down` 图标，并说「最后一个 `<svg>` 会被自动旋转成展开指示」。`show-me.css` 里没有任何旋转规则，展开指示是 `summary::after` 画的 `+` / `−`。照示例写，标题右侧会同时出现图标和加号。
- `references/layouts.md`「报告节律」让把口径放进 `.with-rail` 侧栏，但没说侧栏旁边的主栏只有约 640px。800 宽 viewBox 的通栏图（`.fig.wide`）放进主栏只显示约 0.75 倍，图内 9 号字缩到 7px 左右。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `2f0e439`，对不上时以引文为准。

**启动 Chrome 的五处**（都没有代理参数）：

- `scripts/build.py:942-945`，`shoot_sheets()`（`--shot`）：

  ```python
                  subprocess.run(
                      # --no-sandbox：macOS 与普通用户下不需要，Linux 容器里以 root 跑 Chrome 时不加会直接退出
                      [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                       f"--force-device-scale-factor={scale}", "--virtual-time-budget=4000",
                       f"--window-size={w},{h}", f"--screenshot={out}", probe.as_uri()],
                      capture_output=True, text=True, timeout=90, check=True)
  ```

- `scripts/build.py:975`，`snap_page()`（`--snap`，下面两次 `subprocess.run` 都用这个 `base`）：

  ```python
      base = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000"]
  ```

- `scripts/build.py:1050-1055`，`render_check()`（每次构建都跑）：

  ```python
                  out = subprocess.run(
                      # --no-sandbox 见 shoot_sheets 的说明
                      [chrome, "--headless", "--disable-gpu", "--no-sandbox",
                       "--virtual-time-budget=4000", f"--window-size={w},900",
                       "--dump-dom", probe.as_uri()],
                      capture_output=True, text=True, timeout=90).stdout
  ```

- `scripts/build.py:1023-1032`，`find_chrome()`，新函数放在它后面：

  ```python
  def find_chrome():
      import shutil
      for p in CHROME_PATHS:
          if Path(p).exists():
              return p
      for n in ("google-chrome", "chromium", "chromium-browser"):
          p = shutil.which(n)
          if p:
              return p
      return None
  ```

- `scripts/gallery.py:213-223`，`chrome_run()`；`shots()` 在 `:227` 用 `runpy` 从 `build.py` 取 `find_chrome`，在 `:241` 和 `:254` 两处调用 `chrome_run`：

  ```python
  def chrome_run(chrome, *args):
      """偶发卡住（多半在等字体请求）就重试一次。别加 --user-data-dir：新配置没有字体缓存，virtual time 会一直等网络。"""
      for _ in range(2):
          try:
              return subprocess.run(
                  [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-prefers-reduced-motion", *args],
                  capture_output=True, text=True, timeout=45,
              )
  ```

  ```python
  def shots(page, out, index):
      chrome = runpy.run_path(str(BUILD))["find_chrome"]()
  ```

- `scripts/probe_round.mjs:43-49`：

  ```js
  const chrome = spawn(CHROME, [
    "--headless=new",
    "--remote-debugging-port=0",
    "--hide-scrollbars",
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "probe-round-"))}`,
    "about:blank",
  ]);
  ```

**惯例**：`build.py` 顶层只 import `argparse`、`re`、`sys`、`Path`、`HTMLParser`，函数需要别的模块时在函数体内 import（见 `find_chrome` 里的 `import shutil`）。注释和用户可见文字用中文。测试在 `tests/test_build.py`，用 `runpy.run_path(str(BUILD))["函数名"]` 取 `build.py` 里的函数（见文件开头的 `FIND_CHROME = runpy.run_path(str(BUILD))["find_chrome"]`）。

**文档现状**：

- `references/components.md:204-219`（「折叠」一节全文）：

  <!-- prettier-ignore -->
  ````markdown
  ## 折叠（原生 details，无需 JS）

  ```html
  <div class="accordion">
    <details>
      <summary>为什么放弃方案 B<i data-lucide="chevron-down"></i></summary>
      <p>展开后的内容。</p>
    </details>
    <details open>
      <summary>迁移步骤<i data-lucide="chevron-down"></i></summary>
      <p>…</p>
    </details>
  </div>
  ```

  `summary` 里的最后一个 `<svg>` 会被自动旋转成展开指示。
  ````

- `assets/show-me.css:595-602`（展开指示的实际来源，本计划不改）：

  ```css
  summary::after {
    content: "+";
    margin-inline-start: auto;
    color: var(--color-muted-foreground);
    font-family: var(--font-mono);
  }
  details[open] > summary::after {
    content: "−";
  }
  ```

- `references/layouts.md:45-46`（「报告节律」里，侧栏示例代码块之后的两行）：

  ```markdown
  侧栏是卡片面色，sticky，900px 以下落到主栏之后；`data-toc-skip` 让它的标题不进目录。
  一页只有一个侧栏；口径不足三条时不开侧栏，写进首屏 lede 或结尾。来源：lieflat 报告模板 R01。
  ```

- `assets/show-me.css:1206-1211`（主栏宽度的来源：版心减去 2.5rem 间距后按 1.6 : 0.7 分，60rem 版心下主栏约 640px）：

  ```css
  .with-rail {
    display: grid;
    grid-template-columns: minmax(0, 1.6fr) minmax(13rem, 0.7fr);
    align-items: start;
    gap: 2.5rem;
  }
  ```

## Commands you will need

以下命令都在仓库根目录运行。

| Purpose  | Command                                                                                             | Expected on success                         |
| -------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`                                          | 末行 `OK`（本机有 Chrome 时不跳过渲染测试） |
| 语法检查 | `python3 -m py_compile skills/show-me-html/scripts/build.py skills/show-me-html/scripts/gallery.py` | 无输出                                      |
| JS 语法  | `node --check skills/show-me-html/scripts/probe_round.mjs`                                          | 无输出                                      |
| 文档门禁 | `make check`                                                                                        | exit 0                                      |
| 格式化   | `npx prettier --write <file>`                                                                       | 改写文件，exit 0                            |

测试不要用 pytest（仓库没装）。

## Scope

**In scope**（只改这些文件）：

- `skills/show-me-html/scripts/build.py`
- `skills/show-me-html/scripts/gallery.py`
- `skills/show-me-html/scripts/probe_round.mjs`
- `skills/show-me-html/tests/test_build.py`
- `skills/show-me-html/references/components.md`
- `skills/show-me-html/references/layouts.md`
- `plans/README.md`（只改本计划的状态行）

**Out of scope**：

- `assets/show-me.css`：折叠的 `+` / `−` 是对的，只改文档。
- 屏蔽字体域名（`--host-resolver-rules`）：维护者否决了。图内字号下限和计划 019 的倍率阈值是在真实字体下定的，检查必须用真实字体。
- 改成单个 Chrome 实例（CDP）：那是计划 021。本计划只给现有调用加参数，不改调用方式。
- `gallery.py` 的 `chrome_run` 文档字符串里「别加 --user-data-dir」那句：021/022 会整体替换这段代码，现在不动。
- 打印出代理地址：代理 URL 里可能带用户名和密码，任何输出、日志、测试断言里都不要出现真实的环境变量值。

## Git workflow

- 从**本地** `main` 开分支：`git checkout -b advisor/020-show-me-html-chrome-proxy main`。本地 main 可能比 origin 多几个未推送的提交，以本地为准。
- 提交信息用 conventional commits，scope 写技能名，例如仓库里已有的 `fix(show-me-html): drop the Kami pointer and print as A4 without orphaned headings`。建议两个提交：`perf(show-me-html): headless Chrome uses the proxy from the environment` 和 `docs(show-me-html): collapse marker comes from CSS, keep wide figures out of the rail`。
- pre-commit 会跑 prettier 和 `make check`，Markdown 表格对齐被重排属于预期。
- 不要 push。

## Steps

### Step 1: `build.py` 加 `chrome_proxy_args()`，三处启动 Chrome 的地方用上它

1. 在 `scripts/build.py` 的 `find_chrome()` 函数之后、`# 无头 Chrome 把窗口宽度钳在 500px…` 那行注释之前，加一个函数（前后各空两行，与文件里其他顶层函数一致）：

   ```python
   def chrome_proxy_args(env=None):
       """无头 Chrome 不读 HTTP(S)_PROXY / ALL_PROXY 环境变量，只认系统代理或 --proxy-server。
       环境里配了代理就显式传给它，否则每次渲染都直连 Google Fonts，网络不好时一次多等 10～60 秒。
       NO_PROXY 转成 Chrome 的绕行列表（逗号换分号，.example.com 写成 *.example.com）；NO_PROXY=* 时不走代理。"""
       import os
       env = os.environ if env is None else env

       def pick(*names):
           return next((env[n].strip() for n in names if env.get(n, "").strip()), "")

       proxy = pick("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")
       bypass = [h.strip() for h in pick("NO_PROXY", "no_proxy").split(",") if h.strip()]
       if not proxy or "*" in bypass:
           return []
       args = [f"--proxy-server={proxy.rstrip('/')}"]
       if bypass:
           args.append("--proxy-bypass-list=" + ";".join("*" + h if h.startswith(".") else h for h in bypass))
       return args
   ```

2. `shoot_sheets()` 里，把参数列表第一行

   ```python
                       [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
   ```

   改为

   ```python
                       [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", *chrome_proxy_args(),
   ```

3. `snap_page()` 里，把

   ```python
       base = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000"]
   ```

   改为

   ```python
       base = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000",
               *chrome_proxy_args()]
   ```

4. `render_check()` 里，把

   ```python
                       [chrome, "--headless", "--disable-gpu", "--no-sandbox",
                        "--virtual-time-budget=4000", f"--window-size={w},900",
   ```

   改为

   ```python
                       [chrome, "--headless", "--disable-gpu", "--no-sandbox", *chrome_proxy_args(),
                        "--virtual-time-budget=4000", f"--window-size={w},900",
   ```

   不要动这段之前的 `probe.write_text(...)` 一行和之后的正则：计划 018、019 以它们为锚点。

**Verify**: 语法检查无输出；`grep -c 'chrome_proxy_args()' skills/show-me-html/scripts/build.py` → `3`；`grep -c 'def chrome_proxy_args' skills/show-me-html/scripts/build.py` → `1`。

### Step 2: `gallery.py` 和 `probe_round.mjs` 也传代理

1. `scripts/gallery.py` 的 `shots()` 开头，把

   ```python
       chrome = runpy.run_path(str(BUILD))["find_chrome"]()
   ```

   改为

   ```python
       build = runpy.run_path(str(BUILD))
       chrome, proxy = build["find_chrome"](), build["chrome_proxy_args"]()
   ```

   然后把 `shots()` 里两处 `chrome_run(chrome, ` 都改成 `chrome_run(chrome, *proxy, `（一处在 `dom = chrome_run(...)`，一处在内部函数 `shoot()` 里）。`chrome_run` 本身不改。

2. `scripts/probe_round.mjs`：在 `const chrome = spawn(CHROME, [` 这一行**正上方**插入：

   <!-- prettier-ignore -->
   ```js
   // 无头 Chrome 不读 HTTP(S)_PROXY 环境变量：配了代理就显式传，否则每次直连 Google Fonts。规则同 build.py 的 chrome_proxy_args
   const envOf = (...names) =>
     names.map((n) => (process.env[n] || "").trim()).find(Boolean) || "";
   const proxy = envOf("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy");
   const bypass = envOf("NO_PROXY", "no_proxy").split(",").map((h) => h.trim()).filter(Boolean);
   const PROXY_ARGS =
     proxy && !bypass.includes("*")
       ? [
           `--proxy-server=${proxy.replace(/\/$/, "")}`,
           ...(bypass.length
             ? [`--proxy-bypass-list=${bypass.map((h) => (h.startsWith(".") ? "*" + h : h)).join(";")}`]
             : []),
         ]
       : [];
   ```

   再在 `spawn(CHROME, [...])` 的参数数组里，`"about:blank",` 这一项的**正上方**加一行 `  ...PROXY_ARGS,`。

**Verify**: 语法检查无输出；`node --check skills/show-me-html/scripts/probe_round.mjs` 无输出；`grep -c 'chrome_run(chrome, \*proxy, ' skills/show-me-html/scripts/gallery.py` → `2`；`grep -c 'PROXY_ARGS' skills/show-me-html/scripts/probe_round.mjs` → `2`。

### Step 3: 单元测试

在 `tests/test_build.py` 的 `class BuildCliTests` 里，`test_render_check_flags_chart_text_below_font_floor` 这个方法**之前**（它上面的装饰器 `@unittest.skipUnless(...)` 之前）加一个测试。这个测试不需要 Chrome，不加装饰器。环境变量值都是虚构的：

```python
    def test_chrome_proxy_args_follow_proxy_env(self):
        """Chrome 不读代理环境变量：有代理时传 --proxy-server，HTTPS 优先，NO_PROXY 转绕行列表，NO_PROXY=* 不走代理。"""
        proxy_args = runpy.run_path(str(BUILD))["chrome_proxy_args"]
        self.assertEqual(proxy_args({}), [])
        self.assertEqual(proxy_args({"https_proxy": "http://127.0.0.1:7890/"}),
                         ["--proxy-server=http://127.0.0.1:7890"])
        self.assertEqual(proxy_args({"HTTP_PROXY": "http://a.test:1", "HTTPS_PROXY": "http://b.test:2"}),
                         ["--proxy-server=http://b.test:2"])
        self.assertEqual(proxy_args({"ALL_PROXY": "socks5://127.0.0.1:7891", "NO_PROXY": "localhost, .corp.test"}),
                         ["--proxy-server=socks5://127.0.0.1:7891", "--proxy-bypass-list=localhost;*.corp.test"])
        self.assertEqual(proxy_args({"HTTPS_PROXY": "http://b.test:2", "no_proxy": "*"}), [])
```

**Verify**: `python3 -m unittest skills.show-me-html.tests.test_build -k proxy` → `Ran 1 test`、`OK`；全量单元测试 → `OK`，测试数比执行前多 1。

### Step 4: 实测提速

本步只测量、不改代码。先看执行环境里有没有代理：

```sh
python3 -c "import runpy; a = runpy.run_path('skills/show-me-html/scripts/build.py')['chrome_proxy_args'](); print('有代理' if a else '无代理')"
```

- 打印 `无代理`：在汇报里写「执行环境没有代理变量，未测提速」，跳到 Step 5。
- 打印 `有代理`：用最近一轮冻结场景里的 status-report 页面，对比带代理和去掉代理变量两次构建：

  ```sh
  T=$(mktemp -d)
  cp /Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-22-6d39fa5-printbreak/status-report.html "$T/a.html"
  cp "$T/a.html" "$T/b.html"
  /usr/bin/time -p python3 skills/show-me-html/scripts/build.py "$T/a.html" 2>&1 | tail -5
  env -u HTTPS_PROXY -u https_proxy -u HTTP_PROXY -u http_proxy -u ALL_PROXY -u all_proxy \
    /usr/bin/time -p python3 skills/show-me-html/scripts/build.py "$T/b.html" 2>&1 | tail -5
  ```

**Verify**: 两次都打印 `自检通过。` 和同一行 `渲染检查：500px / 1024px / 1280px 无横向溢出。…`；把两次的 `real` 秒数写进汇报（维护者本机预期：带代理约 15 秒以内，不带代理 18～34 秒；网络状况会让数字浮动，不作为通过条件）。场景目录不存在时，换成 `skills/show-me-html/tests/fixtures/component-states.html` 的副本，并在汇报里注明。

### Step 5: 文档

1. `references/components.md`「折叠」一节：示例里两处 `<i data-lucide="chevron-down"></i>` 删掉（`summary` 里只留文字），代码块之后那一行 `` `summary` 里的最后一个 `<svg>` 会被自动旋转成展开指示。`` 替换为：

   <!-- prettier-ignore -->
   ```markdown
   展开指示是骨架画的：标题右侧收起时是 `+`、展开时是 `−`（`summary::after`）。`summary` 里只写文字，不另放 chevron 之类的图标，否则会和加减号同时出现。
   ```

   「下拉菜单」一节里的 `chevron-down` 属于另一个组件，不动。

2. `references/layouts.md`「报告节律」：在 `一页只有一个侧栏；口径不足三条时不开侧栏，写进首屏 lede 或结尾。来源：lieflat 报告模板 R01。` 这一行之后另起一行（同一段落内，紧接着写，不空行）加：

   <!-- prettier-ignore -->
   ```markdown
   `.with-rail` 的主栏只放正文、窄表和半宽图：主栏约占版心的七成，60rem 版心下约 640px，800 宽 viewBox 的 `.fig.wide` 放进去只显示约 0.75 倍，图内 9 号字缩到 7px 左右。通栏图和宽表放在 `.with-rail` 之外，口径侧栏放到不含宽证据的那一节。
   ```

3. `npx prettier --write skills/show-me-html/references/components.md skills/show-me-html/references/layouts.md`

**Verify**: `make check` → exit 0；`grep -c 'chevron-down' skills/show-me-html/references/components.md` → 比改前少 2（改前先跑一次记下数字）；`grep -c '自动旋转' skills/show-me-html/references/components.md` → `0`；`grep -c '主栏只放正文、窄表和半宽图' skills/show-me-html/references/layouts.md` → `1`。

### Step 6: 回归

1. 全量单元测试 → `OK`，测试数比执行前多 1，没有失败。
2. 冻结场景：五页用新 `build.py` 重建，结果与上一轮一致。

   ```sh
   PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-22-6d39fa5-printbreak
   NEW=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-020
   mkdir -p "$NEW"
   for n in status-report approach-compare code-review concept-explainer triage-board; do
     cp "$PREV/$n.html" "$NEW/" && python3 skills/show-me-html/scripts/build.py "$NEW/$n.html" | tail -2
   done
   node skills/show-me-html/scripts/probe_round.mjs "$NEW" "$PREV"
   ```

**Verify**: 五次构建各打印 `自检通过。`；探针五行都是 `无问题`。截图逐字节相同属于预期，不相同时打开两边的同名截图看差别：只差字体渲染细节（例如此前直连时字体没加载完、这次加载完了）可以接受并在汇报里说明，版式变化就 STOP。轮次目录在 `.gitignore` 里，不进提交。

## Test plan

- 新增 `test_chrome_proxy_args_follow_proxy_env`：无变量、HTTPS 优先于 HTTP、小写变量名、去掉末尾斜杠、`ALL_PROXY` 加 `NO_PROXY` 转绕行列表、`NO_PROXY=*` 不走代理。纯函数测试，不需要 Chrome。
- 现有四个渲染测试（`test_snap_renders_both_themes_and_exports_markdown`、三个 `test_render_check_*`）在本机有 Chrome 时会真跑，用来确认加参数后渲染行为不变。
- `probe_round.mjs` 没有单元测试，靠 Step 6 的冻结场景轮次覆盖。

## Done criteria

- [ ] `python3 -m unittest skills.show-me-html.tests.test_build` 末行 `OK`，测试数比执行前多 1
- [ ] `grep -c 'chrome_proxy_args()' skills/show-me-html/scripts/build.py` → `3`
- [ ] `grep -c 'chrome_run(chrome, \*proxy, ' skills/show-me-html/scripts/gallery.py` → `2`
- [ ] `node --check skills/show-me-html/scripts/probe_round.mjs` 无输出，`grep -c 'PROXY_ARGS' skills/show-me-html/scripts/probe_round.mjs` → `2`
- [ ] `grep -c '自动旋转' skills/show-me-html/references/components.md` → `0`
- [ ] `make check` exit 0
- [ ] Step 6 冻结场景五页 `自检通过。`、探针五行 `无问题`
- [ ] `git status` 只显示 Scope 里列出的文件有改动
- [ ] `plans/README.md` 本计划的状态行已更新，汇报里写了 Step 4 的两个耗时（或「无代理环境，未测提速」）

## STOP conditions

- Drift check 有输出，且「Current state」里的摘录与代码对不上。
- 带代理的构建报 `渲染检查跑不起来`、截图失败，或者比不带代理更慢：说明代理本身连不上或拦了本地请求。不要改成默认关闭，汇报两次的完整输出。
- Step 6 的冻结场景截图出现版式变化（不只是字体细节）。
- 你发现需要改 `show-me.css` 才能让折叠文档成立。

## Maintenance notes

- 计划 021 会把 `build.py` 里的 Chrome 调用换成单实例 CDP 运行器，`probe_round.mjs` 里的 `PROXY_ARGS` 搬进共用的 `scripts/cdp.mjs`（`proxyArgs()`）。计划 022 让 `gallery.py` 也改走运行器后，Python 版的 `chrome_proxy_args` 没有调用方，连同本计划的测试一起换成对 `cdp.mjs` 的测试。在那之前，Python 和 JS 两份实现要保持同一规则。
- 计划 018、019 的「Current state」引用了 `render_check()` 里的 `probe.write_text(...)`、正则和 `PROBE` 末尾几行，本计划都没有碰；它们的 drift check 会看到 `build.py` 有改动，`plans/README.md` 里已注明这属于预期。
- 审阅时看一眼：输出、测试、注释里没有出现真实的代理地址。
