from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.depends import Templates
from src.routers.user.schemas import UserContext
from src.routers.auth.depends import CurrentUserOrNone

router: APIRouter = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(
    templates: Templates, request: Request, current_user: CurrentUserOrNone
):
    return templates.TemplateResponse(
        request=request,
        name="index.jinja",
        context=UserContext(user=current_user).model_dump(),
    )


@router.get("/about", response_class=HTMLResponse)
async def about(
    templates: Templates, request: Request, current_user: CurrentUserOrNone
):
    return templates.TemplateResponse(
        request=request,
        name="about.jinja",
        context=UserContext(user=current_user).model_dump(),
    )


@router.get("/participants", response_class=HTMLResponse)
async def participants(
    templates: Templates, request: Request, current_user: CurrentUserOrNone
):
    return templates.TemplateResponse(
        request=request,
        name="participants.jinja",
        context=UserContext(user=current_user).model_dump(),
    )


@router.get("/gallery", response_class=HTMLResponse)
async def gallery(
    templates: Templates, request: Request, current_user: CurrentUserOrNone
):
    return templates.TemplateResponse(
        request=request,
        name="gallery.jinja",
        context=UserContext(user=current_user).model_dump(),
    )
