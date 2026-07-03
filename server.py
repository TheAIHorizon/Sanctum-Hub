#!/usr/bin/env python3
"""Sanctum Hub — local launcher backend (stdlib only).

Serves the hub UI and provides:
  GET  /api/status        -> {app_id: {"up": bool, "port": int}}
  POST /api/launch {id}   -> starts an app's `start` command in its `dir`

Loopback-only by design. It runs the commands you put in apps.json on your own
machine — treat apps.json as trusted config.
"""
import json
import os
import socket
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", int(os.environ.get("SANCTUM_HUB_PORT", "7080"))


def load_registry():
    with open(ROOT / "apps.json") as f:
        return json.load(f)


def expand(p: str) -> Path:
    return Path(os.path.expanduser(p))


def port_up(port: int, timeout: float = 0.35) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            return s.connect_ex(("127.0.0.1", int(port))) == 0
        except OSError:
            return False


def statuses():
    reg = load_registry()
    out = {}
    for a in reg["apps"]:
        out[a["id"]] = {"up": port_up(a["port"]), "port": a["port"],
                        "dir_exists": expand(a["dir"]).is_dir()}
    return out


def launch(app_id: str):
    reg = load_registry()
    app = next((a for a in reg["apps"] if a["id"] == app_id), None)
    if not app:
        return {"ok": False, "error": f"unknown app '{app_id}'"}
    workdir = expand(app["dir"])
    if not workdir.is_dir():
        return {"ok": False, "error": f"not cloned yet: {app['dir']} (clone {app['repo']})"}
    logdir = ROOT / "logs"
    logdir.mkdir(exist_ok=True)
    logfile = open(logdir / f"{app_id}.log", "ab")
    try:
        subprocess.Popen(
            app["start"], shell=True, cwd=str(workdir),
            stdout=logfile, stderr=logfile,
            stdin=subprocess.DEVNULL, start_new_session=True,
        )
        return {"ok": True, "started": app["start"], "cwd": str(workdir)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/status"):
            return self._send(200, statuses())
        # static files
        rel = self.path.split("?", 1)[0].lstrip("/") or "index.html"
        fp = (ROOT / rel).resolve()
        if ROOT not in fp.parents and fp != ROOT / rel or not fp.is_file():
            fp = ROOT / "index.html"
        ctype = {"html": "text/html", "json": "application/json",
                 "js": "text/javascript", "css": "text/css"}.get(fp.suffix.lstrip("."), "text/plain")
        return self._send(200, fp.read_bytes(), ctype + "; charset=utf-8")

    def do_POST(self):
        if self.path.startswith("/api/launch"):
            n = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"ok": False, "error": "bad JSON"})
            return self._send(200, launch(body.get("id", "")))
        return self._send(404, {"ok": False, "error": "not found"})

    def log_message(self, *a):  # quiet
        pass


def main():
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Sanctum Hub → http://{HOST}:{PORT}  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
        srv.shutdown()


if __name__ == "__main__":
    sys.exit(main())
