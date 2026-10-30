"""Web UI for CyberSec Toolkit (Flask)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, render_template, request, jsonify
from core.web_vuln import WebVulnScanner
from core.cve import CVELookup
from core.ssl_audit import SSLAudit
from core.subdomain import SubdomainEnum

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
