"""SSL/TLS audit."""
import ssl, socket, datetime, certifi

class SSLAudit:
    def __init__(self, host, port=443):
        self.host = host
        self.port = port

    def audit(self):
        ctx = ssl.create_default_context(cafile=certifi.where())
        res = {}
        try:
            with socket.create_connection((self.host, self.port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    cert = ssock.getpeercert()
                    res["protocol"] = ssock.version()
                    res["cipher"] = ssock.cipher()
                    # expiry
                    not_after = cert.get("notAfter")
                    res["not_after"] = not_after
                    if not_after:
                        exp = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        res["days_until_expiry"] = (exp - datetime.datetime.utcnow()).days
                    res["subject"] = cert.get("subject")
                    res["issuer"] = cert.get("issuer")
                    res["san"] = cert.get("subjectAltName")
        except Exception as e:
            res["error"] = str(e)
        return res
