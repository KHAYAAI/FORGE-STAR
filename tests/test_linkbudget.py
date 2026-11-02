from forgestar.linkbudget import LINKS, fspl_db, off_nadir_deg, slant_range_km


def test_geometry():
    assert abs(slant_range_km(90) - 550) < 1e-6
    assert 1750 < slant_range_km(10) < 1900  # ~1816 km at 550 km altitude
    assert abs(off_nadir_deg(90)) < 1e-6


def test_fspl_reference():
    # 1000 km at 2 GHz ≈ 158.5 dB
    assert abs(fspl_db(1000, 2000) - 158.47) < 0.05


def test_margins_increase_with_elevation():
    for l in LINKS.values():
        assert l.margin_db(80) > l.margin_db(20)


def test_uplink_mask_sensible():
    m = LINKS["nbiot_uplink"].min_elevation(3.0)
    assert m is not None and 10 <= m <= 35
