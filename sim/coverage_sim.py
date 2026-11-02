"""FORGE STAR coverage and revisit simulation.

First-order but physical: circular Walker-delta constellations, spherical Earth,
Earth rotation, J2 nodal precession ignored (it shifts planes together and barely
changes revisit statistics over one day). Replaces the hand estimates in
docs/strategy.md section 06. Upgrade path: Orekit (J2, drag) then OpenSN (network).

Usage:  python3 sim/coverage_sim.py                    # 20° min elevation (NB-IoT NTN)
        MIN_ELEV_DEG=10 python3 sim/coverage_sim.py    # 10° (AIS, optimistic IoT)
Writes sim/results/coverage_elevNN.md and coverage_by_site_elevNN.csv
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

RE = 6371.0           # km
MU = 398600.4418      # km^3/s^2
OMEGA_E = 7.2921159e-5  # rad/s

# Ground points: where FORGE STAR customers are. (name, region, lat, lon)
SITES = [
    ("Johannesburg", "SA", -26.2, 28.0),
    ("Cape Town", "SA", -33.9, 18.4),
    ("SA EEZ south (Agulhas)", "SA", -38.0, 22.0),
    ("Marion Island EEZ", "SA", -46.9, 37.7),
    ("Windhoek", "SADC", -22.6, 17.1),
    ("Lusaka", "SADC", -15.4, 28.3),
    ("Dar es Salaam", "SADC", -6.8, 39.3),
    ("Kinshasa", "Africa", -4.3, 15.3),
    ("Nairobi", "Africa", -1.3, 36.8),
    ("Lagos", "Africa", 6.5, 3.4),
    ("Dakar", "Africa", 14.7, -17.4),
    ("Cairo", "Africa", 30.0, 31.2),
    ("Tunis", "Africa", 36.8, 10.2),
]

# Constellations to test: (label, total sats, planes, inclination deg)
CONFIGS = [
    ("1 sat SSO (rideshare demo)", 1, 1, 97.6),
    ("2 sats SSO", 2, 1, 97.6),
    ("6 sats 45°", 6, 2, 45.0),
    ("6 sats SSO", 6, 3, 97.6),
    ("12 sats 45°", 12, 3, 45.0),
    ("12 sats SSO", 12, 4, 97.6),
    ("24 sats 45°", 24, 4, 45.0),
    ("24 sats mixed 45°+SSO", 24, 4, None),
    ("36 sats 45°", 36, 6, 45.0),
    ("48 sats 45°", 48, 6, 45.0),
    ("48 sats mixed 45°+SSO", 48, 6, None),
    ("80 sats 50°", 80, 8, 50.0),
    ("120 sats 50°", 120, 10, 50.0),
    ("150 sats 50°", 150, 10, 50.0),
]

ALT_KM = 550.0
import os
MIN_ELEV_DEG = float(os.environ.get("MIN_ELEV_DEG", 20.0))   # NB-IoT NTN user link; AIS works lower (~10°)
DAYS = 2.0
STEP_S = 20.0


def walker(n: int, planes: int, inc_deg: float | None, f: int = 1):
    """Return arrays (inc, raan, phase0) for a Walker-delta i:n/p/f. None inc = half 45°, half SSO."""
    per = n // planes
    incs, raans, phases = [], [], []
    for p in range(planes):
        if inc_deg is None:
            inc = 45.0 if p % 2 == 0 else 97.6
        else:
            inc = inc_deg
        for k in range(per):
            incs.append(math.radians(inc))
            raans.append(2 * math.pi * p / planes)
            phases.append(2 * math.pi * k / per + 2 * math.pi * f * p / n)
    extra = n - per * planes  # put leftovers in plane 0
    for k in range(extra):
        incs.append(math.radians(inc_deg or 45.0)); raans.append(0.0)
        phases.append(2 * math.pi * (k + 0.5) / max(per, 1))
    return np.array(incs), np.array(raans), np.array(phases)


def visibility(cfg, t):
    _, n, planes, inc = cfg
    r = RE + ALT_KM
    w = math.sqrt(MU / r**3)
    i, O, u0 = walker(n, planes, inc)
    u = u0[None, :] + w * t[:, None]                      # (T,N) argument of latitude
    x = r * (np.cos(O) * np.cos(u) - np.sin(O) * np.sin(u) * np.cos(i))
    y = r * (np.sin(O) * np.cos(u) + np.cos(O) * np.sin(u) * np.cos(i))
    z = r * (np.sin(u) * np.sin(i))
    th = OMEGA_E * t[:, None]                             # ECI -> ECEF
    xe = np.cos(th) * x + np.sin(th) * y
    ye = -np.sin(th) * x + np.cos(th) * y
    sat = np.stack([xe, ye, z], -1)                       # (T,N,3)
    lat = np.radians([s[2] for s in SITES]); lon = np.radians([s[3] for s in SITES])
    up = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)  # (P,3)
    g = RE * up
    d = sat[:, None, :, :] - g[None, :, None, :]          # (T,P,N,3)
    rng = np.linalg.norm(d, axis=-1)
    sin_el = np.einsum("tpnk,pk->tpn", d, up) / rng
    return (sin_el >= math.sin(math.radians(MIN_ELEV_DEG))).any(-1)  # (T,P)


def gaps(vis_col, step):
    """Return list of outage lengths (s) for one site, treating the series as periodic-free."""
    out, run = [], 0
    for v in vis_col:
        if v:
            if run: out.append(run * step)
            run = 0
        else:
            run += 1
    if run: out.append(run * step)
    return out


def main():
    t = np.arange(0, DAYS * 86400, STEP_S)
    res_dir = Path(__file__).parent / "results"; res_dir.mkdir(exist_ok=True)
    rows = []
    for cfg in CONFIGS:
        vis = visibility(cfg, t)
        for j, (name, region, lat, lon) in enumerate(SITES):
            g = gaps(vis[:, j], STEP_S)
            rows.append(dict(config=cfg[0], sats=cfg[1], site=name, region=region,
                             coverage_pct=round(100 * vis[:, j].mean(), 1),
                             mean_gap_min=round(np.mean(g) / 60, 1) if g else 0.0,
                             max_gap_min=round(max(g) / 60, 1) if g else 0.0))
        print(f"done {cfg[0]}")
    with open(res_dir / f"coverage_by_site_elev{MIN_ELEV_DEG:.0f}.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=rows[0].keys()); wr.writeheader(); wr.writerows(rows)

    # Regional summary: worst site in each region (that is what a customer SLA has to promise)
    lines = ["# Coverage simulation results", "",
             f"Walker-delta, {ALT_KM:.0f} km circular, min elevation {MIN_ELEV_DEG:.0f}°, "
             f"{DAYS:.0f} days at {STEP_S:.0f} s steps. Worst site per region shown. "
             "Generated by `sim/coverage_sim.py`; illustrative, first-order.", "",
             "| Constellation | SA mean gap | SA max gap | SA coverage | SADC max gap | Africa max gap | Africa min coverage |",
             "|---|---|---|---|---|---|---|"]
    def fmt_gap(m): return "none" if m == 0 else (f"{m/60:.1f} h" if m >= 90 else f"{m:.0f} min")
    for cfg in CONFIGS:
        sub = [r for r in rows if r["config"] == cfg[0]]
        def worst(reg, key, fn=max):
            regs = {"SA": ["SA"], "SADC": ["SA", "SADC"], "Africa": ["SA", "SADC", "Africa"]}[reg]
            return fn(r[key] for r in sub if r["region"] in regs)
        lines.append(f"| {cfg[0]} | {fmt_gap(worst('SA','mean_gap_min'))} | {fmt_gap(worst('SA','max_gap_min'))} | {worst('SA','coverage_pct',min):.0f}% | "
                     f"{fmt_gap(worst('SADC','max_gap_min'))} | {fmt_gap(worst('Africa','max_gap_min'))} | "
                     f"{worst('Africa','coverage_pct',min):.0f}% |")
    (res_dir / f"coverage_elev{MIN_ELEV_DEG:.0f}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
