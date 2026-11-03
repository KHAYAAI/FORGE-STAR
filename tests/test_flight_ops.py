"""Integration: command the real F´ payload binary over its ground link, with command authentication.
Skipped unless the deployment has been built (cd flight/fprime && fprime-util build)."""
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "flight/fprime/build-artifacts/Linux/Payload/bin/Payload"
DICT = ROOT / "flight/fprime/build-artifacts/Linux/Payload/dict/PayloadTopologyDictionary.json"
sys.path.insert(0, str(ROOT / "ground" / "ops"))
pytestmark = pytest.mark.skipif(not EXE.exists(), reason="F´ deployment not built")


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


@pytest.fixture
def flight(tmp_path):
    import forge_ops
    from cmd_auth import Signer
    key = secrets.token_bytes(32)
    port = free_port()
    dic = forge_ops.Dictionary(DICT)
    link = forge_ops.GroundLink(dic, port, Signer(key, tmp_path / "counter"))
    env = dict(os.environ, FORGE_CMD_KEY=key.hex(), FORGE_CYCLE_MS="50", FORGE_DOWNLINK=str(tmp_path / "dl.raw"))
    p = subprocess.Popen([str(EXE), "-a", "127.0.0.1", "-p", str(port)], cwd=tmp_path, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    link.wait_for_flight(timeout=30)
    yield link, dic, forge_ops
    p.terminate(); p.wait(timeout=10); link.close()


def test_signed_command_runs_unsigned_and_replayed_do_not(flight):
    link, dic, ops = flight
    # unsigned: rejected by CmdAuth, never reaches the dispatcher
    link.conn.sendall(ops.frame(ops.command_packet(dic, "Payload.cmdDisp.CMD_NO_OP", [])))
    assert link.wait_event("cmdAuth.Rejected", 10)["args"][0] in ("BAD_SIGNATURE", "TOO_SHORT", "CmdAuth_RejectReason.BAD_SIGNATURE")
    assert not any("NoOpReceived" in e["name"] for e in link.dl.events)
    # signed: executes
    signed = link.signer.sign(ops.command_packet(dic, "Payload.cmdDisp.CMD_NO_OP", []))
    link.conn.sendall(ops.frame(signed))
    assert link.wait_event("NoOpReceived", 10)
    # replay of the same signed packet: rejected
    n_noop = sum("NoOpReceived" in e["name"] for e in link.dl.events)
    link.conn.sendall(ops.frame(signed)); time.sleep(1.5)
    assert sum("NoOpReceived" in e["name"] for e in link.dl.events) == n_noop
    assert any("REPLAY" in str(e["args"]) for e in link.dl.events if "Rejected" in e["name"])
    # tampered (flip a byte in the opcode): rejected
    bad = bytearray(link.signer.sign(ops.command_packet(dic, "Payload.cmdDisp.CMD_NO_OP", []))); bad[7] ^= 1
    link.conn.sendall(ops.frame(bytes(bad))); time.sleep(1.0)
    assert sum("NoOpReceived" in e["name"] for e in link.dl.events) == n_noop


def test_payload_commands_and_telemetry(flight):
    link, dic, ops = flight
    link.send("Payload.storeForward.SF_PASS_START")
    assert link.wait_event("PassStarted", 10)
    t0 = time.time()
    while "Payload.storeForward.BlocksSent" not in link.dl.telemetry and time.time() - t0 < 10:
        time.sleep(0.1)
    assert link.dl.telemetry.get("Payload.cmdAuth.Accepted", 0) >= 1
    assert "Payload.storeForward.Stored" in link.dl.telemetry


def test_safe_mode_stops_transmission_and_needs_healthy_power(flight):
    link, dic, ops = flight
    link.send("Payload.modeManager.MM_SAFE")
    assert link.wait_event("EnteredSafe", 10)
    assert link.wait_event("storeForward.ModeChanged", 10)["args"][0] is True
    n_blocks = link.dl.telemetry.get("Payload.storeForward.BlocksSent", 0)
    link.send("Payload.storeForward.SF_PASS_START"); time.sleep(2.0)
    assert link.dl.telemetry.get("Payload.storeForward.BlocksSent", 0) == n_blocks   # transmitter inhibited
    link.send("Payload.modeManager.MM_NOMINAL")                                     # bus at 7.4 V -> allowed
    assert link.wait_event("ExitedSafe", 10)


def test_store_survives_restart(tmp_path):
    """Messages stored before a reboot are restored and still downlink afterwards."""
    import forge_ops
    from cmd_auth import Signer
    key = secrets.token_bytes(32); store = tmp_path / "store.bin"
    dic = forge_ops.Dictionary(DICT)
    for run in range(2):
        port = free_port()
        link = forge_ops.GroundLink(dic, port, Signer(key, tmp_path / "counter"))
        env = dict(os.environ, FORGE_CMD_KEY=key.hex(), FORGE_CYCLE_MS="50", FORGE_STORE=str(store),
                   FORGE_DOWNLINK=str(tmp_path / f"dl{run}.raw"))
        p = subprocess.Popen([str(EXE), "-a", "127.0.0.1", "-p", str(port)], cwd=tmp_path, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        link.wait_for_flight(timeout=30)
        if run == 0:
            time.sleep(0.6)                       # store some messages (no pass yet: first pass is at ~22 s sim)
            link.send("Payload.storeForward.SF_SAVE")
            assert link.wait_event("storeForward.Saved", 10)
        else:
            ev = link.wait_event("storeForward.Restored", 10)
            assert ev and ev["args"][0] > 0
        p.terminate(); p.wait(timeout=10); link.close()
