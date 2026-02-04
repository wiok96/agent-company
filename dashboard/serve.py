#!/usr/bin/env python3
"""
Simple HTTP server for testing the AACS dashboard locally.
Run this script and open http://localhost:8000 in your browser.
"""

import http.server
import socketserver
import os
import sys

# Change to dashboard directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow local file access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        # Handle requests for files in parent directories
        if self.path.startswith('/board/') or self.path.startswith('/meetings/'):
            # Serve files from parent directory
            file_path = '..' + self.path
            if os.path.exists(file_path):
                self.path = file_path
        
        return super().do_GET()

if __name__ == "__main__":
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"🚀 AACS Dashboard Server running at http://localhost:{PORT}")
            print("📋 Open this URL in your browser to view the dashboard")
            print("⏹️  Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        sys.exit(0)
    except OSError as e:
        if e.errno == 10048:  # Port already in use on Windows
            print(f"❌ Port {PORT} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)