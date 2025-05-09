from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from src.schemas import BaseContext


def get_templates() -> Jinja2Templates:
    return Jinja2Templates(directory=Path(__file__).parent / "templates")


Templates = Annotated[Jinja2Templates, Depends(get_templates)]


def render_template(request: Request, name: str, context: BaseContext):
    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name=name,
        context=context.model_dump(),
    )
