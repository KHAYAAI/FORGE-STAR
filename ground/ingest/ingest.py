"""Kafka iot.uplink -> TimescaleDB (and ThingsBoard if a device token is mapped)."""
import json, os, time
import psycopg, requests
from kafka import KafkaConsumer

def connect():
    for _ in range(60):
        try:
            return psycopg.connect(os.environ["PG_DSN"], autocommit=True)
        except psycopg.OperationalError:
            time.sleep(2)
    raise SystemExit("no database")

db = connect()
tb = os.environ.get("TB_URL")
consumer = KafkaConsumer("iot.uplink", bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"],
                         group_id="ingest", value_deserializer=lambda b: json.loads(b))
print("ingest: listening on iot.uplink", flush=True)
n = 0
for msg in consumer:
    m = msg.value
    db.execute("INSERT INTO devices (device_id, kind, customer) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
               (m["device_id"], m["kind"], m["customer"]))
    db.execute("INSERT INTO uplinks (time, device_id, path, lat, lon, payload) VALUES (to_timestamp(%s),%s,%s,%s,%s,%s)",
               (m["ts"], m["device_id"], m["path"], m.get("lat"), m.get("lon"), json.dumps(m["data"])))
    if tb and m.get("tb_token"):
        try: requests.post(f"{tb}/api/v1/{m['tb_token']}/telemetry", json=m["data"], timeout=2)
        except requests.RequestException: pass
    n += 1
    if n % 100 == 0: print(f"ingest: {n} uplinks stored", flush=True)
