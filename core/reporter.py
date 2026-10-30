"""Report generator."""
import json, datetime, os

class Reporter:
    def __init__(self, outdir="reports"):
        self.outdir = outdir
        os.makedirs(outdir, exist_ok=True)

    def save_json(self, data, name="report"):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.outdir, f"{name}_{ts}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def save_html(self, data, name="report"):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.outdir, f"{name}_{ts}.html")
        rows = ""
        for k, v in data.items():
            rows += f"<tr><td><b>{k}</b></td><td><pre>{v}</pre></td></tr>"
        html = f"""<!DOCTYPE html><html><head><meta charset=utf-8><title>Report</title>
<style>body{{font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}}table{{width:100%;border-collapse:collapse}}td,th{{border:1px solid #30363d;padding:8px;vertical-align:top}}pre{{white-space:pre-wrap}}</style></head>
<body><h1>CyberSec Toolkit Report</h1><p>{ts}</p><table>{rows}</table></body></html>"""
        with open(path, "w") as f:
            f.write(html)
        return path
