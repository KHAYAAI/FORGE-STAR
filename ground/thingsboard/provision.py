"""Provision ThingsBoard for the FORGE STAR Stage 0 platform.

Creates one device per simulated (or real) field device, writes their access
tokens to ground/thingsboard/tokens.json (ingest forwards telemetry with them),
and creates a "FORGE STAR — Operations" dashboard with:
  * an entities table: device, customer, battery, last latency
  * a map of device positions
  * a latency time-series chart (store-and-forward delay per device)

Usage (with `docker compose --profile full up -d` running):
  python3 ground/thingsboard/provision.py --url http://localhost:8080 --devices 50
Defaults to ThingsBoard's demo tenant login; pass --user/--password for a real tenant.
Standard library only, so it runs anywhere.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
KINDS = [("pump", "Mining co (Limpopo)"), ("soil", "Farm co-op (N Cape)"), ("collar", "Private reserve"),
         ("vessel", "DFFE fisheries (AIS)"), ("tracker", "FORGE Freight")]


class TB:
    def __init__(self, url: str):
        self.url = url.rstrip("/"); self.token = None

    def call(self, method: str, path: str, body=None, ok404=False):
        req = urllib.request.Request(self.url + path, method=method,
                                     data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              **({"X-Authorization": f"Bearer {self.token}"} if self.token else {})})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if ok404 and e.code == 404:
                return None
            raise SystemExit(f"ThingsBoard {method} {path} -> {e.code}: {e.read()[:300]!r}")

    def login(self, user: str, pw: str, wait_s: int = 300):
        t0 = time.time()
        while True:
            try:
                self.token = self.call("POST", "/api/auth/login", {"username": user, "password": pw})["token"]
                return
            except (urllib.error.URLError, ConnectionError, SystemExit) as e:
                if time.time() - t0 > wait_s:
                    raise SystemExit(f"cannot log in to ThingsBoard at {self.url}: {e}")
                time.sleep(5)


def device_names(n: int):
    """Same naming as ground/simulator/simulate.py, so simulated telemetry lands on these devices."""
    return [(f"{KINDS[i % 5][0]}-{i:04d}", KINDS[i % 5][0], KINDS[i % 5][1]) for i in range(n)]


def ensure_device(tb: TB, name: str, kind: str, customer: str) -> str:
    dev = tb.call("GET", f"/api/tenant/devices?deviceName={urllib.request.quote(name)}", ok404=True)
    if not dev:
        dev = tb.call("POST", "/api/device", {"name": name, "type": kind, "label": customer})
        tb.call("POST", f"/api/plugins/telemetry/DEVICE/{dev['id']['id']}/SERVER_SCOPE",
                {"customer": customer, "kind": kind})
    creds = tb.call("GET", f"/api/device/{dev['id']['id']}/credentials")
    return creds["credentialsId"]


# Candidate widget type FQNs, newest naming first. ThingsBoard renamed widgets between releases.
WIDGETS = {
    "table": ["entities_table", "cards.entities_table"],
    "map": ["openstreetmap", "maps_v2.openstreetmap", "map"],
    "chart": ["time_series_chart", "charts.basic_timeseries", "charts.timeseries"],
}


def find_widget(tb: TB, candidates):
    for fqn in candidates:
        w = tb.call("GET", f"/api/widgetType?fqn={urllib.request.quote('system.' + fqn)}", ok404=True)
        if w:
            return w
    return None


def dashboard(tb: TB, widgets: dict) -> dict:
    alias = "aliasAllDevices"
    ds = [{"type": "entity", "entityAliasId": alias, "dataKeys": []}]
    keys = {
        "table": [("latest", "battery_v", "Battery (V)"), ("latest", "latency_s", "Last latency (s)"),
                  ("attribute", "customer", "Customer")],
        "map": [("timeseries", "latitude", "latitude"), ("timeseries", "longitude", "longitude")],
        "chart": [("timeseries", "latency_s", "Store-and-forward latency (s)")],
    }
    layout, wmap, col = {}, {}, 0
    sizes = {"table": (12, 8), "map": (12, 8), "chart": (24, 7)}
    pos = {"table": (0, 0), "map": (12, 0), "chart": (0, 8)}
    for kind, wt in widgets.items():
        if not wt:
            continue
        wid = f"w_{kind}"
        d = json.loads(json.dumps(ds))
        for t, k, label in keys[kind]:
            d[0]["dataKeys"].append({"name": k, "type": "timeseries" if t in ("latest", "timeseries") else "attribute",
                                     "label": label, "settings": {}})
        desc = wt.get("descriptor", {})
        wmap[wid] = {"id": wid, "typeFullFqn": wt.get("fqn") or "system." + kind, "type": desc.get("type", "latest"),
                     "sizeX": sizes[kind][0], "sizeY": sizes[kind][1],
                     "config": {"title": {"table": "Devices", "map": "Where they are", "chart": "Latency"}[kind],
                                "showTitle": True, "datasources": d,
                                "timewindow": {"realtime": {"timewindowMs": 6 * 3600 * 1000}},
                                "settings": json.loads(desc.get("defaultConfig", "{}")).get("settings", {})}}
        layout[wid] = {"sizeX": sizes[kind][0], "sizeY": sizes[kind][1], "row": pos[kind][1], "col": pos[kind][0]}
    return {
        "title": "FORGE STAR — Operations",
        "configuration": {
            "description": "Stage 0 platform: devices, positions and store-and-forward latency.",
            "widgets": wmap,
            "entityAliases": {alias: {"id": alias, "alias": "All devices",
                                      "filter": {"type": "entityType", "entityType": "DEVICE", "resolveMultiple": True}}},
            "states": {"default": {"name": "FORGE STAR", "root": True,
                                   "layouts": {"main": {"widgets": layout, "gridSettings": {"columns": 24}}}}},
            "timewindow": {"realtime": {"timewindowMs": 6 * 3600 * 1000}},
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8080")
    ap.add_argument("--user", default="tenant@thingsboard.org")
    ap.add_argument("--password", default="tenant")
    ap.add_argument("--devices", type=int, default=50)
    ap.add_argument("--tokens", default=str(HERE / "tokens.json"))
    a = ap.parse_args()
    tb = TB(a.url); tb.login(a.user, a.password)
    tokens = {name: ensure_device(tb, name, kind, cust) for name, kind, cust in device_names(a.devices)}
    Path(a.tokens).write_text(json.dumps(tokens, indent=1))
    print(f"provisioned {len(tokens)} devices -> {a.tokens}")
    found = {k: find_widget(tb, v) for k, v in WIDGETS.items()}
    missing = [k for k, v in found.items() if not v]
    if missing:
        print(f"warning: widget types not found on this ThingsBoard version: {missing} (dashboard created without them)")
    existing = tb.call("GET", "/api/tenant/dashboards?pageSize=100&page=0&textSearch=FORGE%20STAR")
    body = dashboard(tb, found)
    for d in (existing or {}).get("data", []):
        if d.get("title") == body["title"]:
            body["id"] = d["id"]; body["version"] = d.get("version")
    saved = tb.call("POST", "/api/dashboard", body)
    print(f"dashboard: {a.url}/dashboards/{saved['id']['id']}")


if __name__ == "__main__":
    main()
