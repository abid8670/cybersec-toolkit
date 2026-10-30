"""CyberSec Toolkit CLI entry point."""
import argparse, json
from core.scanner import NetworkScanner
from core.web_vuln import WebVulnScanner
from core.hping import HPing
from core.reporter import Reporter
import urllib3
urllib3.disable_warnings()

def main():
    p = argparse.ArgumentParser(prog="cybersec-toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan-network"); s.add_argument("target"); s.add_argument("--ports", default="1-1024")
    w = sub.add_parser("scan-web"); w.add_argument("url")
    h = sub.add_parser("hping"); h.add_argument("target"); h.add_argument("--mode", choices=["syn","udp","icmp"], default="syn"); h.add_argument("--count", type=int, default=1000); h.add_argument("--port", type=int, default=80); h.add_argument("--flood", action="store_true")
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
