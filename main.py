"""CyberSec Toolkit CLI entry point."""
import argparse, json
from core.cve import CVELookup
from core.remote import RemoteChecker
from core.agent_monitor import monitor
from core.subdomain import SubdomainEnum
from core.ssl_audit import SSLAudit
from core.flood import PyFlood
from core.scanner import NetworkScanner
from core.web_vuln import WebVulnScanner
from core.hping import HPing
from core.reporter import Reporter
import urllib3
urllib3.disable_warnings()

def main():
    print("""
   ____      _               ____            _   _           _ _
  / ___|   _| |__   ___ _ __/ ___|  ___  ___| |_(_) ___ __ _| | |
 | |  | | | | '_ \\ / _ \\ '__\\___ \\ / _ \\/ __| __| |/ __/ _` | | |
 | |__| |_| | |_) |  __/ |   ___) |  __/ (__| |_| | (_| (_| | | |
  \\____\\__, |_.__/ \\___|_|  |____/ \\___|\\___|\\__|_|\\___\\__,_|_|_|
       |___/        CyberSec Toolkit  |  authorized use only
""")
    p = argparse.ArgumentParser(prog="cybersec-toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan-network"); s.add_argument("target"); s.add_argument("--ports", default="1-1024")
    w = sub.add_parser("scan-web"); w.add_argument("url")
    h = sub.add_parser("hping"); h.add_argument("target"); h.add_argument("--mode", choices=["syn","udp","icmp"], default="syn"); h.add_argument("--count", type=int, default=1000); h.add_argument("--port", type=int, default=80); h.add_argument("--flood", action="store_true")
    c = sub.add_parser("cve"); c.add_argument("keyword"); c.add_argument("--limit", type=int, default=10)
    r = sub.add_parser("remote-health"); r.add_argument("host"); r.add_argument("-u","--user", required=True); r.add_argument("-p","--password"); r.add_argument("--key")
    a = sub.add_parser("agent-status"); a.add_argument("--config", default="agents.json")
    sd = sub.add_parser("subdomain"); sd.add_argument("domain")
    ss = sub.add_parser("ssl-audit"); ss.add_argument("host"); ss.add_argument("--port", type=int, default=443)
    fl = sub.add_parser("flood"); fl.add_argument("target"); fl.add_argument("--mode", choices=["syn","udp","icmp"], default="syn"); fl.add_argument("--count", type=int, default=1000); fl.add_argument("--port", type=int, default=80)
    hp = sub.add_parser("honeypot"); hp.add_argument("--ports", default="2222,8080,2323")
    f = sub.add_parser("full"); f.add_argument("target"); f.add_argument("--web", action="store_true")

    args = p.parse_args()
    rep = Reporter()

    if args.cmd == "scan-network":
        ns = NetworkScanner(args.target)
        data = {"hosts": ns.host_discovery(), "ports": ns.port_scan(args.ports)}
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "network"))

    elif args.cmd == "scan-web":
        ws = WebVulnScanner(args.url)
        data = ws.full()
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "web"))

    elif args.cmd == "hping":
        hp = HPing(args.target)
        data = hp.run(mode=args.mode, count=args.count, port=args.port, flood=args.flood)
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "hping"))

    elif args.cmd == "cve":
        cl = CVELookup()
        data = cl.search(args.keyword, args.limit)
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "cve"))

    elif args.cmd == "remote-health":
        rc = RemoteChecker(args.host, args.user, password=args.password, key=args.key)
        data = rc.health()
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "remote"))

    elif args.cmd == "agent-status":
        with open(args.config) as f:
            agents = json.load(f)
        data = monitor(agents)
        for d in data:
            print(f"[{d['status']}] {d['name']} ({d['url']})")
            if d["status"] == "UP":
                print("   ", d["data"])
        print("Saved:", rep.save_json(data, "agents"))

    elif args.cmd == "subdomain":
        se = SubdomainEnum(args.domain)
        data = se.crtsh()
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "subdomain"))

    elif args.cmd == "ssl-audit":
        sa = SSLAudit(args.host, args.port)
        data = sa.audit()
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "ssl"))

    elif args.cmd == "flood":
        pf = PyFlood(args.target, args.port)
        if args.mode == "syn":
            data = pf.syn(args.count)
        elif args.mode == "udp":
            data = pf.udp(args.count)
        else:
            data = pf.icmp(args.count)
        print(json.dumps(data, indent=2, default=str))
        print("Saved:", rep.save_json(data, "flood"))

    elif args.cmd == "honeypot":
        import honeypot
        honeypot.run()
        return

    elif args.cmd == "full":
        ns = NetworkScanner(args.target)
        data = {"network": {"hosts": ns.host_discovery(), "ports": ns.port_scan()}}
        if args.web:
            for h in data["network"]["hosts"]:
                try:
                    ws = WebVulnScanner(f"http://{h['ip']}")
                    data.setdefault("web", {})[h["ip"]] = ws.full()
                except Exception as e:
                    data.setdefault("web", {})[h["ip"]] = {"error": str(e)}
        print("Saved:", rep.save_json(data, "full"))

if __name__ == "__main__":
    main()
