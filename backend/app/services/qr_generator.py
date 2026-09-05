import base64
import io
import tempfile
from pathlib import Path

import segno
from fastapi import HTTPException
from PIL import Image, ImageColor, ImageDraw

from app.models import GenerateRequest
from app.services.content import build_payload
from app.services.qr_scanner import decode_image
from app.services.qr_styling import clear_logo_modules, draw_styled_modules, render_matrix_svg
from app.utils.image_processing import decode_data_url, open_image_bytes, sanitize_svg

ERROR_MAP = {"L": "L", "M": "M", "Q": "Q", "H": "H"}


def _make_qr(payload: str, error: str) -> segno.QRCode:
    return segno.make(payload, error=ERROR_MAP[error], micro=False)


def _matrix(qr: segno.QRCode) -> list[list[bool]]:
    return [[bool(cell) for cell in row] for row in qr.matrix]


def _prepare_logo(data_url: str, max_bytes: int) -> Image.Image:
    mime, data = decode_data_url(data_url, max_bytes)
    if mime == "image/svg+xml":
        sanitize_svg(data)
        try:
            import cairosvg
        except Exception as exc:
            raise HTTPException(status_code=400, detail="SVG logo rendering requires cairosvg") from exc
        data = cairosvg.svg2png(bytestring=data)
    elif mime != "image/png":
        raise HTTPException(status_code=415, detail="Logo must be PNG or SVG")
    return open_image_bytes(data).convert("RGBA")


def _safe_logo_href(data_url: str) -> str:
    mime, data = decode_data_url(data_url, 2 * 1024 * 1024)
    if mime == "image/svg+xml":
        data = sanitize_svg(data)
    elif mime != "image/png":
        raise HTTPException(status_code=415, detail="Logo must be PNG or SVG")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _embed_logo(base: Image.Image, request: GenerateRequest) -> Image.Image:
    if not request.logo.enabled or not request.logo.data_url:
        return base
    logo = _prepare_logo(request.logo.data_url, 2 * 1024 * 1024)
    side = round(min(base.size) * (request.logo.size_percent / 100))
    logo.thumbnail((side, side), Image.Resampling.LANCZOS)
    padding = request.logo.padding
    box_w = logo.width + padding * 2
    box_h = logo.height + padding * 2
    x = (base.width - box_w) // 2
    y = (base.height - box_h) // 2
    draw = ImageDraw.Draw(base)
    bg = ImageColor.getrgb(request.logo.background) + (255,)
    radius = min(box_w, box_h) // 6 if request.logo.rounded_container else 0
    rect = (x, y, x + box_w, y + box_h)
    draw.rounded_rectangle(rect, radius=radius, fill=bg)
    base.alpha_composite(logo, (x + padding, y + padding))
    return base


def modified_matrix_for_request(request: GenerateRequest) -> tuple[list[list[bool]], str, tuple[int, int, int, int] | None]:
    payload = build_payload(request.data_type, request.value)
    qr = _make_qr(payload, request.error_correction.value)
    matrix, logo_area = clear_logo_modules(_matrix(qr), request)
    return matrix, payload, logo_area


def render_qr_image(request: GenerateRequest) -> tuple[Image.Image, str, list[str]]:
    matrix, payload, _ = modified_matrix_for_request(request)
    image = draw_styled_modules(matrix, request).convert("RGBA")
    warnings: list[str] = []
    if request.logo.enabled:
        image = _embed_logo(image, request)
    decoded = decode_image(image)
    if not decoded.found or decoded.results[0].raw != payload:
        warnings.append("The generated QR could not be decoded after styling. Reduce logo size or use H error correction.")
    return image, payload, warnings


def render_vector(request: GenerateRequest, fmt: str) -> bytes:
    if fmt == "svg":
        matrix, _, _ = modified_matrix_for_request(request)
        logo_href = _safe_logo_href(request.logo.data_url) if request.logo.enabled and request.logo.data_url else None
        return render_matrix_svg(matrix, request, logo_href=logo_href).encode("utf-8")

    payload = build_payload(request.data_type, request.value)
    qr = _make_qr(payload, request.error_correction.value)
    stream = io.BytesIO()
    background = None if request.transparent_background else request.background
    dark = request.gradient.start if request.gradient.enabled else request.foreground
    qr.save(stream, kind="eps", scale=10, dark=dark, light=background or "#ffffff")
    return stream.getvalue()


def render_pdf(request: GenerateRequest) -> bytes:
    from reportlab.lib import pagesizes
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    image, _, _ = render_qr_image(request)
    page_size = pagesizes.A4 if request.pdf.page_size == "A4" else pagesizes.A5
    if request.pdf.page_size == "custom":
        page_size = ((request.pdf.custom_width_mm or 210) * mm, (request.pdf.custom_height_mm or 297) * mm)
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=page_size)
    page_w, page_h = page_size
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = Path(temp_dir) / "qr.png"
        image.save(image_path)
        count = request.pdf.multiple_per_page
        cols = 1 if count == 1 else 2 if count <= 4 else 3
        rows = max(1, (count + cols - 1) // cols)
        cell_w = page_w / cols
        cell_h = page_h / rows
        for idx in range(count):
            col = idx % cols
            row = idx // cols
            max_side = min(cell_w, cell_h) * 0.62
            x = col * cell_w + (cell_w - max_side) / 2
            y = page_h - (row + 1) * cell_h + (cell_h - max_side) / 2
            if request.pdf.title:
                pdf.setFont("Helvetica-Bold", 13)
                pdf.drawCentredString(col * cell_w + cell_w / 2, min(page_h - 24, y + max_side + 28), request.pdf.title)
            pdf.drawImage(str(image_path), x, y, max_side, max_side, mask="auto")
            if request.pdf.description:
                pdf.setFont("Helvetica", 9)
                pdf.drawCentredString(col * cell_w + cell_w / 2, max(18, y - 18), request.pdf.description[:100])
        pdf.showPage()
        pdf.save()
    return output.getvalue()
