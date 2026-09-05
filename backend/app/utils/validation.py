import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException

IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}


def assert_supported_image(content_type: str | None) -> None:
    normalized = (content_type or "").split(";")[0].strip().lower()
    if normalized not in IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported image type")


def assert_max_size(size: int, limit: int) -> None:
    if size > limit:
        raise HTTPException(status_code=413, detail="File is too large")


def is_public_http_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        return False

    for family, _, _, _, sockaddr in addresses:
        address = sockaddr[0]
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    return True
