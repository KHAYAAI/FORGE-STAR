"""Data access for the customer API. PgRepo talks to TimescaleDB; tests use MemoryRepo."""
from __future__ import annotations

import datetime as dt
import hashlib
import secrets
from typing import Protocol


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


class Repo(Protocol):
    def customer_for_key(self, key_hash: str) -> str | None: ...
    def devices(self, customer: str) -> list[dict]: ...
    def messages(self, customer: str, device_id: str, since: dt.datetime | None, limit: int) -> list[dict]: ...
    def sla(self, customer: str, since: dt.datetime) -> list[dict]: ...
    def usage(self, customer: str, start: dt.datetime, end: dt.datetime) -> dict: ...


class PgRepo:
    def __init__(self, dsn: str):
        import psycopg
        from psycopg.rows import dict_row
        self.db = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
        self.db.execute("""CREATE TABLE IF NOT EXISTS api_keys (
            key_hash TEXT PRIMARY KEY, customer TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), revoked BOOLEAN NOT NULL DEFAULT false)""")

    def create_key(self, customer: str) -> str:
        key = "fs_" + secrets.token_urlsafe(24)
        self.db.execute("INSERT INTO api_keys (key_hash, customer) VALUES (%s, %s)", (hash_key(key), customer))
        return key

    def customer_for_key(self, key_hash):
        r = self.db.execute("SELECT customer FROM api_keys WHERE key_hash=%s AND NOT revoked", (key_hash,)).fetchone()
        return r["customer"] if r else None

    def devices(self, customer):
        return self.db.execute("""
            SELECT d.device_id, d.kind, d.created_at, max(u.time) AS last_seen, count(u.*) AS messages_7d
            FROM devices d LEFT JOIN uplinks u ON u.device_id = d.device_id AND u.time > now() - interval '7 days'
            WHERE d.customer = %s GROUP BY d.device_id, d.kind, d.created_at ORDER BY d.device_id""", (customer,)).fetchall()

    def messages(self, customer, device_id, since, limit):
        return self.db.execute("""
            SELECT u.time, u.received_at, u.path, u.sat, u.lat, u.lon, u.payload
            FROM uplinks u JOIN devices d USING (device_id)
            WHERE d.customer = %s AND u.device_id = %s AND (%s::timestamptz IS NULL OR u.time > %s)
            ORDER BY u.time DESC LIMIT %s""", (customer, device_id, since, since, limit)).fetchall()

    def sla(self, customer, since):
        return self.db.execute("""
            SELECT u.path, count(*) AS messages,
                   percentile_cont(0.5)  WITHIN GROUP (ORDER BY extract(epoch FROM u.received_at - u.time)) AS p50_s,
                   percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM u.received_at - u.time)) AS p95_s,
                   max(extract(epoch FROM u.received_at - u.time)) AS max_s
            FROM uplinks u JOIN devices d USING (device_id)
            WHERE d.customer = %s AND u.time > %s GROUP BY u.path ORDER BY u.path""", (customer, since)).fetchall()

    def usage(self, customer, start, end):
        r = self.db.execute("""
            SELECT count(DISTINCT u.device_id) AS active_devices, count(*) AS messages,
                   coalesce(sum(octet_length(u.payload::text)), 0) AS payload_bytes
            FROM uplinks u JOIN devices d USING (device_id)
            WHERE d.customer = %s AND u.time >= %s AND u.time < %s""", (customer, start, end)).fetchone()
        return dict(r)


class MemoryRepo:
    """In-memory stand-in with the same behaviour, for tests and demos."""

    def __init__(self):
        self.keys, self.devs, self.ups = {}, [], []

    def create_key(self, customer):
        key = "fs_" + secrets.token_urlsafe(24); self.keys[hash_key(key)] = customer; return key

    def customer_for_key(self, key_hash):
        return self.keys.get(key_hash)

    def devices(self, customer):
        now = dt.datetime.now(dt.timezone.utc)
        out = []
        for d in self.devs:
            if d["customer"] != customer: continue
            mine = [u for u in self.ups if u["device_id"] == d["device_id"] and u["time"] > now - dt.timedelta(days=7)]
            out.append({"device_id": d["device_id"], "kind": d["kind"], "created_at": d.get("created_at", now),
                        "last_seen": max((u["time"] for u in mine), default=None), "messages_7d": len(mine)})
        return sorted(out, key=lambda x: x["device_id"])

    def _owned(self, customer, device_id):
        return any(d["device_id"] == device_id and d["customer"] == customer for d in self.devs)

    def messages(self, customer, device_id, since, limit):
        if not self._owned(customer, device_id): return []
        rows = [u for u in self.ups if u["device_id"] == device_id and (since is None or u["time"] > since)]
        return sorted(rows, key=lambda u: u["time"], reverse=True)[:limit]

    def sla(self, customer, since):
        import statistics
        mine = {d["device_id"] for d in self.devs if d["customer"] == customer}
        by = {}
        for u in self.ups:
            if u["device_id"] in mine and u["time"] > since:
                by.setdefault(u["path"], []).append((u["received_at"] - u["time"]).total_seconds())
        out = []
        for p, v in sorted(by.items()):
            v.sort()
            q = lambda f: v[min(len(v) - 1, int(round(f * (len(v) - 1))))]
            out.append({"path": p, "messages": len(v), "p50_s": statistics.median(v), "p95_s": q(0.95), "max_s": v[-1]})
        return out

    def usage(self, customer, start, end):
        mine = {d["device_id"] for d in self.devs if d["customer"] == customer}
        rows = [u for u in self.ups if u["device_id"] in mine and start <= u["time"] < end]
        import json
        return {"active_devices": len({u["device_id"] for u in rows}), "messages": len(rows),
                "payload_bytes": sum(len(json.dumps(u["payload"])) for u in rows)}
