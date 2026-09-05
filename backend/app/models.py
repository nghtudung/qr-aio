from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ErrorCorrection(str, Enum):
    L = "L"
    M = "M"
    Q = "Q"
    H = "H"


class ModuleStyle(str, Enum):
    square = "square"
    rounded = "rounded"
    circle = "circle"


class FinderStyle(str, Enum):
    square = "square"
    rounded = "rounded"
    circle = "circle"


class ExportFormat(str, Enum):
    png = "png"
    jpg = "jpg"
    webp = "webp"
    svg = "svg"
    eps = "eps"
    pdf = "pdf"


class DataType(str, Enum):
    text = "text"
    url = "url"
    email = "email"
    phone = "phone"
    sms = "sms"
    wifi = "wifi"
    vcard = "vcard"
    json = "json"


class Gradient(BaseModel):
    enabled: bool = False
    start: str = "#111827"
    end: str = "#2563eb"
    direction: Literal["horizontal", "vertical", "diagonal"] = "diagonal"


class LogoOptions(BaseModel):
    enabled: bool = False
    data_url: str | None = None
    size_percent: int = Field(default=15, ge=10, le=25)
    padding: int = Field(default=14, ge=0, le=80)
    rounded_container: bool = True
    border: bool = False
    background: str = "#ffffff"


class PdfOptions(BaseModel):
    page_size: Literal["A4", "A5", "custom"] = "A4"
    custom_width_mm: float | None = Field(default=None, ge=40, le=1000)
    custom_height_mm: float | None = Field(default=None, ge=40, le=1000)
    title: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    multiple_per_page: int = Field(default=1, ge=1, le=24)


class GenerateRequest(BaseModel):
    data_type: DataType = DataType.text
    value: str = Field(min_length=1, max_length=4096)
    error_correction: ErrorCorrection = ErrorCorrection.H
    width: int = Field(default=1024, ge=128, le=4096)
    height: int = Field(default=1024, ge=128, le=4096)
    foreground: str = "#111827"
    background: str = "#ffffff"
    transparent_background: bool = False
    gradient: Gradient = Field(default_factory=Gradient)
    module_style: ModuleStyle = ModuleStyle.square
    finder_style: FinderStyle = FinderStyle.square
    logo: LogoOptions = Field(default_factory=LogoOptions)
    export_format: ExportFormat = ExportFormat.png
    pdf: PdfOptions = Field(default_factory=PdfOptions)

    @field_validator("foreground", "background")
    @classmethod
    def validate_colour(cls, value: str) -> str:
        if value == "transparent":
            return value
        if not value.startswith("#") or len(value) not in (4, 7):
            raise ValueError("colour must be a hex value")
        int(value[1:], 16)
        return value


class GenerateResponse(BaseModel):
    filename: str
    media_type: str
    data: str
    readable: bool
    decoded_text: str | None = None
    warnings: list[str] = Field(default_factory=list)


class BatchItem(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=4096)
    data_type: DataType = DataType.url


class BatchGenerateRequest(BaseModel):
    items: list[BatchItem] = Field(min_length=1, max_length=250)
    options: GenerateRequest
    include_pdf_sheet: bool = False


class ScanUrlRequest(BaseModel):
    url: HttpUrl


class DetectedResult(BaseModel):
    raw: str
    content_type: str
    parsed: dict[str, Any] = Field(default_factory=dict)


class ScanResponse(BaseModel):
    found: bool
    results: list[DetectedResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
