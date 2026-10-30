# RAT Architecture Lab — Simulated C2

An **educational simulator** of the client/server (C2) pattern used by remote
access tools, built for a security course task. It demonstrates the architecture
and the failure modes — not a deployable implant.

> ⚠️ **Read this first.** A real RAT is malware. This project is deliberately
> built so it *cannot* act like one. It runs only on loopback, only exposes
> read-only allowlisted commands, never spawns a shell, and never hides.
> Only run it on machines you own.

## Why this is a simulator and not a RAT

| Real RAT behaviour | This lab |
| --- | --- |
| Connects to any host | Refuses anything except `127.0.0.1` |
| Executes arbitrary commands (`shell=True`) | Fixed allowlist of 7 read-only commands |
| Exfiltrates any file on disk | Only files inside `sandbox/` |
| Persistence / autostart | None |
| Hides from the user | Visible banner + audit log |
| Captures the real desktop | Generates a synthetic PNG |
| Encrypted/covert channel | Plaintext JSON over loopback |

If your assignment asks for persistence, evasion, credential theft or remote
shell access, that crosses from a lab exercise into malware development. Don't
build that, and don't run it against anyone else's machine.

## Architecture

```
+---------------------+        loopback TCP :4444        +----------------------+
|  sim_server.py      |  <---- length-prefixed JSON ---->  |  sim_agent.py        |
|  (C2 console)       |                                   |  (visible simulator) |
|                     |   hello  ->  agent metadata        |                      |
|  command dispatch   |   command -> allowlisted action    |  allowlist handlers  |
|  transcript + files |   response <- output / base64 file |  sandbox + audit log |
+---------------------+                                   +----------------------+
```

The wire protocol is a 4-byte big-endian length header followed by a UTF-8 JSON
body (`protocol.py`). The original `rat_simulator` used bare `recv(4096)`, which
loses message boundaries as soon as a file is bigger than one TCP segment —
this lab fixes that.

## Run it

Two terminals, in `rat_simulator_lab/`:

```bash
# terminal 1 — C2 console
python sim_server.py --consent

# terminal 2 — agent
python sim_agent.py --consent
```

Then at the `c2>` prompt:

```
c2> sysinfo
c2> ls
c2> getfile lab_notes.txt
c2> screenshot
c2> exit
```

Scripted demo (useful for a class presentation):

```bash
python sim_server.py --consent --demo
```

Downloads land in `sessions/downloads/`; the full transcript is written to
`sessions/session_*.json` and `.log`; every agent-side command is appended to
`sessions/agent_audit.log`.

## Commands

| Command | What it does |
| --- | --- |
| `sysinfo` | hostname, user, OS, Python, PID, allowlist |
| `whoami` | current user |
| `hostname` | machine name |
| `date` | agent clock |
| `ls` | files in the sandbox |
| `getfile <name>` | download one sandbox file (base64, 5 MB cap) |
| `screenshot` | download a synthetic PNG |
| `exit` | end the session |

## What the exercise teaches

1. **C2 architecture** — agent registration, request/response correlation by id,
   session lifecycle.
2. **Framing** — why length-prefixed messages beat raw `recv()`.
3. **File transfer** — base64 over JSON, size caps, sandbox path validation.
4. **Least privilege** — an allowlist instead of `subprocess(shell=True)`.
5. **Auditability** — every action is logged on both sides.

## Detection & defence (the part that matters)

How defenders actually spot this pattern:

- **Beaconing** — periodic outbound connections to one host on an unusual port.
  Look at NetFlow/proxy logs for regular intervals and small, consistent payloads.
- **Listening ports** — `netstat -ano` / `ss -tlnp`; a listener on `4444`, `1337`,
  etc. is a classic indicator.
- **Process lineage** — a Python/Office/browser process spawning a shell is
  suspicious; EDR rules like "Office → cmd.exe" catch it.
- **Autoruns** — `Run` keys, scheduled tasks, services, `systemd` units. Real
  RATs persist; this lab deliberately does not.
- **File telemetry** — mass reads of documents, archives, browser profiles.
- **Egress filtering** — deny outbound traffic by default; allow only what the
  business needs. This alone breaks most C2 channels.

Try the detection exercise: run the lab, then use `netstat -ano | findstr 4444`
and Process Explorer to see how visible it is compared with a stealthy implant.

## Files

```
protocol.py       length-prefixed JSON framing
sim_agent.py      visible, allowlisted agent (loopback only)
sim_server.py     C2 console, transcript, downloads
sandbox/          the only directory the agent can read
sessions/         transcripts, audit log, downloads (created at runtime)
```
