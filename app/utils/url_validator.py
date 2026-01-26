import ipaddress
from urllib.parse import urlparse

from fastapi import HTTPException,status
from pydantic import HttpUrl


def valid_base_url(url:HttpUrl)->str:
    parsed = urlparse(str(url))

    if parsed.scheme not in ("http","https"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid URL Scheme")

    if parsed.path not in ("","/") or parsed.query or parsed.fragment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Only base URLs are allowed (no path, query, or fragment)")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid hostname")
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Private or Internal ips are not allowed")
    except ValueError:
        pass
    base_url=f"{parsed.scheme}//{hostname}"
    if parsed.port:
        base_url+=f":{parsed.port}"
    return base_url

