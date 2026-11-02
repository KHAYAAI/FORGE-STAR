"""Run provision.py against a fake ThingsBoard REST API."""
import json, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ground" / "thingsboard"))
import provision  # noqa: E402

STATE = {"devices": {}, "dashboards": []}


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body=None):
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers()
        if body is not None: self.wfile.write(json.dumps(body).encode())
    def _body(self):
        n = int(self.headers.get("Content-Length", 0)); return json.loads(self.rfile.read(n) or b"{}")
    def do_POST(self):
        b = self._body()
        if self.path == "/api/auth/login": return self._send(200, {"token": "t"})
        assert self.headers.get("X-Authorization") == "Bearer t"
        if self.path == "/api/device":
            did = f"id-{len(STATE['devices'])}"; STATE["devices"][b["name"]] = did
            return self._send(200, {"id": {"id": did}, "name": b["name"]})
        if self.path.startswith("/api/plugins/telemetry/"): return self._send(200)
        if self.path == "/api/dashboard":
            STATE["dashboards"].append(b); return self._send(200, {"id": {"id": "dash-1"}})
        self._send(404)
    def do_GET(self):
        if self.path.startswith("/api/tenant/devices"): return self._send(404)
        if self.path.startswith("/api/device/"):
            return self._send(200, {"credentialsId": "tok-" + self.path.split("/")[3]})
        if self.path.startswith("/api/widgetType"):
            fqn = self.path.split("fqn=")[1].replace("system.", "")
            # like ThingsBoard 3.8: known types return their fqn (no "system." prefix); unknown -> 200 with {}
            known = {"cards.entities_table", "maps_v2.openstreetmap"}
            return self._send(200, {"fqn": fqn, "descriptor": {"type": "latest", "defaultConfig": "{}"}} if fqn in known else {})
        if self.path.startswith("/api/tenant/dashboards"): return self._send(200, {"data": []})
        self._send(404)


def test_provision(tmp_path, monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), Fake); threading.Thread(target=srv.serve_forever, daemon=True).start()
    tok = tmp_path / "tokens.json"
    monkeypatch.setattr(sys, "argv", ["provision.py", "--url", f"http://127.0.0.1:{srv.server_port}", "--devices", "10", "--tokens", str(tok)])
    monkeypatch.delenv("HTTP_PROXY", raising=False); monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1"); monkeypatch.setenv("no_proxy", "127.0.0.1")
    provision.main(); srv.shutdown()
    tokens = json.loads(tok.read_text())
    assert len(tokens) == 10 and tokens["pump-0000"].startswith("tok-")
    d = STATE["dashboards"][-1]
    assert d["title"] == "FORGE STAR — Operations"
    w = d["configuration"]["widgets"]
    assert set(w) == {"w_table", "w_map"}  # chart type unknown on the fake -> skipped, not referenced
    assert w["w_table"]["typeFullFqn"] == "system.cards.entities_table"
    assert w["w_map"]["typeFullFqn"] == "system.maps_v2.openstreetmap"
