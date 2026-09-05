import base64
import io

from PIL import Image

from app.models import GenerateRequest
from app.services.exporter import export_qr
from app.services.qr_generator import modified_matrix_for_request, render_qr_image, render_vector
from app.services.qr_scanner import decode_image
from app.utils.validation import is_public_http_url


def test_png_generation_is_readable() -> None:
    request = GenerateRequest(value="https://example.com")
    image, payload, warnings = render_qr_image(request)
    decoded = decode_image(image)
    assert payload == "https://example.com"
    assert decoded.found
    assert decoded.results[0].raw == payload
    assert warnings == []


def test_svg_export_is_vector() -> None:
    request = GenerateRequest(value="hello", export_format="svg")
    svg = render_vector(request, "svg").decode("utf-8")
    assert "<svg" in svg
    assert "<path" in svg
    assert "<image" not in svg


def test_export_response_base64() -> None:
    response = export_qr(GenerateRequest(value="plain text"))
    assert response.media_type == "image/png"
    assert response.data
    assert response.readable


def test_private_url_rejected() -> None:
    assert not is_public_http_url("http://127.0.0.1/image.png")


def test_logo_area_clears_matrix_before_rendering() -> None:
    request = GenerateRequest(
        value="https://example.com/logo",
        logo={"enabled": True, "data_url": _logo_data_url(), "size_percent": 20, "padding": 16},
    )
    matrix, _, logo_area = modified_matrix_for_request(request)
    assert logo_area is not None
    start_col, start_row, end_col, end_row = logo_area
    assert all(not matrix[row][col] for row in range(start_row, end_row) for col in range(start_col, end_col))
    assert any(matrix[row][col] for row in range(7) for col in range(7))


def test_logo_png_generation_validates_final_image() -> None:
    request = GenerateRequest(
        value="https://example.com/logo",
        logo={"enabled": True, "data_url": _logo_data_url(), "size_percent": 10, "padding": 8},
    )
    image, payload, warnings = render_qr_image(request)
    decoded = decode_image(image)
    assert decoded.found
    assert decoded.results[0].raw == payload
    assert warnings == []


def _logo_data_url() -> str:
    image = Image.new("RGBA", (64, 64), "#0f766e")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('ascii')}"
