from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.schemas import BaseContext
from src.depends import Templates

router: APIRouter = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request, name="index.jinja", context=BaseContext().model_dump()
    )


@router.get("/about", response_class=HTMLResponse)
async def about(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request, name="about.jinja", context=BaseContext().model_dump()
    )


@router.get("/participants", response_class=HTMLResponse)
async def participants(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="participants.jinja",
        context=BaseContext().model_dump(),
    )


@router.get("/gallery", response_class=HTMLResponse)
async def gallery(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="gallery.jinja",
        context=BaseContext().model_dump(),
    )
