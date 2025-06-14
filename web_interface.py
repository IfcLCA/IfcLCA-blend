import http.server
import socketserver
import threading
import webbrowser
import json
from pathlib import Path

_results_text = ""
_server = None
_thread = None
PORT = 0

class WebHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/results':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'results': _results_text}).encode('utf-8'))
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = _get_html()
            self.wfile.write(html.encode('utf-8'))
        else:
            super().do_GET()

def _get_html():
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'/>
    <title>IfcLCA Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2em; }}
        pre {{ background: #f0f0f0; padding: 1em; }}
    </style>
</head>
<body>
    <h1>IfcLCA Results</h1>
    <pre id='results'>Loading...</pre>
    <script>
        async function load() {{
            const r = await fetch('/api/results');
            const j = await r.json();
            document.getElementById('results').textContent = j.results || 'No results';
        }}
        load();
        setInterval(load, 2000);
    </script>
</body>
</html>"""
    return html

def start_server(port: int = 0):
    global _server, _thread, PORT
    if _server:
        return PORT
    handler = WebHandler
    _server = socketserver.TCPServer(('localhost', port), handler)
    PORT = _server.server_address[1]
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    webbrowser.open(f'http://localhost:{PORT}/')
    return PORT

def stop_server():
    global _server, _thread
    if _server:
        _server.shutdown()
        _server.server_close()
        _server = None
    if _thread:
        _thread.join()
        _thread = None

def update_results(text: str):
    global _results_text
    _results_text = text
