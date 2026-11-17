from datetime import date
from decimal import Decimal

import pytest

from settlekit.settlement import Txn, settle


def test_net_rounds_half_even():
    txns = [Txn("M1001", Decimal("10.005"), Decimal("0"), "CNY")]
    assert settle("M1001", date(2026, 11, 1), txns).net == Decimal("10.00")


def test_mixed_currency_rejected():
    txns = [
        Txn("M1001", Decimal("1"), Decimal("0"), "CNY"),
        Txn("M1001", Decimal("1"), Decimal("0"), "HKD"),
    ]
    with pytest.raises(ValueError):
        settle("M1001", date(2026, 11, 1), txns)
