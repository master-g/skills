"""把结算结果写成各家银行要求的定长或分隔符文件。"""

from collections.abc import Iterable

from settlekit.settlement import Settlement


def write_delimited(settlements: Iterable[Settlement], sep: str = "|") -> str:
    lines = [
        sep.join([s.merchant_id, s.settle_date.strftime("%Y%m%d"), s.currency, f"{s.net:.2f}"])
        for s in settlements
    ]
    return "\r\n".join(lines) + "\r\n"
