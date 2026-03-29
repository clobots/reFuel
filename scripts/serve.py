#!/usr/bin/env python3
"""Local dev server with /api/refresh endpoint to re-fetch FuelCheck data."""

import http.server
import json
import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_DIR)

class RefuelHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/refresh":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                # Run fetch + pipeline
                result = subprocess.run(
                    [sys.executable, "scripts/fetch_fuelcheck.py"],
                    capture_output=True, text=True, timeout=30
                )
                fetch_ok = result.returncode == 0
                fetch_out = result.stdout + result.stderr

                result2 = subprocess.run(
                    [sys.executable, "scripts/run_all.py"],
                    capture_output=True, text=True, timeout=30
                )
                pipe_ok = result2.returncode == 0
                pipe_out = result2.stdout + result2.stderr

                self.wfile.write(json.dumps({
                    "ok": fetch_ok and pipe_ok,
                    "fetch": fetch_out.strip(),
                    "pipeline": pipe_out.strip(),
                }).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.end_headers()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = http.server.HTTPServer(("", port), RefuelHandler)
    print(f"reFuel server running at http://localhost:{port}")
    print("POST /api/refresh to re-fetch FuelCheck prices")
    server.serve_forever()
