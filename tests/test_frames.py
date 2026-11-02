import sys
import time
from pathlib import Path
import pytest
from forgestar.frames import MAX_FRAME, Frame, FrameError, Record, decode, pack, short_id

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ground" / "gateway"))
import gateway as gwmod  # noqa: E402


def rec(i):
    return Record(short_id(f"pump-{i:04d}"), 1_790_000_000 + i, -24.12345, 29.54321, {"flow_lpm": 120.5, "i": i})


def test_round_trip():
    raw = Frame(7, 42, 1_790_000_100, [rec(1), rec(2)]).encode()
    f = decode(raw)
    assert (f.sat_id, f.seq, len(f.records)) == (7, 42, 2)
    assert f.records[0].payload == {"flow_lpm": 120.5, "i": 1}
    assert abs(f.records[0].lat + 24.12345) < 1e-5


def test_crc_detects_corruption():
    raw = bytearray(Frame(1, 1, 0, [rec(1)]).encode()); raw[20] ^= 0xFF
    with pytest.raises(FrameError):
        decode(bytes(raw))


def test_pack_splits_large_batches():
    frames = pack(3, 100, 0, [rec(i) for i in range(500)])
    assert len(frames) > 1 and all(len(f) <= MAX_FRAME for f in frames)
    decoded = [decode(f) for f in frames]
    assert sum(len(f.records) for f in decoded) == 500
    assert [f.seq for f in decoded] == list(range(100, 100 + len(frames)))
    assert all(f.more for f in decoded[:-1]) and not decoded[-1].more


def test_gateway_decodes_dedupes_and_maps_devices():
    out = []
    reg = {short_id("pump-0001"): {"device_id": "pump-0001", "kind": "pump", "customer": "Mine"}}
    g = gwmod.Gateway(out.append, reg.get)
    raw = Frame(5, 9, 1_790_000_500, [rec(1), rec(2)]).encode()
    assert g.handle(raw, "test", received_ts=1_790_000_600) == 2
    assert g.handle(raw, "test") == 0 and g.stats["duplicates"] == 1   # overlapping gateway pass
    assert out[0]["device_id"] == "pump-0001" and out[0]["path"] == "satellite" and out[0]["sat"] == 5
    assert out[0]["received_ts"] - out[0]["ts"] == 599
    assert out[1]["device_id"].startswith("unknown-") and g.stats["unknown_device"] == 1
    assert g.handle(b"garbage-bytes-here-xx", "test") is None and g.stats["bad"] == 1


def test_gateway_frame_dir(tmp_path):
    out = []
    g = gwmod.Gateway(out.append, lambda s: None)
    (tmp_path / "pass1.bin").write_bytes(Frame(1, 1, 0, [rec(1)]).encode())
    (tmp_path / "junk.bin").write_bytes(b"nope")
    (tmp_path / "pass1-again.bin").write_bytes(Frame(1, 1, 0, [rec(1)]).encode())  # duplicate -> done, not bad
    gwmod.scan_dir(g, tmp_path)
    assert (tmp_path / "done" / "pass1-again.bin").exists()
    assert (tmp_path / "done" / "pass1.bin").exists() and (tmp_path / "bad" / "junk.bin").exists() and len(out) == 1


def test_gateway_link_with_errors():
    from forgestar.fec import encode_block
    import random
    out = []; g = gwmod.Gateway(out.append, lambda s: None)
    blk = bytearray(encode_block(Frame(2, 5, 0, [rec(i) for i in range(10)]).encode()))
    for p in random.Random(9).sample(range(4, len(blk)), 10): blk[p] ^= 0x5A
    assert g.handle_link(b"noise" + bytes(blk), "test") == 10
    assert g.stats["fec_corrected_bytes"] == 10 and g.stats["link_blocks"] == 1


def test_gateway_holds_unregistered_devices_until_registered():
    out, reg = [], {}
    g = gwmod.Gateway(out.append, reg.get, grace_s=60)
    g.handle(Frame(1, 1, 0, [rec(1)]).encode(), "test")
    assert out == [] and len(g.unresolved) == 1
    reg[short_id("pump-0001")] = {"device_id": "pump-0001", "kind": "pump", "customer": "Mine"}
    g.retry_unresolved()
    assert out[0]["device_id"] == "pump-0001" and not g.unresolved and g.stats["unknown_device"] == 0
    g.handle(Frame(1, 2, 0, [rec(2)]).encode(), "test")
    g.retry_unresolved(now=time.time() + 61)          # never registered -> published as unknown after grace
    assert out[-1]["device_id"].startswith("unknown-")
