"""CVE lookup via NVD API."""
import requests

class CVELookup:
    BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def search(self, keyword, results=10):
        try:
            r = requests.get(self.BASE, params={"keywordSearch": keyword, "resultsPerPage": results}, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            return {"error": str(e)}
        out = []
        for v in data.get("vulnerabilities", []):
            cve = v.get("cve", {})
            metrics = cve.get("metrics", {})
            cvss = None
            for k in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                if k in metrics and metrics[k]:
                    cvss = metrics[k][0].get("cvssData", {}).get("baseScore")
                    break
            desc = ""
            for d in cve.get("descriptions", []):
                if d.get("lang") == "en":
                    desc = d.get("value", "")
            out.append({"id": cve.get("id"), "cvss": cvss, "description": desc[:300]})
        return {"keyword": keyword, "count": len(out), "cves": out}
