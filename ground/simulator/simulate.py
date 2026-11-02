"""Fake FORGE STAR field devices. Store-and-forward: messages are delayed like a satellite pass would delay them."""
import json, os, random, time
from kafka import KafkaProducer

KINDS = [  # kind, customer, lat range, lon range
    ("pump",    "Mining co (Limpopo)",  (-24.5, -22.5), (28.0, 31.0)),
    ("soil",    "Farm co-op (N Cape)",  (-30.0, -27.0), (20.0, 24.0)),
    ("collar",  "Private reserve",      (-25.5, -24.0), (31.0, 32.0)),
    ("vessel",  "DFFE fisheries (AIS)", (-38.0, -33.0), (16.0, 28.0)),
    ("tracker", "FORGE Freight",        (-26.5, -15.0), (27.0, 36.0)),
]
prod = None
for _ in range(60):
    try:
        prod = KafkaProducer(bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"], value_serializer=lambda v: json.dumps(v).encode())
        break
    except Exception:
        time.sleep(2)
n = int(os.environ.get("DEVICES", 50)); step = float(os.environ.get("INTERVAL_S", 5))
devs = []
for i in range(n):
    kind, cust, la, lo = KINDS[i % len(KINDS)]
    devs.append(dict(device_id=f"{kind}-{i:04d}", kind=kind, customer=cust,
                     lat=random.uniform(*la), lon=random.uniform(*lo)))
print(f"simulator: {n} devices", flush=True)
while True:
    for d in random.sample(devs, max(1, n // 5)):
        d["lat"] += random.gauss(0, 0.01 if d["kind"] in ("vessel", "tracker", "collar") else 0)
        data = {"battery_v": round(random.uniform(3.4, 4.2), 2)}
        if d["kind"] == "pump":   data |= {"flow_lpm": round(random.uniform(0, 400), 1), "running": random.random() > .1}
        if d["kind"] == "soil":   data |= {"moisture_pct": round(random.uniform(5, 45), 1)}
        if d["kind"] == "vessel": data |= {"mmsi": 601000000 + int(d["device_id"][-4:]), "sog_kn": round(random.uniform(0, 12), 1)}
        delay = random.choice([0, 0, 60, 600, 1800])   # resale/ground = 0, satellite store-and-forward = minutes
        prod.send("iot.uplink", dict(ts=time.time() - delay, device_id=d["device_id"], kind=d["kind"], customer=d["customer"],
                                     path="sim", lat=round(d["lat"], 5), lon=round(d["lon"], 5), data=data))
    prod.flush(); time.sleep(step)
