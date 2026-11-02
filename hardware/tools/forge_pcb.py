"""FORGE STAR in-house PCB pipeline (open-source replacement for an AI PCB service).

circuit-as-code (SKiDL)  ->  placement (this file, KiCad pcbnew API)  ->  autoroute (Freerouting)
 ->  ground pours + DRC (pcbnew)  ->  fab outputs (kicad-cli: Gerbers, drill, pick-and-place, BOM, SVG)

Usage (from a board script):
    from forge_pcb import Board
    Board("pib", width_mm=50, height_mm=36, ic_positions={...}).build(circuit)
Needs: KiCad 7+ (pcbnew Python module, kicad-cli), Java 17+, freerouting.jar (FREEROUTING_JAR env var).
"""
from __future__ import annotations

import csv
import math
import os
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import pcbnew

FP_DIR = Path(os.environ.get("KICAD_FOOTPRINT_DIR", "/usr/share/kicad/footprints"))
POWER_NETS = {"GND", "+3V3", "VIN", "VIN_SENSE", "RADIO_PWR"}


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


class Board:
    def __init__(self, name: str, out_dir: Path, width_mm: float, height_mm: float,
                 ic_positions: dict[str, tuple[float, float, float]], edge_parts: dict[str, tuple[float, float, float]],
                 track_mm: float = 0.2, power_track_mm: float = 0.5, clearance_mm: float = 0.15):
        self.name, self.out = name, Path(out_dir)
        self.w, self.h = width_mm, height_mm
        self.ic_pos, self.edge_pos = ic_positions, edge_parts
        self.track, self.ptrack, self.clear = track_mm, power_track_mm, clearance_mm
        self.board = pcbnew.BOARD()
        self.fps: dict[str, pcbnew.FOOTPRINT] = {}
        self.log: list[str] = []

    # ---------------- board spec (parts, footprints, pin->net) -> footprints + nets ----------------
    def load(self, parts: list[dict]):
        nets: dict[str, pcbnew.NETINFO_ITEM] = {}
        for part in parts:
            lib, fp_name = part["footprint"].split(":")
            fp = pcbnew.FootprintLoad(str(FP_DIR / f"{lib}.pretty"), fp_name)
            if fp is None:
                raise RuntimeError(f"footprint not found: {part['footprint']}")
            fp.SetReference(part["ref"]); fp.SetValue(part["value"])
            self.board.Add(fp); self.fps[part["ref"]] = fp
            for num, net in part["pins"].items():
                if net not in nets:
                    ni = pcbnew.NETINFO_ITEM(self.board, net); self.board.Add(ni); nets[net] = ni
                for pad in fp.Pads():
                    if pad.GetNumber() == num:
                        pad.SetNet(nets[net])
        self.parts = {p["ref"]: p for p in parts}
        self.log.append(f"{len(self.fps)} footprints, {len(nets)} nets")

    # ---------------- placement ----------------
    def _part_nets(self, ref):
        return {pad.GetNetname() for pad in self.fps[ref].Pads() if pad.GetNetname()}

    def place(self):
        def put(ref, x, y, rot=0.0):
            fp = self.fps[ref]
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); fp.SetOrientationDegrees(rot)
        for ref, (x, y, r) in {**self.ic_pos, **self.edge_pos}.items():
            put(ref, x, y, r)
        anchors = list(self.ic_pos)
        ring = defaultdict(int)
        # each passive goes next to the IC it shares the most signal nets with (power nets count less)
        for ref in sorted(self.fps):
            if ref in self.ic_pos or ref in self.edge_pos:
                continue
            mine = self._part_nets(ref)
            def score(a):
                common = mine & self._part_nets(a)
                return sum(3 if n not in POWER_NETS else 1 for n in common)
            best = max(anchors, key=score)
            ax, ay, _ = self.ic_pos[best]
            k = ring[best]; ring[best] += 1
            ang = (k * 47) % 360  # spread around the anchor
            rad = 4.2 + 1.6 * (k // 6)
            x = min(max(ax + rad * math.cos(math.radians(ang)), 2.5), self.w - 2.5)
            y = min(max(ay + rad * math.sin(math.radians(ang)), 2.5), self.h - 2.5)
            put(ref, x, y, 90.0 if (k % 2) else 0.0)
        self._spread()

    def _spread(self, iters=200):
        """Push overlapping footprints apart (courtyard bounding boxes), keeping ICs/connectors fixed."""
        fixed = set(self.ic_pos) | set(self.edge_pos)
        for _ in range(iters):
            moved = False
            items = list(self.fps.items())
            for i, (ra, a) in enumerate(items):
                ba = a.GetBoundingBox(False, False)
                for rb, b in items[i + 1:]:
                    bb = b.GetBoundingBox(False, False)
                    if not ba.Intersects(bb):
                        continue
                    if ra in fixed and rb in fixed:
                        continue
                    mover, other = (b, a) if (ra in fixed or (rb not in fixed and rb > ra)) else (a, b)
                    pm, po = mover.GetPosition(), other.GetPosition()
                    dx, dy = pm.x - po.x, pm.y - po.y
                    d = math.hypot(dx, dy) or 1.0
                    step = mm(0.4)
                    nx = min(max(pm.x + int(step * dx / d), mm(2.0)), mm(self.w - 2.0))
                    ny = min(max(pm.y + int(step * dy / d), mm(2.0)), mm(self.h - 2.0))
                    mover.SetPosition(pcbnew.VECTOR2I(nx, ny)); moved = True
                    ba = a.GetBoundingBox(False, False)
            if not moved:
                break

    # ---------------- outline, rules ----------------
    def outline(self):
        pts = [(0, 0), (self.w, 0), (self.w, self.h), (0, self.h)]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            s = pcbnew.PCB_SHAPE(self.board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1))); s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); self.board.Add(s)
        ds = self.board.GetDesignSettings()
        nc = ds.m_NetSettings.m_DefaultNetClass
        nc.SetTrackWidth(mm(self.track)); nc.SetClearance(mm(self.clear))
        nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
        pwr = pcbnew.NETCLASS("Power")
        pwr.SetTrackWidth(mm(self.ptrack)); pwr.SetClearance(mm(self.clear))
        pwr.SetViaDiameter(mm(0.8)); pwr.SetViaDrill(mm(0.4))
        ds.m_NetSettings.m_NetClasses["Power"] = pwr
        for n in POWER_NETS - {"GND"}:
            ds.m_NetSettings.m_NetClassPatternAssignments.append((pcbnew.EDA_COMBINED_MATCHER(n, pcbnew.CTX_NETCLASS), "Power")) \
                if hasattr(ds.m_NetSettings, "m_NetClassPatternAssignments") else None
        ds.SetCopperLayerCount(2)

    # ---------------- autoroute ----------------
    def route(self, jar: str | None, passes: int = 40):
        jar = jar or os.environ.get("FREEROUTING_JAR")
        dsn, ses = self.out / f"{self.name}.dsn", self.out / f"{self.name}.ses"
        if not pcbnew.ExportSpecctraDSN(self.board, str(dsn)):
            raise RuntimeError("DSN export failed")
        if not jar or not Path(jar).exists():
            self.log.append("autoroute skipped (no freerouting.jar)"); return False
        cmd = ["java", "-jar", jar, "-de", str(dsn), "-do", str(ses), "-mp", str(passes), "-host-mode", "cli"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if not ses.exists():
            raise RuntimeError("freerouting produced no session file:\n" + r.stdout[-2000:] + r.stderr[-2000:])
        if not pcbnew.ImportSpecctraSES(self.board, str(ses)):
            raise RuntimeError("SES import failed")
        self.log.append(f"autorouted: {sum(1 for t in self.board.GetTracks())} track/via items")
        return True

    def ground_pours(self):
        # Zone filling needs a board with full project/connectivity state: save, reload, then fill.
        tmp = self.out / f"{self.name}.kicad_pcb"
        self.board.Save(str(tmp))
        self.board = pcbnew.LoadBoard(str(tmp))
        self.fps = {fp.GetReference(): fp for fp in self.board.GetFootprints()}
        gnd = self.board.FindNet("GND")
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(self.board); z.SetLayer(layer); z.SetNet(gnd)
            z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.2))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            ol = z.Outline(); ol.NewOutline()
            for x, y in [(0.5, 0.5), (self.w - 0.5, 0.5), (self.w - 0.5, self.h - 0.5), (0.5, self.h - 0.5)]:
                ol.Append(mm(x), mm(y))
            self.board.Add(z)
        self.board.BuildConnectivity()
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())

    # ---------------- checks + outputs ----------------
    # DRC categories that stop a board going to fab; the rest are reviewed but not blocking.
    BLOCKING = {"clearance", "shorting_items", "tracks_crossing", "courtyards_overlap", "copper_edge_clearance",
                "hole_clearance", "hole_to_hole", "track_width", "via_diameter", "annular_width",
                "drill_out_of_range", "items_not_allowed", "malformed_courtyard", "invalid_outline",
                "solder_mask_bridge", "unconnected_items"}

    def drc(self) -> dict:
        import re
        rpt = self.out / f"{self.name}-drc.rpt"
        pcbnew.WriteDRCReport(self.board, str(rpt), pcbnew.EDA_UNITS_MILLIMETRES, True)
        cats: dict[str, int] = defaultdict(int)
        for c in re.findall(r"^\[([a-z_]+)\]", rpt.read_text(), re.M):
            cats[c] += 1
        res = {"blocking": {k: v for k, v in cats.items() if k in self.BLOCKING},
               "review": {k: v for k, v in cats.items() if k not in self.BLOCKING},
               "unconnected": cats.get("unconnected_items", 0)}
        res["violations"] = sum(v for k, v in res["blocking"].items() if k != "unconnected_items")
        self.log.append(f"DRC: {res}")
        return res

    def write_project_libs(self, libs):
        """Project fp-lib-table so DRC can compare footprints with their source library."""
        rows = "\n".join(f'  (lib (name "{l}")(type "KiCad")(uri "{FP_DIR / (l + ".pretty")}")(options "")(descr ""))' for l in sorted(libs))
        (self.out / "fp-lib-table").write_text(f"(fp_lib_table\n  (version 7)\n{rows}\n)\n")
        (self.out / f"{self.name}.kicad_pro").write_text("{}\n") if not (self.out / f"{self.name}.kicad_pro").exists() else None

    def save(self) -> Path:
        path = self.out / f"{self.name}.kicad_pcb"
        self.board.Save(str(path))
        return path

    def fab_outputs(self, pcb: Path):
        fab = self.out / "fab"; fab.mkdir(exist_ok=True)
        cli = shutil.which("kicad-cli")
        if cli:
            layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
            subprocess.run([cli, "pcb", "export", "gerbers", "--layers", layers, "-o", str(fab) + "/", str(pcb)], check=True, capture_output=True)
            subprocess.run([cli, "pcb", "export", "drill", "-o", str(fab) + "/", str(pcb)], check=True, capture_output=True)
            subprocess.run([cli, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "-o", str(fab / f"{self.name}-pos.csv"), str(pcb)], check=True, capture_output=True)
            subprocess.run([cli, "pcb", "export", "svg", "--layers", "F.Cu,B.Cu,F.SilkS,Edge.Cuts", "--page-size-mode", "2",
                            "--exclude-drawing-sheet", "-o", str(self.out / f"{self.name}.svg"), str(pcb)], check=True, capture_output=True)
        with open(fab / f"{self.name}-bom.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Qty", "Value", "Footprint", "References"])
            groups = defaultdict(list)
            for ref, p in self.parts.items():
                groups[(p["value"], p["footprint"])].append(ref)
            for (val, fp), refs in sorted(groups.items()):
                w.writerow([len(refs), val, fp, " ".join(sorted(refs))])
        archive = shutil.make_archive(str(self.out / f"{self.name}-fab"), "zip", fab)
        self.log.append(f"fab package: {archive}")

    def build(self, parts: list[dict], jar: str | None = None) -> dict:
        self.out.mkdir(parents=True, exist_ok=True)
        self.write_project_libs({p["footprint"].split(":")[0] for p in parts})
        self.load(parts); self.log.append("loaded"); self.place(); self.log.append("placed"); self.outline()
        routed = self.route(jar)
        self.ground_pours()
        pcb = self.save()
        result = self.drc() | {"routed": routed, "pcb": str(pcb)}
        self.fab_outputs(pcb)
        (self.out / "build.log").write_text("\n".join(self.log) + "\n")
        return result


def main(argv=None):
    import argparse, faulthandler, json, sys
    faulthandler.enable()
    ap = argparse.ArgumentParser(description="Board spec JSON -> placed, (auto)routed, DRC-checked KiCad PCB + fab files")
    ap.add_argument("spec"); ap.add_argument("--jar", default=os.environ.get("FREEROUTING_JAR"))
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.spec).read_text())
    b = Board(spec["name"], Path(a.spec).parent, spec["width_mm"], spec["height_mm"],
              {k: tuple(v) for k, v in spec["ic_positions"].items()}, {k: tuple(v) for k, v in spec["edge_positions"].items()})
    res = b.build(spec["parts"], a.jar)
    print("PCB:", json.dumps(res))
    print("\n".join(b.log))
    ok = res["violations"] == 0 and (res["unconnected"] == 0 or not res["routed"])
    if not res["routed"]:
        print("NOTE: not routed. Placement checks only; run with --jar freerouting.jar to autoroute.")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
