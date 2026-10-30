"""Web UI for CyberSec Toolkit (Flask)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, render_template, request, jsonify
from core.web_vuln import WebVulnScanner
from core.cve import CVELookup
from core.ssl_audit import SSLAudit
from core.subdomain import SubdomainEnum
from core.flood import PyFlood
from core.scanner import NetworkScanner

app = Flask(__name__, template_folder="templates")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scan-web", methods=["POST"])
def api_scan_web():
    url = request.json.get("url")
    return jsonify(WebVulnScanner(url).full())

@app.route("/api/cve", methods=["POST"])
def api_cve():
    kw = request.json.get("keyword")
    return jsonify(CVELookup().search(kw, request.json.get("limit", 10)))

@app.route("/api/ssl", methods=["POST"])
def api_ssl():
    host = request.json.get("host")
    return jsonify(SSLAudit(host, request.json.get("port", 443)).audit())

@app.route("/api/subdomain", methods=["POST"])
def api_subdomain():
    return jsonify(SubdomainEnum(request.json.get("domain")).crtsh())

@app.route("/api/flood", methods=["POST"])
def api_flood():
    d = request.json
    pf = PyFlood(d.get("target"), d.get("port", 80))
    mode = d.get("mode", "syn")
    if mode == "syn":
        return jsonify(pf.syn(d.get("count", 1000)))
    if mode == "udp":
        return jsonify(pf.udp(d.get("count", 1000)))
    return jsonify(pf.icmp(d.get("count", 1000)))

@app.route("/api/scan-network", methods=["POST"])
def api_scan_network():
    t = request.json.get("target")
    ports = request.json.get("ports", "1-1024")
    ns = NetworkScanner(t)
    return jsonify({"hosts": ns.host_discovery(), "ports": ns.port_scan(ports)})

@app.route("/api/honeypot-logs", methods=["GET"])
def api_honeypot_logs():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "honeypot.log")
    lines = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except Exception:
                        lines.append({"raw": line})
    return jsonify({"count": len(lines), "logs": lines[-100:]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
