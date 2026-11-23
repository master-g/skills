"""在派发项目中生成 Pi CLI 的模型清单。"""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def list_models(binary):
    result = subprocess.run([binary, "--list-models"], capture_output=True,
                            text=True, timeout=30, check=True)
    lines = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if not lines or lines[0][:2] != ["provider", "model"]:
        raise ValueError("Pi 目录缺少 provider/model 表头")
    models = []
    for row in lines[1:]:
        if len(row) != len(lines[0]):
            raise ValueError("Pi 目录行与表头不匹配")
        fields = dict(zip(lines[0], row))
        models.append({"id": f"{fields['provider']}/{fields['model']}",
                       "thinking_supported": {"yes": True, "no": False}.get(fields.get("thinking")),
                       "thinking_levels": None})
    return models


def main():
    binary = shutil.which("pi")
    catalog = {"entry": "headless", "harness": "pi", "binary": binary,
               "source": "pi --list-models", "scope": str(Path.cwd()),
               "observed_at": datetime.now(timezone.utc).isoformat(), "models": []}
    try:
        if not binary:
            raise ValueError("PATH 中未找到 pi")
        catalog["models"] = list_models(binary)
        if not catalog["models"]:
            raise ValueError("Pi 目录没有可用模型")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        catalog["error"] = str(error)
    output = Path(".farm/pi-catalog.json")
    output.parent.mkdir(exist_ok=True)
    data = json.dumps(catalog, indent=2, ensure_ascii=False)
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, delete=False) as temp:
        temp.write(data + "\n")
    Path(temp.name).replace(output)
    print(data)
    return 0 if catalog["models"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
