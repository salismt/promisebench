"""HTTP front for orders.app. Run: python3 -m orders.server --port 8080"""
import argparse
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .app import handle_request


class OrdersHandler(BaseHTTPRequestHandler):
    server_version = "orders-api"

    def _dispatch(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        resp = handle_request({
            "method": self.command,
            "path": self.path,
            "headers": dict(self.headers),
            "body": body,
        })
        data = resp["body"].encode("utf-8")
        self.send_response(resp["status"])
        for name, value in resp["headers"].items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _dispatch

    def log_message(self, fmt, *args):
        logging.getLogger("orders.http").info(fmt, *args)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Orders API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    httpd = ThreadingHTTPServer((args.host, args.port), OrdersHandler)
    logging.info("listening on %s:%d", args.host, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
