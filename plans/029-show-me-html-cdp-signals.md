# Plan 029: 无头 Chrome 运行器被 SIGINT / SIGTERM 打断时结束 Chrome、删掉配置目录

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。索引 `plans/README.md` 由审阅者维护，你不要改它。
>
> **Drift check (run first)**: `git diff --stat dff9227..HEAD -- skills/show-me-html/scripts/cdp.mjs skills/show-me-html/scripts/probe_page.mjs skills/show-me-html/scripts/build.py skills/show-me-html/tests/test_build.py` 应无输出。有输出就对照下面「Current state」里的引文，引文原样还在就继续，对不上就 STOP。
>
> 本文件里的 js 代码块前都有 `<!-- prettier-ignore -->`，内容已经是 prettier 格式，原样粘贴即可，粘贴后 `prettier --check` 应直接通过。python 代码块原样粘贴（prettier 不管 `.py`）。

## Status

- **Priority**: P3
- **Effort**: S（`cdp.mjs` 加一个信号处理、删目录加重试，`probe_page.mjs` 删掉重复的那段，`build.py` 改停止方式，两个测试）
- **Risk**: LOW（只改收尾：被打断时的处理和删配置目录时的重试；打开页面、截图、出结果的逻辑不变）
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `dff9227`, 2026-10-23

## Why this matters

show-me-html 的三个脚本都通过 `scripts/cdp.mjs` 的 `launch()` 启动无头 Chrome：`render.mjs`（`build.py` 的渲染检查、`--snap`、`--shot`、`--pdf`，以及 `gallery.py --shots`）、`probe_round.mjs`（冻结场景轮次）、`probe_page.mjs`（单页交互探针）。每次启动都会在系统临时目录建一个 Chrome 配置目录，每个 15–24 MB，正常结束时由 `close()` 删掉。但运行中被打断时没人收拾：只给 node 发 SIGTERM 或 SIGINT（命令超时、`kill`），Chrome 的进程会全部变成孤儿；`build.py` 被 Ctrl-C 或超时打断时，会对运行器整组发 SIGKILL，Chrome 虽然结束了，配置目录却每次都留下。

本计划让 `launch()` 自己接 SIGINT / SIGTERM：先 `close()`，再按惯例以 130 / 143 退出。`build.py` 停运行器时改为先发 SIGTERM，给它收拾的机会，5 秒内没退再 SIGKILL。规划时还查出 `close()` 本身有个竞态：Chrome 主进程退出后，网络服务还在往配置目录里写临时文件，删目录偶尔失败，错误又被吞掉。所以删目录也要加重试。

## Current state

技能目录是 `skills/show-me-html/`（下文路径都相对这个目录）。行号按 `dff9227`。

- `scripts/cdp.mjs:31-59`，`launch()` 的说明和开头。`close()` 结束 Chrome、等它退出、删配置目录；`:60` 起是连 WebSocket 的 `let ws; try {…}`：

  ```js
  // 启动一个无头 Chrome 并连上。返回 send(方法, 参数, sessionId)、until(事件名, {sessionId, timeout})、on(监听)、close()。
  // close() 返回 Promise：结束 Chrome，等它退出后删掉这次的配置目录（每次几 MB 到几十 MB）。
  // 启动失败时先收拾干净再抛错，不留 Chrome 进程和目录。
  export async function launch(chromePath, prefix = "show-me-cdp-") {
    ...
    const close = async () => {
      chrome.kill();
      await exited;
      try {
        rmSync(dir, { recursive: true, force: true });
      } catch {}
    };
    let ws;
  ```

  `close()` 里的 `rmSync` 有竞态：Chrome 主进程退出、`exited` 已经 resolve 时，它的网络服务还可能往 `Default/` 里写一个临时文件（`.com.google.Chrome.Network Persistent State.XXXXXX`），`rmSync` 删到最后报 `ENOTEMPTY`，被 `catch {}` 吞掉，整个目录就留下了。规划时给 `close()` 加日志，在「空闲 120 秒后启动 Chrome、一连上就发 SIGINT」的条件下试了 4 次，其中 2 次是这样；热状态下连续 25 次一次也没有。正常结束走的也是这个 `close()`，所以正常路径同样可能漏目录。Node 的 `rmSync` 自带 `maxRetries` / `retryDelay`，遇到 `ENOTEMPTY` 会按递增间隔重试。

  配置目录建在 `os.tmpdir()` 下，Node 的 `os.tmpdir()` 和 Python 的 `tempfile` 都读环境变量 `TMPDIR`。新测试就是给子进程一个新建的空 `TMPDIR`，再数里面剩下的目录。

- `scripts/probe_page.mjs:52-57`，这是唯一自己接了信号的调用方（计划 025 加的）。`launch()` 接管后，这段要删掉，否则同一个信号会触发两次收尾：

  ```js
  const { send, until, on, close } = cdp;
  // 被 Ctrl-C 或命令超时的 SIGTERM 打断时也结束 Chrome、删掉配置目录（SIGKILL 拦不住）
  for (const sig of ["SIGINT", "SIGTERM"])
    process.once(sig, () =>
      close().finally(() => process.exit(sig === "SIGINT" ? 130 : 143))
    );
  let code = 2;
  ```

  `render.mjs`、`probe_round.mjs` 没有接信号，改完后通过 `launch()` 自动有了收尾，这两个文件不用改。

- `scripts/build.py:1134-1147`，`run_jobs()` 启动运行器。它用 `start_new_session=True` 让运行器单独成一个进程组，因此收不到终端发来的 Ctrl-C，只能靠 `build.py` 自己 `killpg`；现在发的是 SIGKILL，node 没机会收拾：

  ```python
          # 运行器单独一个进程组：超时或被中断时连同它启动的 Chrome 一起结束，不留孤儿进程
          proc = subprocess.Popen([node, str(RENDER_SCRIPT), str(spec)], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, encoding="utf-8", start_new_session=True)
          try:
              out, err = proc.communicate(timeout=90 * len(jobs) + 30)
          except subprocess.TimeoutExpired:
              with contextlib.suppress(ProcessLookupError):  # 进程组可能恰好已经自己退出
                  os.killpg(proc.pid, signal.SIGKILL)
              proc.communicate()
              return None, "Chrome 运行器超时"
          except BaseException:  # Ctrl-C 等：单独的进程组收不到终端发来的信号，要自己结束它
              with contextlib.suppress(ProcessLookupError):
                  os.killpg(proc.pid, signal.SIGKILL)
              raise
  ```

  `run_jobs()` 开头已经 `import contextlib, json, os, shutil, signal, subprocess, tempfile`。

- 规划时在 `dff9227` 的副本上实测：
  - 只给 node 发信号：SIGTERM 与 SIGINT 两种情况都留下 9 个 Chrome 进程和 1 个配置目录，退出码分别是 -15 和 -2。在终端里按 Ctrl-C 时，信号发给整个进程组，Chrome 自己也会退，但目录同样会留下。
  - `build.py --snap` 跑到一半被 SIGINT：Chrome 进程 0 个，配置目录留下 1 个。
  - 只改 `cdp.mjs`：只给 node 发信号时零残留，退出码 143 / 130；但 `build.py` 被打断后仍留 1 个目录，因为它发的是 SIGKILL。`cdp.mjs` 和 `build.py` 都改之后才是 0。

- 测试的写法照 `tests/test_build.py:473` 的 `test_cdp_proxy_args_follow_proxy_env`：用 `node -e` 动态 `import()` `cdp.mjs`。需要 Chrome 的测试用装饰器 `@unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")`；`FIND_CHROME()` 返回 Chrome 路径，`self.copy_fixture()` 复制 `tests/fixtures/minimal-shell.html`。

## Commands you will need

| Purpose  | Command                                                      | Expected on success                          |
| -------- | ------------------------------------------------------------ | -------------------------------------------- |
| 单元测试 | `python3 -m unittest skills.show-me-html.tests.test_build`   | `Ran 62 tests`、末行 `OK`（执行前是 60）     |
| JS 语法  | `node --check <文件>`                                        | 无输出                                       |
| Py 语法  | `python3 -m py_compile skills/show-me-html/scripts/build.py` | 无输出                                       |
| 格式     | `npx prettier --check <文件>`                                | `All matched files use Prettier code style!` |
| 文档门禁 | `make check`                                                 | exit 0，`技能文档引用检查通过`               |

命令都在仓库根目录跑。Step 4、Step 5 的 shell 片段用 bash（本机默认 shell 是 fish，`VAR=$(…)` 赋值和 `${PIPESTATUS[0]}` 在 fish 里不成立）。

## Scope

**In scope**：`skills/show-me-html/scripts/cdp.mjs`、`skills/show-me-html/scripts/probe_page.mjs`（只删一段）、`skills/show-me-html/scripts/build.py`（只改 `run_jobs()` 里停运行器的那段）、`skills/show-me-html/tests/test_build.py`。

**Out of scope**：

- `scripts/render.mjs`、`scripts/probe_round.mjs`、`scripts/gallery.py`：它们通过 `launch()` 或 `run_jobs()` 自动拿到新行为，不用改。
- SIGHUP（关掉终端窗口）、SIGKILL：不处理，SIGKILL 本来也拦不住。
- 清理以前留下的旧配置目录：不在本计划里做。
- `plans/README.md`：审阅者维护。

## Git workflow

从本地 `main` 开分支 `advisor/029-show-me-html-cdp-signals`。提交信息例如 `fix(show-me-html): Chrome runner cleans up on SIGINT / SIGTERM`。pre-commit 会跑 prettier 和 `make check`。不要 push。

## Steps

### Step 1: `launch()` 接 SIGINT / SIGTERM，`probe_page.mjs` 不再自己接

**1a.** `scripts/cdp.mjs`，在 `// 启动失败时先收拾干净再抛错，不留 Chrome 进程和目录。`（`:34`）这一行之后加一行：

<!-- prettier-ignore -->
```js
// 进程收到 SIGINT / SIGTERM 时也先 close() 再退出（退出码 130 / 143），调用方不用自己接信号。
```

**1b.** 同一文件，`close()` 里删目录的那一行

<!-- prettier-ignore -->
```js
      rmSync(dir, { recursive: true, force: true });
```

改为

<!-- prettier-ignore -->
```js
      // Chrome 的网络服务退出时还会往 Default/ 里写临时文件，删目录可能撞上 ENOTEMPTY：让 rmSync 重试几次
      rmSync(dir, {
        recursive: true,
        force: true,
        maxRetries: 5,
        retryDelay: 100,
      });
```

**1c.** 同一文件，`close` 的定义（以 `  };` 结束）之后、`  let ws;` 之前插入：

<!-- prettier-ignore -->
```js
  // 被 Ctrl-C、命令超时的 SIGTERM 或 build.py 打断时，也结束 Chrome、删掉配置目录（SIGKILL 拦不住）。
  // 接了信号 node 就不会自己退出，收拾完按惯例用 128 + 信号值退出：SIGINT 130，SIGTERM 143。
  for (const [sig, code] of [
    ["SIGINT", 130],
    ["SIGTERM", 143],
  ])
    process.once(sig, () => close().finally(() => process.exit(code)));
```

放在这个位置，是为了 Chrome 已经启动、但 WebSocket 还没连上时收到信号也能收拾。

**1d.** `scripts/probe_page.mjs`，把

<!-- prettier-ignore -->
```js
const { send, until, on, close } = cdp;
// 被 Ctrl-C 或命令超时的 SIGTERM 打断时也结束 Chrome、删掉配置目录（SIGKILL 拦不住）
for (const sig of ["SIGINT", "SIGTERM"])
  process.once(sig, () =>
    close().finally(() => process.exit(sig === "SIGINT" ? 130 : 143))
  );
let code = 2;
```

改为

<!-- prettier-ignore -->
```js
const { send, until, on, close } = cdp;
let code = 2;
```

**Verify**：

- `node --check skills/show-me-html/scripts/cdp.mjs` 和 `node --check skills/show-me-html/scripts/probe_page.mjs` 都无输出。
- `npx prettier --check skills/show-me-html/scripts/cdp.mjs skills/show-me-html/scripts/probe_page.mjs` → `All matched files use Prettier code style!`（不要跑 `--write`）。
- `grep -c 'process.once' skills/show-me-html/scripts/cdp.mjs` → `1`；`grep -c 'maxRetries: 5' skills/show-me-html/scripts/cdp.mjs` → `1`；`grep -c 'process.once' skills/show-me-html/scripts/probe_page.mjs` → `0`；`grep -c 'SIG' skills/show-me-html/scripts/probe_page.mjs` → `0`。

### Step 2: `build.py` 停运行器时先发 SIGTERM

`scripts/build.py` 的 `run_jobs()` 里，把 `proc = subprocess.Popen(…)` 之后的这段

```python
        try:
            out, err = proc.communicate(timeout=90 * len(jobs) + 30)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):  # 进程组可能恰好已经自己退出
                os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            return None, "Chrome 运行器超时"
        except BaseException:  # Ctrl-C 等：单独的进程组收不到终端发来的信号，要自己结束它
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            raise
```

改为（前面空一行，`def stop()` 与 `try:` 之间也空一行）：

```python

        def stop():
            # 先对整组发 SIGTERM：运行器（cdp.mjs）收到后结束 Chrome、删掉配置目录再退出；最多等 5 秒，再 SIGKILL 剩下的。
            # 进程组可能已经全部退出（ProcessLookupError）；macOS 上组长被回收后再 killpg 还可能报 PermissionError。
            # 两种都忽略，否则会盖掉原来的 KeyboardInterrupt，或让超时路径崩掉
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGTERM)
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGKILL)

        try:
            out, err = proc.communicate(timeout=90 * len(jobs) + 30)
        except subprocess.TimeoutExpired:
            stop()
            proc.communicate()
            return None, "Chrome 运行器超时"
        except BaseException:  # Ctrl-C 等：单独的进程组收不到终端发来的信号，要自己结束它
            stop()
            raise
```

两次 `killpg` 都要同时忽略 `ProcessLookupError` 和 `PermissionError`：规划时把第一次临时改成 SIGKILL 做反证，node 被杀、被 `wait` 回收之后，第二次 `killpg` 在 macOS 上报了 `PermissionError: [Errno 1] Operation not permitted`，盖掉了 `KeyboardInterrupt`，`build.py` 以 1 退出。

`proc.wait(timeout=5)` 等的时候管道还开着：运行器收到信号后不再往 stdout 写（`render.mjs` 只在全部任务跑完后写一次），所以不会因为管道写满而卡住；就算卡住，5 秒后也会 SIGKILL。

**Verify**：

- `python3 -m py_compile skills/show-me-html/scripts/build.py` 无输出。
- `grep -c 'os.killpg(proc.pid, signal.SIGKILL)' skills/show-me-html/scripts/build.py` → `1`（改前是 `2`）；`grep -c 'os.killpg(proc.pid, signal.SIGTERM)' skills/show-me-html/scripts/build.py` → `1`；`grep -c '            stop()$' skills/show-me-html/scripts/build.py` → `2`；`grep -c 'ProcessLookupError, PermissionError' skills/show-me-html/scripts/build.py` → `2`。

### Step 3: 测试

**3a.** `tests/test_build.py` 的 import 按字母序补两个：`import json` 与 `import re` 之间加 `import os`，`import shutil` 与 `import subprocess` 之间加 `import signal`。

**3b.** 在 `def png_size(path):`（`:24`）之前插入下面这个函数，函数后空两行：

```python
def chrome_pids(tmpdir):
    """命令行里带着 tmpdir 的进程：Chrome 的 --user-data-dir 在 TMPDIR 下。"""
    return subprocess.run(["pgrep", "-f", str(tmpdir)], capture_output=True, text=True).stdout.split()
```

**3c.** 在 `test_cdp_proxy_args_follow_proxy_env` 之后（它的最后一行是 `            ["--proxy-server=socks5://127.0.0.1:7891", "--proxy-bypass-list=localhost;*.corp.test"], []])`，后面空一行）插入下面两个测试，最后空一行：

```python
    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_cdp_signal_closes_chrome_and_removes_profile(self):
        """launch() 接 SIGINT / SIGTERM：结束 Chrome、删掉配置目录，再按 130 / 143 退出。"""
        script = ("import(process.argv[1]).then(async (m) => { await m.launch(process.argv[2], 'sigtest-');"
                  " console.log('ready'); setInterval(() => {}, 1000); })")
        for sig, code in ((signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(sig=sig.name), tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
                proc = subprocess.Popen(["node", "-e", script, (SKILL / "scripts" / "cdp.mjs").as_uri(), FIND_CHROME()],
                                        stdout=subprocess.PIPE, text=True, env={**os.environ, "TMPDIR": td})
                try:
                    self.assertEqual(proc.stdout.readline().strip(), "ready")
                    proc.send_signal(sig)
                    self.assertEqual(proc.wait(timeout=30), code)
                    self.assertEqual([p.name for p in Path(td).iterdir() if p.name.startswith("sigtest-")], [])
                    self.assertEqual(chrome_pids(td), [], "Chrome 进程还在")
                finally:
                    proc.kill()
                    proc.stdout.close()
                    subprocess.run(["pkill", "-KILL", "-f", td])

    @unittest.skipUnless(RENDERER, "需要本机 Chrome/Chromium 和 node")
    def test_interrupted_build_leaves_no_chrome_profile(self):
        """构建中途被 Ctrl-C：build.py 先对运行器发 SIGTERM，运行器结束 Chrome、删掉配置目录后才退出。"""
        page = self.copy_fixture()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            def profiles():
                return [p.name for p in Path(td).iterdir() if p.name.startswith("show-me-cdp-")]
            proc = subprocess.Popen([sys.executable, str(BUILD), str(page), "--no-render", "--snap", str(page.parent / "snap")],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    env={**os.environ, "TMPDIR": td})
            try:
                for _ in range(200):  # 等运行器建好配置目录，说明 Chrome 已经起来
                    if profiles():
                        break
                    time.sleep(0.05)
                time.sleep(0.5)
                self.assertIsNone(proc.poll(), "构建在打断之前就结束了")
                proc.send_signal(signal.SIGINT)
                proc.communicate(timeout=30)
                self.assertEqual(proc.returncode, -signal.SIGINT)
                self.assertEqual(profiles(), [])
                self.assertEqual(chrome_pids(td), [], "Chrome 进程还在")
            finally:
                proc.kill()
                subprocess.run(["pkill", "-KILL", "-f", td])
```

两个测试都给子进程一个新建的空 `TMPDIR`，配置目录就建在里面，测试只数这个目录里剩下的东西。`finally` 里用 `pkill -KILL -f` 清掉残留，保证测试失败时也不留 Chrome 进程；`ignore_cleanup_errors=True` 是因为刚被杀的 Chrome 可能还在往目录里写，删临时目录时会偶尔报错。这两处只在测试已经失败时起作用，规划时没有它们，反证偶尔会多出一个与断言无关的 ERROR。第一个测试只用 `readline()` 读了 stdout，没有 `communicate()`，所以 `finally` 里要自己 `proc.stdout.close()`，否则每个子测试报一条 `ResourceWarning: unclosed file`（审阅时补上；改前全量测试一条 `ResourceWarning` 也没有）。第二个测试里，默认的 `--snap` 在最小夹具上要跑 3 秒左右，配置目录出现后再等 0.5 秒打断，打断时构建一定还在跑；万一已经跑完，测试会报「构建在打断之前就结束了」，不会误判为通过。

**Verify**：

- `python3 -m unittest skills.show-me-html.tests.test_build -k cdp_signal -k interrupted_build` → `Ran 2 tests`、`OK`。
- 下面三处临时改动各做一次，看到预期结果后改回。前两处跑上面那条测试命令：
  1. 把 Step 2 的 `os.killpg(proc.pid, signal.SIGTERM)` 临时改成 `os.killpg(proc.pid, signal.SIGKILL)`：`test_interrupted_build_leaves_no_chrome_profile` 失败，信息形如 `Lists differ: ['show-me-cdp-…'] != []`。
  2. 把 Step 1c 插入的那段临时删掉：`test_cdp_signal_closes_chrome_and_removes_profile` 的两个子测试分别失败于 `-2 != 130` 和 `-15 != 143`；`test_interrupted_build_leaves_no_chrome_profile` 也会失败。
  3. 超时路径（单测不覆盖）：把 `proc.communicate(timeout=90 * len(jobs) + 30)` 临时改成 `proc.communicate(timeout=0.3)`（比 Chrome 启动还短，一定超时），然后用 bash 跑下面的脚本。预期输出两行：`(None, 'Chrome 运行器超时')` 和 `profiles 0 chrome 0`。规划时改动前的代码在同样条件下是 `profiles 1`。

```sh
python3 - <<'EOF'
import os, runpy, subprocess, tempfile
from pathlib import Path
td = tempfile.mkdtemp(prefix="totd-"); os.environ["TMPDIR"] = td; tempfile.tempdir = None
run_jobs = runpy.run_path("skills/show-me-html/scripts/build.py")["run_jobs"]
page = Path("skills/show-me-html/tests/fixtures/minimal-shell.html").resolve()
print(run_jobs([{"url": page.as_uri()}]))
left = [x.name for x in Path(td).iterdir() if x.name.startswith("show-me-cdp-")]
print("profiles", len(left), "chrome", len(subprocess.run(["pgrep", "-f", td], capture_output=True, text=True).stdout.split()))
subprocess.run(["rm", "-rf", td])
EOF
```

- 三次临时改动都改回后：`git diff` 里 `cdp.mjs`、`build.py` 的改动与 Step 1、Step 2 一致，Step 1、Step 2 的计数仍然满足。
- 全量 → `Ran 62 tests`、`OK`。跑完后 `pgrep -f 'sigtest-|show-me-cdp-'` 无输出（没有残留的 Chrome）。

### Step 4: `probe_page.mjs` 被 SIGTERM 时行为不变

`probe_page.mjs` 原来自己处理信号，现在交给 `launch()`，退出码和清理应该与原来一样。用 bash 跑：

```sh
python3 - <<'EOF'
import os, signal, subprocess, tempfile, time
from pathlib import Path
page = "/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-eec315f-026/triage-board.html"
td = tempfile.mkdtemp(prefix="pptd-")
p = subprocess.Popen(["node", "skills/show-me-html/scripts/probe_page.mjs", page], stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True, env={**os.environ, "TMPDIR": td})
time.sleep(4)
alive = p.poll() is None
p.send_signal(signal.SIGTERM); p.communicate(timeout=30); time.sleep(0.5)
left = [x.name for x in Path(td).iterdir() if x.name.startswith("probe-page-cdp-")]
procs = subprocess.run(["pgrep", "-f", td], capture_output=True, text=True).stdout.split()
print("alive", alive, "exit", p.returncode, "profiles", len(left), "chrome", len(procs))
for pid in procs: os.kill(int(pid), signal.SIGKILL)
subprocess.run(["rm", "-rf", td])
EOF
```

页面在主检出目录的轮次 `2026-10-23-eec315f-026` 里，只读。triage-board 有 19 个控件，探针要跑 30 秒左右，4 秒时一定还在跑。

**Verify**：输出 `alive True exit 143 profiles 0 chrome 0`。规划时，改前和改后都是这一行。

### Step 5: 冻结场景轮次

MAINTENANCE.md 规定改 `scripts/build.py` 后要跑冻结场景轮次。本计划只改被打断时的收尾，重建出来的页面应该与上一轮逐字节相同。上一轮 `2026-10-23-eec315f-026` 只存在于主检出目录，用绝对路径只读；新的一轮建在你当前工作的检出里（`rounds/` 被 gitignore）。用 bash 跑：

```sh
PREV=/Users/mg/github/skills/skills/show-me-html/scenarios/rounds/2026-10-23-eec315f-026
RND=skills/show-me-html/scenarios/rounds/$(date +%F)-$(git rev-parse --short HEAD)-029
mkdir -p "$RND"
for n in status-report approach-compare code-review concept-explainer triage-board; do
  cp "$PREV/$n.html" "$RND/" && python3 skills/show-me-html/scripts/build.py "$RND/$n.html" | grep -E '^(ERROR|WARN)|自检通过'
  cmp -s "$PREV/$n.html" "$RND/$n.html" && echo "$n 与上一轮相同" || echo "$n 与上一轮不同"
done
node skills/show-me-html/scripts/probe_round.mjs "$RND" "$PREV" | grep -E '^[a-z-]+: |字体|probe\.json|截图：|Markdown 不同'
echo "exit=${PIPESTATUS[0]}"
```

**Verify**（规划时在副本上就是这些结果）：

- 五行 `自检通过。`，五行 `<场景> 与上一轮相同`。
- 探针五行 `无问题`，没有 `字体未就绪`，`exit=0`。
- `与上一轮对比：probe.json 相同`，`截图：30/30 张逐字节相同`，没有 `Markdown 不同`。

页面逐字节相同，探针又会等字体到齐（计划 028），所以截图应该直接是 30/30，不需要重跑。

## Test plan

- 新增 `test_cdp_signal_closes_chrome_and_removes_profile`：分别发 SIGINT、SIGTERM，退出码 130 / 143，配置目录和 Chrome 进程都不留。
- 新增 `test_interrupted_build_leaves_no_chrome_profile`：`build.py --snap` 跑到一半被 SIGINT，配置目录和 Chrome 进程都不留。
- 反证：`build.py` 退回 SIGKILL、`cdp.mjs` 去掉处理器，各让对应的测试失败；超时路径用临时改短的超时查一次。
- Step 4：`probe_page.mjs` 被 SIGTERM 时退出 143、零残留，与改前相同。
- Step 5：冻结场景轮次与上一轮完全相同。
- 没测的：SIGHUP；清理期间再按一次 Ctrl-C。`rmSync` 的重试（Step 1b）没有确定性的测试：竞态只在 Chrome 冷启动后立刻被关时出现，规划时在冷启动条件下验证过（见 `plans/README.md`「029 规划记录」）；执行时只查 Step 1 的计数。

## Done criteria

- [ ] Step 1、Step 2 的语法检查、格式检查和计数全部满足
- [ ] `python3 -m unittest skills.show-me-html.tests.test_build` → `Ran 62 tests`、`OK`
- [ ] 两次反证都按预期失败，超时路径输出 `(None, 'Chrome 运行器超时')` 和 `profiles 0 chrome 0`；三处临时改动都改回后 `git diff` 与 Step 1–3 一致
- [ ] Step 4 输出 `alive True exit 143 profiles 0 chrome 0`
- [ ] Step 5：五页与上一轮相同，五页 `无问题`，`exit=0`，`probe.json 相同`，30/30，没有 `Markdown 不同`
- [ ] `make check` exit 0；`git status` 只显示 Scope 里的四个文件
- [ ] 跑完后 `pgrep -f 'sigtest-|show-me-cdp-|probe-page-cdp-'` 无输出

## STOP conditions

- Drift check 有输出，且「Current state」里的引文对不上。
- 新测试在改动后仍然失败，或者反证时没有失败。
- `test_interrupted_build_leaves_no_chrome_profile` 报「构建在打断之前就结束了」，而且重跑一次仍然如此（说明这台机器跑得太快，测试的时机要重新设计）。
- Step 4 的输出不是 `alive True exit 143 profiles 0 chrome 0`。
- Step 5 有页面与上一轮不同，或者截图不是 30/30、`probe.json` 不同。不要靠重跑把它跑过去。
- 为了让检查通过，需要改 Scope 之外的文件。

## Maintenance notes

- `launch()` 现在会注册进程级的信号处理。以后若有一个进程里多次调用 `launch()`，每次都会注册一对处理器，收到信号时各自收拾自己那个 Chrome；第一个收拾完的会先 `process.exit`，其他的可能来不及。目前所有调用方都只启动一次。
- 已知的两个窄窗口，都不修：一是 Chrome 已启动、WebSocket 还没连上时收到信号，处理器里的 `exit(130/143)` 和 `launch()` 失败后调用方的 `exit(2)` 谁先到不确定；二是 `process.once`，清理期间再来一次同样的信号会走默认行为，立即退出，可能留下目录。
- `build.py` 停运行器最多多等 5 秒。正常情况下运行器收到 SIGTERM 后 1 秒内就收拾完退出。
- `rmSync` 的重试按递增间隔最多等约 1.5 秒（100、200 … 500 毫秒）。如果以后又看到 `show-me-cdp-*` / `probe-round-*` / `probe-page-cdp-*` 残留，先看目录里剩的是什么文件；如果还是 `Network Persistent State` 一类的临时文件，就把 `maxRetries` 调大。
- 新测试 `test_cdp_signal_closes_chrome_and_removes_profile` 在加重试之前，冷启动时偶尔失败于 `Lists differ: ['sigtest-…'] != []`，那就是这个竞态。以后它再偶发失败，不要放宽断言，先按上一条查剩下的文件。
- SIGHUP（关掉终端窗口）和 SIGKILL 仍然会留下配置目录；需要时可以在 `cdp.mjs` 的列表里加 `["SIGHUP", 129]`。
