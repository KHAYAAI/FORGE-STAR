"""Build flight/libforge with the system C compiler and decode its downlink in Python."""
import shutil
import subprocess
from pathlib import Path

import pytest

from forgestar.fec import decode_stream
from forgestar.frames import decode

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "flight" / "libforge"


@pytest.mark.skipif(not shutil.which("cc"), reason="no C compiler")
def test_c_payload_downlink_decodes_on_ground(tmp_path):
    exe = tmp_path / "test_libforge"
    subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic", "-I", str(LIB / "include"),
                    "-I", str(LIB / "test"), str(LIB / "src" / "forge.c"), str(LIB / "test" / "test_libforge.c"),
                    "-o", str(exe)], check=True)
    out = tmp_path / "downlink.raw"
    r = subprocess.run([str(exe), str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    frames, st = decode_stream(out.read_bytes())
    assert st["failed"] == 0 and st["blocks"] == len(frames) > 1
    decoded = [decode(f) for f in frames]
    assert sum(len(f.records) for f in decoded) == 16384               # FORGE_SF_CAPACITY
    assert [f.seq for f in decoded] == list(range(len(decoded)))
    times = [r.t_created for f in decoded for r in f.records]
    assert times == sorted(times) and times[0] == 1790000000           # oldest first, nothing lost
