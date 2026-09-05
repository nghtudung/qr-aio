import cv2
import numpy as np
from PIL import Image

try:
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:  # pragma: no cover - depends on system zbar shared library
    zbar_decode = None

from app.models import DetectedResult, ScanResponse
from app.services.content import classify_result


def _result(raw: str) -> DetectedResult:
    content_type, parsed = classify_result(raw)
    return DetectedResult(raw=raw, content_type=content_type, parsed=parsed)


def decode_image(image: Image.Image) -> ScanResponse:
    rgb = image.convert("RGB")
    array = np.array(rgb)
    detector = cv2.QRCodeDetector()
    results: list[str] = []

    decoded, _, _ = detector.detectAndDecode(array)
    if decoded:
        results.append(decoded)

    multi_ok, decoded_multi, _, _ = detector.detectAndDecodeMulti(array)
    if multi_ok:
        results.extend(value for value in decoded_multi if value)

    if zbar_decode is not None:
        for item in zbar_decode(rgb):
            text = item.data.decode("utf-8", errors="replace")
            if text:
                results.append(text)

    deduped = list(dict.fromkeys(results))
    return ScanResponse(found=bool(deduped), results=[_result(text) for text in deduped])
