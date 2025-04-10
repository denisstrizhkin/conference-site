from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi.templating import Jinja2Templates


def get_templates() -> Jinja2Templates:
    return Jinja2Templates(directory=Path(__file__).parent / "templates")


Templates = Annotated[Jinja2Templates, Depends(get_templates)]
