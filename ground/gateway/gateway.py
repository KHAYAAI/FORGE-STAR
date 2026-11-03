"""FORGE STAR gateway downlink handler.

Turns downlinked store-and-forward frames (forgestar.frames v1) into device
messages on Kafka iot.uplink. Frame sources, all optional and combinable:

  * Kafka topic ground.frames   - frames from the simulated space segment (sandf, EMIT=frames)
                                  or from a modem/SDR decoder on the gateway LAN
  * FRAME_DIR                   - *.bin (decoded v1 frames), *.raw (demodulated bytes, FEC-decoded here)
                                  or *.cf32 (complex baseband IQ at 8 samples/symbol, demodulated by forgestar.modem)
                                  e.g. satnogs-client output; files move to done/ or bad/
  * SATNOGS_STATION_ID + token  - polls SatNOGS Network for this station's observations of NORAD_ID
                                  and fetches their demodulated data (hex frames)

The device registry (short id -> device name, customer, kind) comes from
TimescaleDB's devices table, so devices only need registering once.
Deduplicates on (sat, seq) so overlapping gateway passes don't double-count.
"""
from __future__ import annotations

import base64
import json
import os
import time
from collections import OrderedDict
from pathlib import Path

from forgestar.fec import decode_stream
from forgestar.frames import FrameError, decode, frame_kind, pack_acks, short_id
from forgestar.fec import encode_block

SEEN_MAX = 100000


class Gateway:
    def __init__(self, publish, registry, grace_s: float = 0.0):
        self.publish = publish          # callable(dict)
        self.registry = registry        # callable(short_id) -> dict | None
        self.grace_s = grace_s          # hold records of unregistered devices this long before giving up
        self.unresolved: list[tuple[float, int, dict]] = []
        self.delivered: OrderedDict = OrderedDict()   # (short id, t_created) -> time landed: dedupe + acks
        self.ack_seq = 0
        self.seen: OrderedDict = OrderedDict()
        self.stats = {"frames": 0, "records": 0, "duplicates": 0, "bad": 0, "unknown_device": 0,
                      "link_blocks": 0, "fec_corrected_bytes": 0, "fec_failed": 0, "duplicate_records": 0, "acks_sent": 0}

    def handle_link(self, stream: bytes, source: str, received_ts: float | None = None) -> int:
        """Raw received bytes (one or more link blocks, with noise) -> FEC decode -> frames."""
        frames, st = decode_stream(stream)
        frames = [f for f in frames if frame_kind(f) == "data"]
        self.stats["link_blocks"] += st["blocks"]; self.stats["fec_corrected_bytes"] += st["corrected_bytes"]
        self.stats["fec_failed"] += st["failed"]
        return sum(self.handle(f, source, received_ts) or 0 for f in frames)

    def handle(self, raw: bytes, source: str, received_ts: float | None = None) -> int | None:
        """Records published, 0 for a duplicate frame, None for an undecodable frame."""
        try:
            f = decode(raw)
        except FrameError as e:
            self.stats["bad"] += 1
            print(f"gateway: bad frame from {source}: {e}", flush=True)
            return None
        key = (f.sat_id, f.seq)
        if key in self.seen:
            self.stats["duplicates"] += 1; return 0
        self.seen[key] = True
        if len(self.seen) > SEEN_MAX: self.seen.popitem(last=False)
        self.stats["frames"] += 1
        now = received_ts if received_ts is not None else time.time()
        n = 0
        for r in f.records:
            key = (r.device_short_id, r.t_created)
            if key in self.delivered:                 # another satellite carried the same message
                self.stats["duplicate_records"] += 1; continue
            self.delivered[key] = now
            if len(self.delivered) > SEEN_MAX: self.delivered.popitem(last=False)
            payload = dict(r.payload)
            sim_lat = payload.pop("_sim_latency_s", None)   # simulated space segment only (sandf)
            msg = {"ts": (now - sim_lat) if sim_lat is not None else r.t_created, "received_ts": now, "path": "satellite", "sat": f.sat_id,
                   "lat": r.lat, "lon": r.lon, "data": payload, "frame_seq": f.seq, "source": source}
            dev = self.registry(r.device_short_id)
            if dev:
                self.publish({**dev, **msg})
            elif self.grace_s > 0:
                self.unresolved.append((time.time(), r.device_short_id, msg))  # registration may still be in flight
            else:
                self._publish_unknown(r.device_short_id, msg)
            n += 1
        self.stats["records"] += n
        return n


    def ack_blocks(self, gateway_id: int, window_s: float, now: float | None = None) -> list[bytes]:
        """FEC link blocks carrying acks for everything landed in the last window_s seconds.
        Re-broadcast every interval so satellites passing later still learn them."""
        now = time.time() if now is None else now
        keys = [k for k, t in self.delivered.items() if now - t <= window_s]
        if not keys:
            return []
        frames = pack_acks(gateway_id, self.ack_seq, int(now), keys)
        self.ack_seq += len(frames); self.stats["acks_sent"] += len(keys)
        return [encode_block(f) for f in frames]

    def _publish_unknown(self, sid: int, msg: dict):
        self.stats["unknown_device"] += 1
        self.publish({"device_id": f"unknown-{sid:08x}", "kind": "unknown", "customer": "unregistered", **msg})

    def retry_unresolved(self, now: float | None = None):
        now = time.time() if now is None else now
        keep = []
        for t0, sid, msg in self.unresolved:
            dev = self.registry(sid)
            if dev:
                self.publish({**dev, **msg})
            elif now - t0 >= self.grace_s:
                self._publish_unknown(sid, msg)
            else:
                keep.append((t0, sid, msg))
        self.unresolved = keep


def scan_dir(gw: Gateway, d: Path):
    for sub in ("done", "bad"):
        (d / sub).mkdir(exist_ok=True)
    for p in sorted(d.glob("*.bin")):          # already-decoded v1 frames
        n = gw.handle(p.read_bytes(), f"file:{p.name}")
        p.rename(d / ("bad" if n is None else "done") / p.name)
    for p in sorted(d.glob("*.cf32")):         # complex baseband IQ recordings (SDR / SatNOGS): demodulate first
        import numpy as np
        from forgestar.modem import demodulate
        before = gw.stats["link_blocks"]
        gw.handle_link(demodulate(np.fromfile(p, dtype=np.complex64).astype(np.complex128)), f"iq:{p.name}")
        p.rename(d / ("done" if gw.stats["link_blocks"] > before else "bad") / p.name)
    for p in sorted(d.glob("*.raw")):          # raw demodulated bytes from the radio: needs FEC
        before = gw.stats["link_blocks"]
        gw.handle_link(p.read_bytes(), f"file:{p.name}")
        p.rename(d / ("done" if gw.stats["link_blocks"] > before else "bad") / p.name)


def poll_satnogs(gw: Gateway, station: str, norad: str, token: str, since: dict):
    """SatNOGS Network API: observations for this station and satellite, then their demod data."""
    import requests
    h = {"Authorization": f"Token {token}"} if token else {}
    url = f"https://network.satnogs.org/api/observations/?ground_station={station}&satellite__norad_cat_id={norad}&status=good"
    for obs in requests.get(url, headers=h, timeout=30).json():
        if obs["id"] <= since.get("last", 0):
            continue
        for dd in obs.get("demoddata", []):
            raw = requests.get(dd["payload_demod"], headers=h, timeout=30).content
            try:
                raw = bytes.fromhex(raw.decode().strip())  # SatNOGS stores frames as hex text
            except (UnicodeDecodeError, ValueError):
                pass
            gw.handle_link(raw, f"satnogs:{obs['id']}")
        since["last"] = max(since.get("last", 0), obs["id"])


def main():
    from kafka import KafkaConsumer, KafkaProducer
    import psycopg
    boot = os.environ["KAFKA_BOOTSTRAP"]
    for _ in range(60):
        try:
            prod = KafkaProducer(bootstrap_servers=boot, value_serializer=lambda v: json.dumps(v).encode())
            cons = KafkaConsumer("ground.frames", bootstrap_servers=boot, group_id="gateway", auto_offset_reset="earliest", consumer_timeout_ms=500)
            db = psycopg.connect(os.environ["PG_DSN"], autocommit=True)
            break
        except Exception:
            time.sleep(2)
    cache: dict[int, dict] = {}

    last_load = [0.0]

    def registry(sid: int):
        if sid not in cache and time.time() - last_load[0] > 2:  # reload at most every 2 s
            last_load[0] = time.time()
            for dev_id, kind, cust in db.execute("SELECT device_id, kind, customer FROM devices"):
                cache[short_id(dev_id)] = {"device_id": dev_id, "kind": kind, "customer": cust}
        return cache.get(sid)

    gw = Gateway(lambda m: prod.send("iot.uplink", m), registry, grace_s=float(os.environ.get("UNKNOWN_GRACE_S", 60)))
    frame_dir = Path(os.environ["FRAME_DIR"]) if os.environ.get("FRAME_DIR") else None
    station, norad = os.environ.get("SATNOGS_STATION_ID"), os.environ.get("NORAD_ID")
    since, last_poll, last_report, last_ack = {}, 0.0, time.time(), 0.0
    gw_id = int(os.environ.get("GATEWAY_ID", 1))
    ack_every, ack_window = float(os.environ.get("ACK_INTERVAL_S", 5)), float(os.environ.get("ACK_WINDOW_S", 3 * 3600))
    print("gateway: listening on ground.frames" + (f", {frame_dir}" if frame_dir else "")
          + (f", SatNOGS station {station}" if station and norad else ""), flush=True)
    while True:
        for msg in cons:
            env = json.loads(msg.value)
            if "link" in env:
                gw.handle_link(base64.b64decode(env["link"]), "kafka", env.get("received_ts"))
            else:
                gw.handle(base64.b64decode(env["frame"]), "kafka", env.get("received_ts"))
        if frame_dir: scan_dir(gw, frame_dir)
        if station and norad and time.time() - last_poll > 300:
            try: poll_satnogs(gw, station, norad, os.environ.get("SATNOGS_API_TOKEN", ""), since)
            except Exception as e: print(f"gateway: SatNOGS poll failed: {e}", flush=True)
            last_poll = time.time()
        gw.retry_unresolved()
        if time.time() - last_ack > ack_every:    # acks go up on the next pass of every satellite
            for blk in gw.ack_blocks(gw_id, ack_window):
                prod.send("ground.uplink", {"link": base64.b64encode(blk).decode(), "gateway": gw_id})
            last_ack = time.time()
        prod.flush()
        if time.time() - last_report > 30:
            print(f"gateway: {gw.stats}", flush=True); last_report = time.time()


if __name__ == "__main__":
    main()
