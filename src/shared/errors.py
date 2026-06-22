from __future__ import annotations


class AppError(Exception):
    code: str = "ERROR"
    http_status: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    http_status = 400


def error_payload(error: AppError) -> dict[str, str]:
    return {"code": error.code, "message": error.message}
