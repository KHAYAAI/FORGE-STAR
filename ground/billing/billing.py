"""FORGE STAR monthly billing: usage + SLA -> invoices.

For each customer with traffic in the month: active devices, messages, the satellite-path p95 delivery
time, the plan price, a minimum charge and an SLA credit when the p95 target is missed. Writes the
invoices table (idempotent per customer and month) and prints a summary.

Usage: PG_DSN=... python3 ground/billing/billing.py 2026-11
Defaults (no plan row): $3.50/device/month (model/assumptions.yaml), SLA 95% <= 60 min, 10% credit.
Amounts are a usage statement for finance; tax and payment terms come from the customer contract.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass
class Plan:
    price_per_device: Decimal = Decimal("3.50")
    min_monthly: Decimal = Decimal("0")
    sla_p95_min: Decimal = Decimal("60")
    sla_credit_pct: Decimal = Decimal("10")
    currency: str = "USD"


@dataclass
class Invoice:
    customer: str
    month: str
    active_devices: int
    messages: int
    sla_p95_min: float | None
    sla_met: bool | None
    subtotal: Decimal
    credit: Decimal
    total: Decimal
    currency: str


def cents(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute(customer: str, month: str, active_devices: int, messages: int, p95_min: float | None, plan: Plan) -> Invoice:
    subtotal = max(plan.price_per_device * active_devices, plan.min_monthly)
    met = None if p95_min is None else Decimal(str(p95_min)) <= plan.sla_p95_min
    credit = subtotal * plan.sla_credit_pct / 100 if met is False else Decimal("0")
    return Invoice(customer, month, active_devices, messages, p95_min, met, cents(subtotal), cents(credit),
                   cents(subtotal - credit), plan.currency)


def month_bounds(month: str):
    y, m = map(int, month.split("-"))
    start = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    return start, dt.datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=dt.timezone.utc)


def run(dsn: str, month: str) -> list[Invoice]:
    import psycopg
    start, end = month_bounds(month)
    db = psycopg.connect(dsn, autocommit=True)
    plans = {r[0]: Plan(*[Decimal(str(v)) for v in r[1:5]], r[5]) for r in db.execute(
        "SELECT customer, price_per_device, min_monthly, sla_p95_min, sla_credit_pct, currency FROM customer_plans")}
    rows = db.execute("""
        SELECT d.customer, count(DISTINCT u.device_id), count(*),
               percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM u.received_at - u.time))
                 FILTER (WHERE u.path = 'satellite') / 60
        FROM uplinks u JOIN devices d USING (device_id)
        WHERE u.time >= %s AND u.time < %s GROUP BY d.customer ORDER BY d.customer""", (start, end)).fetchall()
    out = []
    for cust, devices, msgs, p95 in rows:
        inv = compute(cust, month, devices, msgs, None if p95 is None else float(p95), plans.get(cust, Plan()))
        db.execute("""INSERT INTO invoices (customer, month, active_devices, messages, sla_p95_min, sla_met, subtotal,
                      credit, total, currency) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                      ON CONFLICT (customer, month) DO UPDATE SET active_devices=EXCLUDED.active_devices,
                      messages=EXCLUDED.messages, sla_p95_min=EXCLUDED.sla_p95_min, sla_met=EXCLUDED.sla_met,
                      subtotal=EXCLUDED.subtotal, credit=EXCLUDED.credit, total=EXCLUDED.total, created_at=now()""",
                   (inv.customer, inv.month, inv.active_devices, inv.messages, inv.sla_p95_min, inv.sla_met,
                    inv.subtotal, inv.credit, inv.total, inv.currency))
        out.append(inv)
    return out


def main():
    month = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().strftime("%Y-%m")
    invs = run(os.environ["PG_DSN"], month)
    print(f"{'Customer':28s} {'Devices':>7s} {'Msgs':>7s} {'p95 min':>8s} {'SLA':>4s} {'Total':>10s}")
    for i in invs:
        sla = "-" if i.sla_met is None else ("ok" if i.sla_met else "MISS")
        p95 = "-" if i.sla_p95_min is None else f"{i.sla_p95_min:.1f}"
        print(f"{i.customer:28s} {i.active_devices:7d} {i.messages:7d} {p95:>8s} {sla:>4s} {i.total:>7} {i.currency}")


if __name__ == "__main__":
    main()
