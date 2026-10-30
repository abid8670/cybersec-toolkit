#!/usr/bin/env python3
"""SIMULATED agent for the RAT architecture lab.

This is an educational simulator, not malware. It is intentionally
incapable of behaving like a real RAT:

- it refuses to connect to anything except 127.0.0.1 (loopback)
- it exposes only an allowlisted set of read-only commands
- it never spawns a shell or executes arbitrary commands
- it is visible: banner on start, audit log, no persistence, no stealth

Run it only on a machine you own, inside a lab.
"""

import argparse
import base64
import getpass
import io
import json
import os
import platform
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

from protocol import ProtocolError, recv_message, send_message

LOOPBACK = "127.0.0.1"

BANNER = r"""
+----------------------------------------------------------------+
|  SIMULATED AGENT  -  RAT architecture lab                       |
|  Visible by design. Read-only allowlisted commands only.        |
|  Talks to 127.0.0.1 only. Never runs a shell. No persistence.   |
+----------------------------------------------------------------+
"""

ALLOWED_COMMANDS = [
    "sysinfo",
    "whoami",
    "hostname",
    "date",
    "ls",
    "getfile",
    "screenshot",
    "exit",
]

MAX_FILE_BYTES = 5 * 1024 * 1024


def build_parser():
    parser = argparse.ArgumentParser(
        description="Simulated agent (educational, loopback-only, allowlisted commands)."
    )
    parser.add_argument("--port", type=int, default=4444)
    parser.add_argument("--sandbox", default="sandbox", help="Directory shared with the server.")
    parser.add_argument("--name", default=platform.node() or "lab-agent")
    parser.add_argument(
        "--consent",
        action="store_true",
        help="Confirm you own this machine and understand this is a simulation.",
    )
    parser.add_argument("--retry", type=int, default=30, help="Seconds to wait for the server.")
    return parser


def audit(log_path, line):
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")


def safe_sandbox_path(sandbox, name):
    """Resolve a file name inside the sandbox and reject traversal attempts."""
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError("invalid file name")
    candidate = (sandbox / name).resolve()
    if candidate.parent != sandbox:
        raise ValueError("path escapes the sandbox")
    return candidate


def cmd_sysinfo(ctx, sandbox, params):
    info = {
        "agent_name": ctx.name,
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "pid": os.getpid(),
        "simulation": True,
        "allowed_commands": ALLOWED_COMMANDS,
    }
    return {"ok": True, "output": json.dumps(info, indent=2)}


def cmd_whoami(ctx, sandbox, params):
    return {"ok": True, "output": getpass.getuser()}


def cmd_hostname(ctx, sandbox, params):
    return {"ok": True, "output": socket.gethostname()}


def cmd_date(ctx, sandbox, params):
    return {"ok": True, "output": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")}


def cmd_ls(ctx, sandbox, params):
    rows = []
    for path in sorted(sandbox.iterdir()):
        stat = path.stat()
        rows.append(f"{stat.st_size:>10}  {datetime.fromtimestamp(stat.st_mtime):%Y-%m-%d %H:%M}  {path.name}")
    return {"ok": True, "output": "\n".join(rows) or "(sandbox is empty)"}


def cmd_getfile(ctx, sandbox, params):
    name = str(params.get("name", ""))
    path = safe_sandbox_path(sandbox, name)
    if not path.is_file():
        return {"ok": False, "output": f"file not found in sandbox: {name}"}
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        return {"ok": False, "output": "file too large for the lab (5 MB limit)"}
    return {
        "ok": True,
        "output": f"sent {len(data)} bytes",
        "file": {"name": path.name, "b64": base64.b64encode(data).decode("ascii")},
    }


def cmd_screenshot(ctx, sandbox, params):
    """Return a synthetic PNG. The real desktop is never captured."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return {"ok": False, "output": "Pillow not installed; run: pip install pillow"}

    img = Image.new("RGB", (800, 450), "#0d1117")
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 770, 420], outline="#30363d", width=2)
    draw.text((55, 55), "SIMULATED SCREENSHOT", fill="#58a6ff")
    draw.text((55, 85), f"Agent: {ctx.name}", fill="#c9d1d9")
    draw.text((55, 110), f"Captured: {datetime.now():%Y-%m-%d %H:%M:%S}", fill="#c9d1d9")
    draw.text((55, 145), "No real desktop content is captured by this lab.", fill="#8b949e")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    data = buffer.getvalue()
    return {
        "ok": True,
        "output": f"synthetic screenshot ({len(data)} bytes)",
        "file": {"name": "screenshot.png", "b64": base64.b64encode(data).decode("ascii")},
    }


HANDLERS = {
    "sysinfo": cmd_sysinfo,
    "whoami": cmd_whoami,
    "hostname": cmd_hostname,
    "date": cmd_date,
    "ls": cmd_ls,
    "getfile": cmd_getfile,
    "screenshot": cmd_screenshot,
}


def connect_with_retry(port, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            return socket.create_connection((LOOPBACK, port), timeout=5)
        except OSError:
            time.sleep(1)
    return None


def main(argv=None):
    args = build_parser().parse_args(argv)

    if not args.consent:
        print("[!] Refusing to start without --consent.")
        print("    Read README.md first. This simulator is for your own machine only.")
        return 3

    sandbox = Path(args.sandbox).resolve()
    sandbox.mkdir(parents=True, exist_ok=True)

    log_dir = Path("sessions").resolve()
    log_dir.mkdir(exist_ok=True)
    audit_log = log_dir / "agent_audit.log"

    print(BANNER)
    print(f"[i] sandbox   : {sandbox}")
    print(f"[i] audit log : {audit_log}")
    audit(audit_log, f"agent start name={args.name} pid={os.getpid()}")

    sock = connect_with_retry(args.port, args.retry)
    if sock is None:
        print(f"[!] Could not reach {LOOPBACK}:{args.port} within {args.retry}s.")
        return 1

    print(f"[+] Connected to {LOOPBACK}:{args.port}")
    send_message(
        sock,
        {
            "type": "hello",
            "agent": {
                "name": args.name,
                "hostname": socket.gethostname(),
                "user": getpass.getuser(),
                "os": f"{platform.system()} {platform.release()}",
                "pid": os.getpid(),
                "simulation": True,
                "allowed_commands": ALLOWED_COMMANDS,
            },
        },
    )

    try:
        while True:
            message = recv_message(sock)
            if message is None:
                print("[i] Server closed the connection.")
                break
            if message.get("type") != "command":
                continue

            command = str(message.get("cmd", "")).lower()
            params = message.get("args") or {}
            request_id = message.get("id")

            if command == "exit":
                send_message(sock, {"id": request_id, "ok": True, "output": "agent shutting down"})
                audit(audit_log, "cmd=exit")
                break

            handler = HANDLERS.get(command)
            if handler is None:
                result = {"ok": False, "output": f"command not allowlisted: {command}"}
            else:
                try:
                    result = handler(args, sandbox, params)
                except Exception as exc:  # keep the session alive on a bad request
                    result = {"ok": False, "output": f"error: {exc}"}

            result["id"] = request_id
            send_message(sock, result)
            audit(audit_log, f"cmd={command} ok={result.get('ok')} output={str(result.get('output'))[:200]!r}")
    except ProtocolError as exc:
        print(f"[!] Protocol error: {exc}")
    finally:
        sock.close()
        audit(audit_log, "agent stop")
        print("[i] Agent stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
