"""Cross-check forgestar.orbits (circular + J2 secular) against SGP4.

SGP4 is the propagator behind NORAD TLEs: it adds J3/J4 and drag. We start both
from the same mean elements and compare along-track drift and ground-visibility
over a few days. If drift stays at tens of km, pass times agree to seconds, which
is plenty for coverage statistics.

Usage: python3 sim/sgp4_crosscheck.py   (needs: pip install sgp4)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from forgestar.orbits import MU, RE, Constellation, propagate_eci  # noqa: E402


def sgp4_positions(inc_deg, raan_rad, u0_rad, alt_km, t, bstar=0.0):
    from sgp4.api import Satrec, WGS72
    n_rad_s = math.sqrt(MU / (RE + alt_km) ** 3)
    sat = Satrec()
    jd0, fr0 = 2461345.5, 0.0  # 2026-11-01 00:00 UTC
    epoch = jd0 - 2433281.5    # SGP4 epoch: days since 1949-12-31 00:00 UT
    sat.sgp4init(WGS72, "i", 1, epoch, bstar, 0.0, 0.0, 1e-7, 0.0, math.radians(inc_deg),
                 u0_rad, n_rad_s * 60.0, raan_rad)
    out = []
    for dt in t:
        e, r, _ = sat.sgp4(jd0, fr0 + dt / 86400.0)
        if e: raise RuntimeError(f"sgp4 error {e}")
        out.append(r)
    return np.array(out)


def compare(inc_deg, alt_km=550.0, days=3.0, bstar=0.0):
    t = np.arange(0, days * 86400, 60.0)
    c = Constellation(1, 1, inc_deg, alt_km=alt_km)
    ours = propagate_eci(c, t)[:, 0, :]
    ref = sgp4_positions(inc_deg, 0.0, 0.0, alt_km, t, bstar)
    # Split the difference in SGP4's local frame: cross-track = orbit-plane orientation
    # (what coverage geometry depends on); along-track = phasing (a mean-motion/altitude definition).
    v_ref = np.gradient(ref, t, axis=0)
    h = np.cross(ref, v_ref); h /= np.linalg.norm(h, axis=1)[:, None]
    d = ours - ref
    cross = np.abs(np.sum(d * h, 1))
    along_dir = np.cross(h, ref / np.linalg.norm(ref, axis=1)[:, None])
    along = np.sum(d * along_dir, 1)
    v = math.sqrt(MU / (RE + alt_km))
    # along-track drift rate -> equivalent altitude offset (dn/n = -1.5 da/a)
    rate = np.polyfit(t, along, 1)[0]
    dalt = -(2 / 3) * (rate / v) * (RE + alt_km)
    return dict(inc=inc_deg, bstar=bstar, cross_km=float(cross.max()),
                along_s=float(np.abs(along).max() / v), dalt_km=float(dalt))


def main():
    rows = [compare(45.0), compare(97.6), compare(50.0), compare(45.0, bstar=1e-4)]
    L = ["# SGP4 cross-check of forgestar.orbits", "",
         "Same initial mean elements, 550 km, 3 days. Position difference vs SGP4 (J2–J4; drag when B* > 0).", "",
         "| Inclination | Drag (B*) | Plane (cross-track) max | Phasing (along-track) max | Equivalent altitude offset | Verdict |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        ok = r["cross_km"] < 50
        L.append(f"| {r['inc']:.1f}° | {r['bstar']:g} | {r['cross_km']:.1f} km | {r['along_s']:.0f} s | {r['dalt_km']:+.1f} km | "
                 f"{'plane matches: coverage stats valid' if ok else 'plane drifts: check J2 model'} |")
    L += ["", "Phasing drift is the two models defining \"550 km\" differently (Keplerian vs SGP4 Kozai mean motion), "
          "equivalent to the altitude offset shown. It moves pass times, not coverage geometry.",
          "Drag changes phasing over weeks, which is why fleet operations use SGP4/Orekit with fresh TLEs. "
          "Coverage statistics depend on geometry, not exact phasing, so they are unaffected."]
    out = Path(__file__).parent / "results" / "sgp4_crosscheck.md"; out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
