#!/usr/bin/env python3
"""
Callback Server for R730 NixOS Installation
Listens for the installer to phone home
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

LISTEN_PORT = 9999

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests from installer"""
        print(f"\n{'='*60}")
        print(f"🔔 CALLBACK RECEIVED at {datetime.now()}")
        print(f"{'='*60}")
        print(f"Path: {self.path}")
        print(f"Client: {self.client_address[0]}")
        print(f"Headers: {dict(self.headers)}")
        print(f"{'='*60}\n")

        if self.path == '/ready':
            print("✅ R730 NixOS installer is READY!")
            print("\nYou can now proceed with installation commands.")
            print("The installer is waiting for your input.\n")

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Callback received! Claude is ready to help.\n')

    def do_POST(self):
        """Handle POST requests with data"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        print(f"\n{'='*60}")
        print(f"🔔 CALLBACK WITH DATA at {datetime.now()}")
        print(f"{'='*60}")
        print(f"Client: {self.client_address[0]}")
        print(f"Data: {post_data.decode('utf-8', errors='ignore')}")
        print(f"{'='*60}\n")

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Data received!\n')

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def main():
    server = HTTPServer(('0.0.0.0', LISTEN_PORT), CallbackHandler)

    print(f"""
{'='*60}
🎯 R730 Installation Callback Server
{'='*60}

Server listening on: http://0.0.0.0:{LISTEN_PORT}
Local access: http://192.168.1.175:{LISTEN_PORT}

Waiting for R730 to phone home...

When R730 boots to NixOS installer, run this command:
    curl http://192.168.1.175:{LISTEN_PORT}/ready

This will signal that you're ready for installation!

Press Ctrl+C to stop.
{'='*60}
    """)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down callback server...")
        server.shutdown()

if __name__ == '__main__':
    main()
