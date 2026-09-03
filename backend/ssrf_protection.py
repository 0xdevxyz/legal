"""
SSRF (Server-Side Request Forgery) Protection

Validates URLs before they are fetched by the scanner/crawler to prevent
the backend from being abused as a proxy to internal services.

Blocked targets:
- Private IPv4 ranges (10.x, 172.16-31.x, 192.168.x, 127.x, 169.254.x)
- IPv6 loopback / link-local / ULA (::1, fe80::, fc00::, fd00::)
- Cloud metadata endpoints (169.254.169.254, metadata.google.internal, etc.)
- Non-HTTP/HTTPS schemes
- Raw IP addresses as hostnames (no legitimate site uses them directly)
"""

import ipaddress
import socket
import logging
from urllib.parse import urlparse
from typing import Optional

logger = logging.getLogger(__name__)

_BLOCKED_HOSTS = {
    "169.254.169.254",          # AWS / Azure / GCP metadata
    "metadata.google.internal",
    "metadata.google",
    "metadata",
    "localhost",
    "0.0.0.0",
}

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("fc00::/7"),
]

_MAX_URL_LENGTH = 2048
_ALLOWED_SCHEMES = {"http", "https"}


class SSRFError(ValueError):
    pass


def validate_url(url: str) -> str:
    """
    Validate a user-supplied URL against SSRF attack vectors.

    Returns the (possibly normalised) URL on success.
    Raises SSRFError with a safe message on failure.
    """
    if not url or len(url) > _MAX_URL_LENGTH:
        raise SSRFError("Invalid URL length")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        raise SSRFError("Malformed URL")

    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise SSRFError(f"URL scheme '{scheme}' is not allowed")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFError("URL has no hostname")

    hostname = hostname.lower().rstrip(".")

    if hostname in _BLOCKED_HOSTS:
        raise SSRFError("URL resolves to a blocked host")

    # Reject bare IP addresses as hostnames (most legit sites use domain names)
    try:
        addr = ipaddress.ip_address(hostname)
        _check_ip(addr)
    except ValueError:
        # Not an IP literal — resolve DNS and check resolved addresses
        try:
            resolved = socket.getaddrinfo(hostname, None)
            for result in resolved:
                addr_str = result[4][0]
                try:
                    addr = ipaddress.ip_address(addr_str)
                    _check_ip(addr)
                except SSRFError:
                    raise
                except ValueError:
                    pass
        except SSRFError:
            raise
        except Exception as e:
            logger.debug(f"DNS resolution failed for {hostname}: {e}")
            raise SSRFError("URL hostname could not be resolved")

    return url


def _check_ip(addr: ipaddress._BaseAddress) -> None:
    if addr.is_loopback:
        raise SSRFError("URL resolves to loopback address")
    if addr.is_link_local:
        raise SSRFError("URL resolves to link-local address")
    if addr.is_private:
        raise SSRFError("URL resolves to private address")
    if addr.is_reserved:
        raise SSRFError("URL resolves to reserved address")
    for network in _PRIVATE_NETWORKS:
        if addr in network:
            raise SSRFError("URL resolves to a private/internal network")


def safe_url_or_none(url: str) -> Optional[str]:
    """Like validate_url but returns None instead of raising."""
    try:
        return validate_url(url)
    except SSRFError as e:
        logger.warning(f"SSRF blocked URL '{url}': {e}")
        return None
