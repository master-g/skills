"""把查询结果逐行写成 CSV，供 Excel 和下游脚本读取。"""

import csv
import io
from collections.abc import Iterable, Iterator, Sequence

# Excel 会把这些字符开头的单元格当公式执行
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return text


def iter_csv(header: Sequence[str], rows: Iterable[Sequence[object]]) -> Iterator[str]:
    """逐行产出 CSV 文本，第一行带 BOM，方便 Excel 识别 UTF-8。"""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(header)
    yield "﻿" + buf.getvalue()
    for row in rows:
        buf.seek(0)
        buf.truncate()
        writer.writerow([sanitize(v) for v in row])
        yield buf.getvalue()
