import os
import sys
import webbrowser
import http.server
import socketserver

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

def main():
    print("=" * 76)
    print(" HEALYTICS: Obsidian & Gold Executive Suite Intelligence Terminal")
    print("=" * 76)
    print(f" Serving dashboard from: {APP_DIR}")
    print(f" Local URL: http://localhost:{PORT}")
    print(f" Network:   http://127.0.0.1:{PORT}")
    print("=" * 76)
    print(" Opening browser... (Press Ctrl+C to stop the server)")
    
    webbrowser.open(f"http://localhost:{PORT}")
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            sys.exit(0)

if __name__ == "__main__":
    main()
