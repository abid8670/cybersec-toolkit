#!/usr/bin/env python3
"""SIMULATED command-and-control console for the RAT architecture lab.

Binds to 127.0.0.1 only and drives the allowlisted simulator agent. It cannot
execute shell commands, persist, or hide itself. Educational use only.
"""

import argparse
import base64
import json
import os
import shlex
import socket
from datetime import datetime
from pathlib import Path

from protocol import ProtocolError, recv_message, send_message

LOOPBACK = "127.0.0.1"

BANNER = r"""
+----------------------------------------------------------------+
|  SIMULATED C2 CONSOLE  -  RAT architecture lab                  |
|  Loopback only. Allowlisted commands. No shell. No persistence. |
+----------------------------------------------------------------+
"""

ETHICS = """\
This console binds to 127.0.0.1 and can only drive the simulated agent that
ships with this repository. It cannot run shell commands, install persistence,
or hide from the user. Use it only on machines you own, in a lab.
"""

COMMANDS = {
    "sysinfo": "agent system information",
    "whoami": "current user on the agent",
    "hostname": "agent machine name",
    "date": "agent clock",
    "ls": "list files in the agent sandbox",
    "getfile <name>": "download a file from the agent sandbox",
    "screenshot": "download a synthetic screenshot",
    "help": "show this help",
    "exit": "end the session",
}

DEMO_SEQUENCE = [
    ("sysinfo", {}),
    ("whoami", {}),
    ("hostname", {}),
    ("date", {}),
    ("ls", {}),
    ("getfile", {"name": "lab_notes.txt"}),
    ("screenshot", {}),
]


def build_parser():
    parser = argparse.ArgumentParser(
        description="Simulated C2 console (educational, loopback-only)."
    )
    parser.add_argument("--port", type=int, default=4444)
    parser.add_argument(
        "--consent",
        action="store_true",
        help="Confirm you own the machines involved and understand this is a simulation.",
    )
    parser.add_argument("--demo", action="store_true", help="Run a scripted demonstration.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Command response timeout.")
    parser.add_argument("--accept-timeout", type=float, default=300.0, help="Seconds to wait for an agent.")
    return parser


def print_help():
    print("\nAvailable commands:")
    for name, description in COMMANDS.items():
        print(f"  {name:<20} {description}")
    print()


class Session:
    def __init__(self):
        self.transcript = []
        self.request_id = 0
        self.downloads = Path("sessions/downloads")
        self.downloads.mkdir(parents=True, exist_ok=True)

    def record(self, direction, **payload):
        self.transcript.append(
            {"ts": datetime.now().isoformat(timespec="seconds"), "direction": direction, **payload}
        )

    def save(self):
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        base = sessions_dir / f"session_{datetime.now():%Y%m%d_%H%M%S}"

        json_path = base.with_suffix(".json")
        json_path.write_text(json.dumps(self.transcript, indent=2), encoding="utf-8")

        lines = []
        for entry in self.transcript:
            if entry["direction"] == "out":
                lines.append(f"> {entry['cmd']}")
            else:
                lines.append(entry.get("output", ""))
                lines.append("")
        log_path = base.with_suffix(".log")
        log_path.write_text("\n".join(lines), encoding="utf-8")
        return json_path, log_path


def send_command(sock, session, command, params=None, timeout=120.0):
    session.request_id += 1
    request_id = session.request_id

    session.record("out", cmd=command, args=params or {})
    send_message(sock, {"type": "command", "id": request_id, "cmd": command, "args": params or {}})

    sock.settimeout(timeout)
    response = recv_message(sock)
    if response is None:
        return None

    session.record("in", cmd=command, ok=response.get("ok"), output=response.get("output", ""))

    file_info = response.get("file")
    if file_info and file_info.get("b64"):
        data = base64.b64decode(file_info["b64"])
        target = session.downloads / Path(file_info.get("name", "download.bin")).name
        target.write_bytes(data)
        response["saved_to"] = str(target)

    return response


def print_response(command, response):
    if response is None:
        print("[-] no response (connection closed)")
        return
    if response.get("ok"):
        print(f"[+] {command}:")
        print(response.get("output", ""))
        if response.get("saved_to"):
            print(f"[+] saved to {response['saved_to']}")
    else:
        print(f"[-] {command} failed: {response.get('output')}")
    print()


def run_demo(sock, session, timeout):
    print("[i] Running scripted demo ...\n")
    for command, params in DEMO_SEQUENCE:
        print(f"c2> {command} {' '.join(params.values())}".rstrip())
        response = send_command(sock, session, command, params, timeout)
        print_response(command, response)
    send_command(sock, session, "exit", {}, timeout)
    print("[i] Demo complete.")


def interactive(sock, session, timeout):
    print_help()
    while True:
        try:
            line = input("c2> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue

        if line in ("help", "?"):
            print_help()
            continue
        if line == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue

        try:
            parts = shlex.split(line)
        except ValueError as exc:
            print(f"[-] {exc}")
            continue

        command = parts[0].lower()

        if command == "exit":
            send_command(sock, session, "exit", {}, timeout)
            break

        if command == "getfile":
            if len(parts) != 2:
                print("usage: getfile <name>")
                continue
            response = send_command(sock, session, "getfile", {"name": parts[1]}, timeout)
        elif command in ("sysinfo", "whoami", "hostname", "date", "ls", "screenshot"):
            response = send_command(sock, session, command, {}, timeout)
        else:
            print("[-] unknown command; type help")
            continue

        print_response(command, response)


def main(argv=None):
    args = build_parser().parse_args(argv)

    if not args.consent:
        print("[!] Refusing to start without --consent.")
        print(ETHICS)
        return 3

    print(BANNER)
    print(ETHICS)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOOPBACK, args.port))
    server.listen(1)
    server.settimeout(args.accept_timeout)

    print(f"[i] listening on {LOOPBACK}:{args.port} (loopback only)")
    print("[i] start the agent in another terminal:")
    print(f"    python sim_agent.py --consent --port {args.port}\n")

    try:
        sock, address = server.accept()
    except socket.timeout:
        print("[!] No agent connected before the accept timeout.")
        server.close()
        return 1

    session = Session()

    try:
        hello = recv_message(sock)
        if hello is None:
            print("[-] Agent disconnected before sending hello.")
            return 1

        agent = hello.get("agent", {})
        print(f"[+] Agent connected from {address[0]}:{address[1]}")
        print(f"    name     : {agent.get('name')}")
        print(f"    hostname : {agent.get('hostname')}")
        print(f"    user     : {agent.get('user')}")
        print(f"    os       : {agent.get('os')}")
        print(f"    pid      : {agent.get('pid')}")
        print(f"    allowed  : {', '.join(agent.get('allowed_commands', []))}")
        print(f"    simulation: {agent.get('simulation')}\n")

        if args.demo:
            run_demo(sock, session, args.timeout)
        else:
            interactive(sock, session, args.timeout)
    except ProtocolError as exc:
        print(f"[!] Protocol error: {exc}")
    finally:
        sock.close()
        server.close()
        json_path, log_path = session.save()
        print(f"[i] transcript : {json_path}")
        print(f"[i] readable   : {log_path}")
        print(f"[i] downloads  : {session.downloads}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
