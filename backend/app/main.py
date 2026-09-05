from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.api.generate import router as generate_router
from app.api.scan import router as scan_router
from app.config import get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(
    title="QR AIO API",
    description="Stateless QR code generator and scanner API with raster, vector, and PDF export.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(generate_router, prefix="/api")
app.include_router(scan_router, prefix="/api")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded: {exc.detail}"})


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
