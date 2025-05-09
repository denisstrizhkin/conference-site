from pathlib import Path
from typing import Annotated, Optional

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from src.schemas import BaseContext


def get_templates() -> Jinja2Templates:
    return Jinja2Templates(directory=Path(__file__).parent / "templates")


Templates = Annotated[Jinja2Templates, Depends(get_templates)]


class Renderer:
    def __init__(self, request: Request, templates: Jinja2Templates):
        self._request = request
        self._templates = templates

    def render(self, name: str, context: Optional[BaseContext] = None):
        if context is None:
            context = BaseContext()
        return self._templates.TemplateResponse(
            request=self._request, name=name, context=context.model_dump()
        )


def build_renderer(request: Request, templates: Templates) -> Renderer:
    return Renderer(request, templates)


TemplateRenderer = Annotated[Renderer, Depends(build_renderer)]
