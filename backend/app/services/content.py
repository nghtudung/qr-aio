import json
import re
from email.utils import parseaddr
from urllib.parse import quote

from fastapi import HTTPException

from app.models import DataType


def build_payload(data_type: DataType, value: str) -> str:
    value = value.strip()
    if data_type == DataType.text:
        return value
    if data_type == DataType.url:
        if not re.match(r"^https?://", value, re.I):
            raise HTTPException(status_code=422, detail="URL must start with http:// or https://")
        return value
    if data_type == DataType.email:
        _, address = parseaddr(value)
        if "@" not in address:
            raise HTTPException(status_code=422, detail="Invalid email address")
        return f"mailto:{address}"
    if data_type == DataType.phone:
        cleaned = re.sub(r"[^\d+]", "", value)
        if len(cleaned) < 5:
            raise HTTPException(status_code=422, detail="Invalid phone number")
        return f"tel:{cleaned}"
    if data_type == DataType.sms:
        parts = value.split("|", 1)
        phone = re.sub(r"[^\d+]", "", parts[0])
        message = quote(parts[1]) if len(parts) > 1 else ""
        return f"SMSTO:{phone}:{message}"
    if data_type == DataType.wifi:
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="WiFi must be JSON") from exc
        ssid = str(data.get("ssid", "")).replace(";", r"\;")
        password = str(data.get("password", "")).replace(";", r"\;")
        auth = str(data.get("auth", "WPA")).upper()
        hidden = "true" if data.get("hidden") else "false"
        return f"WIFI:T:{auth};S:{ssid};P:{password};H:{hidden};;"
    if data_type == DataType.vcard:
        return value if value.upper().startswith("BEGIN:VCARD") else f"BEGIN:VCARD\nVERSION:3.0\nFN:{value}\nEND:VCARD"
    if data_type == DataType.json:
        try:
            return json.dumps(json.loads(value), separators=(",", ":"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="Invalid JSON payload") from exc
    return value


def classify_result(raw: str) -> tuple[str, dict[str, str]]:
    text = raw.strip()
    if re.match(r"^https?://", text, re.I):
        return "url", {"url": text}
    if text.upper().startswith("WIFI:"):
        parsed: dict[str, str] = {}
        for item in text[5:].strip(";").split(";"):
            if ":" in item:
                key, value = item.split(":", 1)
                parsed[key] = value
        return "wifi", parsed
    if text.upper().startswith("BEGIN:VCARD"):
        contact: dict[str, str] = {}
        for line in text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                contact[key] = value
        return "vcard", contact
    if text.startswith("{"):
        try:
            return "json", json.loads(text)
        except json.JSONDecodeError:
            pass
    if text.lower().startswith("mailto:"):
        return "email", {"email": text[7:]}
    if text.lower().startswith("tel:"):
        return "phone", {"phone": text[4:]}
    return "text", {"text": text}
