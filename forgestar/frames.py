"""FORGE STAR store-and-forward downlink frame format (v1).

One frame carries a batch of device messages that a satellite stored on board.
The payload firmware encodes these; the SA gateway decodes them. Big-endian.

  Frame header (16 bytes)
    0  u8   magic 0xF5
    1  u8   version (1)
    2  u16  satellite id
    4  u32  frame sequence number (per satellite, wraps)
    8  u32  downlink time, unix seconds
    12 u16  record count
    14 u16  flags (bit 0: more frames follow in this pass)
  Records (repeated)
    0  u32  device short id   (crc32 of the device name; registry maps it back)
    4  u32  time created on the device, unix seconds
    8  i32  latitude  × 1e5
    12 i32  longitude × 1e5
    16 u16  payload length N
    18 N    payload (compact JSON; CBOR later)
  Trailer
       u32  CRC-32 of everything before it

Max frame size is 4096 bytes (fits one X-band transfer unit with room for FEC).
"""
from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass, field

MAGIC, VERSION, MAX_FRAME = 0xF5, 1, 4096
_HDR = struct.Struct(">BBHIIHH")
_REC = struct.Struct(">IIiiH")


class FrameError(ValueError):
    pass


def short_id(device_id: str) -> int:
    return zlib.crc32(device_id.encode()) & 0xFFFFFFFF


@dataclass
class Record:
    device_short_id: int
    t_created: int
    lat: float
    lon: float
    payload: dict

    def encode(self) -> bytes:
        body = json.dumps(self.payload, separators=(",", ":")).encode()
        if len(body) > 0xFFFF:
            raise FrameError("payload too large")
        return _REC.pack(self.device_short_id, self.t_created, round(self.lat * 1e5), round(self.lon * 1e5), len(body)) + body


@dataclass
class Frame:
    sat_id: int
    seq: int
    t_downlink: int
    records: list[Record] = field(default_factory=list)
    more: bool = False

    def encode(self) -> bytes:
        body = b"".join(r.encode() for r in self.records)
        raw = _HDR.pack(MAGIC, VERSION, self.sat_id, self.seq & 0xFFFFFFFF, self.t_downlink, len(self.records), int(self.more)) + body
        raw += struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)
        if len(raw) > MAX_FRAME:
            raise FrameError(f"frame {len(raw)} bytes > {MAX_FRAME}")
        return raw


def decode(raw: bytes) -> Frame:
    if len(raw) < _HDR.size + 4:
        raise FrameError("too short")
    (crc,) = struct.unpack(">I", raw[-4:])
    if zlib.crc32(raw[:-4]) & 0xFFFFFFFF != crc:
        raise FrameError("CRC mismatch")
    magic, ver, sat, seq, t, n, flags = _HDR.unpack_from(raw, 0)
    if magic != MAGIC or ver != VERSION:
        raise FrameError(f"bad magic/version {magic:#x}/{ver}")
    off, recs = _HDR.size, []
    for _ in range(n):
        sid, tc, la, lo, ln = _REC.unpack_from(raw, off); off += _REC.size
        recs.append(Record(sid, tc, la / 1e5, lo / 1e5, json.loads(raw[off:off + ln]))); off += ln
    if off != len(raw) - 4:
        raise FrameError("length mismatch")
    return Frame(sat, seq, t, recs, bool(flags & 1))


def pack(sat_id: int, seq0: int, t_downlink: int, records: list[Record]) -> list[bytes]:
    """Split records into as many frames as needed to respect MAX_FRAME."""
    frames, cur, size, seq = [], [], _HDR.size + 4, seq0
    for r in records:
        b = len(r.encode())
        if cur and size + b > MAX_FRAME:
            frames.append(Frame(sat_id, seq, t_downlink, cur, more=True)); seq += 1; cur, size = [], _HDR.size + 4
        cur.append(r); size += b
    if cur or not frames:
        frames.append(Frame(sat_id, seq, t_downlink, cur))
    return [f.encode() for f in frames]
