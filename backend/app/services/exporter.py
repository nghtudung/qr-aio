import base64
import io
import zipfile

from app.models import BatchGenerateRequest, GenerateRequest, GenerateResponse
from app.services.qr_generator import render_pdf, render_qr_image, render_vector
from app.utils.image_processing import image_to_bytes

MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "eps": "application/postscript",
    "pdf": "application/pdf",
}


def export_qr(request: GenerateRequest) -> GenerateResponse:
    fmt = request.export_format.value
    warnings: list[str] = []
    decoded_text = None
    readable = True
    if fmt in {"svg", "eps"}:
        data = render_vector(request, fmt)
        if fmt == "svg":
            _, payload, warnings = render_qr_image(request)
            readable = not warnings
            decoded_text = payload if readable else None
    elif fmt == "pdf":
        data = render_pdf(request)
    else:
        image, payload, warnings = render_qr_image(request)
        decoded_text = payload if not warnings else None
        readable = not warnings
        data = image_to_bytes(image, "jpeg" if fmt == "jpg" else fmt)
    return GenerateResponse(
        filename=f"qr-code.{fmt}",
        media_type=MEDIA_TYPES[fmt],
        data=base64.b64encode(data).decode("ascii"),
        readable=readable,
        decoded_text=decoded_text,
        warnings=warnings,
    )


def export_batch_zip(request: BatchGenerateRequest) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in request.items:
            options = request.options.model_copy(update={"value": item.value, "data_type": item.data_type, "export_format": "png"})
            image, _, _ = render_qr_image(options)
            archive.writestr(f"{item.name}.png", image_to_bytes(image, "png"))
        if request.include_pdf_sheet:
            pdf_options = request.options.model_copy(update={"export_format": "pdf", "pdf": request.options.pdf.model_copy(update={"multiple_per_page": min(len(request.items), 24)})})
            archive.writestr("sheet.pdf", render_pdf(pdf_options))
    return output.getvalue()
