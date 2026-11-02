"""FORGE STAR gateway downlink handler.

Turns downlinked store-and-forward frames (forgestar.frames v1) into device
messages on Kafka iot.uplink. Frame sources, all optional and combinable:

  * Kafka topic ground.frames   - frames from the simulated space segment (sandf, EMIT=frames)
                                  or from a modem/SDR decoder on the gateway LAN
  * FRAME_DIR                   - a folder of *.bin files (e.g. satnogs-client output); moved to done/ or bad/
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

from forgestar.frames import FrameError, decode, short_id

SEEN_MAX = 100000


class Gateway:
    def __init__(self, publish, registry):
        self.publish = publish          # callable(dict)
        self.registry = registry        # callable(short_id) -> dict | None
        self.seen: OrderedDict = OrderedDict()
        self.stats = {"frames": 0, "records": 0, "duplicates": 0, "bad": 0, "unknown_device": 0}

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
            dev = self.registry(r.device_short_id)
            if not dev:
                self.stats["unknown_device"] += 1
                dev = {"device_id": f"unknown-{r.device_short_id:08x}", "kind": "unknown", "customer": "unregistered"}
            self.publish({**dev, "ts": r.t_created, "received_ts": now, "path": "satellite", "sat": f.sat_id,
                          "lat": r.lat, "lon": r.lon, "data": r.payload, "frame_seq": f.seq, "source": source})
            n += 1
        self.stats["records"] += n
        return n


def scan_dir(gw: Gateway, d: Path):
    for sub in ("done", "bad"):
        (d / sub).mkdir(exist_ok=True)
    for p in sorted(d.glob("*.bin")):
        n = gw.handle(p.read_bytes(), f"file:{p.name}")
        p.rename(d / ("bad" if n is None else "done") / p.name)


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
            gw.handle(raw, f"satnogs:{obs['id']}")
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

    def registry(sid: int):
        if sid not in cache:
            for dev_id, kind, cust in db.execute("SELECT device_id, kind, customer FROM devices"):
                cache[short_id(dev_id)] = {"device_id": dev_id, "kind": kind, "customer": cust}
        return cache.get(sid)

    gw = Gateway(lambda m: prod.send("iot.uplink", m), registry)
    frame_dir = Path(os.environ["FRAME_DIR"]) if os.environ.get("FRAME_DIR") else None
    station, norad = os.environ.get("SATNOGS_STATION_ID"), os.environ.get("NORAD_ID")
    since, last_poll, last_report = {}, 0.0, time.time()
    print("gateway: listening on ground.frames" + (f", {frame_dir}" if frame_dir else "")
          + (f", SatNOGS station {station}" if station and norad else ""), flush=True)
    while True:
        for msg in cons:
            env = json.loads(msg.value)
            gw.handle(base64.b64decode(env["frame"]), "kafka", env.get("received_ts"))
        if frame_dir: scan_dir(gw, frame_dir)
        if station and norad and time.time() - last_poll > 300:
            try: poll_satnogs(gw, station, norad, os.environ.get("SATNOGS_API_TOKEN", ""), since)
            except Exception as e: print(f"gateway: SatNOGS poll failed: {e}", flush=True)
            last_poll = time.time()
        prod.flush()
        if time.time() - last_report > 30:
            print(f"gateway: {gw.stats}", flush=True); last_report = time.time()


if __name__ == "__main__":
    main()
