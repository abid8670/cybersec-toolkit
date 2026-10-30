"""Subdomain enumeration via crt.sh."""
import requests

class SubdomainEnum:
    def __init__(self, domain):
        self.domain = domain

    def crtsh(self):
        url = f"https://crt.sh/?q=%25.{self.domain}&output=json"
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            return {"error": str(e)}
        subs = set()
        for e in data:
            name = e.get("name_value", "")
            for line in name.split("\n"):
                line = line.strip().lower()
                if line.endswith(self.domain):
                    subs.add(line)
        return {"domain": self.domain, "count": len(subs), "subdomains": sorted(subs)}
