"""FORGE STAR coverage, revisit and pass simulation.

Uses forgestar.orbits (circular orbits + J2 secular drift, Earth rotation) and
forgestar.linkbudget (per-elevation margins). Answers, for each constellation:
  * how long a device in SA / SADC / Africa waits for a satellite (mean and worst)
  * what share of time it is covered
  * passes per day over the Johannesburg gateway (store-and-forward downlink)
The elevation mask comes from the link budget unless MIN_ELEV_DEG overrides it.

Usage:
  python3 sim/coverage_sim.py                    # mask from link budget (NB-IoT uplink, 3 dB margin)
  MIN_ELEV_DEG=10 python3 sim/coverage_sim.py    # fixed mask
  DAYS=1 STEP_S=60 python3 sim/coverage_sim.py   # quick run (CI)
Writes sim/results/coverage_elevNN.md, coverage_by_site_elevNN.csv, link_budget.md.
Illustrative, first-order. Mission-grade work: Orekit (drag, full gravity), then OpenSN.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from forgestar.linkbudget import LINKS, table  # noqa: E402
from forgestar.orbits import Constellation, Site, find_passes, look, propagate_ecef  # noqa: E402

SITES = [
    Site("Johannesburg", "SA", -26.2, 28.0),
    Site("Cape Town", "SA", -33.9, 18.4),
    Site("SA EEZ south (Agulhas)", "SA", -38.0, 22.0),
    Site("Marion Island EEZ", "SA", -46.9, 37.7),
    Site("Windhoek", "SADC", -22.6, 17.1),
    Site("Lusaka", "SADC", -15.4, 28.3),
    Site("Dar es Salaam", "SADC", -6.8, 39.3),
    Site("Kinshasa", "Africa", -4.3, 15.3),
    Site("Nairobi", "Africa", -1.3, 36.8),
    Site("Lagos", "Africa", 6.5, 3.4),
    Site("Dakar", "Africa", 14.7, -17.4),
    Site("Cairo", "Africa", 30.0, 31.2),
    Site("Tunis", "Africa", 36.8, 10.2),
]
GATEWAY = Site("Hartebeesthoek gateway", "SA", -25.89, 27.69)

CONFIGS = [
    Constellation(1, 1, 97.6, label="1 sat SSO (rideshare demo)"),
    Constellation(2, 1, 97.6, label="2 sats SSO"),
    Constellation(6, 2, 45.0, label="6 sats 45°"),
    Constellation(6, 3, 97.6, label="6 sats SSO"),
    Constellation(12, 3, 45.0, label="12 sats 45°"),
    Constellation(12, 4, 97.6, label="12 sats SSO"),
    Constellation(24, 4, 45.0, label="24 sats 45°"),
    Constellation(24, 4, None, label="24 sats mixed 45°+SSO"),
    Constellation(36, 6, 45.0, label="36 sats 45°"),
    Constellation(48, 6, 45.0, label="48 sats 45°"),
    Constellation(48, 6, None, label="48 sats mixed 45°+SSO"),
    Constellation(80, 8, 50.0, label="80 sats 50°"),
    Constellation(120, 10, 50.0, label="120 sats 50°"),
    Constellation(150, 10, 50.0, label="150 sats 50°"),
]

# a device must hear the downlink before it can send, so the mask is the higher of the two
LB_MASK = max(LINKS["nbiot_uplink"].min_elevation(3.0), LINKS["nbiot_downlink"].min_elevation(3.0))
MIN_ELEV_DEG = float(os.environ.get("MIN_ELEV_DEG", LB_MASK))
DAYS = float(os.environ.get("DAYS", 3.0))
STEP_S = float(os.environ.get("STEP_S", 30.0))
CHUNK = 1500


def visibility(c: Constellation, t: np.ndarray) -> np.ndarray:
    """(T, P) bool: any satellite above the mask, computed in time chunks to bound memory."""
    out = []
    for a in range(0, len(t), CHUNK):
        el, _ = look(propagate_ecef(c, t[a:a + CHUNK]), SITES)
        out.append((el >= MIN_ELEV_DEG).any(-1))
    return np.concatenate(out)


def gaps(col: np.ndarray, step: float) -> list[float]:
    out, run = [], 0
    for v in col:
        if v:
            if run: out.append(run * step)
            run = 0
        else:
            run += 1
    if run: out.append(run * step)
    return out


def fmt(m: float) -> str:
    return "none" if m == 0 else (f"{m/60:.1f} h" if m >= 90 else f"{m:.0f} min")


def main():
    t = np.arange(0, DAYS * 86400, STEP_S)
    res = Path(__file__).parent / "results"; res.mkdir(exist_ok=True)
    rows, gw = [], {}
    for c in CONFIGS:
        vis = visibility(c, t)
        for j, s in enumerate(SITES):
            g = gaps(vis[:, j], STEP_S)
            rows.append(dict(config=c.label, sats=c.n, site=s.name, region=s.region,
                             coverage_pct=round(100 * vis[:, j].mean(), 1),
                             mean_gap_min=round(np.mean(g) / 60, 1) if g else 0.0,
                             max_gap_min=round(max(g) / 60, 1) if g else 0.0))
        tg = np.arange(0, min(DAYS, 1.0) * 86400, 10.0)
        p = find_passes(c, [GATEWAY], tg, min_el=10.0)
        gw[c.label] = (len(p) / min(DAYS, 1.0), np.mean([x.duration for x in p]) / 60 if p else 0)
        print(f"done {c.label}", flush=True)

    tag = f"elev{MIN_ELEV_DEG:.0f}"
    with open(res / f"coverage_by_site_{tag}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

    regions = {"SA": ["SA"], "SADC": ["SA", "SADC"], "Africa": ["SA", "SADC", "Africa"]}
    L = ["# Coverage simulation results", "",
         f"Walker-delta, 550 km circular, **J2 secular drift**, Earth rotation. Min elevation **{MIN_ELEV_DEG:.0f}°**"
         + (" (from the NB-IoT link budget: the higher of uplink and downlink, 3 dB margin)" if "MIN_ELEV_DEG" not in os.environ else "")
         + f". {DAYS:g} days at {STEP_S:g} s steps. Worst site per region shown. "
         "Gateway passes: Hartebeesthoek, 10° mask. Generated by `sim/coverage_sim.py`; illustrative.", "",
         "| Constellation | SA mean gap | SA max gap | SA coverage | SADC max gap | Africa max gap | Africa min coverage | Gateway passes/day |",
         "|---|---|---|---|---|---|---|---|"]
    for c in CONFIGS:
        sub = [r for r in rows if r["config"] == c.label]
        def worst(reg, key, fn=max):
            return fn(r[key] for r in sub if r["region"] in regions[reg])
        L.append(f"| {c.label} | {fmt(worst('SA','mean_gap_min'))} | {fmt(worst('SA','max_gap_min'))} | "
                 f"{worst('SA','coverage_pct',min):.0f}% | {fmt(worst('SADC','max_gap_min'))} | "
                 f"{fmt(worst('Africa','max_gap_min'))} | {worst('Africa','coverage_pct',min):.0f}% | "
                 f"{gw[c.label][0]:.0f} (avg {gw[c.label][1]:.0f} min) |")
    (res / f"coverage_{tag}.md").write_text("\n".join(L) + "\n")

    el, lb = table()
    B = ["# Link budget (illustrative, 550 km)", "", "Margin in dB at each elevation. Generated from `forgestar/linkbudget.py`.", "",
         "| Link | " + " | ".join(f"{e}°" for e in el) + " | Closes (3 dB) from |", "|---|" + "---|" * (len(el) + 1)]
    for name, m, mn in lb:
        B.append(f"| {name} | " + " | ".join(f"{x:+.1f}" for x in m) + f" | {'never' if mn is None else f'{mn:.0f}°'} |")
    (res / "link_budget.md").write_text("\n".join(B) + "\n")
    print("\n".join(L)); print(); print("\n".join(B))


if __name__ == "__main__":
    main()
