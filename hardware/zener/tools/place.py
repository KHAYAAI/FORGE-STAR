"""Place parts, draw the outline and add ground pours on a board that `pcb layout` generated.

`pcb layout` creates the KiCad board with every footprint but no placement. This script reads
`boards/<name>/placement.json` and moves each part to its position. Parts are found by their Zener
instance name (the footprint's "Path" field), so positions survive reference renumbering.

placement.json: {"size_mm": [w, h], "parts": {"MCU": [x, y, rotation_deg], ...}}
Coordinates are mm from the board's top-left corner.

Usage: python3 tools/place.py boards/pib            (needs KiCad's pcbnew Python module, KiCad 10)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pcbnew

OX, OY = 100.0, 100.0  # board origin on the KiCad sheet, mm


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def field(fp, name: str) -> str:
    for f in fp.GetFields():
        if f.GetName() == name:
            return f.GetText()
    return ""


def _paths(bdir: Path):
    name = bdir.name
    return name, json.loads((bdir / "placement.json").read_text()), bdir / "eda" / f"{name}.kicad_pcb"


def stage_move(bdir: Path) -> int:
    """Move parts and remove any earlier outline and zones."""
    name, spec, path = _paths(bdir)
    board = pcbnew.LoadBoard(str(path))
    missing = dict(spec["parts"])
    unplaced = []
    for fp in board.GetFootprints():
        inst = field(fp, "Path").split(".")[0]
        if inst in spec["parts"]:
            x, y, rot = spec["parts"][inst]
            fp.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
            fp.SetOrientationDegrees(rot)
            missing.pop(inst, None)
        else:
            unplaced.append(inst)
    if missing or unplaced:
        print(f"placement.json names not on the board: {sorted(missing)}; parts with no position: {sorted(unplaced)}")
        return 1
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(d)
    for z in list(board.Zones()):
        board.Remove(z)
    board.Save(str(path))
    return 0


def stage_outline(bdir: Path) -> int:
    """Draw the board outline and add ground pours on the front, first inner and back layers."""
    name, spec, path = _paths(bdir)
    w, h = spec["size_mm"]
    board = pcbnew.LoadBoard(str(path))
    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pcbnew.VECTOR2I(mm(OX), mm(OY)))
    rect.SetEnd(pcbnew.VECTOR2I(mm(OX + w), mm(OY + h)))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(mm(0.1))
    board.Add(rect)
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.B_Cu):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(gnd)
        zone.SetZoneName(f"GND_{board.GetLayerName(layer)}")
        pts = pcbnew.VECTOR_VECTOR2I()
        for px, py in ((0, 0), (w, 0), (w, h), (0, h)):
            pts.append(pcbnew.VECTOR2I(mm(OX + px), mm(OY + py)))
        zone.AddPolygon(pts)
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        board.Add(zone)
    board.Save(str(path))
    return 0


def stage_fill(bdir: Path) -> int:
    name, spec, path = _paths(bdir)
    board = pcbnew.LoadBoard(str(path))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(path))
    return 0


STAGES = {"move": stage_move, "outline": stage_outline, "fill": stage_fill}


def main() -> int:
    bdir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        return STAGES[sys.argv[2]](bdir)
    # each stage runs in its own process: pcbnew's Python objects misbehave after a save or removal
    import subprocess
    for stage in STAGES:
        r = subprocess.run([sys.executable, __file__, str(bdir), stage], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout + r.stderr[-800:])
            return r.returncode
    name, spec, _ = _paths(bdir)
    print(f"{name}: placed {len(spec['parts'])} parts on {spec['size_mm'][0]} x {spec['size_mm'][1]} mm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
