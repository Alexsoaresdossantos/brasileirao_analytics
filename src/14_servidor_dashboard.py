import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "reports/dashboard/brasileirao_dashboard.html"


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD.parent), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/dashboard", "/brasileirao_dashboard.html"}:
            self.path = "/brasileirao_dashboard.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/atualizar":
            self.send_error(404)
            return

        try:
            result = subprocess.run(
                [sys.executable, "src/13_atualizar_dashboard.py"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            payload = {"ok": True, "output": result.stdout[-6000:]}
            status = 200
        except subprocess.CalledProcessError as error:
            payload = {
                "ok": False,
                "output": (error.stdout or "")[-3000:],
                "error": (error.stderr or str(error))[-3000:],
            }
            status = 500

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"Dashboard: http://127.0.0.1:{port}/")
    print("Use Ctrl+C para encerrar.")
    server.serve_forever()


if __name__ == "__main__":
    main()
