from fastapi import APIRouter, Depends, Path, Query, status, Request
from fastapi.responses import HTMLResponse

from src.depends import Templates

router: APIRouter = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.jinja",
        context={"title": "StudConfAU"}
    )


@router.get("/about", response_class=HTMLResponse)
async def about(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="about.jinja",
        context={"title": "StudConfAU"}
    )


@router.get("/participants", response_class=HTMLResponse)
async def participants(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="participants.jinja",
        context={"title": "StudConfAU"}
    )


@router.get("/gallery", response_class=HTMLResponse)
async def gallery(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="gallery.jinja",
        context={"title": "StudConfAU"}
    )
