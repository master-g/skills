"""在派发项目中生成 Pi CLI 的模型清单。"""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def input_capability(value, source, basis="catalog"):
    status = {True: "supported", False: "unsupported", None: "unknown"}[value]
    return {"status": status, "source": source, "basis": basis}


def list_models(binary):
    result = subprocess.run([binary, "--list-models"], capture_output=True,
                            text=True, timeout=30, check=True)
    lines = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if result.stdout.strip().startswith("No models available"):
        return []
    if not lines or lines[0][:2] != ["provider", "model"]:
        raise ValueError("Pi 目录缺少 provider/model 表头")
    models = []
    for row in lines[1:]:
        if len(row) != len(lines[0]):
            raise ValueError("Pi 目录行与表头不匹配")
        fields = dict(zip(lines[0], row))
        models.append({"id": f"{fields['provider']}/{fields['model']}",
                       "thinking_supported": {"yes": True, "no": False}.get(fields.get("thinking")),
                       "images": {"yes": True, "no": False}.get(fields.get("images")),
                       "thinking_levels": None})
    return models


def cached_models(harness, cache):
    data = json.loads(cache.read_text())
    models = []
    if harness == "codex":
        for item in data["models"]:
            if item.get("visibility") != "list":
                continue
            levels = item.get("supported_reasoning_levels")
            modalities = item.get("input_modalities")
            models.append({"id": item["slug"],
                           "thinking_levels": [row["effort"] for row in levels] if levels is not None else None,
                           "text": "text" in modalities if isinstance(modalities, list) else None,
                           "images": "image" in modalities if isinstance(modalities, list) else None})
    else:
        for model_id, record in data["models"].items():
            info = record["info"]
            if info.get("hidden"):
                continue
            levels = info.get("reasoning_efforts")
            models.append({"id": model_id,
                           "thinking_levels": [row["id"] for row in levels] if levels is not None else None,
                           "images": None})
    return models, data.get("fetched_at")


def discover(harness):
    binary = shutil.which(harness)
    base = os.environ.get(harness.upper() + "_HOME") or Path.home() / ("." + harness)
    cache = Path(base) / "models_cache.json"
    catalog = {"entry": "headless" if harness == "pi" else "herdr-pane",
               "harness": harness, "binary": binary,
               "source": "pi --list-models" if harness == "pi" else str(cache),
               "scope": str(Path.cwd()), "observed_at": datetime.now(timezone.utc).isoformat(),
               "models": []}
    try:
        if not binary:
            raise ValueError("PATH 中未找到 " + harness)
        if harness == "pi":
            catalog["models"] = list_models(binary)
        else:
            catalog["models"], catalog["fetched_at"] = cached_models(harness, cache)
        catalog["delivery"] = {"text": {"method": "读取 brief", "source": "farm brief 协议"},
                               "local-image": {"method": None, "source": "需核对当前入口工具"}}
        for model in catalog["models"]:
            text_input = (input_capability(model.pop("text"), catalog["source"])
                          if "text" in model else input_capability(True, "文本 worker 接口", "protocol"))
            model["inputs"] = {"text": text_input,
                               "local-image": input_capability(model["images"], catalog["source"])}
        if not catalog["models"]:
            raise ValueError(harness + " 目录没有可用模型")
    except (OSError, ValueError, KeyError, AttributeError, TypeError, subprocess.SubprocessError) as error:
        catalog["error"] = str(error)
    output = Path(".farm") / (harness + "-catalog.json")
    output.parent.mkdir(exist_ok=True)
    data = json.dumps(catalog, indent=2, ensure_ascii=False)
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, delete=False) as temp:
        temp.write(data + "\n")
    Path(temp.name).replace(output)
    return catalog


def main():
    parser = argparse.ArgumentParser(description="检查当前项目可见的模型目录")
    parser.add_argument("--harness", choices=["pi", "codex", "grok"])
    args = parser.parse_args()
    names = [args.harness] if args.harness else ["pi", "codex", "grok"]
    catalogs = [discover(name) for name in names]
    print(json.dumps(catalogs[0] if args.harness else catalogs, ensure_ascii=False, indent=2))
    return 0 if any(catalog["models"] for catalog in catalogs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
