This project is 100% vibe-coding, sorry 😅.

# QR AIO

A stateless QR Code Generator and Scanner web application.

The backend is FastAPI and keeps no database, no accounts, and no persistent uploads. QR artifacts are generated in memory; PDF composition uses temporary files inside automatically cleaned temporary directories. The frontend is React, TypeScript, and TailwindCSS.

## Features

- Generate QR codes from text, URLs, email, phone, SMS, WiFi JSON, vCard, or custom JSON.
- Customize error correction, dimensions, colors, gradients, transparent background, module style, and finder pattern style.
- Embed PNG or sanitized SVG logos with a cleared central logo area, padding, border, container background, and post-generation readability validation.
- Export PNG, JPG, WEBP, true vector SVG, EPS, and PDF.
- Scan QR codes from camera, uploaded image, or public image URL.
- Batch generation from JSON API or CSV/XLSX/JSON upload into a ZIP archive.
- Safe file handling: upload size limits, MIME checks, timeout-limited URL fetches, SVG sanitization, SSRF-aware public host validation, and rate limiting.

## Local Development

Backend:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs are available at `http://localhost:8000/docs`.

## Docker

```bash
docker compose up --build
```

Frontend: `http://localhost:8080`

Backend API: `http://localhost:8000`

## Environment

Copy `.env.example` and adjust values as needed:

- `QR_AIO_CORS_ORIGINS`: JSON list of allowed frontend origins.
- `QR_AIO_MAX_UPLOAD_BYTES`: upload size limit.
- `QR_AIO_MAX_URL_DOWNLOAD_BYTES`: remote image download size limit.
- `QR_AIO_REQUEST_TIMEOUT_SECONDS`: outbound image URL timeout.
- `QR_AIO_RATE_LIMIT`: default SlowAPI limit.

## API

- `GET /api/health`
- `POST /api/generate`
- `POST /api/generate/batch`
- `POST /api/generate/batch/upload`
- `POST /api/scan/upload`
- `POST /api/scan/url`

`POST /api/generate` returns a base64 artifact and metadata:

```json
{
  "data_type": "url",
  "value": "https://example.com",
  "error_correction": "H",
  "width": 1024,
  "height": 1024,
  "foreground": "#111827",
  "background": "#ffffff",
  "transparent_background": false,
  "gradient": {
    "enabled": false,
    "start": "#111827",
    "end": "#0f766e",
    "direction": "diagonal"
  },
  "module_style": "square",
  "finder_style": "rounded",
  "logo": {
    "enabled": false,
    "data_url": null,
    "size_percent": 15,
    "padding": 14,
    "rounded_container": true,
    "border": true,
    "background": "#ffffff"
  },
  "export_format": "png",
  "pdf": {
    "page_size": "A4",
    "custom_width_mm": null,
    "custom_height_mm": null,
    "title": null,
    "description": null,
    "multiple_per_page": 1
  }
}
```

## QR Algorithms

Raster rendering builds a Segno QR matrix with the selected error correction level, then draws modules directly with Pillow. Square, rounded, and circular modules are rendered from the boolean matrix. Gradients are sampled per module so foreground color remains deterministic.

Logo embedding uses high error correction by default and modifies the QR matrix before rendering. The service calculates a central logo exclusion area, clears modules inside that area, preserves finder patterns and separators, then renders the modified matrix to PNG or SVG. Padding, border, and background are drawn only inside the already-cleared logo container before the logo is composited. The final generated image is decoded immediately with OpenCV and optional zbar support; a warning is returned when readability validation fails.

SVG export renders the modified matrix as vector paths, so the QR modules remain true vector geometry instead of an embedded PNG. EPS export uses Segno's vector writer.

Scanning uses OpenCV `QRCodeDetector` for single and multi-code reads, with `pyzbar` as an optional fallback when system `zbar` is installed. Results are classified as URL, WiFi, vCard, JSON, email, phone, or text.
