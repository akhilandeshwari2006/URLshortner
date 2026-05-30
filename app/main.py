from uuid import uuid4
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import error_response
from app.routers import links, redirect
from sqlalchemy import text

from app.cache import redis_client
from app.database import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI(title="UPSK URL Shortener API")
app.include_router(links.router)
app.include_router(redirect.router)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=error_response("VALIDATION_ERROR", "Invalid request", request.state.request_id),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response("HTTP_ERROR", str(exc.detail), request.state.request_id),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=500,
        content=error_response("INTERNAL_SERVER_ERROR", "Something went wrong", request.state.request_id),
    )


@app.get("/health")
@app.get("/live")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/ready")
async def ready() -> dict[str, str]:
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()

        await redis_client.ping()

        return {"status": "ready"}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Dependency check failed",
        )
