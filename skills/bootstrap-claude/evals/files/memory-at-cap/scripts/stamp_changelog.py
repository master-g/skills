"""把 CHANGELOG.md 顶部的「未发布」标题改成带版本号和日期的标题。"""

import datetime
import sys
from pathlib import Path

HEADING = "## 未发布"


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else ""
    if not version:
        sys.exit("用法: stamp_changelog.py <版本号>")
    path = Path("CHANGELOG.md")
    text = path.read_text(encoding="utf-8")
    if HEADING not in text:
        sys.exit("CHANGELOG.md 里没有「未发布」一节")
    stamped = f"{HEADING}\n\n## {version} ({datetime.date.today().isoformat()})"
    path.write_text(text.replace(HEADING, stamped, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
