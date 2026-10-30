"""Network / LAN scanner using nmap."""
import os
os.environ["PATH"] = r"C:\Program Files (x86)\Nmap" + ";" + os.environ.get("PATH", "")
import nmap
import socket
from tqdm import tqdm

class NetworkScanner:
    def __init__(self, target):
        self.target = target
        self.nm = nmap.PortScanner()

    def host_discovery(self):
        print(f"[+] Host discovery: {self.target}")
        self.nm.scan(hosts=self.target, arguments="-sn")
        hosts = []
        for h in self.nm.all_hosts():
            hosts.append({"ip": h, "state": self.nm[h].state(), "hostname": self.nm[h].hostname()})
        return hosts

    def port_scan(self, ports="1-1024", service=True):
        print(f"[+] Port scan {self.target} ports {ports}")
        args = f"-sS -p {ports}" + (" -sV" if service else "")
        self.nm.scan(hosts=self.target, arguments=args)
        res = {}
        for h in self.nm.all_hosts():
            res[h] = {"state": self.nm[h].state(), "ports": {}}
            for proto in self.nm[h].all_protocols():
                for p in self.nm[h][proto]:
                    info = self.nm[h][proto][p]
                    res[h]["ports"][p] = {
                        "state": info.get("state"),
                        "name": info.get("name"),
                        "product": info.get("product"),
                        "version": info.get("version"),
                    }
        return res

    def vuln_scripts(self):
        print(f"[+] Running nmap vuln scripts on {self.target}")
        self.nm.scan(hosts=self.target, arguments="-sV --script vuln")
        return self.nm.csv()

    @staticmethod
    def resolve(host):
        try:
            return socket.gethostbyname(host)
        except Exception as e:
            return str(e)
