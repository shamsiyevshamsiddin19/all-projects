import ipaddress
import socket
from urllib.parse import urlparse

# Private / reserved subnets that should NEVER be accessed by the proxy
PRIVATE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"), # Cloud metadata (AWS, GCP, Oracle)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def is_safe_url(url: str) -> bool:
    """
    Checks if a URL is safe to proxy and does not point to internal infrastructure or private IPs.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False

        # Disallow loopback names
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal"):
            return False

        # Resolve hostname to IP
        try:
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
        except Exception:
            return False

        for net in PRIVATE_NETWORKS:
            if ip_obj in net:
                return False

        return True
    except Exception:
        return False
