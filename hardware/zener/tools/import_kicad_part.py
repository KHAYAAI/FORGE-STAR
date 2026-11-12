"""Copy one symbol and its footprint from the installed KiCad libraries into a Zener board package.

Zener's `Component()` reads a single-symbol `.kicad_sym` file and a `.kicad_mod` footprint that live
inside the package. This tool extracts the symbol (flattening KiCad's `extends` aliases) and copies
the footprint, so boards do not depend on the machine's KiCad install.

Usage: python3 tools/import_kicad_part.py <board_dir> <SymbolLib>:<Symbol> [<FootprintLib>:<Footprint>]
Example: python3 tools/import_kicad_part.py boards/pib Interface_CAN_LIN:SN65HVD230 Package_SO:SOIC-8_3.9x4.9mm_P1.27mm
KiCad libraries are CC-BY-SA 4.0 with the KiCad library exception.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

SYM_DIR = Path("/usr/share/kicad/symbols")
FP_DIR = Path("/usr/share/kicad/footprints")


def _block(text: str, start: int) -> str:
    depth = 0
    in_str = False
    i = start
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise ValueError("unbalanced s-expression")


def _symbol(lib_text: str, name: str) -> str:
    m = re.search(r'\n\s*\(symbol "%s"' % re.escape(name), lib_text)
    if not m:
        raise KeyError(name)
    return _block(lib_text, lib_text.index("(symbol", m.start()))


def _props(block: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r'\(property "([^"]+)"', block):
        out[m.group(1)] = _block(block, m.start())
    return out


def extract(lib: str, name: str) -> tuple[str, str]:
    """Return (flattened symbol s-expression, footprint property)."""
    text = (SYM_DIR / f"{lib}.kicad_sym").read_text()
    blk = _symbol(text, name)
    ext = re.search(r'\(extends "([^"]+)"\)', blk)
    if ext:
        parent, _ = extract(lib, ext.group(1))
        pname = ext.group(1)
        child_props = _props(blk)
        flat = parent.replace(f'(symbol "{pname}"', f'(symbol "{name}"', 1)
        flat = flat.replace(f'(symbol "{pname}_', f'(symbol "{name}_')
        for key, pblk in _props(flat).items():
            if key in child_props:
                flat = flat.replace(pblk, child_props[key])
        blk = flat
    fp = re.search(r'\(property "Footprint" "([^"]*)"', blk)
    return blk, fp.group(1) if fp else ""


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    board = Path(sys.argv[1])
    lib, name = sys.argv[2].split(":")
    blk, fp = extract(lib, name)
    if len(sys.argv) > 3:
        fp = sys.argv[3]
    parts = board / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    if fp:
        flib, fname = fp.split(":")
        src = FP_DIR / f"{flib}.pretty" / f"{fname}.kicad_mod"
        shutil.copy(src, parts / f"{fname}.kicad_mod")
        blk = re.sub(r'\(property "Footprint" "[^"]*"', f'(property "Footprint" "{fname}"', blk, count=1)
    (parts / f"{safe}.kicad_sym").write_text(
        "(kicad_symbol_lib (version 20220914) (generator forge_import)\n  " + blk + "\n)\n")
    print(f"{parts / (safe + '.kicad_sym')}  footprint: {fp or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
