import json
import urllib.request
import time

from web_interface import start_server


def test_web_server_serves_results():
    data = {"Mat": {"total_volume": 1.0, "total_mass": 2.0, "total_carbon": 3.0}}
    server = start_server(data, port=0)
    port = server.server_address[1]
    # Allow server to start
    time.sleep(0.1)
    with urllib.request.urlopen(f"http://localhost:{port}/results") as resp:
        body = resp.read().decode()
    server.shutdown()
    received = json.loads(body)
    assert received == data
