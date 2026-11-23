"""将各 brief 已选定的计划按派发顺序放入 worker 池。"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-j", type=int, required=True, metavar="N")
    parser.add_argument("--active", action="append", default=[], type=Path, help="已启动、待审计的 brief")
    parser.add_argument("--passed", action="append", default=[], type=Path, help="已通过审计的 brief")
    parser.add_argument("selections", nargs="+", type=Path, help="entry_plan.py 的选型结果")
    args = parser.parse_args()
    if args.j < 1:
        parser.error("并发上限至少为 1")
    queue = []
    briefs = set()
    try:
        for path in args.selections:
            result = json.loads(path.read_text())
            if "error" in result or not result.get("plan"):
                raise ValueError(f"{path} 缺少已选定的计划")
            plan = result["plan"]
            if plan["location"] != str(Path.cwd()) or plan["brief"] in briefs:
                raise ValueError(f"{path} 的项目不匹配或 brief 重复")
            briefs.add(plan["brief"])
            queue.append(plan)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"无法生成派发队列：{error}\n")
    active = {str(path.resolve()) for path in args.active}
    passed = {str(path.resolve()) for path in args.passed}
    if (active | passed) - briefs or active & passed or len(active) > args.j:
        parser.error("请核对池中 brief 的状态与并发上限")
    pending = [plan for plan in queue if plan["brief"] not in active | passed]
    print(json.dumps({"max_active": min(args.j, len(queue)), "queue": queue,
                      "ready": pending[:args.j - len(active)]},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
