import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ground" / "billing"))
import billing as b  # noqa: E402


def test_invoice_without_sla_miss():
    i = b.compute("Mine", "2026-11", 40, 9000, 35.0, b.Plan())
    assert i.subtotal == Decimal("140.00") and i.credit == 0 and i.total == Decimal("140.00") and i.sla_met


def test_sla_miss_gives_credit():
    i = b.compute("Freight", "2026-11", 10, 500, 85.4, b.Plan())
    assert i.sla_met is False and i.credit == Decimal("3.50") and i.total == Decimal("31.50")


def test_minimum_charge_and_resale_only():
    i = b.compute("Reserve", "2026-11", 2, 20, None, b.Plan(min_monthly=Decimal("50")))
    assert i.total == Decimal("50.00") and i.sla_met is None      # resale-only traffic: no satellite SLA


def test_month_bounds_wrap_year():
    s, e = b.month_bounds("2026-12")
    assert (s.year, s.month, e.year, e.month) == (2026, 12, 2027, 1)
