"""按当前会话和项目目录列出候选，核对主模型为 brief 选择的入口。"""
import argparse
import json
from pathlib import Path

from pair_config import selection_source
from text_plan import read_task


def entry_catalog(row, entry, harness):
    if row.get("error"):
        raise ValueError(row["error"])
    for field, label in (("launch", "启动"), ("completion", "完成信号")):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError("缺少" + label)
    if entry == "native" or (entry, harness) == ("herdr-pane", "claude"):
        return row
    cli_entries = {"herdr-pane": ("pi", "codex", "grok"), "headless": ("pi",)}
    if harness not in cli_entries.get(entry, ()):
        raise ValueError("不支持该运行位置")
    path = Path(".farm") / f"{harness}-catalog.json"
    catalog = json.loads(path.read_text())
    if catalog["harness"] != harness or catalog["scope"] != str(Path.cwd()):
        raise ValueError("请在当前项目刷新 setup-farm 清单")
    if catalog.get("error"):
        raise ValueError(catalog["error"])
    return catalog


def input_evidence(model, row, input_type, catalog):
    if input_type == "text":
        capability = {"status": "supported", "basis": "protocol", "source": "文本 worker 接口"}
        delivery = catalog.get("delivery", {}).get("text", {"method": "读取 brief", "source": "farm brief 协议"})
    else:
        capability = {"status": "unknown", "basis": "catalog", "source": "目录未声明图片输入"}
        delivery = row.get("local_image") or {}
    capability = model.get("inputs", {}).get(input_type, capability)
    verified = row.get("verified_inputs", {}).get(model["id"], {}).get(input_type)
    if verified and verified.get("method") == delivery.get("method") and verified.get("source"):
        capability = {"basis": "verified", "source": verified["source"], "status": verified["status"]}
    status = capability["status"]
    if status != "supported" or not str(capability.get("source") or "").strip():
        label = "不支持" if status == "unsupported" else "能力未知"
        raise ValueError(f"{input_type} {label}（{capability.get('source') or '缺少证据来源'}）")
    if not all(isinstance(delivery.get(k), str) and delivery[k].strip() for k in ("method", "source")):
        raise ValueError(f"缺少入口取得 {input_type} 材料的方法或证据来源")
    return {"type": input_type, "capability": capability, "delivery": delivery}


def candidates_for(row, args, source, input_type, excluded):
    entry, harness = row["entry"], row["harness"]
    if not isinstance(harness, str) or not harness.strip():
        raise ValueError("缺少 harness 名称")
    variant = args.variant
    fixed_model = None
    if args.named and [entry, harness] != args.named:
        raise ValueError("本次点名 " + " ".join(args.named))
    if "worker" in source:
        backend, sep, reference = source["worker"].partition(":")
        fixed_model, marker, level = reference.partition("#")
        if not sep or not backend or not fixed_model or (marker and not level):
            raise ValueError(f"固定映射格式错误：{source['worker']}")
        if backend != harness or (backend == "opencode" and entry != "native") or (
                backend in ("pi", "codex", "grok") and entry == "native"):
            raise ValueError(f"固定映射要求 {source['worker']} 对应的入口")
        if level and variant and variant != level:
            raise ValueError(f"固定档位 {level} 与所需档位 {variant} 冲突")
        variant = level or variant
    if args.pane and entry != "herdr-pane":
        raise ValueError("需要可见 Herdr pane")
    catalog = entry_catalog(row, entry, harness)
    models = catalog["models"]
    if fixed_model:
        ids = {model["id"] for model in models}
        if fixed_model not in ids and harness == "pi" and "/" not in fixed_model:
            matches = [mid for mid in ids if mid.rpartition("/")[2] == fixed_model]
            if not matches:
                matches = [mid for mid in ids if fixed_model.casefold() in mid.casefold()]
            if len(matches) > 1:
                raise ValueError(f"Pi 固定简称 {fixed_model} 匹配多个模型：{', '.join(sorted(matches))}")
            if matches:
                fixed_model = matches[0]
        if fixed_model not in ids:
            raise ValueError(f"目录中没有固定模型：{fixed_model}")
        if args.model and args.model != fixed_model:
            raise ValueError(f"固定模型 {fixed_model} 与所选模型 {args.model} 冲突")
    variant_input = row.get("variant_input")
    if variant and not (isinstance(variant_input, str) and variant_input.strip()):
        raise ValueError("缺少启动时指定档位的方法")
    choices = []
    requested_model = fixed_model or args.model
    matched_model = False
    input_rejected = False
    for model in models:
        model_id = model["id"]
        if not isinstance(model_id, str) or not model_id.strip():
            raise ValueError("缺少完整模型 ID")
        if requested_model and requested_model != model_id:
            continue
        matched_model = True
        levels = model.get("thinking_levels")
        if levels is not None and not isinstance(levels, list):
            raise ValueError("档位清单格式错误")
        if variant and variant not in (levels or []):
            continue
        try:
            evidence = input_evidence(model, row, input_type, catalog)
        except ValueError as error:
            excluded.append({"entry": entry, "harness": harness, "model": model_id, "error": str(error)})
            input_rejected = True
            continue
        choices.append({"input": evidence, "entry": entry, "harness": harness, "model": model_id,
                        "thinking_levels": levels, "variant": variant,
                        "variant_input": variant_input, "launch": row["launch"], "completion": row["completion"]})
    if not choices and not input_rejected:
        if matched_model:
            raise ValueError(f"匹配的模型未公布档位 {variant}")
        raise ValueError(f"目录中没有指定的模型：{args.model}" if args.model else "模型目录为空")
    return choices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--orchestrator", metavar="HOST:MODEL")
    parser.add_argument("--named", nargs="*", metavar="ENTRY/HARNESS")
    parser.add_argument("--pane", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--variant")
    parser.add_argument("--select", nargs=2, metavar=("ENTRY", "HARNESS"))
    parser.add_argument("--reason")
    args = parser.parse_args()
    try:
        brief, task, input_type = read_task(args.brief)
        session = json.loads(args.session.read_text())
        if session["scope"] != str(Path.cwd()):
            raise ValueError("会话能力来自其他项目，请重新核对")
        if not isinstance(session["entries"], list):
            raise ValueError("entries 应为入口列表")
        if args.named is not None and len(args.named) not in (0, 2):
            raise ValueError("--named 可单独使用，或给出 ENTRY HARNESS")
        if args.named is not None and not args.model:
            raise ValueError("本次点名组合需要 --model 完整模型 ID")
        source = selection_source(args.orchestrator, args.named)
        choices, excluded = [], []
        for row in session["entries"]:
            try:
                choices.extend(candidates_for(row, args, source, input_type, excluded))
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
                excluded.append({"entry": row.get("entry") if isinstance(row, dict) else None,
                                 "harness": row.get("harness") if isinstance(row, dict) else None,
                                 "error": str(error)})
        result = {"task": task, "brief": str(brief), "candidates": choices, "excluded": excluded, "source": source}
        if not choices:
            if args.named is not None or "worker" in source:
                requested = " ".join([*args.named, args.model]) if args.named is not None else source["worker"]
                detail = "请核对 excluded 中各入口的原因" if excluded else "会话清单没有入口"
                result["error"] = f"{requested} 无合格入口：{detail}，等待用户选择"
            else:
                result["error"] = "当前会话没有合格入口，请核对模型目录、启动工具和完成信号"
        elif args.select:
            if not args.model or not (args.reason or "").strip():
                raise ValueError("选择计划需要完整模型 ID 和理由")
            selected = [c for c in choices if [c["entry"], c["harness"]] == args.select]
            if len(selected) != 1:
                result["error"] = "指定组合未唯一匹配当前候选"
            else:
                result["plan"] = {**selected[0], "brief": str(brief), "task": task, "source": source, "reason": args.reason, "location": str(Path.cwd())}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int("error" in result)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"无法生成派发计划：{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
