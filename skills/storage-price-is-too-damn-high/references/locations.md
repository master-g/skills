# 常见位置

按领域分组。每条：位置，档位，查看或清理命令，代价与注意。档位的定义在 SKILL.md 的「分类」。路径是默认位置，被挪走时以所属工具报告的为准，见「重定向」。mole 的 `mo clean` 已覆盖的长尾小缓存不在这里重复。

## 重定向

缓存和产物常被配置挪到别处。布局里出现陌生的大目录时，按下面的顺序找所属工具：

- Rust：`~/.cargo/config.toml` 的 `build-dir`、`target-dir`（共享构建目录常有几十 GB），环境变量 `CARGO_TARGET_DIR`、`CARGO_HOME`、`RUSTUP_HOME`
- Go：`go env GOCACHE GOMODCACHE`
- Node：`npm config get cache`、`pnpm store path`、`yarn cache dir`
- Python：`uv cache dir`、`pip cache dir`；Hugging Face：`HF_HOME`、`HF_HUB_CACHE`
- 其他：`GRADLE_USER_HOME`、`OLLAMA_MODELS`、`XDG_CACHE_HOME`
- 环境变量用用户的登录 shell 查：`"$(dscl . -read ~ UserShell | awk '{print $2}')" -lic env`。agent 所在 shell 的 `$SHELL` 可能是 zsh，而用户的登录 shell 是 fish，配置不是同一份。
- 仍查不到时搜配置：`grep -rl '<目录名>' ~/.config ~/.cargo ~/.zshrc ~/.zprofile ~/.bashrc`

## Xcode 与模拟器

- `~/Library/Developer/Xcode/DerivedData`：可再生。先退出 Xcode，整目录删；代价是下次全量构建。
- 不可用的模拟器设备：可再生。`xcrun simctl delete unavailable`。
- 模拟器 runtime：待定。存放在系统管理的安全存储里，du 看不到，`xcrun simctl runtime list` 给出每个的大小和合计。只通过 `xcrun simctl runtime delete` 删，先加 `--dry-run`；`--unusable`、`--outdated`、`--notUsedSinceDays <天数>` 可按条件选。每个 iOS runtime 约 8 GB，重新下载。
- `~/Library/Developer/CoreSimulator/Devices`：待定。`xcrun simctl erase <设备>` 会清掉模拟器里的 app 和数据。
- `~/Library/Developer/Xcode/iOS DeviceSupport`（及 watchOS、tvOS）：待定。保留仍在调试的设备的系统版本；连接设备时重新生成，耗时较长。
- `~/Library/Developer/Xcode/Archives`：待定。里面的 dSYM 用来符号化线上崩溃，已发布版本的归档由用户决定。

## Android 与 JVM

- `~/.gradle/caches`：可再生。先 `./gradlew --stop`；Gradle 自带按最近使用时间的自动清理，整删的代价是所有依赖重新下载，网络慢的用户常把它加进 mole 白名单。
- `~/.gradle/wrapper/dists`：可再生。保留项目在用的 Gradle 版本。
- `~/.m2/repository`：可再生。代价是重新下载。
- `~/.konan`：可再生。Kotlin/Native 的工具链和依赖，下次构建重新下载。
- `~/Library/Android/sdk/system-images`、`~/.android/avd`：待定。用 Android Studio 的 SDK Manager 和 Device Manager 删。
- `~/Library/Android/sdk/ndk/<版本>`：待定。保留项目 `ndkVersion` 指定的版本。

## JavaScript

- `~/.npm`：可再生。`npm cache clean --force`；其中 `_npx` 是 npx 下载过的包，可整目录删。
- pnpm store：可再生。`pnpm store prune` 只删没被任何项目引用的包。
- Yarn：可再生。`yarn cache clean`。
- Bun：可再生。`bun pm cache rm`。
- `~/.nvm/versions/node/<版本>`：待定。`nvm uninstall <版本>`，保留项目 `.nvmrc` 指定的版本。

## Python

- pip：可再生。`pip cache purge`。
- uv：可再生。`uv cache prune` 只删用不到的条目，`uv cache clean` 全删。
- conda：可再生。`conda clean --all`。

## Rust 与 Go

- Cargo 的 `build-dir` / `target-dir`：可再生。整目录删；共享目录被所有项目共用，代价是全部重新编译。
- `~/.cargo/registry`、`~/.cargo/git`：可再生。代价是重新下载依赖。
- `~/.rustup/toolchains`：待定。`rustup toolchain list` 查看，`rustup toolchain uninstall <名称>` 删；保留各项目 `rust-toolchain.toml` 指定的版本。
- Go：可再生。`go clean -cache`、`go clean -modcache`。

## 项目产物

- git 仓库里被忽略的 `node_modules`、`target`、`build`、`dist`、`.venv`、`.next`、`.astro` 等：待定。判定见 SKILL.md 的「分类」；装了 mole 时候选来自 `mo purge --dry-run`，逐条筛过再删，用 `trash`。

## 容器与虚拟机

- Docker / OrbStack：先 `docker system df -v`，需要引擎在运行；引擎没运行时只记磁盘镜像的大小，分项写「未测」，启动引擎由用户决定。
  - 构建缓存：可再生。`docker builder prune`。
  - 悬空镜像：可再生。`docker image prune`。
  - 没被容器使用的镜像：待定。`docker image prune -a`，代价是重新拉取。
  - 已停止的容器：待定。`docker container prune`。
  - 卷：用户数据，数据库等状态都在卷里。只删用户点名的卷：`docker volume rm <名称>`。
  - 磁盘镜像：OrbStack 的数据在 `~/Library/Group Containers/HUAQ24HBR6.dev.orbstack/data`，删了容器里的数据会自动收缩；Docker Desktop 的 `Docker.raw` 是稀疏文件，用 `du -h` 看实际占用，`ls -l` 显示的是上限。
- UTM、Parallels、VMware 的虚拟机（`*.utm`、`*.pvm`、`*.vmwarevm`）：用户数据。

## Homebrew

- `brew cleanup`：可再生。先 `brew cleanup --dry-run` 看清单；`--prune=all` 连同全部下载缓存一起删。
- `brew autoremove`：待定。删不再被依赖的包，先 `--dry-run`。

## AI 模型与编码工具

- Hugging Face `~/.cache/huggingface/hub`：待定。`hf cache ls` 查看、`hf cache rm <id>` 删（旧版 CLI 是 `huggingface-cli scan-cache` / `delete-cache`，以 `--help` 为准）；模型重新下载动辄几 GB。
- Ollama `~/.ollama/models`：待定。`ollama list` 查看，`ollama rm <模型>` 删，两者都要 ollama 服务在运行；没运行时只记目录大小。
- LM Studio `~/.lmstudio/models`：待定。在 app 里删。
- Claude Code `~/.claude`、Codex `~/.codex`、Cursor `~/.cursor`：用户数据，主要是会话记录。Claude Code 按 `cleanupPeriodDays`（默认 30 天）自动删旧会话。

## 常用 app

- 浏览器缓存（Chrome、Safari、Edge、Firefox）：可再生。mole 长尾已覆盖；没装 mole 时在浏览器设置里清。浏览器的 `Application Support` 目录是配置文件（书签、密码、扩展），属于用户数据。
- 无头 Chrome 的临时 profile `~/Library/Application Support/Google/Chrome-headless/scoped_dir*`：待定。无头 Chrome 每次启动建一个，进程被强杀时留下，本机实测 153 个、2.1 GB。`pgrep -f -- --headless` 没输出时再 `trash`。同名的 `~/Library/Caches/Google/Chrome-headless` 是缓存，mole 长尾已覆盖。
- 微信、QQ、企业微信、飞书 / Lark、钉钉、WPS、Telegram、Slack、Discord、网易云音乐：用户数据。数据多在 `~/Library/Containers/<bundle id>` 或 `~/Library/Application Support/<app>`，用 app 内的存储空间管理或清除缓存。
- Steam `~/Library/Application Support/Steam/steamapps`：待定。在 Steam 里卸载游戏。
- `/Applications` 和 `~/Applications` 里的大 app：待定。`mdls -name kMDItemLastUsedDate <app 路径>` 看最近使用时间；卸载由用户在 Finder 或 `mo uninstall` 里做，本技能只列出。

## 系统与杂项

- 本地 Time Machine 快照：待定。`tmutil listlocalsnapshots /` 查看；`tmutil deletelocalsnapshots <日期>` 删除后，被删文件的空间才真正释放，同时失去对应的本地还原点。
- 废纸篓 `~/.Trash`：待定。清空后不可恢复，列出最大的几项给用户看。
- `~/Downloads` 里的安装包（`.dmg`、`.pkg`、`.iso`、`.xip`，以及安装用的 `.zip`）：待定。装了 mole 时用 `mo installer --dry-run` 列出。
- `~/Downloads` 里的其他大文件：用户数据。
- iPhone / iPad 备份 `~/Library/Application Support/MobileSync/Backup`：用户数据。在 Finder 的设备页「管理备份」里删。
- 信息附件 `~/Library/Messages/Attachments`、照片图库、`~/Library/Mail`：用户数据。用系统设置的「储存空间」或对应 app 管理。
- `~/Library/Developer/CoreDevice`：跳过，里面的 `DeviceFS` 是挂载点。
- 用户临时目录 `$TMPDIR`（`/var/folders/` 下的 `T`）：不在家目录里，布局的 du 测不到，单独 `du -skx "$TMPDIR"` 记总量。条目常有几万个，`"$TMPDIR"/*` 会超出参数长度；`du -d 1` 只列子目录，顶层的大文件用 `find "$TMPDIR" -maxdepth 1 -type f -size +100M` 找。
  - Instruments 录制残留 `instruments*.ktrace`：待定。录制时写的原始 trace，本机实测 3 天积累了 25 个、36.5 GB，mole 不清。已另存的 `.trace` 文档不受影响，没另存的录制删掉就没了。`pgrep -x Instruments` 和 `pgrep -f xctrace` 都没输出时再 `trash`。
  - 其余条目多是运行中程序的临时文件，按文件名前缀找所属程序，查不到的记为「未归类」。
