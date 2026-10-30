# CyberSec Toolkit

A Python-based security assessment toolkit for **authorized** testing of your own infrastructure.

## Modules
- **Network Scanner** — host discovery, port scan, service/version detection (nmap)
- **Local IP Scanner** — ARP/ping sweep of the LAN
- **Web Vulnerability Scanner** — headers, CORS, XSS, SQLi, SSRF, open redirects, sensitive files
- **hping3 Wrapper** — TCP/UDP/ICMP flood & SYN flood for stress-testing own servers
- **Reporter** — JSON + HTML reports

## Install
```bash
pip install -r requirements.txt
# hping3 (external): sudo apt install hping3  (Linux) / download on Windows
```

## Usage
```bash
python main.py --help
python main.py scan-network 192.168.0.0/21
python main.py scan-web https://target.example
python main.py hping 192.168.0.4 --mode syn --count 1000
python main.py full 192.168.0.0/21 --web
```

## Authorization
Only scan systems you own or have written permission to test. Unauthorized scanning is illegal.
