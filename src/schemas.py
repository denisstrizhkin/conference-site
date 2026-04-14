from pydantic import BaseModel


class BaseContext(BaseModel):
    title: str = "StudConfAU"
    message: str | None = None
    error: str | None = None


class ErrorContext(BaseContext):
    message: str
    code: int
