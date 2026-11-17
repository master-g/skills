import os

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


def test_orders_table_has_expected_columns():
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        cols = conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'orders'")
        ).scalars()
        assert {"id", "customer_name", "created_at"} <= set(cols)
