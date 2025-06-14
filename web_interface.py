import http.server
import socketserver
import threading
import webbrowser
import json
from pathlib import Path

WEB_DIR = Path(__file__).parent / 'assets' / 'web'

class ResultsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, results=None, **kwargs):
        self.results = results or {}
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        if self.path.rstrip('/') == '/results':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.results).encode('utf-8'))
        else:
            super().do_GET()

def start_server(results, port=0):
    handler = lambda *args, **kwargs: ResultsHandler(*args, results=results, **kwargs)
    httpd = socketserver.TCPServer(('localhost', port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd

def launch_results_browser(results):
    server = start_server(results)
    port = server.server_address[1]
    url = f'http://localhost:{port}/index.html'
    try:
        webbrowser.open(url)
    except Exception:
        pass
    return server
