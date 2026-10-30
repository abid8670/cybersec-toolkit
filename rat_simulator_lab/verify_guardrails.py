#!/usr/bin/env python3
"""Adversarial self-test: acts as a rogue C2 and verifies the agent's guardrails.

Checks that the simulated agent refuses shell execution and sandbox escape even
when a malicious server asks for them.
"""

import socket
import subprocess
import sys

from protocol import recv_message, send_message

PORT = 4466

# (command, params, should_succeed)
CASES = [
    ("exec", {"command": "whoami"}, False),
    ("shell", {"command": "dir"}, False),
    ("powershell", {}, False),
    ("getfile", {"name": "../../etc/passwd"}, False),
    ("getfile", {"name": "..\\..\\windows\\win.ini"}, False),
    ("getfile", {"name": "C:\\Windows\\win.ini"}, False),
    ("getfile", {"name": "lab_notes.txt"}, True),
    ("ls", {}, True),
]


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", PORT))
    server.listen(1)

    agent = subprocess.Popen(
        [sys.executable, "sim_agent.py", "--consent", "--port", str(PORT), "--retry", "10"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        sock, _ = server.accept()
        hello = recv_message(sock)
        print(f"[i] agent hello: {hello['agent']['name']} (simulation={hello['agent']['simulation']})")

        failures = 0
        for index, (command, params, should_succeed) in enumerate(CASES, start=1):
            send_message(sock, {"type": "command", "id": index, "cmd": command, "args": params})
            response = recv_message(sock)
            succeeded = bool(response and response.get("ok"))
            passed = succeeded == should_succeed
            failures += 0 if passed else 1
            label = "PASS" if passed else "FAIL"
            print(
                f"[{label}] {command:<10} {str(params):<45} "
                f"ok={succeeded} expected={should_succeed} :: {response.get('output', '')[:60]!r}"
            )

        send_message(sock, {"type": "command", "id": 99, "cmd": "exit", "args": {}})
        recv_message(sock)
        sock.close()
        print(f"\n[{'OK' if failures == 0 else 'FAILED'}] {len(CASES) - failures}/{len(CASES)} guardrail checks passed")
        return 0 if failures == 0 else 1
    finally:
        agent.terminate()
        server.close()


if __name__ == "__main__":
    raise SystemExit(main())
