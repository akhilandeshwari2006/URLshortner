from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def error_response(code: str, message: str, request_id: str) -> dict[str, dict[str, str]]:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }