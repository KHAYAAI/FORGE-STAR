from dataclasses import replace

from forgestar.capacity import Capacity
from forgestar.linkbudget import (LINKS, cos_beam_gain_dbi, fspl_db, half_beam_for_gain_deg, isoflux_edge_gain_dbi,
                                  off_nadir_deg, slant_range_km)


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


def test_downlink_sets_the_mask():
    # the review finding: devices must hear the downlink first, and it closes later than the uplink
    up, dn = LINKS["nbiot_uplink"].min_elevation(3.0), LINKS["nbiot_downlink"].min_elevation(3.0)
    assert dn > up


def test_beam_gain_physics():
    # a +/-30 degree beam has about 9.7 dBi at 80% efficiency, never 14 dBi
    assert abs(cos_beam_gain_dbi(30.0) - 9.7) < 0.1
    assert abs(half_beam_for_gain_deg(cos_beam_gain_dbi(25.0)) - 25.0) < 1e-6
    assert cos_beam_gain_dbi(20.0) > cos_beam_gain_dbi(40.0)
    assert 5.0 < isoflux_edge_gain_dbi(20.0) < 10.0


def test_all_links_have_consistent_gain():
    for key, l in LINKS.items():
        assert l.gain_is_consistent(), f"{key}: {l.sat_gain_dbi} dBi exceeds {l.gain_limit_dbi():.1f} dBi for its beam"
    bad = replace(LINKS["nbiot_uplink"], rx_gain_dbi=14.0)
    assert not bad.gain_is_consistent()


def test_capacity_model():
    c = Capacity()
    assert abs(c.seconds_per_message - 3.2) < 1e-9
    assert abs(c.messages_per_second - 6.0) < 1e-9
    assert replace(c, deep_coverage_factor=4.0).messages_per_second == c.messages_per_second / 4
    assert replace(c, carriers=4).messages_per_day(0.5) == 4 * c.messages_per_day(0.5)
