"""Remote server health checks over SSH (IT admin use)."""
import paramiko

class RemoteChecker:
    def __init__(self, host, user, password=None, key=None, port=22):
        self.host = host
        self.user = user
        self.password = password
        self.key = key
        self.port = port

    def _exec(self, cmd):
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(self.host, port=self.port, username=self.user, password=self.password, key_filename=self.key, timeout=15)
        stdin, stdout, stderr = c.exec_command(cmd, timeout=30)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        c.close()
        return out, err

    def health(self):
        cmds = {
            "uptime": "uptime",
            "cpu": "top -bn1 | grep 'Cpu(s)'",
            "mem": "free -h",
            "disk": "df -h",
            "services": "systemctl --failed --no-pager 2>/dev/null || service --status-all 2>/dev/null",
            "listening": "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null",
        }
        res = {}
        for k, v in cmds.items():
            try:
                o, e = self._exec(v)
                res[k] = o.strip() or e.strip()
            except Exception as ex:
                res[k] = f"ERROR: {ex}"
        return res
