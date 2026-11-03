import datetime as dt
import sys
from pathlib import Path
import pytest
pytest.importorskip("fastapi"); pytest.importorskip("httpx")
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ground" / "api"))
import app as api  # noqa: E402
from repo import MemoryRepo  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)


@pytest.fixture
def client():
    r = MemoryRepo()
    r.devs = [{"device_id": "pump-0000", "kind": "pump", "customer": "Mine"},
              {"device_id": "vessel-0003", "kind": "vessel", "customer": "DFFE"}]
    for i in range(20):
        t = NOW - dt.timedelta(hours=i)
        r.ups.append({"device_id": "pump-0000", "time": t, "received_at": t + dt.timedelta(minutes=5 + i),
                      "path": "satellite", "sat": 3, "lat": -24.1, "lon": 29.5, "payload": {"flow_lpm": i}})
    r.ups.append({"device_id": "vessel-0003", "time": NOW, "received_at": NOW, "path": "resale",
                  "sat": None, "lat": -34, "lon": 18, "payload": {"mmsi": 1}})
    keys = {"Mine": r.create_key("Mine"), "DFFE": r.create_key("DFFE")}
    api.app.dependency_overrides[api.get_repo] = lambda: r
    yield TestClient(api.app), keys
    api.app.dependency_overrides.clear()


def test_requires_valid_key(client):
    c, _ = client
    assert c.get("/v1/devices").status_code == 422          # header missing
    assert c.get("/v1/devices", headers={"X-API-Key": "nope"}).status_code == 401
    assert c.get("/health").status_code == 200


def test_customer_sees_only_own_devices(client):
    c, k = client
    r = c.get("/v1/devices", headers={"X-API-Key": k["Mine"]}).json()
    assert [d["device_id"] for d in r["devices"]] == ["pump-0000"] and r["devices"][0]["messages_7d"] == 20
    # another customer's device is invisible, not forbidden (no information leak)
    assert c.get("/v1/devices/vessel-0003/messages", headers={"X-API-Key": k["Mine"]}).status_code == 404


def test_messages_latest_and_since(client):
    c, k = client
    h = {"X-API-Key": k["Mine"]}
    assert c.get("/v1/devices/pump-0000/latest", headers=h).json()["payload"] == {"flow_lpm": 0}
    since = (NOW - dt.timedelta(hours=4, minutes=30)).isoformat()
    m = c.get("/v1/devices/pump-0000/messages", headers=h, params={"since": since}).json()["messages"]
    assert len(m) == 5


def test_sla_and_report(client):
    c, k = client
    h = {"X-API-Key": k["Mine"]}
    s = c.get("/v1/sla", headers=h).json()["paths"][0]
    assert s["path"] == "satellite" and s["messages"] == 20 and 20 <= s["p95_min"] <= 25 and s["meets_target"]
    rep = c.get("/v1/report", headers=h, params={"month": NOW.strftime("%Y-%m")}).json()
    assert rep["active_devices"] == 1 and rep["amount_usd"] == api.PRICE_PER_DEVICE_MONTH
    assert c.get("/v1/report", headers=h, params={"month": "2026-13x"}).status_code == 422


def test_rate_limit_security_headers_audit_metrics(client, monkeypatch):
    c, k = client
    monkeypatch.setattr(api, "RATE_PER_MIN", 5); api._buckets.clear()
    h = {"X-API-Key": k["Mine"]}
    codes = [c.get("/v1/devices", headers=h).status_code for _ in range(8)]
    assert codes[:5] == [200] * 5 and 429 in codes[5:]
    r = c.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"
    repo = api.app.dependency_overrides[api.get_repo]()
    m = c.get("/metrics").text
    assert 'route="/v1/devices",status="200"' in m and 'status="429"' in m
    api._buckets.clear()


def test_revoked_key_is_refused(client):
    c, k = client
    repo = api.app.dependency_overrides[api.get_repo]()
    assert c.get("/v1/devices", headers={"X-API-Key": k["DFFE"]}).status_code == 200
    assert repo.revoke_key(k["DFFE"])
    assert c.get("/v1/devices", headers={"X-API-Key": k["DFFE"]}).status_code == 401
