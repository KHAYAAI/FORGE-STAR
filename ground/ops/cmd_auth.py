"""Ground-side command signing: HMAC-SHA256 over <command packet || u32 counter>.

Matches flight/libforge/src/forge_auth.c. The counter must always increase; it is kept in a
small state file so it survives operator restarts (seeded from the clock the first time).
Keys: one per satellite, generated with `python3 ground/ops/cmd_auth.py new-key`, stored in the
operator's secret store (never in the repo), and loaded onto the satellite before launch.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import struct
import sys
import time
from pathlib import Path

EPOCH = 1_767_225_600  # 2026-01-01 UTC: counters start near (now - EPOCH) so a lost state file never goes backwards


class Signer:
    def __init__(self, key: bytes, state_file: str | Path | None = None):
        self.key = key
        self.state = Path(state_file or os.environ.get("FORGE_CMD_COUNTER_FILE", Path.home() / ".forge_cmd_counter"))
        try:
            self.counter = int(self.state.read_text())
        except (OSError, ValueError):
            self.counter = 0
        self.counter = max(self.counter, int(time.time()) - EPOCH)

    def sign(self, packet: bytes) -> bytes:
        self.counter += 1
        try:
            self.state.write_text(str(self.counter))
        except OSError:
            pass
        body = packet + struct.pack(">I", self.counter)
        return body + hmac.new(self.key, body, hashlib.sha256).digest()


def verify(key: bytes, signed: bytes, last_counter: int) -> tuple[bool, int]:
    """Reference verifier (same rules as the satellite)."""
    body, tag = signed[:-32], signed[-32:]
    if not hmac.compare_digest(hmac.new(key, body, hashlib.sha256).digest(), tag):
        return False, last_counter
    counter = struct.unpack(">I", body[-4:])[0]
    return (counter > last_counter), max(counter, last_counter)


if __name__ == "__main__":
    if sys.argv[1:] == ["new-key"]:
        print(secrets.token_hex(32))
    else:
        print(__doc__)
