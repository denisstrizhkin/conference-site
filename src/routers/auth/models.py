from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    id: int
    expires: datetime
