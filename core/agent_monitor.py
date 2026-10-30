"""Central monitor for generic agents."""
import json, urllib.request, time

def check_agent(url, token):
    try:
        req = urllib.request.Request(url + "/health", headers={"X-Token": token})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        return {"status": "UP", "data": data}
    except Exception as e:
        return {"status": "DOWN", "error": str(e)}

def monitor(agents):
    # agents: list of {name, url, token}
    out = []
    for a in agents:
        res = check_agent(a["url"], a.get("token", "changeme"))
        out.append({"name": a["name"], "url": a["url"], **res})
    return out
