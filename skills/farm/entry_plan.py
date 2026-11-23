"""按当前会话和项目目录列出候选，核对主模型为 brief 选择的入口。"""
import argparse
import json
from pathlib import Path

from text_plan import read_task


def entry_models(row, entry, harness):
    if row.get("error"):
        raise ValueError(row["error"])
    for field, label in (("launch", "启动"), ("completion", "完成信号")):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError("缺少" + label)
    if entry == "native" or (entry, harness) == ("herdr-pane", "claude"):
        return row["models"]
    cli_entries = {"herdr-pane": ("pi", "codex", "grok"), "headless": ("pi",)}
    if harness not in cli_entries.get(entry, ()):
        raise ValueError("不支持该运行位置")
    path = Path(".farm") / f"{harness}-catalog.json"
    catalog = json.loads(path.read_text())
    if catalog["harness"] != harness or catalog["scope"] != str(Path.cwd()):
        raise ValueError("请在当前项目刷新 setup-farm 清单")
    if catalog.get("error"):
        raise ValueError(catalog["error"])
    return catalog["models"]


def candidates_for(row, args):
    entry, harness = row["entry"], row["harness"]
    if not isinstance(harness, str) or not harness.strip():
        raise ValueError("缺少 harness 名称")
    if args.pane and entry != "herdr-pane":
        raise ValueError("需要可见 Herdr pane")
    models = entry_models(row, entry, harness)
    variant_input = row.get("variant_input")
    if args.variant and not (isinstance(variant_input, str) and variant_input.strip()):
        raise ValueError("缺少启动时指定档位的方法")
    choices = []
    matched_model = False
    for model in models:
        model_id = model["id"]
        if not isinstance(model_id, str) or not model_id.strip():
            raise ValueError("缺少完整模型 ID")
        if args.model and args.model != model_id:
            continue
        matched_model = True
        levels = model.get("thinking_levels")
        if levels is not None and not isinstance(levels, list):
            raise ValueError("档位清单格式错误")
        if args.variant and args.variant not in (levels or []):
            continue
        choices.append({"entry": entry, "harness": harness, "model": model_id,
                        "thinking_levels": levels, "variant": args.variant,
                        "variant_input": variant_input, "launch": row["launch"], "completion": row["completion"]})
    if not choices:
        if matched_model:
            raise ValueError(f"匹配的模型未公布档位 {args.variant}")
        raise ValueError(f"目录中没有指定的模型：{args.model}" if args.model else "模型目录为空")
    return choices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--pane", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--variant")
    parser.add_argument("--select", nargs=2, metavar=("ENTRY", "HARNESS"))
    parser.add_argument("--reason")
    args = parser.parse_args()
    try:
        brief, task = read_task(args.brief)
        session = json.loads(args.session.read_text())
        if session["scope"] != str(Path.cwd()):
            raise ValueError("会话能力来自其他项目，请重新核对")
        if not isinstance(session["entries"], list):
            raise ValueError("entries 应为入口列表")
        choices, excluded = [], []
        for row in session["entries"]:
            try:
                choices.extend(candidates_for(row, args))
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
                excluded.append({"entry": row.get("entry") if isinstance(row, dict) else None,
                                 "harness": row.get("harness") if isinstance(row, dict) else None,
                                 "error": str(error)})
        result = {"task": task, "brief": str(brief), "candidates": choices, "excluded": excluded}
        if not choices:
            result["error"] = "当前会话没有合格入口，请核对模型目录、启动工具和完成信号"
        elif args.select:
            if not args.model or not (args.reason or "").strip():
                raise ValueError("选择计划需要完整模型 ID 和理由")
            selected = [c for c in choices if [c["entry"], c["harness"]] == args.select]
            if len(selected) != 1:
                result["error"] = "指定组合未唯一匹配当前候选"
            else:
                result["plan"] = {**selected[0], "reason": args.reason, "location": str(Path.cwd())}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int("error" in result)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"无法生成派发计划：{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
