"""
Local website server for the mapping demo.

Run:
    .\\.venv\\Scripts\\python.exe mapping_demo_server.py

Then open:
    http://127.0.0.1:8031/Rover%20Iterations/updatedinnovaiton.html#mapping-demo
"""

from __future__ import annotations

import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8031
ROOT = Path(__file__).resolve().parent
RECENT_SCAN_DIR = ROOT / "guided_room_scan_recent"
ALL_SCAN_DIR = ROOT / "guided_room_scan"
STITCH_SCRIPT = ROOT / "stitch_room_snapshots.py"
PANORAMA_PATH = ROOT / "room_model" / "room_panorama.jpg"


class MappingDemoHandler(SimpleHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/run-panorama":
            self.send_error(404, "Unknown endpoint")
            return

        folder = RECENT_SCAN_DIR if RECENT_SCAN_DIR.exists() else ALL_SCAN_DIR
        command = [
            sys.executable,
            str(STITCH_SCRIPT),
            "--folder",
            str(folder),
        ]

        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            ok = result.returncode == 0 and PANORAMA_PATH.exists()
            payload = {
                "ok": ok,
                "folder": folder.name,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "panorama": "room_model/room_panorama.jpg",
            }
            status = 200 if ok else 500
        except Exception as exc:
            payload = {"ok": False, "error": str(exc)}
            status = 500

        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), MappingDemoHandler)
    print(f"Mapping demo server running at http://{HOST}:{PORT}/")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
