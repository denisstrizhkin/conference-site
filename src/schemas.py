from typing import Optional
from pydantic import BaseModel


class BaseContext(BaseModel):
    title: str = "StudConfAU"
    error: Optional[str] = None
