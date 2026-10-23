---
name: storage-price-is-too-damn-high
description: 盘点 Mac 用户级磁盘占用，把缓存、构建产物和大文件按风险分档，出一份可逐项执行的清理计划。
license: MIT
disable-model-invocation: true
---

磁盘快满了。盘点用户级的磁盘占用，出一份清理计划：每一项写清大小、命令、代价和恢复途径。交付物是计划，输出后停下，等用户点选。

范围是最常见的目录和 app，逐条清单在 [references/locations.md](references/locations.md)。装了 mole（`mo`）时用它的预览补上长尾缓存和项目产物，用法与坑见 [references/mole.md](references/mole.md)。系统级缓存需要 sudo，不在范围内。命令按 zsh / bash 写。

## 1. 盘点

记录水位。Data 卷才是用户数据所在，`/` 是只读的系统卷：

```sh
df -h /System/Volumes/Data
tmutil listlocalsnapshots /
command -v mo trash docker xcrun brew
```

列出布局，本机实测约 2 分钟。`-x` 让 du 不越过挂载点：`~/Library/Developer/CoreDevice/DeviceFS` 这类 FSKit 挂载会让 du 卡进不可中断状态，`timeout` 和 `kill -9` 都无效。

```sh
du -skx ~/* ~/.[!.]* ~/.cache/* ~/Library/* \
  ~/Library/Application\ Support/* ~/Library/Containers/* \
  ~/Library/Group\ Containers/* /Applications/* \
  2>"${TMPDIR:-/tmp}/storage-du.err" | sort -rn | awk '$1 >= 1048576'
```

`storage-du.err` 里，`Mobile Documents`、`CloudStorage` 下的 `Resource deadlock avoided` 是没下载到本地的云端占位文件，不占空间；`Operation not permitted` 是终端没有完全磁盘访问权限，对应目录记为「未测」。

接着：

- 按 locations.md 测量存在的路径；≥ 1 GB 的条目再跑它的查看命令。
- 布局里出现 locations.md 没有的大目录，按其中「重定向」找所属工具。
- 装了 mole 时跑 mole.md 的「预览」，并读白名单。

**完成条件**：可用空间和本地快照数已记录；布局里每个 ≥ 1 GB 的条目（父目录由子条目代表）都对上了 locations.md 的一条、mole 清单的一项，或标为「未归类」并写出所属程序（查不到写「未知」）；locations.md 里存在的每条都有大小或「未测 + 原因」。

## 2. 分类

每个候选落进一档：

- **可再生**：写得出所属工具的清理命令或再生方式，删掉的代价只是重新下载或重新构建。写不出的进不了这一档。
- **待定**：能删，删不删取决于用户还用不用：模型、镜像、模拟器 runtime、工具链、项目产物、安装包、大 app、废纸篓、本地快照。
- **用户数据**：聊天记录、文档、照片、设备备份、虚拟机、容器卷、会话记录，以及 `~/Library/Application Support`、`Containers`、`Group Containers` 下 locations.md 没有列为缓存的目录。mole 的 Mac app 曾把仍在使用的 Quicken 的 `Application Support` 当残留删掉，连同全部备份（mole issue #1475）。这一档只报大小和 app 自己的存储管理入口。
- **受保护**：命中 mole 白名单的路径，优先于上面三档。照列大小，问用户是否仍要保留。

判定规则：

- 项目产物（`node_modules`、`target`、`build`、`dist`、`.venv` 等）只认 git 仓库里被忽略的目录，即 `git -C <仓库> check-ignore -q <路径>` 返回 0；第三方工具安装目录里的同名目录是工具本身的一部分。
- 项目产物和待定项近 7 天有写入的（`find <路径> -mtime -7 -print -quit` 有输出），标「近期在用」。
- 拿不准时放进更保守的一档：可再生 → 待定 → 用户数据。

删除方式跟着恢复途径走：

- 可再生：有所属工具命令就用它；没有的整目录 `rm -rf`，恢复途径就是再生。
- 待定：`trash`（系统自带的 `/usr/bin/trash`）移进废纸篓，恢复途径是废纸篓；空间要等清空废纸篓才释放，计划里写明。
- mole 长尾：整体运行 `mo clean`，永久删除。

**完成条件**：每个候选恰好一档；每条可再生都带具体命令；每条都写了删除方式和恢复途径。

## 3. 出计划并停下

按这个顺序输出：

1. **水位**：可用空间、本地快照数。有快照时写明：被删文件的空间要等快照过期或删除后才回来。
2. **可再生**、**待定**两张表，各按大小降序，编号连续。列：编号、项目、大小、命令、删除方式、代价与恢复。表尾写合计。「mole 长尾」一行的大小只算 `clean-list.txt` 里没被其他行覆盖的路径，并写明它与哪些行重叠（运行 `mo clean` 也会清掉那些行）。
3. **用户数据**：按大小列前十，附管理入口。
4. **受保护**、**未测**、**未归类**：每条一行原因。
5. 用户给了目标空间时，写出达到目标的最小组合，优先可再生。

du 把 APFS 克隆重复计数，表里的大小是估计，实际回收以执行后 `df` 的差值为准。

输出后停下，等用户点编号。

## 4. 执行选中项

用户点了编号并回复「确认」后才执行，只执行点到的编号：

- 按路径删除前，退出所属 app（Xcode、Simulator、IDE、浏览器）；Gradle 先 `./gradlew --stop`。
- 顺序：`mo clean` → 所属工具命令 → `rm -rf` → `trash`。`mo clean` 会清空废纸篓，必须排在所有 `trash` 之前。
- 每项执行后记一次 `df -h /System/Volumes/Data`。

**完成条件**：每个选中编号都有结果（成功、失败及输出、跳过及原因）；报告逐项的估计与实际释放，差额写出原因：废纸篓未清空、本地快照、磁盘镜像未收缩、克隆重复计数。
