"""Length-prefixed JSON framing shared by the simulator server and agent.

The original rat_simulator used raw `recv(4096)` calls, which breaks whenever
a command or file is larger than one TCP segment. A 4-byte length header makes
message boundaries explicit and is the standard fix for this class of bug.
"""

import json
import struct

HEADER = struct.Struct("!I")  # 4-byte big-endian length
MAX_MESSAGE = 8 * 1024 * 1024  # 8 MB hard cap


class ProtocolError(Exception):
    pass


def recv_exact(sock, size):
    """Read exactly `size` bytes, or return None if the peer closed early."""
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_message(sock, payload):
    data = json.dumps(payload).encode("utf-8")
    if len(data) > MAX_MESSAGE:
        raise ProtocolError("message exceeds size limit")
    sock.sendall(HEADER.pack(len(data)) + data)


def recv_message(sock):
    header = recv_exact(sock, HEADER.size)
    if header is None:
        return None
    (size,) = HEADER.unpack(header)
    if size > MAX_MESSAGE:
        raise ProtocolError("peer announced an oversized message")
    data = recv_exact(sock, size)
    if data is None:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"invalid JSON payload: {exc}") from exc
