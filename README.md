# 💀 CyberSec Toolkit

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Nmap](https://img.shields.io/badge/Nmap-integrated-005B64?style=flat-square)
![NVD](https://img.shields.io/badge/CVE-NVD%20API-blue?style=flat-square)

A Python-based cybersecurity assessment toolkit for **authorized** testing of your own infrastructure. Terminal-first CLI with modular scanners and reporting.

![Logo](logo.svg)

## Modules

| Module | Description |
|---|---|
| **Network Scanner** | Host discovery, port scan, service/version detection via nmap |
| **Local IP Scanner** | LAN sweep (ARP/ping) |
| **Web Vuln Scanner** | Security headers, CORS, forms, SQLi/XSS probes, sensitive files, open redirect |
| **hping3 Wrapper** | TCP SYN / UDP / ICMP flood for stress-testing own servers |
| **CVE Lookup** | Live CVE search via NVD API (CVSS + descriptions) |
| **Remote Health** | SSH-based server monitoring (uptime, CPU, mem, disk, services, ports) |
| **Subdomain Enum** | crt.sh certificate transparency lookup |
| **SSL Audit** | TLS version, cipher, cert expiry, issuer |
| **Python Flood** | scapy-based SYN/UDP/ICMP flood (Windows-friendly) |
| **Honeypot** | Fake SSH/HTTP/telnet, logs attacker IP + payload |
| **Reporter** | JSON + HTML reports |

## Install

### Windows
1. Python 3.10+ (python.org, add to PATH).
2. `pip install -r requirements.txt`
3. Nmap: https://nmap.org/download.html
4. hping3: use WSL/VM (Linux) — native Windows nahi hai.

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y python3 python3-pip nmap hping3
git clone https://github.com/abid8670/cybersec-toolkit.git
cd cybersec-toolkit
pip3 install -r requirements.txt
python3 main.py --help
```

## Usage

```bash
python main.py --help
python main.py scan-network 192.168.0.0/21 --ports 1-1024
python main.py scan-web https://target.example
python main.py cve "apache 2.4" --limit 10
python main.py hping 192.168.0.4 --mode syn --count 1000 --flood
python main.py remote-health 192.168.0.4 -u root -p <password>
python main.py agent-status --config agents.json.example
python main.py flood 192.168.3.185 --mode syn --count 1000 --port 80
python main.py honeypot
python main.py full 192.168.0.0/21 --web
```

## Authorization

Only scan systems you own or have written permission to test. Unauthorized scanning is illegal.

## Roadmap

- Subdomain enumeration (crt.sh)
- Directory brute-force
- SSL/TLS audit
- DNS zone transfer check
- Reverse-shell *detection* rules (defensive)
- Async scanning

## How Each Module Works

- **Network Scanner**: nmap host discovery + port/service scan. Identifies open ports, services, versions on a target/range.
- **Web Vuln Scanner**: checks security headers, CORS misconfig, forms, SQLi/XSS probes, sensitive files (.env, .git), open redirects.
- **hping3 Wrapper / Python Flood**: sends SYN/UDP/ICMP packets to stress-test own servers (load testing). Python flood works on Windows without hping3.
- **CVE Lookup**: queries NVD API for CVEs by keyword/product, returns CVSS + description.
- **Remote Health**: SSH into a server, returns uptime, CPU, memory, disk, failed services, listening ports.
- **Agent Monitor**: generic agent (agent.py) runs on each server exposing /health; central tool polls all agents and shows UP/DOWN + metrics.
- **Subdomain Enum**: crt.sh certificate transparency lookup to find subdomains.
- **SSL Audit**: TLS version, cipher, cert expiry, issuer, SAN.
- **Honeypot**: fake SSH/HTTP/telnet services on ports 2222/8080/2323. Logs attacker IP + payload to honeypot.log. Use to detect/identify attackers on your network (decoy).

## Honeypot Benefit
Attackers scanning your network hit the honeypot (decoy) instead of real services. You capture their IP, attempted credentials/commands, and timing. Helps identify malicious IPs for firewall blocking and incident response.

## Author

Abid Iqbal — IT professional, 6+ years experience (Digital Transformation, Infrastructure, ERP, Security).
GitHub: https://github.com/abid8670
