---
name: setup-farm
description: 在派发项目中探测 Pi CLI 的模型目录，为 farm 的无头文本 worker 准备候选模型。
license: MIT
disable-model-invocation: true
---

# setup-farm

在用户准备运行 farm 的项目根目录执行 `python3 <本技能目录>/discover.py`。脚本调用当前 PATH 中的 `pi --list-models`，将查询结果写入项目的 `.farm/pi-catalog.json`，并输出同一份 JSON。再次运行可刷新。

向用户汇报入口、探测范围、时间、模型数量和完整模型 ID。Pi 的 thinking 列给出是否支持推理，未公布的逐模型档位记为未知。目录记录描述本次查询，实际派发由 farm 根据 brief 和当前会话确认。

退出码非零时展示具体原因。找不到 pi 时检查 PATH；已发现 CLI 但查询失败时，在同一项目核对目录命令。刷新失败的清单也会保存，供 farm 解释阻塞。
