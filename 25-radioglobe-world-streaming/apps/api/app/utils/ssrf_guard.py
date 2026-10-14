"""SSRF himoyasi.

Muhim: bu modul faqat "URL xavfsizmi?" degan savolga javob beradi. Redirect
zanjirining HAR BIR qadami alohida tekshirilishi kerak — chunki boshlang'ich
URL xavfsiz bo'lib, redirect ichki manzilga olib borishi mumkin.
"""

import asyncio
import ipaddress
import socket
from typing import List
from urllib.parse import urlparse

# Hech qachon proxy qilinmaydigan tarmoqlar
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # bulut metadata (AWS/GCP/OCI)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::ffff:0:0/96"),    # IPv4-mapped IPv6
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "instance-data",
}


def _ip_is_blocked(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True

    # IPv4-mapped IPv6 (::ffff:127.0.0.1) ni haqiqiy IPv4 sifatida tekshirish
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return True

    return any(ip in net for net in BLOCKED_NETWORKS)


def _resolve_all(hostname: str) -> List[str]:
    """Hostname'ning BARCHA IP manzillarini qaytaradi (IPv4 va IPv6).

    `socket.gethostbyname` faqat bitta IPv4 qaytaradi — shuning uchun u yetarli emas:
    host bir vaqtda ham ommaviy, ham ichki manzilga resolve bo'lishi mumkin.
    """
    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except Exception:
        return []
    return list({info[4][0] for info in infos})


def is_safe_url_sync(url: str) -> bool:
    """Bloklanadigan bo'lsa False. Hamma resolve bo'lgan IP tekshiriladi."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        return False
    if hostname in BLOCKED_HOSTNAMES:
        return False

    # Hostname o'zi IP bo'lsa — to'g'ridan-to'g'ri tekshiramiz
    try:
        ipaddress.ip_address(hostname)
        return not _ip_is_blocked(hostname)
    except ValueError:
        pass

    ips = _resolve_all(hostname)
    if not ips:
        return False

    # Bittasi ham bloklangan bo'lsa — rad etamiz
    return not any(_ip_is_blocked(ip) for ip in ips)


async def is_safe_url(url: str) -> bool:
    """`is_safe_url_sync` ning async o'ramchisi.

    DNS so'rovi bloklovchi tizim chaqiruvi — uni to'g'ridan-to'g'ri async
    handler ichida chaqirish event loop'ni muzlatadi. Shuning uchun thread'ga
    uzatiladi.
    """
    return await asyncio.to_thread(is_safe_url_sync, url)
