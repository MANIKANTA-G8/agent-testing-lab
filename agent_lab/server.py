import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .core import run_suite, save_run

ROOT = Path(__file__).resolve().parent.parent


class Handler(BaseHTTPRequestHandler):
    def send(self, status, content, kind="application/json"):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", kind + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            return self.send(200, (ROOT / "web/index.html").read_text(encoding="utf-8"), "text/html")
        if self.path == "/api/runs":
            runs = []
            for folder in (ROOT / "examples", ROOT / "runs"):
                for path in folder.glob("*.json"):
                    try:
                        runs.append(json.loads(path.read_text(encoding="utf-8")))
                    except (OSError, ValueError):
                        continue
            return self.send(200, json.dumps(sorted(runs, key=lambda r: r["created_at"], reverse=True)))
        return self.send(404, '{"error":"Not found"}')

    def do_POST(self):
        if self.path != "/api/run":
            return self.send(404, '{"error":"Not found"}')
        # Local application: reject browser requests from other origins.
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
            return self.send(403, '{"error":"Origin rejected"}')
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Request body must be between 1 and 4096 bytes")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object")
            run = run_suite(body.get("variant", "improved"), body.get("repeats", 1))
            save_run(run, ROOT / "runs")
            self.send(201, json.dumps(run))
        except (ValueError, TypeError) as error:
            self.send(400, json.dumps({"error": str(error)}))


def serve(port=8765):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Agent Testing Lab: http://127.0.0.1:{port} (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
