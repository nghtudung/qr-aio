import html

from PIL import Image, ImageColor, ImageDraw

from app.models import GenerateRequest

QUIET_ZONE_MODULES = 4


def make_gradient(size: tuple[int, int], start: str, end: str, direction: str) -> Image.Image:
    width, height = size
    start_rgb = ImageColor.getrgb(start)
    end_rgb = ImageColor.getrgb(end)
    image = Image.new("RGB", size)
    pixels = image.load()
    denominator = max(1, width + height if direction == "diagonal" else width if direction == "horizontal" else height)
    for y in range(height):
        for x in range(width):
            ratio = (x + y if direction == "diagonal" else x if direction == "horizontal" else y) / denominator
            colour = tuple(round(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * ratio) for i in range(3))
            pixels[x, y] = colour
    return image


def finder_origins(module_count: int) -> set[tuple[int, int]]:
    return {(0, 0), (module_count - 7, 0), (0, module_count - 7)}


def is_finder_protected(row: int, col: int, module_count: int) -> bool:
    for origin_col, origin_row in finder_origins(module_count):
        if origin_col - 1 <= col <= origin_col + 7 and origin_row - 1 <= row <= origin_row + 7:
            return True
    return False


def clear_logo_modules(matrix: list[list[bool]], request: GenerateRequest) -> tuple[list[list[bool]], tuple[int, int, int, int] | None]:
    if not request.logo.enabled or not request.logo.data_url:
        return [row[:] for row in matrix], None

    modules = len(matrix)
    module_px = min(request.width, request.height) / (modules + QUIET_ZONE_MODULES * 2)
    logo_px = min(request.width, request.height) * (request.logo.size_percent / 100)
    container_px = logo_px + request.logo.padding * 2
    container_modules = max(1, round(container_px / module_px))
    if container_modules % 2 == 0:
        container_modules += 1

    start = max(0, (modules - container_modules) // 2)
    end = min(modules, start + container_modules)
    modified = [row[:] for row in matrix]
    for row in range(start, end):
        for col in range(start, end):
            if not is_finder_protected(row, col, modules):
                modified[row][col] = False
    return modified, (start, start, end, end)


def draw_styled_modules(matrix: list[list[bool]], request: GenerateRequest) -> Image.Image:
    modules = len(matrix)
    quiet = QUIET_ZONE_MODULES
    canvas_modules = modules + quiet * 2
    scale = max(1, min(request.width, request.height) // canvas_modules)
    size = canvas_modules * scale
    mode = "RGBA" if request.transparent_background else "RGB"
    background = (255, 255, 255, 0) if request.transparent_background else request.background
    image = Image.new(mode, (size, size), background)
    draw = ImageDraw.Draw(image)
    gradient = None
    if request.gradient.enabled:
        gradient = make_gradient((size, size), request.gradient.start, request.gradient.end, request.gradient.direction)

    def fill_for(box: tuple[int, int, int, int]) -> str | tuple[int, int, int]:
        if gradient is None:
            return request.foreground
        cx = min(size - 1, max(0, (box[0] + box[2]) // 2))
        cy = min(size - 1, max(0, (box[1] + box[3]) // 2))
        return gradient.getpixel((cx, cy))

    for row_idx, row in enumerate(matrix):
        for col_idx, enabled in enumerate(row):
            if not enabled:
                continue
            x0 = (col_idx + quiet) * scale
            y0 = (row_idx + quiet) * scale
            x1 = x0 + scale
            y1 = y0 + scale
            in_finder = any(ox <= col_idx < ox + 7 and oy <= row_idx < oy + 7 for ox, oy in finder_origins(modules))
            style = request.finder_style if in_finder else request.module_style
            fill = fill_for((x0, y0, x1, y1))
            if style == "circle":
                draw.ellipse((x0, y0, x1, y1), fill=fill)
            elif style == "rounded":
                draw.rounded_rectangle((x0, y0, x1, y1), radius=max(2, scale // 3), fill=fill)
            else:
                draw.rectangle((x0, y0, x1, y1), fill=fill)
    if image.size != (request.width, request.height):
        image = image.resize((request.width, request.height), Image.Resampling.LANCZOS)
    return image


def render_matrix_svg(matrix: list[list[bool]], request: GenerateRequest, logo_href: str | None = None) -> str:
    modules = len(matrix)
    quiet = QUIET_ZONE_MODULES
    canvas_modules = modules + quiet * 2
    cell = min(request.width, request.height) / canvas_modules
    width = request.width
    height = request.height
    bg = "" if request.transparent_background else f'<rect width="100%" height="100%" fill="{html.escape(request.background)}"/>'
    defs = ""
    fill = html.escape(request.foreground)
    if request.gradient.enabled:
        x2, y2 = ("100%", "0%") if request.gradient.direction == "horizontal" else ("0%", "100%") if request.gradient.direction == "vertical" else ("100%", "100%")
        defs = (
            '<defs><linearGradient id="qr-gradient" x1="0%" y1="0%" '
            f'x2="{x2}" y2="{y2}"><stop offset="0%" stop-color="{html.escape(request.gradient.start)}"/>'
            f'<stop offset="100%" stop-color="{html.escape(request.gradient.end)}"/></linearGradient></defs>'
        )
        fill = "url(#qr-gradient)"
    path_parts: list[str] = []
    for row_idx, row in enumerate(matrix):
        for col_idx, enabled in enumerate(row):
            if enabled:
                x = (col_idx + quiet) * cell
                y = (row_idx + quiet) * cell
                path_parts.append(f"M{x:.3f},{y:.3f}h{cell:.3f}v{cell:.3f}h-{cell:.3f}z")
    path = f'<path fill="{fill}" d="{" ".join(path_parts)}"/>'
    logo = ""
    if logo_href and request.logo.enabled:
        logo_px = min(request.width, request.height) * (request.logo.size_percent / 100)
        container_px = logo_px + request.logo.padding * 2
        x = (request.width - container_px) / 2
        y = (request.height - container_px) / 2
        radius = container_px / 6 if request.logo.rounded_container else 0
        logo_x = x + request.logo.padding
        logo_y = y + request.logo.padding
        logo = (
            f'<rect x="{x:.3f}" y="{y:.3f}" width="{container_px:.3f}" height="{container_px:.3f}" '
            f'rx="{radius:.3f}" fill="{html.escape(request.logo.background)}"/>'
            f'<image href="{html.escape(logo_href)}" x="{logo_x:.3f}" y="{logo_y:.3f}" '
            f'width="{logo_px:.3f}" height="{logo_px:.3f}" preserveAspectRatio="xMidYMid meet"/>'
        )
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{defs}{bg}{path}{logo}</svg>'
