import base64
import io
import re

from defusedxml import ElementTree
from fastapi import HTTPException
from PIL import Image, ImageOps

DATA_URL_RE = re.compile(r"^data:(?P<mime>[-\w.+/]+);base64,(?P<data>.+)$", re.DOTALL)


def open_image_bytes(data: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image") from exc
    return ImageOps.exif_transpose(image)


def image_to_bytes(image: Image.Image, fmt: str) -> bytes:
    buffer = io.BytesIO()
    save_kwargs: dict[str, object] = {}
    if fmt.upper() in {"JPEG", "JPG"}:
        image = image.convert("RGB")
        save_kwargs["quality"] = 95
        fmt = "JPEG"
    image.save(buffer, format=fmt.upper(), **save_kwargs)
    return buffer.getvalue()


def decode_data_url(data_url: str, max_bytes: int) -> tuple[str, bytes]:
    match = DATA_URL_RE.match(data_url)
    if not match:
        raise HTTPException(status_code=400, detail="Logo must be a base64 data URL")
    mime = match.group("mime").lower()
    try:
        payload = base64.b64decode(match.group("data"), validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 data URL") from exc
    if len(payload) > max_bytes:
        raise HTTPException(status_code=413, detail="Logo is too large")
    return mime, payload


def sanitize_svg(svg_bytes: bytes) -> bytes:
    text = svg_bytes.decode("utf-8", errors="ignore")
    lowered = text.lower()
    blocked = ("<script", "javascript:", "onload=", "onerror=", "<foreignobject")
    if any(token in lowered for token in blocked):
        raise HTTPException(status_code=400, detail="Unsafe SVG logo")
    try:
        ElementTree.fromstring(svg_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid SVG logo") from exc
    return svg_bytes
