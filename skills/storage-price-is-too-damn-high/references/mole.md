# mole 辅助

mole（`mo`）在本技能里只做预览，删除按计划逐条执行。子命令和参数以 `mo <命令> --help` 为准；下面是 `--help` 里查不到的行为，在 mole 1.61.0 上核实。

## 预览

- `mo clean --dry-run < /dev/null`：本机约 80 秒，非终端下照常运行。终端输出里 `→` 是会清理的项，`⊙` 只是提示（Docker、Gradle、Android 镜像等大头），`◎` 是跳过。逐条清单写在 `~/.config/mole/clean-list.txt`，按分类分节，每行 `路径  # 大小`，解析它比解析终端输出稳。
- `mo purge --dry-run < /dev/null`：列出扫描根下的全部候选，交互模式下默认不选的近 7 天项也在里面，且不显示修改时间。扫描根在 `~/.config/mole/purge_paths`。
- `mo installer --dry-run < /dev/null`：列出下载目录等处的安装包。
- 系统级缓存的预览会提示要 `sudo -v`，照抄进计划的「未测」。
- 目录布局用 SKILL.md「盘点」里的 `du -skx`。`mo analyze` 不跳过挂载点：本机扫 `~/Library` 时进了 CoreDevice 的 `DeviceFS`，进程卡在不可中断状态，`timeout` 和 `kill -9` 都无效。

## 白名单

`~/.config/mole/whitelist` 每行一个路径或通配，是用户明确要保留的东西。命中的条目在计划里归入「受保护」。

## 执行时的坑

- `mo clean` 一次清掉预览里全部 `→` 项，不能按分类挑；删除是永久的（`rm -rf`），并且默认清空废纸篓。非终端下它不等确认直接开始，sudo 凭据还在缓存时连系统级一起清，所以运行前先 `sudo -k`。它在计划里只占一条「mole 长尾」，用户看过 `clean-list.txt` 并选中这条才运行；用户想保留废纸篓时，先在 `mo clean --whitelist` 里勾选 Trash。执行顺序见 SKILL.md 的「执行选中项」。
- `mo purge --yes` 永久删除全部候选，而候选里有误报：本机实测把 Ghidra 安装目录里的 `pypkg/dist`（工具自带的 Python 包）也列成了构建产物。项目产物按 SKILL.md「分类」的判定规则逐条筛，再逐条 `trash`。
