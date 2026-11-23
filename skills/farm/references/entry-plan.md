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

按 brief 列出候选。可见 pane 是硬约束时加 `--pane`，用户点名模型或档位时加 `--model '<完整 ID>'` 或 `--variant '<档位>'`。指定入口或显式 pair 只从相应入口选。输出的 excluded 说明被排除的原因。

```sh
python3 <farm>/entry_plan.py .farm/edit-brief.md --session .farm/session.json
```

在同一命令上保留全部约束，加 `--select <entry> <harness> --model '<完整 ID>' --reason '<选择理由>'` 取得确认屏使用的 plan。variant 为 null 表示使用入口默认。脚本只生成计划；启动和返工时按所选入口传入计划里的模型与档位。项目目录或工具能力在确认后有变化时重新列候选、核对并展示受影响的计划。
