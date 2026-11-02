import sys
from pathlib import Path
import pytest
pytest.importorskip("sgp4")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sim"))
import sgp4_crosscheck as x  # noqa: E402


@pytest.mark.parametrize("inc", [45.0, 97.6])
def test_orbit_plane_matches_sgp4(inc):
    r = x.compare(inc, days=3.0)
    assert r["cross_km"] < 10          # J2 nodal precession right
    assert abs(r["dalt_km"]) < 5        # only a small mean-motion definition offset
