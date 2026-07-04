from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handler — catches unhandled errors and returns clean JSON."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            # Log the full traceback
            traceback.print_exc()

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error. Please try again later.",
                    "error_type": type(e).__name__,
                },
            )
