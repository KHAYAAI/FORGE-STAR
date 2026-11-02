"""FORGE STAR store-and-forward service (simulated space segment).

Kafka iot.device_tx  ->  [device waits for a satellite]  ->  [onboard buffer]
                     ->  [downlink when the satellite sees an SA gateway]  ->  Kafka iot.uplink

The constellation is propagated with forgestar.orbits on an accelerated clock
(SPEEDUP, default 60x). Latencies are reported in real-constellation seconds:
each output message carries ts = now - latency and received_ts = now, so the
TimescaleDB view latency_hourly shows what customers of that constellation would see.

By default (EMIT=frames) it sends forgestar.frames v1 frames, wrapped in
forgestar.fec link blocks (Reed–Solomon + randomiser + sync marker), to Kafka
ground.frames, exactly as the payload will downlink them, and ground/gateway
decodes them. When the real payload flies, only this service goes away.
"""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque

import numpy as np

from forgestar.orbits import Constellation, Site, look, propagate_ecef
from forgestar.logic import Buffer, Pending, step
from forgestar.frames import Record, pack, short_id
from forgestar.fec import encode_block
import base64
import random

SATS = int(os.environ.get("SATS", 24))
PLANES = int(os.environ.get("PLANES", 4))
INC = os.environ.get("INC", "45")
SPEEDUP = float(os.environ.get("SPEEDUP", 60))
TICK_S = float(os.environ.get("TICK_S", 1.0))
UPLINK_MASK = float(os.environ.get("UPLINK_MASK_DEG", 22))
GATEWAY_MASK = float(os.environ.get("GATEWAY_MASK_DEG", 10))
BUFFER_MSGS = int(os.environ.get("BUFFER_MSGS", 200000))
DOWNLINK_MSGS_PER_S = int(os.environ.get("DOWNLINK_MSGS_PER_S", 2000))
EMIT = os.environ.get("EMIT", "frames")  # frames: binary frames to ground.frames (production path); json: straight to iot.uplink
CHANNEL_BER = float(os.environ.get("CHANNEL_BER", 0))  # inject random bit errors to exercise FEC
GATEWAYS = [Site("Hartebeesthoek", "SA", -25.89, 27.69), Site("Cape Town", "SA", -33.93, 18.42)]


def main():
    from kafka import KafkaConsumer, KafkaProducer
    boot = os.environ["KAFKA_BOOTSTRAP"]
    for _ in range(60):
        try:
            cons = KafkaConsumer("iot.device_tx", bootstrap_servers=boot, group_id="sandf", auto_offset_reset="earliest",
                                 value_deserializer=lambda b: json.loads(b), consumer_timeout_ms=50)
            prod = KafkaProducer(bootstrap_servers=boot, value_serializer=lambda v: json.dumps(v).encode())
            break
        except Exception:
            time.sleep(2)
    c = Constellation(SATS, PLANES, None if INC == "mixed" else float(INC), label="sandf")
    pending: deque[Pending] = deque()
    buffers = defaultdict(Buffer)
    wall0 = time.time(); last_report = wall0; stats = defaultdict(int); seq = defaultdict(int)
    print(f"sandf: {SATS} sats / {PLANES} planes / inc {INC}, speedup {SPEEDUP}x", flush=True)
    while True:
        tick_start = time.time()
        sim_t = (tick_start - wall0) * SPEEDUP
        for msg in cons:  # drain what has arrived (consumer_timeout_ms bounds this)
            pending.append(Pending(msg.value, sim_t))
            stats["in"] += 1
            if len(pending) > 500000: pending.popleft(); stats["dropped_device_queue"] += 1
        sat = propagate_ecef(c, np.array([sim_t]))
        gw_el, _ = look(sat, GATEWAYS)
        out = step(sim_t, pending, buffers, sat[0], gw_el[0].max(0) >= GATEWAY_MASK,
                   UPLINK_MASK, BUFFER_MSGS, int(DOWNLINK_MSGS_PER_S * TICK_S * SPEEDUP), stats)
        now = time.time()
        if EMIT == "json":
            for m, latency_sim_s, sat_id in out:
                m = dict(m); m.update(path="satellite", sat=sat_id, ts=now - latency_sim_s, received_ts=now,
                                      sf_latency_s=round(latency_sim_s, 1))
                prod.send("iot.uplink", m)
        else:
            by_sat = defaultdict(list)
            for m, latency_sim_s, sat_id in out:
                by_sat[sat_id].append(Record(short_id(m["device_id"]), int(now - latency_sim_s), m["lat"], m["lon"], m["data"]))
            for sat_id, recs in by_sat.items():
                for raw in pack(sat_id, seq[sat_id], int(now), recs):
                    blk = bytearray(encode_block(raw))      # what the radio actually transmits
                    if CHANNEL_BER:
                        for i in range(len(blk) * 8):
                            if random.random() < CHANNEL_BER: blk[i // 8] ^= 1 << (i % 8)
                    prod.send("ground.frames", {"link": base64.b64encode(bytes(blk)).decode(), "received_ts": now})
                    seq[sat_id] += 1; stats["frames"] += 1
        if out: prod.flush()
        if now - last_report > 30:
            onboard = sum(len(b.q) for b in buffers.values())
            print(f"sandf: in={stats['in']} uplinked={stats['uplinked']} downlinked={stats['downlinked']} "
                  f"frames={stats['frames']} waiting_on_ground={len(pending)} onboard={onboard} dropped={stats['dropped_full']}", flush=True)
            last_report = now
        time.sleep(max(0.0, TICK_S - (time.time() - tick_start)))


if __name__ == "__main__":
    main()
