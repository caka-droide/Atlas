"""Petit serveur HTTP pour satisfaire le health-check d'un hébergeur type Render."""
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import config


class _KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"{config.BOT_NAME} en ligne !".encode("utf-8"))

    def log_message(self, format, *args):
        pass


def _run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), _KeepAliveHandler)
    server.serve_forever()


def start_keepalive_server() -> None:
    threading.Thread(target=_run_web_server, daemon=True).start()
