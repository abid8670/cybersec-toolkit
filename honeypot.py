"""Simple honeypot: fake SSH/HTTP/telnet that logs attacker activity."""
import socket, threading, datetime, json, os, time

LOG = "honeypot.log"

def log(event):
    with open(LOG, "a") as f:
        f.write(json.dumps(event) + "\n")
    print("[HONEYPOT]", event)

def fake_service(port, banner, name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    print(f"[+] {name} honeypot listening on {port}")
    while True:
        c, addr = s.accept()
        threading.Thread(target=handle, args=(c, addr, banner, name), daemon=True).start()

def handle(c, addr, banner, name):
    event = {"ts": datetime.datetime.now().isoformat(), "src": addr[0], "port": addr[1], "service": name}
    try:
        c.sendall(banner.encode() + b"\r\n")
        c.settimeout(10)
        data = c.recv(1024)
        event["payload"] = data.decode(errors="replace").strip()
        log(event)
        c.sendall(b"Access denied.\r\n")
    except Exception as e:
        event["error"] = str(e)
        log(event)
    finally:
        c.close()

def run(services=None):
    if services is None:
        services = [("ssh", 2222, "SSH-2.0-OpenSSH_8.9p1"), ("http", 8080, "HTTP/1.1 200 OK"), ("telnet", 2323, "Welcome to Ubuntu 22.04")]
    for name, port, banner in services:
        threading.Thread(target=fake_service, args=(port, banner, name), daemon=True).start()
    print("[+] Honeypot running. Logs:", LOG)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("stopped")

if __name__ == "__main__":
    import time
    run()
