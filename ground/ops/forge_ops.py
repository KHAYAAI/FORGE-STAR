"""FORGE STAR mission operations: command and monitor the F´ payload software over its ground link.

A small, dependency-free alternative to fprime-gds for operators and CI:
  * listens as the ground end of the F´ TCP link (the flight software's TcpClient connects to it)
  * frames commands with F´'s protocol (0xDEADBEEF start word, size, packet, CRC-32)
  * decodes downlinked events and telemetry using the deployment's generated JSON dictionary
  * signs commands (HMAC-SHA256 + counter) when the flight software has command authentication on

Usage:
  python3 ground/ops/forge_ops.py --dict <PayloadTopologyDictionary.json> --port 50000 \
      --cmd Payload.cmdDisp.CMD_NO_OP --cmd "Payload.storeForward.SF_PASS_START" --listen 10
  (then start the flight software with -a 127.0.0.1 -p 50000)
"""
from __future__ import annotations

import argparse
import json
import socket
import struct
import threading
import time
import zlib
from dataclasses import dataclass, field
from pathlib import Path

START_WORD = 0xDEADBEEF
PKT_COMMAND, PKT_TELEM, PKT_LOG = 0, 1, 2

_INT = {(8, True): "b", (8, False): "B", (16, True): "h", (16, False): "H", (32, True): "i", (32, False): "I",
        (64, True): "q", (64, False): "Q"}


class Dictionary:
    def __init__(self, path: str | Path):
        d = json.loads(Path(path).read_text())
        self.types = {t["qualifiedName"]: t for t in d.get("typeDefinitions", [])}
        self.commands = {c["name"]: c for c in d["commands"]}
        self.events = {e["id"]: e for e in d["events"]}
        self.channels = {c["id"]: c for c in d["telemetryChannels"]}
        self.event_by_name = {e["name"]: e for e in d["events"]}

    # ---- (de)serialisation of F´ types (big-endian) ----
    def _resolve(self, t):
        if t.get("kind") == "qualifiedIdentifier":
            return self.types[t["name"]]
        return t

    def decode(self, t, buf: bytes, off: int):
        t = self._resolve(t)
        kind = t.get("kind")
        if kind == "integer":
            f = ">" + _INT[(t["size"], t["signed"])]
            return struct.unpack_from(f, buf, off)[0], off + struct.calcsize(f)
        if kind == "float":
            f = ">f" if t["size"] == 32 else ">d"
            return struct.unpack_from(f, buf, off)[0], off + struct.calcsize(f)
        if kind == "bool":
            return buf[off] != 0, off + 1
        if kind == "string":
            n = struct.unpack_from(">H", buf, off)[0]
            return buf[off + 2:off + 2 + n].decode(errors="replace"), off + 2 + n
        if kind == "enum":
            v, off = self.decode(t["representationType"], buf, off)
            names = {c["value"]: c["name"] for c in t["enumeratedConstants"]}
            return names.get(v, v), off
        if kind == "struct":
            out = {}
            for name, m in sorted(t["members"].items(), key=lambda kv: kv[1].get("index", 0)):
                out[name], off = self.decode(m["type"], buf, off)
            return out, off
        if kind == "array":
            out = []
            for _ in range(t["size"]):
                v, off = self.decode(t["elementType"], buf, off); out.append(v)
            return out, off
        raise ValueError(f"unsupported type {t}")

    def encode(self, t, v) -> bytes:
        t = self._resolve(t)
        kind = t.get("kind")
        if kind == "integer":
            return struct.pack(">" + _INT[(t["size"], t["signed"])], int(v))
        if kind == "float":
            return struct.pack(">f" if t["size"] == 32 else ">d", float(v))
        if kind == "bool":
            return b"\x01" if str(v).lower() in ("1", "true", "yes") else b"\x00"
        if kind == "string":
            b = str(v).encode(); return struct.pack(">H", len(b)) + b
        if kind == "enum":
            names = {c["name"].split(".")[-1]: c["value"] for c in t["enumeratedConstants"]}
            return self.encode(t["representationType"], names.get(str(v), v))
        raise ValueError(f"unsupported command argument type {t}")


def frame(packet: bytes) -> bytes:
    hdr = struct.pack(">II", START_WORD, len(packet))
    return hdr + packet + struct.pack(">I", zlib.crc32(hdr + packet) & 0xFFFFFFFF)


def command_packet(dic: Dictionary, name: str, args: list[str]) -> bytes:
    c = dic.commands[name]
    params = c["formalParams"]
    if len(args) != len(params):
        raise ValueError(f"{name} takes {len(params)} argument(s): {[p['name'] for p in params]}")
    body = b"".join(dic.encode(p["type"], a) for p, a in zip(params, args))
    return struct.pack(">II", PKT_COMMAND, c["opcode"]) + body


def format_event(fmt: str, args: list) -> str:
    """Fill F´ format strings: {}, {x}, {d}, {.2f} and friends."""
    import re
    it = iter(args)
    def rep(m):
        spec = m.group(1)
        try:
            v = next(it)
        except StopIteration:
            return m.group(0)
        if not spec:
            return str(v)
        spec = spec.lstrip(":")
        try:
            return format(v, spec)
        except (ValueError, TypeError):
            return str(v)
    return re.sub(r"\{([^{}]*)\}", rep, fmt)


def _time(buf: bytes, off: int):
    base, ctx, sec, usec = struct.unpack_from(">HBII", buf, off)
    return sec + usec / 1e6, off + 11


@dataclass
class Downlink:
    events: list[dict] = field(default_factory=list)
    telemetry: dict[str, object] = field(default_factory=dict)
    bad_frames: int = 0


def parse_packets(dic: Dictionary, data: bytes, dl: Downlink) -> bytes:
    """Consume complete frames from data; return what is left (partial frame)."""
    while True:
        i = data.find(struct.pack(">I", START_WORD))
        if i < 0:
            return data[-3:]
        data = data[i:]
        if len(data) < 8:
            return data
        size = struct.unpack_from(">I", data, 4)[0]
        if len(data) < 8 + size + 4:
            return data
        body, crc = data[8:8 + size], struct.unpack_from(">I", data, 8 + size)[0]
        if zlib.crc32(data[:8 + size]) & 0xFFFFFFFF != crc:
            dl.bad_frames += 1; data = data[1:]; continue
        data = data[8 + size + 4:]
        ptype = struct.unpack_from(">I", body, 0)[0]
        if ptype == PKT_LOG:
            eid = struct.unpack_from(">I", body, 4)[0]; t, off = _time(body, 8)
            e = dic.events.get(eid)
            if not e:
                continue
            args = []
            for p in e["formalParams"]:
                v, off = dic.decode(p["type"], body, off); args.append(v)
            text = format_event(e["format"], args)
            dl.events.append({"name": e["name"], "severity": e["severity"], "time": t, "args": args, "text": text})
        elif ptype == PKT_TELEM:
            off = 4
            while off + 15 <= len(body):            # TlmChan packs several (id, time, value) entries
                cid = struct.unpack_from(">I", body, off)[0]; t, off = _time(body, off + 4)
                ch = dic.channels.get(cid)
                if not ch:
                    break
                try:
                    dl.telemetry[ch["name"]], off = dic.decode(ch["type"], body, off)
                except (ValueError, KeyError, struct.error):
                    break


class GroundLink:
    """TCP server the flight software connects to."""

    def __init__(self, dic: Dictionary, port: int, signer=None):
        self.dic, self.signer = dic, signer
        self.srv = socket.socket(); self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("127.0.0.1", port)); self.srv.listen(1)
        self.conn = None; self.dl = Downlink(); self._stop = False

    def wait_for_flight(self, timeout=30.0):
        self.srv.settimeout(timeout); self.conn, _ = self.srv.accept()
        threading.Thread(target=self._rx, daemon=True).start()

    def _rx(self):
        buf = b""
        self.conn.settimeout(0.5)
        while not self._stop:
            try:
                chunk = self.conn.recv(65536)
            except socket.timeout:
                continue
            except OSError:
                return
            if not chunk:
                return
            buf = parse_packets(self.dic, buf + chunk, self.dl)

    def send(self, name: str, *args):
        pkt = command_packet(self.dic, name, list(args))
        if self.signer:
            pkt = self.signer.sign(pkt)
        self.conn.sendall(frame(pkt))

    def wait_event(self, name_part: str, timeout=10.0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            for e in self.dl.events:
                if name_part in e["name"]:
                    return e
            time.sleep(0.05)
        return None

    def close(self):
        self._stop = True
        for s in (self.conn, self.srv):
            try:
                s and s.close()
            except OSError:
                pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dict", required=True); ap.add_argument("--port", type=int, default=50000)
    ap.add_argument("--cmd", action="append", default=[], help='command name and args, e.g. "Payload.cmdDisp.CMD_NO_OP"')
    ap.add_argument("--listen", type=float, default=10.0, help="seconds to show downlink after sending")
    ap.add_argument("--key", help="hex HMAC key (command authentication)")
    a = ap.parse_args()
    dic = Dictionary(a.dict)
    signer = None
    if a.key:
        from cmd_auth import Signer
        signer = Signer(bytes.fromhex(a.key))
    link = GroundLink(dic, a.port, signer)
    print(f"waiting for flight software on 127.0.0.1:{a.port} ...", flush=True)
    link.wait_for_flight(timeout=120)
    print("connected", flush=True)
    for c in a.cmd:
        name, *args = c.split()
        link.send(name, *args); print(f"> {c}", flush=True); time.sleep(0.5)
    t0, shown = time.time(), 0
    while time.time() - t0 < a.listen:
        for e in link.dl.events[shown:]:
            print(f"  [{e['severity']}] {e['name']}: {e['text']}")
        shown = len(link.dl.events); time.sleep(0.2)
    print("telemetry:", json.dumps({k: v for k, v in sorted(link.dl.telemetry.items()) if "storeForward" in k or "payloadSim" in k}, default=str))
    link.close()


if __name__ == "__main__":
    main()
