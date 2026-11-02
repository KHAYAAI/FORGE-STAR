import math
import numpy as np
from forgestar.orbits import Constellation, Site, find_passes, j2_rates, propagate_ecef, RE


def test_radius_constant():
    c = Constellation(6, 2, 45.0)
    r = np.linalg.norm(propagate_ecef(c, np.arange(0, 6000, 60.0)), axis=-1)
    assert np.allclose(r, RE + 550.0)


def test_sso_raan_drift_matches_sun():
    # A sun-synchronous orbit's node must drift ~+0.9856°/day
    raan_dot, _ = j2_rates(550.0, np.array([math.radians(97.6)]))
    assert abs(math.degrees(raan_dot[0]) * 86400 - 0.9856) < 0.05


def test_45deg_regresses():
    raan_dot, _ = j2_rates(550.0, np.array([math.radians(45.0)]))
    assert math.degrees(raan_dot[0]) * 86400 < -4  # ~-5°/day at 550 km


def test_passes_over_johannesburg():
    c = Constellation(1, 1, 45.0)
    p = find_passes(c, [Site("Jhb", "SA", -26.2, 28.0)], np.arange(0, 86400, 10.0), min_el=10)
    assert 2 <= len(p) <= 8
    assert all(2 * 60 < x.duration < 12 * 60 for x in p)
    assert all(x.min_range_km >= 549 for x in p)
