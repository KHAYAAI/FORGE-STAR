"""Autoroute a placed board with Freerouting, then refill the ground pours.

Usage: FREEROUTING_JAR=/path/freerouting.jar python3 tools/route.py boards/pib
Needs KiCad 10 (pcbnew Python module) and Java 17+. Get the JAR from
https://github.com/freerouting/freerouting/releases (v1.9.0 was the version planned for this repo).

Not yet run: executing the downloaded JAR was blocked in the cloud session where this was written.
An autorouted board is a starting point. RF, power and decoupling traces need an engineer's review.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pcbnew


def main() -> int:
    bdir = Path(sys.argv[1])
    name = bdir.name
    pcb = bdir / "eda" / f"{name}.kicad_pcb"
    dsn, ses = pcb.with_suffix(".dsn"), pcb.with_suffix(".ses")
    stage = sys.argv[2] if len(sys.argv) > 2 else None
    if stage == "export":
        board = pcbnew.LoadBoard(str(pcb))
        return 0 if pcbnew.ExportSpecctraDSN(board, str(dsn)) else 1
    if stage == "import":
        board = pcbnew.LoadBoard(str(pcb))
        if not pcbnew.ImportSpecctraSES(board, str(ses)):
            return 1
        board.Save(str(pcb))
        return 0
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
        ["java", "-Djava.awt.headless=true", "-jar", jar, "-de", str(dsn), "-do", str(ses), "-mp", "30"],
        [sys.executable, __file__, str(bdir), "import"],
        [sys.executable, __file__, str(bdir), "fill"],
    ]
    for cmd in steps:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if r.returncode:
            print(" ".join(cmd[:4]), "failed:", (r.stdout + r.stderr)[-600:])
            return r.returncode
    dsn.unlink(missing_ok=True)
    ses.unlink(missing_ok=True)
    print(f"{name}: routed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
