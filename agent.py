"""Generic monitoring agent - run on any server. Exposes /health with token auth."""
import http.server, socketserver, json, os, time, platform
try:
    import psutil
except Exception:
    psutil = None

TOKEN = os.environ.get("AGENT_TOKEN", "changeme")
PORT = int(os.environ.get("AGENT_PORT", "8765"))

def collect():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
    except Exception:
        cpu, mem, disk = None, None, None
    return {
        "host": platform.node(),
        "os": platform.system(),
        "uptime_s": time.time() - psutil.boot_time() if "psutil" in globals() else None,
        "cpu_percent": cpu,
        "mem_percent": mem,
        "disk_percent": disk,
        "timestamp": time.time(),
    }

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404); self.end_headers(); return
        if self.headers.get("X-Token") != TOKEN:
            self.send_response(401); self.end_headers(); return
        data = json.dumps(collect()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"[agent] listening on 0.0.0.0:{PORT} (token from AGENT_TOKEN env)")
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        httpd.serve_forever()
