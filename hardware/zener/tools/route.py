"""Autoroute a placed board with Freerouting, then refill the ground pours.

Usage: FREEROUTING_JAR=/path/freerouting.jar python3 tools/route.py boards/pib
Needs KiCad 10 (pcbnew Python module) and Java 17+. Get the JAR from
https://github.com/freerouting/freerouting/releases (v1.9.0 was the version planned for this repo).

Runs in GitHub CI (.github/workflows/route-boards.yml), which uploads the routed boards.
An autorouted board is a starting point. RF, power and decoupling traces need an engineer's review.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pcbnew


def _seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return ((px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2) ** 0.5


def stitch(pcb: Path) -> int:
    """Add ground vias on a 2.5 mm grid to tie the ground pours on all layers together.

    A via is placed only where it clears every part, pad, keep-out, track and other via by 0.5 mm.
    """
    mm = pcbnew.FromMM
    board = pcbnew.LoadBoard(str(pcb))
    gnd = board.FindNet("GND")
    rects, circles, segs = [], [], []
    for fp in board.GetFootprints():
        boxes = [fp.GetBoundingBox(False)] + [p.GetBoundingBox() for p in fp.Pads()] + [z.GetBoundingBox() for z in fp.Zones()]
        rects += [(b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()) for b in boxes]
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            circles.append((t.GetPosition().x, t.GetPosition().y, t.GetWidth(pcbnew.F_Cu) // 2))
        else:
            segs.append((t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth() // 2))
    box = board.GetBoardEdgesBoundingBox()
    via_r, clear, step, added = mm(0.3), mm(0.5), mm(2.5), 0
    y = box.GetTop() + mm(1.5)
    while y < box.GetBottom() - mm(1.5):
        x = box.GetLeft() + mm(1.5)
        while x < box.GetRight() - mm(1.5):
            ok = all(((x - a) ** 2 + (y - b) ** 2) ** 0.5 > r + via_r + clear for a, b, r in circles)
            ok = ok and all(max(l - x, x - r, tp - y, y - bt) > via_r + clear for l, tp, r, bt in rects)
            ok = ok and all(_seg_dist(x, y, *s[:4]) > s[4] + via_r + clear for s in segs)
            if ok:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(x, y)); v.SetNet(gnd)
                v.SetWidth(pcbnew.F_Cu, via_r * 2); v.SetDrill(mm(0.3))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                board.Add(v)
                circles.append((x, y, via_r))
                added += 1
            x += step
        y += step
    for z in board.Zones():   # drop copper islands that nothing connects to
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Save(str(pcb))
    print(f"stitch: {added} ground vias")
    return 0


def main() -> int:
    bdir = Path(sys.argv[1])
    name = bdir.name
    pcb = bdir / "eda" / f"{name}.kicad_pcb"
    dsn, ses = pcb.with_suffix(".dsn"), pcb.with_suffix(".ses")
    stage = sys.argv[2] if len(sys.argv) > 2 else None
    if stage == "export":
        board = pcbnew.LoadBoard(str(pcb))
        # Export without the ground pours (not saved), so the router wires ground like any other net.
        # With pours present it treats ground as a plane and can fence ground pins in behind other tracks.
        for z in list(board.Zones()):
            board.Remove(z)
        return 0 if pcbnew.ExportSpecctraDSN(board, str(dsn)) else 1
    if stage == "import":
        board = pcbnew.LoadBoard(str(pcb))
        if not pcbnew.ImportSpecctraSES(board, str(ses)):
            return 1
        board.Save(str(pcb))
        return 0
    if stage == "stitch":
        return stitch(pcb)
    if stage == "fill":
        board = pcbnew.LoadBoard(str(pcb))
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(str(pcb))
        return 0
    jar = os.environ.get("FREEROUTING_JAR")
    if not jar:
        print("set FREEROUTING_JAR")
        return 2
    # each pcbnew step runs in its own process (see place.py)
    steps = [
        [sys.executable, __file__, str(bdir), "export"],
        ["java", "-jar", jar, "-de", str(dsn), "-do", str(ses), "-mp", "40", "-oit", "1", "-host-mode", "cli"],
        [sys.executable, __file__, str(bdir), "import"],
        [sys.executable, __file__, str(bdir), "stitch"],
        [sys.executable, __file__, str(bdir), "fill"],
    ]
    for cmd in steps:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if r.returncode or (cmd[0] == "java" and not ses.exists()):
            print(" ".join(cmd[:4]), "failed:", (r.stdout + r.stderr)[-2000:])
            return r.returncode or 1
    dsn.unlink(missing_ok=True)
    ses.unlink(missing_ok=True)
    print(f"{name}: routed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
