"""汇总一个商户一天的交易，算出应结金额。"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal


@dataclass(frozen=True)
class Txn:
    merchant_id: str
    amount: Decimal
    fee: Decimal
    currency: str


@dataclass(frozen=True)
class Settlement:
    merchant_id: str
    settle_date: date
    currency: str
    gross: Decimal
    fee: Decimal

    @property
    def net(self) -> Decimal:
        return (self.gross - self.fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def settle(merchant_id: str, settle_date: date, txns: list[Txn]) -> Settlement:
    currencies = {t.currency for t in txns}
    if len(currencies) > 1:
        raise ValueError(f"{merchant_id} 在 {settle_date} 有多个币种: {sorted(currencies)}")
    return Settlement(
        merchant_id=merchant_id,
        settle_date=settle_date,
        currency=currencies.pop() if currencies else "CNY",
        gross=sum((t.amount for t in txns), Decimal("0")),
        fee=sum((t.fee for t in txns), Decimal("0")),
    )
