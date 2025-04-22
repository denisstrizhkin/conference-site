from typing import Optional
from pydantic import BaseModel


class BaseContext(BaseModel):
    title: str = "StudConfAU"
    message: Optional[str] = None
    error: Optional[str] = None


class ErrorContext(BaseContext):
    message: str
    code: int
