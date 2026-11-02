import sys
from pathlib import Path
import pytest
import yaml
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "readiness"))
import tracker as t  # noqa: E402


def test_dependencies_push_start():
    s = t.schedule([{"id": "a", "start": 0, "months": 3}, {"id": "b", "start": 1, "months": 2, "depends": ["a"]}])
    assert s["b"]["start"] == 3 and s["b"]["end"] == 5 and t.critical_path(s, "b") == ["a", "b"]


def test_cycle_detected():
    with pytest.raises(ValueError, match="cycle"):
        t.schedule([{"id": "a", "start": 0, "months": 1, "depends": ["b"]}, {"id": "b", "start": 0, "months": 1, "depends": ["a"]}])


def test_real_plan_is_valid_and_fast_track_is_faster():
    cfg = yaml.safe_load((ROOT / "readiness" / "readiness.yaml").read_text())
    base = t.schedule(cfg["items"])["V1"]["end"]
    fast = t.schedule(t.apply(cfg["items"], cfg["scenarios"]["fast_track"]))["V1"]["end"]
    assert fast < base
