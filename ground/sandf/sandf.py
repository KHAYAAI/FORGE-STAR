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
from forgestar.logic import Buffer, Pending, ResendNetwork, step
from forgestar.frames import Record, pack, short_id
from forgestar.fec import decode_stream, encode_block
from forgestar.frames import decode_ack, frame_kind
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
POLICY = os.environ.get("POLICY", "resend")  # resend: devices re-send until acked (needs gateway acks); single: one copy
# Orbital shells "n:planes:inclination,...". Default = Stage 3 design (sim/equatorial_study.py): 42 @45° + 6 @10°.
SHELLS = os.environ.get("SHELLS", "")
# Gateways "name:lat:lon;..." Default = the 6-gateway network of the Stage 3 design.
GATEWAY_SPEC = os.environ.get("GATEWAYS", "Hartebeesthoek:-25.89:27.69;Cape Town:-33.93:18.42;Walvis Bay:-22.95:14.5;"
                              "Mauritius:-20.2:57.5;Malindi:-3.0:40.2;Lagos:6.5:3.4")
GATEWAYS = [Site(n, "", float(la), float(lo)) for n, la, lo in (g.split(":") for g in GATEWAY_SPEC.split(";") if g)]


def shells():
    if not SHELLS:
        return [Constellation(SATS, PLANES, None if INC == "mixed" else float(INC))]
    out = []
    for spec in SHELLS.split(","):
        n, p, i = spec.split(":")
        out.append(Constellation(int(n), int(p), float(i)))
    return out


def main():
    from kafka import KafkaConsumer, KafkaProducer
    boot = os.environ["KAFKA_BOOTSTRAP"]
    for _ in range(60):
        try:
            cons = KafkaConsumer("iot.device_tx", "ground.uplink", bootstrap_servers=boot, group_id="sandf", auto_offset_reset="earliest",
                                 value_deserializer=lambda b: json.loads(b), consumer_timeout_ms=50)
            prod = KafkaProducer(bootstrap_servers=boot, value_serializer=lambda v: json.dumps(v).encode())
            break
        except Exception:
            time.sleep(2)
    cs = shells()
    pending: deque[Pending] = deque()
    buffers = defaultdict(Buffer)
    net = ResendNetwork(BUFFER_MSGS)
    wall0 = time.time(); last_report = wall0; stats = defaultdict(int); seq = defaultdict(int)
    print(f"sandf: {sum(c.n for c in cs)} sats in {len(cs)} shell(s) ({SHELLS or f'{SATS}:{PLANES}:{INC}'}), "
          f"{len(GATEWAYS)} gateways, speedup {SPEEDUP}x", flush=True)
    while True:
        tick_start = time.time()
        sim_t = (tick_start - wall0) * SPEEDUP
        for msg in cons:  # drain what has arrived (consumer_timeout_ms bounds this)
            if msg.topic == "ground.uplink":       # gateway acks, uplinked on each satellite's next gateway pass
                frames, _ = decode_stream(base64.b64decode(msg.value["link"]))
                for f in frames:
                    if frame_kind(f) == "ack":
                        net.queue_ground_acks(decode_ack(f).keys); stats["acks_in"] += 1
                continue
            stats["in"] += 1
            if POLICY == "resend":
                net.add(msg.value, sim_t)
            else:
                pending.append(Pending(msg.value, sim_t))
                if len(pending) > 500000: pending.popleft(); stats["dropped_device_queue"] += 1
        sat = np.concatenate([propagate_ecef(c, np.array([sim_t])) for c in cs], axis=1)
        gw_el, _ = look(sat, GATEWAYS)
        budget = int(DOWNLINK_MSGS_PER_S * TICK_S * SPEEDUP)
        gw_vis = gw_el[0].max(0) >= GATEWAY_MASK
        if POLICY == "resend":
            out = net.step(sim_t, sat[0], gw_vis, UPLINK_MASK, budget, stats)
        else:
            out = step(sim_t, pending, buffers, sat[0], gw_vis, UPLINK_MASK, BUFFER_MSGS, budget, stats)
        now = time.time()
        if EMIT == "json":
            for m, latency_sim_s, sat_id in out:
                m = dict(m); m.update(path="satellite", sat=sat_id, ts=now - latency_sim_s, received_ts=now,
                                      sf_latency_s=round(latency_sim_s, 1))
                prod.send("iot.uplink", m)
        else:
            by_sat = defaultdict(list)
            for m, latency_sim_s, sat_id in out:
                # t_created = the device's own timestamp, so copies on different satellites dedupe on the
                # ground; the simulated latency rides along in _sim_latency_s (sandf only, stripped by gateway)
                by_sat[sat_id].append(Record(short_id(m["device_id"]), int(m["ts"]), m["lat"], m["lon"],
                                             {**m["data"], "_sim_latency_s": round(latency_sim_s, 1)}))
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
            onboard = sum(len(b.q) for b in buffers.values()) + sum(len(b) for b in net.buf.values())
            print(f"sandf: in={stats['in']} uplinked={stats['uplinked']} downlinked={stats['downlinked']} "
                  f"frames={stats['frames']} waiting_on_ground={len(pending) + len(net.pending)} onboard={onboard} "
                  f"acked_on_device={stats['acked_on_device']} dropped_acked_onboard={stats['dropped_acked_onboard']} "
                  f"dropped_full={stats['dropped_full']}", flush=True)
            last_report = now
        time.sleep(max(0.0, TICK_S - (time.time() - tick_start)))


if __name__ == "__main__":
    main()
