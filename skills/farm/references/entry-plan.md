# 会话入口清单

在派发项目根目录为本次会话写 `.farm/session.json`。下面示例的项目、工具、模型和档位都要换成当前查询结果。会话或项目变化后重新采集。只记录可用性，不在探测时启动 worker。

```json
{
  "scope": "/absolute/project",
  "entries": [
    {
      "entry": "native",
      "harness": "opencode",
      "launch": "subagent",
      "variant_input": "subagent.model 接受 id#variant",
      "completion": "前台调用返回",
      "models": [{ "id": "demo/text", "thinking_levels": ["high"] }]
    },
    {
      "entry": "headless",
      "harness": "pi",
      "launch": "headless.sh run",
      "completion": "headless.sh wait"
    },
    {
      "entry": "herdr-pane",
      "harness": "codex",
      "error": "当前会话没有可见 Herdr pane"
    }
  ]
}
```

每个运行位置与 harness 写一行。原生入口的 models 取当前工具或当前项目原生目录；Claude CLI 的可见 pane 也要提供该 CLI 自己的目录。别名须能映射到完整 ID。工具未公布可选档位时 thinking_levels 写 null。查询失败、无法启动、缺少完成信号或运行位置不可用时把原因写入 error。

Pi、Codex、Grok CLI 由脚本读取本项目最新生成的 setup-farm 清单。先用 setup-farm 刷新可查询的入口。每次只用该入口自己的证据，CLI 的目录不能证明原生工具能选同名模型。在 variant_input 中写出该启动工具能传档位的具体参数或语法。请求指定档位时，脚本同时要求该方法和模型目录里的精确档位。派发时按此方法传值，复用 pane 时也核对当前模型与档位。

截图 brief 声明 `输入类型：local-image`。在能提供本地图片的会话入口记录 `local_image`，例如 `{"method":"worker 用 read 工具读取 brief 中的绝对路径","source":"本会话 read 工具说明"}`。只把实际能向该模型提供图像内容的工具记为取得方式。未核实时省略。原生目录的模型可提供 `inputs`，与 setup-farm 格式一致。

计划的 input 同时展示模型能力及其依据、入口提供材料的方法及其来源。目录和工具声明足以生成待确认计划。实际验过时，在该入口的 `verified_inputs` 以完整模型 ID、输入类型为两层键，值如 `{"status":"supported","method":"与本入口 method 完全相同的值","source":"本次读图报告路径"}`。同一取得方式的实测结果优先，失败可记为 `unsupported`。

按 brief 列出候选。传当前编排者在 pairs 左栏使用的 `host:model` 键，例如 Claude Code 的 `claude:opus-5.5`。需要可见 pane 时加 `--pane`。

```sh
python3 <farm>/entry_plan.py .farm/edit-brief.md --session .farm/session.json --orchestrator claude:opus-5.5
```

- 用户本次点名时加 `--named <entry> <harness> --model '<完整 ID>'`，只点名模型时用 `--named --model '<完整 ID>'`。指定档位加 `--variant '<档位>'`。
- 其余情况先读 `FARM_PAIRS` 指定的文件，未设置时读 `~/.config/farm/pairs`。在所读文件内按精确键、宿主通配、全局通配匹配。指定文件读取失败时展示路径及原因，等用户选择。用户文件无匹配或只有内置 pairs 时按任务选。
- Pi 固定简称在该入口当前目录中解析为完整 ID，优先匹配模型名，再尝试唯一的模糊匹配。多个匹配时请用户指定完整 ID。

在原命令上保留所有选型参数，加 `--select <entry> <harness> --model '<完整 ID>' --reason '<选择理由>'` 生成 plan。确认屏展示 source.kind；固定映射还展示 file、key 和 worker。variant 为 null 表示入口默认。指定组合与硬约束冲突或目录中已无该组合时，展示 error 和对应入口的 excluded 原因，等待用户选择后重新生成计划。

脚本只生成计划。启动和返工时按所选入口传入计划里的模型与档位。项目目录或工具能力在确认后有变化时重新列候选、核对并展示受影响的计划。
