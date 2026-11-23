"""读取 farm 的现有映射格式，供预检和计划共用。"""
import os
from pathlib import Path


def load_pairs():
    if override := os.environ.get("FARM_PAIRS"):
        path, kind = Path(override), "FARM_PAIRS"
    else:
        path, kind = Path.home() / ".config/farm/pairs", "user"
        if not path.exists():
            path, kind = Path(__file__).with_name("pairs"), "builtin"
    pairs = []
    for line in path.read_text().splitlines():
        line = "".join(line.split())
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            pairs.append({"orchestrator": key, "worker": value})
    return kind, str(path.absolute()), pairs


def selection_source(orchestrator, named):
    if named is not None:
        return {"kind": "named"}
    kind, path, pairs = load_pairs()
    if kind != "builtin" and pairs:
        if not orchestrator or ":" not in orchestrator or not all(orchestrator.split(":", 1)):
            raise ValueError(f"请提供 --orchestrator host:model 以匹配 {path}")
        host = orchestrator.partition(":")[0]
        for key in (orchestrator, host + ":*", "*"):
            for pair in pairs:
                if pair["orchestrator"] == key:
                    return {"kind": kind, "file": path, "key": key, "worker": pair["worker"]}
    return {"kind": "task", "file": path}
