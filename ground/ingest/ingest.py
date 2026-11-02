"""Kafka iot.uplink -> TimescaleDB (and ThingsBoard when provision.py has written device tokens)."""
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
tokens, tokens_mtime = {}, 0.0
def tb_token(device_id):
    """Reload the token map when provision.py rewrites it."""
    global tokens, tokens_mtime
    path = os.environ.get("TB_TOKENS_FILE", "")
    try:
        mt = os.path.getmtime(path)
        if mt != tokens_mtime:
            tokens, tokens_mtime = json.load(open(path)), mt
    except OSError:
        return None
    return tokens.get(device_id)
consumer = KafkaConsumer("iot.uplink", "iot.register", bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"],
                         group_id="ingest", auto_offset_reset="earliest", value_deserializer=lambda b: json.loads(b))
print("ingest: listening on iot.uplink, iot.register", flush=True)
n = 0
for msg in consumer:
    m = msg.value
    if msg.topic == "iot.register":
        db.execute("INSERT INTO devices (device_id, kind, customer) VALUES (%s,%s,%s) "
                   "ON CONFLICT (device_id) DO UPDATE SET kind = EXCLUDED.kind, customer = EXCLUDED.customer",
                   (m["device_id"], m["kind"], m["customer"]))
        continue
    db.execute("INSERT INTO devices (device_id, kind, customer) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
               (m["device_id"], m["kind"], m["customer"]))
    db.execute("INSERT INTO uplinks (time, device_id, path, sat, lat, lon, payload, received_at) "
               "VALUES (to_timestamp(%s),%s,%s,%s,%s,%s,%s,to_timestamp(%s))",
               (m["ts"], m["device_id"], m["path"], m.get("sat"), m.get("lat"), m.get("lon"),
                json.dumps(m["data"]), m.get("received_ts", time.time())))
    tok = tb and tb_token(m["device_id"])
    if tok:
        telemetry = dict(m["data"], latency_s=round(m.get("received_ts", time.time()) - m["ts"], 1),
                         latitude=m.get("lat"), longitude=m.get("lon"))
        try: requests.post(f"{tb}/api/v1/{tok}/telemetry", json={"ts": int(m["ts"] * 1000), "values": telemetry}, timeout=2)
        except requests.RequestException: pass
    n += 1
    if n % 100 == 0: print(f"ingest: {n} uplinks stored", flush=True)
