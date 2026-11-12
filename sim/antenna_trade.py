"""Payload antenna trade study: which S-band antenna closes NB-IoT both ways at a useful elevation?

For each option the same aperture serves uplink (receive) and downlink (transmit).
The usable elevation mask is the higher of the two. We then run 24 sats at 45°
over South Africa to show what that mask does to service.

All parameters are illustrative (mass, power, cost, gain). Replace with vendor quotes.
Usage: python3 sim/antenna_trade.py
"""
from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from forgestar.linkbudget import LINKS, cos_beam_gain_dbi, isoflux_edge_gain_dbi  # noqa: E402
from forgestar.orbits import Constellation, Site, look, propagate_ecef  # noqa: E402

UP, DOWN = LINKS["nbiot_uplink"], LINKS["nbiot_downlink"]
W = lambda watts: 10 * math.log10(watts)   # RF watts -> dBW
PATCH = lambda hb: dict(sat_pattern="cos", sat_half_beam_deg=float(hb))
ISO = lambda edge: dict(sat_pattern="isoflux", edge_el_deg=float(edge))

# name, antenna, gain dBi (None = derive from the beam), RF watts, altitude km, extra link changes,
# DC power W, mass kg, est. cost $k, note
OPTIONS = [
    ("A. Patch, ±30° beam, 2 W (baseline)", PATCH(30), None, 2, 550, {}, 12, 0.4, 15,
     "Simple and cheap. Narrow footprint: devices hear the satellite only when it is high overhead."),
    ("A2. Wide patch, ±42° beam, 2 W", PATCH(42), None, 2, 550, {}, 12, 0.3, 12,
     "Wider beam, less gain. Helps the uplink, not the downlink."),
    ("B. Patch ±30°, 10 W", PATCH(30), None, 10, 550, {}, 45, 0.7, 40,
     "Brute force. DC power and heat are hard on a 6U."),
    ("F. Patch ±30°, 2 W, deep coverage mode", PATCH(30), None, 2, 550, {"deep": True}, 12, 0.4, 15,
     "Software only: more NB-IoT repetitions. About a quarter of the throughput."),
    ("C. Isoflux to 20°, 5 dBi, 2 W", ISO(20), 5.0, 2, 550, {}, 12, 0.5, 35,
     "Shaped beam, even footprint, but too little power to reach devices."),
    ("D. Isoflux to 20°, 5 dBi, 5 W", ISO(20), 5.0, 5, 550, {}, 25, 0.6, 45,
     "Just under the 3 dB margin target."),
    ("D3. Isoflux to 20°, 5 dBi, 8 W", ISO(20), 5.0, 8, 550, {}, 38, 0.7, 55,
     "Closes at the Stage 3 design mask. Needs ~38 W during passes: a 12U, not a 6U."),
    ("D4. Isoflux to 20°, 5 dBi, 5 W, deep coverage mode", ISO(20), 5.0, 5, 550, {"deep": True}, 25, 0.6, 45,
     "Lowest mask for NB-IoT at moderate power. Capacity cost: see sim/capacity_study.py."),
    ("D2. Isoflux to 30°, 6 dBi, 5 W", ISO(30), 6.0, 5, 550, {}, 25, 0.6, 45,
     "Narrower shaped cone: more margin, smaller footprint."),
    ("G. Isoflux to 20°, 5 dBi, 5 W at 450 km", ISO(20), 5.0, 5, 450, {}, 25, 0.6, 45,
     "Lower orbit closes the link at 5 W. Smaller footprint and more drag (shorter life)."),
    ("H. Isoflux to 20°, 5 dBi, 2 W, compact own protocol", ISO(20), 5.0, 2, 550, {"beacon": True}, 12, 0.5, 35,
     "A 15 kHz downlink beacon in place of the 180 kHz NB-IoT carrier. Closes at 2 W but is not 3GPP: custom devices."),
    ("E. 4×4 phased array, 17 dBi, 4 W total", dict(sat_pattern="array", max_scan_deg=60.0), 17.0, 4, 550, {}, 30, 1.2, 150,
     "Steers beams to users. Most capacity. Highest cost and risk: Stage 4."),
]

SA_SITES = [Site("Johannesburg", "SA", -26.2, 28.0), Site("Cape Town", "SA", -33.9, 18.4),
            Site("Agulhas EEZ", "SA", -38.0, 22.0), Site("Marion Island EEZ", "SA", -46.9, 37.7)]


def links_for(opt):
    _, ant, g, watts, alt, extra, *_ = opt
    if g is None:
        g = cos_beam_gain_dbi(ant["sat_half_beam_deg"])
    up = replace(UP, **ant, rx_gain_dbi=g)
    dn = replace(DOWN, **ant, tx_gain_dbi=g, tx_power_dbw=W(watts))
    if extra.get("deep"):       # deeper NB-IoT coverage enhancement: 4 dB more repetition gain both ways
        up = replace(up, required_snr_db=up.required_snr_db - 4.0)
        dn = replace(dn, required_snr_db=dn.required_snr_db - 6.0)
    if extra.get("beacon"):     # compact store-and-forward protocol with a narrowband downlink beacon
        dn = replace(dn, bandwidth_hz=15000.0)
    return up, dn, g, alt


def mask_for(opt):
    up, dn, g, alt = links_for(opt)
    assert up.gain_is_consistent(alt), f"{opt[0]}: gain {g:.1f} dBi exceeds what this beam shape allows"
    mu, md = up.min_elevation(3.0, alt), dn.min_elevation(3.0, alt)
    return mu, md, (None if mu is None or md is None else max(mu, md)), up, dn


def service(mask, alt, shells, sites, days=2.0, step=30.0):
    """Worst site: typical and longest wait for a pass (minutes), and share of time covered (%)."""
    t = np.arange(0, days * 86400, step)
    sat = np.concatenate([propagate_ecef(replace(c, alt_km=alt), t) for c in shells], axis=1)
    el, _ = look(sat, sites)
    vis = (el >= mask).any(-1)
    worst_mean, worst_max = 0.0, 0.0
    for j in range(vis.shape[1]):
        g, run = [], 0
        for v in vis[:, j]:
            if v:
                if run: g.append(run * step)
                run = 0
            else:
                run += 1
        if run: g.append(run * step)
        worst_mean = max(worst_mean, np.mean(g) if g else 0); worst_max = max(worst_max, max(g) if g else 0)
    return worst_mean / 60, worst_max / 60, 100 * vis.mean(0).min()


def fmt(m):
    return f"{m/60:.1f} h" if m >= 90 else f"{m:.0f} min"


STAGE2 = [Constellation(24, 4, 45.0)]
STAGE3 = [Constellation(42, 7, 45.0), Constellation(6, 1, 10.0)]


def main():
    el = lambda x: "never" if x is None else f"{x:.0f}°"
    L = ["# Payload antenna trade study (illustrative)", "",
         "The same S-band antenna serves the NB-IoT uplink (receive) and downlink (transmit). A device must hear the "
         "downlink before it can send, so the usable mask is the higher of the two. Antenna gain is tied to beam shape: "
         f"a ±30° patch has about {cos_beam_gain_dbi(30):.1f} dBi and a ±20° patch about {cos_beam_gain_dbi(20):.1f} dBi "
         f"(80% efficiency); an isoflux antenna shaped out to 20° elevation can have at most about {isoflux_edge_gain_dbi(20):.1f} dBi at its edge. "
         "Service columns: worst South African site (incl. EEZ). Generated by `sim/antenna_trade.py`.", "",
         "| Option | Gain | Uplink from | Downlink from | Usable mask | 24 sats: typical / longest wait | Stage 3 (48): typical / longest wait | DC power | Mass | Est. cost | Note |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for opt in OPTIONS:
        name, _, _, _, alt, _, dc, kg, cost, note = opt
        mu, md, mask, up, dn = mask_for(opt)
        g = up.rx_gain_dbi
        if mask is None:
            best_dl = max(dn.margin_db(e, alt) for e in range(5, 91))
            L.append(f"| {name} | {g:.1f} dBi | {el(mu)} | never (best {best_dl:+.1f} dB) | **no** | — | — | {dc} W | {kg} kg | ${cost}k | {note} |"); continue
        m2, x2, _ = service(mask, alt, STAGE2, SA_SITES)
        m3, x3, _ = service(mask, alt, STAGE3, SA_SITES)
        L.append(f"| {name} | {g:.1f} dBi | {el(mu)} | {el(md)} | **{mask:.0f}°** | {fmt(m2)} / {fmt(x2)} | {fmt(m3)} / {fmt(x3)} | {dc} W | {kg} kg | ${cost}k | {note} |")
    L += ["", "## What changed from the first version", "",
          "- **The patch was too optimistic.** The first version gave a ±30° patch 14 dBi. Physics allows about 9.7 dBi. "
          "The baseline patch now closes the uplink from about 29° and the downlink from about 47°, not 22° and 37°.",
          "- **The isoflux figures hold.** 5 dBi at the edge of a 20° cone is inside the physical limit (about 7.7 dBi), so the 16° Stage 3 mask still needs "
          "the isoflux antenna with about 8 W of RF power (about 38 W DC during passes).",
          "- **The downlink sets the mask in every NB-IoT option.**", "",
          "## Recommendation (illustrative)", "",
          "- **Demonstrator (6U or hosted payload):** simple patch plus deep coverage mode (F). It proves the link and the software. Coverage is poor by design; it is a demonstrator.",
          "- **Stage 2–3 service (12U):** isoflux antenna with 8 W (D3) to hold the 16° mask. Ask bus suppliers to confirm about 38 W for the payload during passes. "
          "If the bus cannot supply it, fall back to 5 W with deep coverage mode for edge-of-footprint devices (D4), or a 450 km orbit (G).",
          "- **Keep the compact protocol (H) as the capacity and power hedge.** It closes at 2 W and carries about three times the messages per carrier, but needs our own device firmware.",
          "- **Phased array (E):** Stage 4, when capacity needs several beams.", "",
          "Check the downlink power against ITU power-flux-density limits for the band before fixing it (see `docs/itu/FILING_PARAMETERS.md`).", "",
          "*Illustrative. Replace gains, powers, masses and costs with vendor data and lab measurements before decisions.*"]
    out = Path(__file__).parent / "results" / "antenna_trade.md"; out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
