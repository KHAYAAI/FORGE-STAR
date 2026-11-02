"""Run the F´ payload deployment headless and check its downlink on the ground side.

  python3 flight/run_payload.py                 # native build (fprime-util build)
  python3 flight/run_payload.py --arch aarch64   # ARM build under qemu-aarch64 (fprime-util build aarch64-linux)

The binary runs with simulated hardware (PayloadSim) at 50x speed; every link block it
"transmits" is decoded by forgestar.fec + frames. Exit 0 only if all blocks decode,
no message is lost or reordered, and at least `--min-passes` passes completed.
"""
from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from forgestar.fec import decode_stream  # noqa: E402
from forgestar.frames import decode  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", choices=["native", "aarch64"], default="native")
    ap.add_argument("--seconds", type=float, default=6.0)
    ap.add_argument("--min-passes", type=int, default=3)
    a = ap.parse_args()
    plat = "Linux" if a.arch == "native" else "aarch64-linux"
    exe = ROOT / "flight/fprime/build-artifacts" / plat / "Payload/bin/Payload"
    if not exe.exists():
        sys.exit(f"build first: cd flight/fprime && fprime-util build {'' if a.arch == 'native' else 'aarch64-linux'}")
    cmd = [str(exe), "-a", "127.0.0.1", "-p", "50997"]
    if a.arch == "aarch64":
        cmd = ["qemu-aarch64", "-L", "/usr/aarch64-linux-gnu"] + cmd
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "downlink.raw"
        env = dict(os.environ, FORGE_CYCLE_MS="20", FORGE_DOWNLINK=str(raw))
        p = subprocess.Popen(cmd, cwd=td, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(a.seconds)
        p.send_signal(signal.SIGINT)
        try:
            log, _ = p.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill(); log, _ = p.communicate()
        passes = len(re.findall(r"PassEnded", log))
        frames, st = decode_stream(raw.read_bytes() if raw.exists() else b"")
    decoded = [decode(f) for f in frames]
    seqs = [r.payload["seq"] for f in decoded for r in f.records]
    ok = st["failed"] == 0 and passes >= a.min_passes and seqs == list(range(len(seqs))) and len(seqs) > 0
    print(f"{a.arch}: {passes} passes, {st['blocks']} link blocks, {len(seqs)} messages, "
          f"failed blocks {st['failed']}, in order and complete: {seqs == list(range(len(seqs)))} -> {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
