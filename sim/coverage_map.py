"""Where FORGE STAR reaches: global coverage map for a constellation and gateway network.

For each point on a lat/lon grid: the share of time a satellite is overhead (16° mask, isoflux antenna)
and the share of time the link can be real time (the same satellite also sees a gateway at 10°).
Draws an equirectangular map (land from global-land-mask) to docs/img/coverage-<name>.png and
writes the numbers to sim/results/coverage_map_<name>.md.

Usage: python3 sim/coverage_map.py            # Stage 3 (48 sats, 14 African gateways)
       python3 sim/coverage_map.py --stage4   # 150 sats
Needs: numpy, Pillow, global-land-mask (pip install global-land-mask) for the land outline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from forgestar.orbits import Constellation, Site, look, propagate_ecef  # noqa: E402

GATEWAYS = [("Hartebeesthoek", -25.89, 27.69), ("Cape Town", -33.93, 18.42), ("Walvis Bay", -22.95, 14.5),
            ("Mauritius", -20.2, 57.5), ("Malindi", -3.0, 40.2), ("Lagos", 6.5, 3.4), ("Lusaka", -15.4, 28.3),
            ("Kinshasa", -4.3, 15.3), ("Luanda", -8.8, 13.2), ("Dar es Salaam", -6.8, 39.3), ("Maputo", -25.97, 32.57),
            ("Abidjan", 5.3, -4.0), ("Addis Ababa", 9.0, 38.7), ("Durban", -29.9, 31.0)]
CITIES = [("Johannesburg", -26.2, 28.0), ("Nairobi", -1.3, 36.8), ("Lagos", 6.5, 3.4), ("Cairo", 30.0, 31.2),
          ("Dubai", 25.2, 55.3), ("Mumbai", 19.1, 72.9), ("Jakarta", -6.2, 106.8), ("Sydney", -33.9, 151.2),
          ("Sao Paulo", -23.5, -46.6), ("Mexico City", 19.4, -99.1), ("Madrid", 40.4, -3.7), ("Tokyo", 35.7, 139.7),
          ("Buenos Aires", -34.6, -58.4), ("Moscow", 55.8, 37.6)]
MASK_USER, MASK_GW = 16.0, 10.0


def compute(shells, lat_step=2.5, lon_step=5.0, days=2.0, dt=120.0, chunk=250):
    t = np.arange(0, days * 86400, dt)
    sat = np.concatenate([propagate_ecef(c, t) for c in shells], axis=1)
    eg, _ = look(sat, [Site(n, "", la, lo) for n, la, lo in GATEWAYS])
    gw_vis = (eg >= MASK_GW).any(1)                                 # (T, N)
    lats = np.arange(-70, 70.01, lat_step); lons = np.arange(-180, 180, lon_step)
    pts = [(la, lo) for la in lats for lo in lons]
    cov = np.zeros(len(pts)); rt = np.zeros(len(pts))
    for a in range(0, len(pts), chunk):
        sites = [Site("", la, "", lo) if False else Site("", "", la, lo) for la, lo in pts[a:a + chunk]]
        e, _ = look(sat, sites)                                     # (T, P, N)
        up = e >= MASK_USER
        cov[a:a + chunk] = up.any(-1).mean(0)
        rt[a:a + chunk] = (up & gw_vis[:, None, :]).any(-1).mean(0)
    return lats, lons, cov.reshape(len(lats), len(lons)), rt.reshape(len(lats), len(lons))


def _font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw(lats, lons, cov, rt, title, out: Path, scale=6):
    """Equirectangular map 360°×140°: colour = service level; land shaded underneath."""
    W, H = 360 * scale // 2, 140 * scale // 2           # 3 px per degree at scale 6
    px = W / 360.0
    img = Image.new("RGB", (W, H + 125), (14, 15, 18))
    d = ImageDraw.Draw(img)
    try:
        from global_land_mask import globe
        glat = np.linspace(70, -70, H); glon = np.linspace(-180, 180, W)
        LO, LA = np.meshgrid(glon, glat)
        land = globe.is_land(LA, LO)
    except ImportError:
        land = np.zeros((H, W), bool)
    # service colours: none / store-and-forward (by coverage) / real-time share
    lat_idx = np.clip(((70 - np.linspace(70, -70, H)) / (lats[1] - lats[0])).round().astype(int), 0, len(lats) - 1)[::-1]
    lon_idx = np.clip(((np.linspace(-180, 180, W) + 180) / (lons[1] - lons[0])).astype(int), 0, len(lons) - 1)
    C = cov[lat_idx][:, lon_idx]; R = rt[lat_idx][:, lon_idx]
    rgb = np.zeros((H, W, 3), np.float32)
    base_sea, base_land = np.array([22, 26, 34]), np.array([58, 62, 70])
    rgb[:] = np.where(land[..., None], base_land, base_sea)
    sf = np.array([70, 140, 220])          # store-and-forward: blue, brighter with more coverage
    real = np.array([255, 90, 31])         # real time: FORGE ember
    a_sf = np.clip(C, 0, 1)[..., None] * 0.85
    rgb = rgb * (1 - a_sf) + sf * a_sf
    a_rt = np.clip(R / np.maximum(C, 1e-6), 0, 1)[..., None] * (C[..., None] > 0.05) * 0.9
    rgb = rgb * (1 - a_rt) + real * a_rt
    rgb = np.where(land[..., None], rgb * 0.75 + base_land * 0.25 + 18, rgb)   # keep land readable
    img.paste(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), (0, 0))
    # graticule
    for la in (-60, -45, -30, -15, 0, 15, 30, 45, 60):
        y = (70 - la) * H / 140
        d.line([(0, y), (W, y)], fill=(60, 64, 72) if la else (95, 100, 110), width=1)
        d.text((3, y - 11), f"{la:+d}°", fill=(150, 155, 165), font=_font(10))
    f = _font(11)
    for n, la, lo in CITIES:
        x, y = (lo + 180) * px, (70 - la) * H / 140
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255))
        d.text((x + 5, y - 7), n, fill=(235, 235, 235), font=f)
    for n, la, lo in GATEWAYS:
        x, y = (lo + 180) * px, (70 - la) * H / 140
        d.rectangle([x - 3, y - 3, x + 3, y + 3], fill=(242, 163, 58), outline=(14, 15, 18))
    # legend
    y0 = H + 14
    d.text((14, y0), title, fill=(255, 255, 255), font=_font(16))
    items = [((255, 90, 31), "Real time (satellite sees user and a gateway)"),
             ((70, 140, 220), "Store-and-forward (brighter = satellite overhead more often)"),
             ((242, 163, 58), "Gateway (14 in Africa)"), ((58, 62, 70), "No service above ~60° latitude")]
    x, yy = 14, y0 + 30
    for col, label in items:
        wlab = 22 + int(d.textlength(label, font=_font(12))) + 26
        if x + wlab > W - 10:
            x, yy = 14, yy + 22
        d.rectangle([x, yy, x + 16, yy + 16], fill=col)
        d.text((x + 22, yy), label, fill=(210, 212, 218), font=_font(12))
        x += wlab
    d.text((14, yy + 26), "550 km circular orbits, J2; 16° user mask (isoflux antenna), 10° gateway mask; 2-day average. "
           "Illustrative. Generated by sim/coverage_map.py", fill=(140, 145, 155), font=_font(11))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage4", action="store_true")
    a = ap.parse_args()
    if a.stage4:
        name, title = "stage4", "Where FORGE STAR reaches — Stage 4: 150 satellites, 14 African gateways"
        shells = [Constellation(120, 12, 45.0), Constellation(30, 3, 10.0)]
    else:
        name, title = "stage3", "Where FORGE STAR reaches — Stage 3: 48 satellites, 14 African gateways"
        shells = [Constellation(42, 7, 45.0), Constellation(6, 1, 10.0)]
    lats, lons, cov, rt = compute(shells)
    draw(lats, lons, cov, rt, title, ROOT / "docs" / "img" / f"coverage-{name}.png")
    # numbers: band averages, share of Earth's surface reached
    w = np.cos(np.radians(lats))[:, None] * np.ones_like(cov)
    surf = lambda m: float((w * m).sum() / (np.cos(np.radians(np.arange(-90, 90.01, 2.5))).sum() * cov.shape[1]))
    L = [f"# Coverage map: {name}", "", f"- Earth's surface with a satellite overhead at least 25% of the time: **{100*surf(cov >= 0.25):.0f}%**",
         f"- ... at least 50% of the time: **{100*surf(cov >= 0.5):.0f}%**",
         f"- Surface with real-time service at least 25% of the time (via African gateways): **{100*surf(rt >= 0.25):.0f}%**", ""]
    (ROOT / "sim" / "results" / f"coverage_map_{name}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
