"""渲染并核对主模型为单个文本 brief 选择的 CLI 派发计划。"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("model", help="清单中的完整 provider/model")
    parser.add_argument("reason", help="主模型依据 brief 给出的选择理由")
    parser.add_argument("--harness", choices=["pi", "codex", "grok"], default="pi")
    parser.add_argument("--pane", action="store_true", help="在 Herdr 可见 pane 中运行")
    args = parser.parse_args()
    try:
        catalog = json.loads(Path(f".farm/{args.harness}-catalog.json").read_text())
        if catalog["harness"] != args.harness:
            raise ValueError("清单的 harness 不匹配")
        if catalog["scope"] != str(Path.cwd()):
            raise ValueError("项目已变化，请在当前项目运行 setup-farm")
        if catalog.get("error"):
            raise ValueError(catalog["error"])
        if args.model not in [item["id"] for item in catalog["models"]]:
            raise ValueError("目录中没有指定的模型：" + args.model)
        brief = args.brief.resolve()
        if brief.parent != Path.cwd() / ".farm" or not brief.name.endswith("-brief.md"):
            raise ValueError("请使用项目中的 .farm/<task>-brief.md")
        heading = brief.read_text().split("\n", 1)[0]
        if not heading.startswith("# ") or not heading[2:].strip() or not args.reason.strip():
            raise ValueError("任务标题和选择理由不能为空")
        plan = {"task": heading[2:].strip(), "brief": str(brief), "location": catalog["scope"],
                "entry": "herdr-pane" if args.pane else catalog["entry"], "harness": catalog["harness"], "model": args.model,
                "thinking": f"{'Pi' if args.harness == 'pi' else args.harness} 默认", "reason": args.reason}
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"无法生成派发计划：{error}\n")
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
