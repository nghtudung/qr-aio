import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.models import ScanResponse, ScanUrlRequest
from app.services.qr_scanner import decode_image
from app.utils.image_processing import open_image_bytes
from app.utils.validation import assert_max_size, assert_supported_image, is_public_http_url

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("/upload", response_model=ScanResponse)
async def scan_upload(file: UploadFile = File(...)) -> ScanResponse:
    settings = get_settings()
    assert_supported_image(file.content_type)
    data = await file.read()
    assert_max_size(len(data), settings.max_upload_bytes)
    return decode_image(open_image_bytes(data))


@router.post("/url", response_model=ScanResponse)
async def scan_url(request: ScanUrlRequest) -> ScanResponse:
    settings = get_settings()
    url = str(request.url)
    if not is_public_http_url(url):
        raise HTTPException(status_code=400, detail="URL must resolve to a public HTTP(S) host")
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        async with client.stream("GET", url) as response:
            if response.status_code >= 400:
                raise HTTPException(status_code=400, detail="Image URL could not be downloaded")
            assert_supported_image(response.headers.get("content-type"))
            content_length = response.headers.get("content-length")
            if content_length:
                assert_max_size(int(content_length), settings.max_url_download_bytes)
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                assert_max_size(total, settings.max_url_download_bytes)
                chunks.append(chunk)
    data = b"".join(chunks)
    return decode_image(open_image_bytes(data))
