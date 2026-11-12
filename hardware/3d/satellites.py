"""FORGE STAR concept 3D models (CadQuery): demonstrator, operational IoT satellite, broadband concept.

These are concept models for presentations and early mechanical discussion. Sizes are illustrative and
follow the strategy (6U-12U IoT satellites; a much larger flat-panel satellite for Stage 5 broadband).
They are not engineering designs: the bus comes from a supplier (Dragonfly Aerospace or CubeSpace).

Axes: -Z is nadir (towards Earth), +X is the flight direction. Units: mm.
Run: python3 hardware/3d/satellites.py   -> hardware/3d/out/<name>.step and .glb
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq

OUT = Path(__file__).resolve().parent / "out"

BUS = cq.Color(0.20, 0.21, 0.24)
PANEL_BACK = cq.Color(0.75, 0.76, 0.78)
CELL = cq.Color(0.05, 0.10, 0.32)
GOLD = cq.Color(0.83, 0.66, 0.22)
WHITE = cq.Color(0.92, 0.92, 0.90)
COPPER = cq.Color(0.72, 0.45, 0.20)
EMBER = cq.Color(1.0, 0.35, 0.12)
BLACK = cq.Color(0.05, 0.05, 0.06)


def box(x, y, z, at=(0, 0, 0)):
    return cq.Workplane("XY").box(x, y, z).translate(at)


def cyl(d, h, at=(0, 0, 0), axis="Z"):
    c = cq.Workplane("XY").circle(d / 2).extrude(h).translate((0, 0, -h / 2))
    if axis == "X":
        c = c.rotate((0, 0, 0), (0, 1, 0), 90)
    if axis == "Y":
        c = c.rotate((0, 0, 0), (1, 0, 0), 90)
    return c.translate(at)


def solar_panel(asm, name, w, l, at, normal="Z", cells=(4, 6)):
    """Panel of size w (X) by l (Y or Z), 4 mm thick, cells on the +normal side."""
    t = 4.0
    if normal == "Z":
        asm.add(box(w, l, t, at), name=f"{name}_substrate", color=PANEL_BACK)
        nx, ny = cells
        cw, cl = (w - 12) / nx, (l - 12) / ny
        for i in range(nx):
            for j in range(ny):
                cx = at[0] - w / 2 + 6 + cw * (i + 0.5)
                cy = at[1] - l / 2 + 6 + cl * (j + 0.5)
                asm.add(box(cw - 3, cl - 3, 0.6, (cx, cy, at[2] + t / 2 + 0.3)), name=f"{name}_cell_{i}_{j}", color=CELL)


def patch_array(asm, name, n, pitch, size, at, color=GOLD, ground=None):
    """n x n patch antennas on the nadir (-Z) face. `at` is the centre of the ground plate."""
    g = ground or (n * pitch + 10)
    asm.add(box(g, g, 3, at), name=f"{name}_ground", color=WHITE)
    for i in range(n):
        for j in range(n):
            px = at[0] + (i - (n - 1) / 2) * pitch
            py = at[1] + (j - (n - 1) / 2) * pitch
            asm.add(box(size, size, 1, (px, py, at[2] - 2)), name=f"{name}_patch_{i}_{j}", color=color)


def demonstrator_6u() -> cq.Assembly:
    """Stage 1 demonstrator: 6U, body-mounted and two deployed panels, patch antenna, AIS monopoles."""
    a = cq.Assembly(name="forge_star_demo_6u")
    X, Y, Z = 366.0, 226.0, 100.0   # long axis along flight direction
    a.add(box(X, Y, Z), name="bus", color=BUS)
    for sx in (-1, 1):
        for sy in (-1, 1):   # corner rails
            a.add(box(X + 14, 8.5, 8.5, (0, sy * (Y / 2 - 4.25), sx * (Z / 2 - 4.25))), name=f"rail_{sx}_{sy}", color=PANEL_BACK)
    solar_panel(a, "body_panel", X - 20, Y - 24, (0, 0, Z / 2 + 2), cells=(6, 4))
    for s in (-1, 1):   # deployed wings, cells facing zenith
        solar_panel(a, f"wing_{'p' if s > 0 else 'n'}", X - 20, Y - 10, (0, s * (Y + 4), Z / 2 + 2), cells=(6, 4))
        a.add(cyl(6, X - 60, (0, s * (Y / 2 + 2), Z / 2), "X"), name=f"hinge_{s}", color=PANEL_BACK)
    patch_array(a, "sband", 2, 70, 56, (-70, 0, -Z / 2 - 1.5))                     # NB-IoT S-band 2x2 patch
    patch_array(a, "xband", 2, 20, 15, (95, 60, -Z / 2 - 1.5), COPPER, ground=50)  # X-band feeder downlink
    for s in (-1, 1):   # VHF AIS tape monopoles, ~lambda/4 at 162 MHz
        a.add(box(460, 6, 0.4, (X / 2 + 230, s * 80, -Z / 2 + 6)), name=f"ais_monopole_{s}", color=GOLD)
    a.add(box(24, 24, 3, (120, -60, Z / 2 + 5.5)), name="gnss_patch", color=WHITE)
    a.add(cyl(26, 34, (X / 2 + 17 - 34, 0, 0), "X"), name="star_tracker", color=BLACK)
    a.add(box(40, 40, 2, (95, -55, -Z / 2 - 1)), name="payload_marker", color=EMBER)
    return a


def iot_12u() -> cq.Assembly:
    """Stage 2-3 operational IoT satellite: 12U, two double wings, isoflux S-band antenna, AIS turnstile."""
    a = cq.Assembly(name="forge_star_iot_12u")
    X, Y, Z = 366.0, 226.0, 226.0
    a.add(box(X, Y, Z), name="bus", color=BUS)
    for sy in (-1, 1):
        for sz in (-1, 1):
            a.add(box(X + 14, 8.5, 8.5, (0, sy * (Y / 2 - 4.25), sz * (Z / 2 - 4.25))), name=f"rail_{sy}_{sz}", color=PANEL_BACK)
    solar_panel(a, "body_panel", X - 20, Y - 24, (0, 0, Z / 2 + 2), cells=(6, 4))
    for s in (-1, 1):   # two panels per side
        for k in (1, 2):
            solar_panel(a, f"wing_{'p' if s > 0 else 'n'}{k}", X - 20, Y - 10, (0, s * (k * (Y + 6) - 2), Z / 2 + 2), cells=(6, 4))
        a.add(cyl(6, X - 60, (0, s * (Y / 2 + 2), Z / 2), "X"), name=f"hinge_{s}", color=PANEL_BACK)
    # isoflux S-band antenna (shaped beam): shown as a quadrifilar helix in a radome on a ground plate
    a.add(box(150, 150, 3, (-80, 0, -Z / 2 - 1.5)), name="isoflux_ground", color=WHITE)
    a.add(cyl(70, 130, (-80, 0, -Z / 2 - 68)), name="isoflux_radome", color=WHITE)
    for k in range(4):
        import math
        ang = k * math.pi / 2
        a.add(cyl(4, 132, (-80 + 37 * math.cos(ang), 37 * math.sin(ang), -Z / 2 - 68)), name=f"isoflux_filar_{k}", color=GOLD)
    patch_array(a, "xband", 4, 20, 15, (110, 0, -Z / 2 - 1.5), COPPER, ground=92)
    for k, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):   # VHF AIS turnstile, four monopoles
        if dx:
            a.add(box(460, 6, 0.4, (dx * (X / 2 + 230), 0, -Z / 2 + 8)), name=f"ais_{k}", color=GOLD)
        else:
            a.add(box(6, 460, 0.4, (150, dy * (Y / 2 + 230), -Z / 2 + 8)), name=f"ais_{k}", color=GOLD)
    a.add(box(30, 30, 3, (120, -60, Z / 2 + 5.5)), name="gnss_patch", color=WHITE)
    a.add(cyl(30, 40, (X / 2 - 3, 60, 40), "X"), name="star_tracker", color=BLACK)
    a.add(cyl(46, 30, (-X / 2 - 15, 0, 0), "X"), name="thruster", color=PANEL_BACK)
    a.add(box(60, 60, 2, (20, -70, -Z / 2 - 1)), name="payload_marker", color=EMBER)
    return a


def broadband_concept() -> cq.Assembly:
    """Stage 5 broadband concept: flat-panel bus, Ku user arrays, Ka gateway antennas, one solar wing.

    Illustrative only (roughly 300 kg class). Real sizing depends on the link budget and the bus supplier.
    """
    a = cq.Assembly(name="forge_star_broadband_concept")
    X, Y, Z = 2600.0, 1300.0, 180.0
    a.add(box(X, Y, Z), name="bus", color=BUS)
    a.add(box(X - 80, Y - 80, 6, (0, 0, Z / 2 + 3)), name="radiator", color=WHITE)
    # Ku-band user phased arrays on the nadir face: transmit and receive
    for nm, cx in (("ku_tx", -720), ("ku_rx", 180)):
        a.add(box(800, 800, 30, (cx, 0, -Z / 2 - 15)), name=f"{nm}_frame", color=PANEL_BACK)
        n = 8
        for i in range(n):
            for j in range(n):
                a.add(box(86, 86, 4, (cx + (i - (n - 1) / 2) * 96, (j - (n - 1) / 2) * 96, -Z / 2 - 32)), name=f"{nm}_tile_{i}_{j}", color=GOLD)
    # Ka-band gateway antennas: two steerable dishes
    for s in (-1, 1):
        cx, cy = 950, s * 380
        a.add(cyl(60, 160, (cx, cy, -Z / 2 - 80)), name=f"ka_mast_{s}", color=PANEL_BACK)
        dish = cq.Workplane("XY").circle(210).workplane(offset=70).circle(40).loft().translate((cx, cy, -Z / 2 - 230))
        a.add(dish, name=f"ka_dish_{s}", color=WHITE)
    # optical inter-satellite links at the four corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.add(cyl(120, 150, (sx * (X / 2 - 110), sy * (Y / 2 + 75), 0), "Y"), name=f"laser_{sx}_{sy}", color=BLACK)
    a.add(cyl(160, 120, (-X / 2 - 60, 300, 0), "X"), name="hall_thruster", color=PANEL_BACK)
    a.add(cyl(90, 110, (X / 2 - 150, -Y / 2 + 150, Z / 2 + 55)), name="star_tracker", color=BLACK)
    # single solar wing, five panels, rising from the zenith side (Starlink-style "open book")
    a.add(box(120, 120, 300, (0, -Y / 2 - 60, Z / 2 + 150)), name="wing_yoke", color=PANEL_BACK)
    pw, ph = 2400.0, 1500.0
    for k in range(5):
        zc = Z / 2 + 300 + ph / 2 + k * (ph + 30)
        a.add(box(pw, 12, ph, (0, -Y / 2 - 60, zc)), name=f"wing_panel_{k}", color=PANEL_BACK)
        for i in range(8):
            for j in range(5):
                a.add(box(pw / 8 - 14, 2, ph / 5 - 14, (-pw / 2 + pw / 8 * (i + 0.5), -Y / 2 - 67, zc - ph / 2 + ph / 5 * (j + 0.5))),
                      name=f"wing_cell_{k}_{i}_{j}", color=CELL)
    a.add(box(400, 400, 4, (-720, 0, Z / 2 + 8)), name="forge_marker", color=EMBER)
    return a


MODELS = {"sat-demo-6u": demonstrator_6u, "sat-iot-12u": iot_12u, "sat-broadband-concept": broadband_concept}


def main():
    OUT.mkdir(exist_ok=True)
    for name, fn in MODELS.items():
        asm = fn()
        asm.save(str(OUT / f"{name}.step"))
        asm.save(str(OUT / f"{name}.glb"))
        bb = asm.toCompound().BoundingBox()
        print(f"{name}: {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm deployed, {len(asm.children)} parts")


if __name__ == "__main__":
    main()
