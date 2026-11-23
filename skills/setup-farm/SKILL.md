---
name: setup-farm
description: 检查本机 Pi、Codex 和 Grok 的模型目录，为 farm 的文本与截图 worker 准备候选模型。
license: MIT
disable-model-invocation: true
---

# setup-farm

在派发项目根目录运行 `python3 <本技能目录>/discover.py`。默认检查三个 CLI，各自写入 `.farm/<harness>-catalog.json`，标准输出汇总结果。指定 `--harness pi|codex|grok` 可单独检查并输出一份清单。

| Harness | 目录来源                                                                                         | farm 入口       |
| ------- | ------------------------------------------------------------------------------------------------ | --------------- |
| Pi      | 当前项目运行 `pi --list-models`，组合 provider 与模型名，读取 thinking 和 images 列              | 无头或可见 pane |
| Codex   | Codex 主目录中的 models_cache.json，取 visibility 为 list 的 slug、推理档位和 input_modalities   | Herdr 可见 pane |
| Grok    | Grok 主目录中的 models_cache.json，取可见模型、reasoning_efforts；该目录未声明图片输入时记为未知 | Herdr 可见 pane |

每个模型的 inputs 按 text、local-image 分列，status 取 supported、unsupported 或 unknown。basis 和 source 记录文本接口约定或模型目录声明。清单的 delivery 说明入口如何取得材料，本地图片的具体方法在派发会话中核对。

报告每个 harness 的完整模型 ID、数量、来源和时间。缓存的 fetched_at 表示 harness 取得目录的时间，observed_at 表示本次读取时间。目录声明的图片输入能力与 worker 实际收到图片的验证分开记录。缓存可能随账号或服务配置变化，派发前在当前会话确认所选模型可用。

有可用目录时继续展示其他入口的错误。三个入口均无候选时脚本返回非零。缺少缓存时报告来源和原因；另行启动 Codex 或 Grok 刷新目录须先取得本次调用授权。
