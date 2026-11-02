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
