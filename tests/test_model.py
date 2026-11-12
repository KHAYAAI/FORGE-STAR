import sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))
import financial_model as fm  # noqa: E402

A = yaml.safe_load((ROOT / "model" / "assumptions.yaml").read_text())


def test_base_case_runs_and_hits_stage3_revenue():
    rows = fm.build(A, A["scenarios"]["base"])
    assert len(rows) == len(A["years"])
    assert 25e6 <= rows[-1]["revenue"] <= 45e6


def test_scenarios_ordered():
    rev = {k: fm.build(A, v)[-1]["revenue"] for k, v in A["scenarios"].items()}
    assert rev["low"] < rev["base"] < rev["high"]


def test_iot_margin_is_tied_to_fleet_capacity():
    base = fm.build(A, A["scenarios"]["base"])
    # too few satellites: nothing on our own network, whatever the year
    for r in base:
        if r["sats_in_service"] < A["network"]["own_network_min_sats"]:
            assert r["iot_own_network_share_pct"] == 0
    assert 0 < base[-1]["iot_own_network_share_pct"] <= 100
    compact = fm.build(A, A["scenarios"]["compact_protocol"])
    hourly = fm.build(A, A["scenarios"]["hourly_plans"])
    assert hourly[-1]["iot_own_network_share_pct"] < base[-1]["iot_own_network_share_pct"] <= compact[-1]["iot_own_network_share_pct"]
    assert hourly[-1]["ebitda"] < base[-1]["ebitda"] <= compact[-1]["ebitda"]
    # capacity doubles with the fleet
    assert abs(fm.own_network_capacity(A, 48) - 2 * fm.own_network_capacity(A, 24)) < 1e-6


def test_monthly_matches_annual_cash():
    rows = fm.build(A, A["scenarios"]["base"])
    mon = fm.monthly(A, rows)
    assert len(mon) == 12 * len(rows)
    assert abs(mon[-1]["cash_end"] - rows[-1]["cash_end"]) < 1.0


def test_hdg_ownership_rule():
    caps = fm.cap_table(A)
    assert all(c["hdg_pct"] >= A["ownership"]["hdg_minimum_pct"] for c in caps)
    for c in caps:
        assert abs(sum(c["holders"].values()) - 100) < 1e-6
