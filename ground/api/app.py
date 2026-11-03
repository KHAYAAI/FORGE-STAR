"""FORGE STAR customer API.

Customers read their own devices' data, delivery SLAs and monthly usage. Data stays in
the SA-hosted TimescaleDB. Every request needs an API key (header X-API-Key); a key only
ever sees its own customer's devices.

Run:  uvicorn app:app --host 0.0.0.0 --port 8000      (PG_DSN env var)
Keys: python app.py create-key "Mining co (Limpopo)"   |   python app.py revoke-key <key>
Hardening: per-key rate limit (API_RATE_PER_MIN), 64 KB request cap, security headers,
audit log (api_audit table), Prometheus /metrics. Run behind TLS (ground/deploy/Caddyfile).
Docs: http://localhost:8000/docs (OpenAPI)
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import threading
import time
from collections import defaultdict

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from repo import MemoryRepo, PgRepo, Repo, hash_key

PRICE_PER_DEVICE_MONTH = float(os.environ.get("PRICE_PER_DEVICE_MONTH", 3.5))  # USD, model/assumptions.yaml arpu
SLA_TARGET_P95_MIN = float(os.environ.get("SLA_TARGET_P95_MIN", 60))

app = FastAPI(title="FORGE STAR API", version="0.1.0",
              description="Sovereign satellite IoT data for Africa. Data hosted in South Africa.")
_repo: Repo | None = None

RATE_PER_MIN = int(os.environ.get("API_RATE_PER_MIN", 120))   # per API key
MAX_BODY = 64 * 1024
_buckets: dict[str, list] = {}
_lock = threading.Lock()
_metrics = defaultdict(int)


def _rate_ok(key_hash: str) -> bool:
    """Token bucket per key: RATE_PER_MIN requests per minute, burst of the same size."""
    now = time.monotonic()
    with _lock:
        tokens, last = _buckets.get(key_hash, [float(RATE_PER_MIN), now])
        tokens = min(float(RATE_PER_MIN), tokens + (now - last) * RATE_PER_MIN / 60.0)
        if tokens < 1.0:
            _buckets[key_hash] = [tokens, now]; return False
        _buckets[key_hash] = [tokens - 1.0, now]; return True


@app.middleware("http")
async def harden(request: Request, call_next):
    if int(request.headers.get("content-length") or 0) > MAX_BODY:
        return PlainTextResponse("request too large", status_code=413)
    response = await call_next(request)
    route = request.scope.get("route")
    _metrics[(request.method, getattr(route, "path", "unmatched"), response.status_code)] += 1
    for k, v in {"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
                 "Cache-Control": "no-store", "Strict-Transport-Security": "max-age=31536000"}.items():
        response.headers[k] = v
    cust = getattr(request.state, "customer", None)
    if cust and request.url.path.startswith("/v1/"):
        try:
            app.dependency_overrides.get(get_repo, get_repo)().audit(cust, request.method, request.url.path, response.status_code,
                             request.client.host if request.client else "")
        except Exception:  # audit must never break a request
            pass
    return response


def get_repo() -> Repo:
    global _repo
    if _repo is None:
        _repo = PgRepo(os.environ["PG_DSN"]) if os.environ.get("PG_DSN") else MemoryRepo()
    return _repo


def customer(request: Request, x_api_key: str = Header(..., description="Customer API key"),
             repo: Repo = Depends(get_repo)) -> str:
    h = hash_key(x_api_key)
    c = repo.customer_for_key(h)
    if not c:
        raise HTTPException(401, "invalid or revoked API key")
    if not _rate_ok(h):
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": "30"})
    request.state.customer = c
    return c


@app.get("/health")
def health():
    return {"status": "ok", "time": dt.datetime.now(dt.timezone.utc).isoformat()}


@app.get("/metrics", include_in_schema=False)
def metrics():
    """Prometheus text format: requests by method, route and status."""
    lines = ["# TYPE forge_api_requests_total counter"]
    for (m, path, code), n in sorted(_metrics.items()):
        lines.append(f'forge_api_requests_total{{method="{m}",route="{path}",status="{code}"}} {n}')
    return PlainTextResponse("\n".join(lines) + "\n")


@app.get("/v1/devices")
def list_devices(cust: str = Depends(customer), repo: Repo = Depends(get_repo)):
    return {"customer": cust, "devices": repo.devices(cust)}


@app.get("/v1/devices/{device_id}/messages")
def device_messages(device_id: str, since: dt.datetime | None = None, limit: int = Query(100, ge=1, le=5000),
                    cust: str = Depends(customer), repo: Repo = Depends(get_repo)):
    if not any(d["device_id"] == device_id for d in repo.devices(cust)):
        raise HTTPException(404, "device not found")  # also hides other customers' devices
    return {"device_id": device_id, "messages": repo.messages(cust, device_id, since, limit)}


@app.get("/v1/devices/{device_id}/latest")
def device_latest(device_id: str, cust: str = Depends(customer), repo: Repo = Depends(get_repo)):
    rows = device_messages(device_id, None, 1, cust, repo)["messages"]
    if not rows:
        raise HTTPException(404, "no messages yet")
    return rows[0]


@app.get("/v1/sla")
def sla(days: int = Query(7, ge=1, le=90), cust: str = Depends(customer), repo: Repo = Depends(get_repo)):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    rows = repo.sla(cust, since)
    for r in rows:
        r["p95_min"] = round(r["p95_s"] / 60, 1) if r["p95_s"] is not None else None
        r["meets_target"] = r["p95_min"] is not None and r["p95_min"] <= SLA_TARGET_P95_MIN
    return {"customer": cust, "days": days, "target_p95_min": SLA_TARGET_P95_MIN, "paths": rows}


@app.get("/v1/invoices")
def invoices(cust: str = Depends(customer), repo: Repo = Depends(get_repo)):
    """Issued monthly statements (ground/billing/billing.py), newest first."""
    return {"customer": cust, "invoices": repo.invoices(cust)}


@app.get("/v1/report")
def monthly_report(month: str = Query(..., pattern=r"^\d{4}-\d{2}$", examples=["2026-11"]),
                   cust: str = Depends(customer), repo: Repo = Depends(get_repo)):
    y, m = map(int, month.split("-"))
    start = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    end = dt.datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=dt.timezone.utc)
    u = repo.usage(cust, start, end)
    return {"customer": cust, "month": month, **u,
            "price_per_device_month_usd": PRICE_PER_DEVICE_MONTH,
            "amount_usd": round(u["active_devices"] * PRICE_PER_DEVICE_MONTH, 2),
            "note": "Usage preview, not an invoice. Billing terms per customer contract."}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "create-key":
        print(PgRepo(os.environ["PG_DSN"]).create_key(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "revoke-key":
        print("revoked" if PgRepo(os.environ["PG_DSN"]).revoke_key(sys.argv[2]) else "not found")
    else:
        print(__doc__)
