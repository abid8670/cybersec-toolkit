"""Web vulnerability scanner."""
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

SECURITY_HEADERS = ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options",
                   "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"]

class WebVulnScanner:
    def __init__(self, url, timeout=10):
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "CyberSecToolkit/1.0"})

    def check_headers(self):
        r = self.session.get(self.url, timeout=self.timeout, verify=False)
        missing = [h for h in SECURITY_HEADERS if h not in r.headers]
        return {"status": r.status_code, "missing_headers": missing, "present": {h: r.headers.get(h) for h in SECURITY_HEADERS if h in r.headers}}

    def check_cors(self):
        r = self.session.get(self.url, headers={"Origin": "https://evil.example"}, timeout=self.timeout, verify=False)
        acao = r.headers.get("Access-Control-Allow-Origin")
        acac = r.headers.get("Access-Control-Allow-Credentials")
        vuln = acao == "*" or (acao == "https://evil.example" and acac == "true")
        return {"acao": acao, "acac": acac, "vulnerable": vuln}

    def find_forms(self):
        r = self.session.get(self.url, timeout=self.timeout, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        forms = []
        for f in soup.find_all("form"):
            forms.append({"action": f.get("action"), "method": f.get("method", "get").lower(),
                          "inputs": [i.get("name") for i in f.find_all("input")]})
        return forms

    def sqli_probe(self, param_url):
        payloads = ["'", "\"", "' OR '1'='1", "\" OR \"1\"=\"1", "';--"]
        results = []
        for p in payloads:
            try:
                r = self.session.get(param_url + p, timeout=self.timeout, verify=False)
                err_markers = ["sql syntax", "mysql", "sqlite", "postgresql", "ora-", "unclosed quotation"]
                hit = any(m in r.text.lower() for m in err_markers)
                results.append({"payload": p, "error_leak": hit, "status": r.status_code})
            except Exception as e:
                results.append({"payload": p, "error": str(e)})
        return results

    def xss_probe(self, param_url):
        payload = "<script>alert(1)</script>"
        r = self.session.get(param_url + payload, timeout=self.timeout, verify=False)
        reflected = payload in r.text
        return {"reflected": reflected}

    def sensitive_files(self):
        paths = ["/.env", "/.git/HEAD", "/config.php", "/wp-config.php", "/robots.txt", "/sitemap.xml", "/admin", "/phpinfo.php"]
        found = []
        for p in paths:
            try:
                r = self.session.get(self.url + p, timeout=self.timeout, verify=False)
                if r.status_code < 400:
                    found.append({"path": p, "status": r.status_code, "size": len(r.content)})
            except Exception:
                pass
        return found

    def open_redirect(self, param_url):
        r = self.session.get(param_url + "https://evil.example", timeout=self.timeout, verify=False, allow_redirects=False)
        loc = r.headers.get("Location", "")
        return {"redirects_to_external": "evil.example" in loc, "location": loc}

    def full(self):
        return {
            "headers": self.check_headers(),
            "cors": self.check_cors(),
            "forms": self.find_forms(),
            "sensitive_files": self.sensitive_files(),
        }
