"""hping3 wrapper for packet crafting / stress testing own infra."""
import subprocess, shutil, time

class HPing:
    def __init__(self, target):
        self.target = target
        self.bin = shutil.which("hping3") or shutil.which("hping")

    def available(self):
        return self.bin is not None

    def run(self, mode="syn", count=1000, port=80, interval=None, flood=False):
        if not self.available():
            return {"error": "hping3 not installed. Install: apt install hping3"}
        cmd = [self.bin, "-S" if mode == "syn" else "-2" if mode == "udp" else "-1", self.target]
        if mode == "syn":
            cmd = [self.bin, "-S", "-p", str(port), self.target]
        elif mode == "udp":
            cmd = [self.bin, "--udp", "-p", str(port), self.target]
        elif mode == "icmp":
            cmd = [self.bin, "--icmp", self.target]
        cmd += ["-c", str(count)]
        if flood:
            cmd.append("--flood")
        if interval:
            cmd += ["-i", f"u{interval}"]
        print("[+] Running:", " ".join(cmd))
        t0 = time.time()
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return {
            "mode": mode, "count": count, "target": self.target,
            "stdout": out.stdout[-2000:], "stderr": out.stderr[-1000:],
            "rc": out.returncode, "elapsed": round(time.time()-t0, 2),
        }
