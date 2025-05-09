from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.depends import TemplateRenderer
from src.routers.user.schemas import UserContext
from src.routers.auth.depends import CurrentUserOrNone

index_router: APIRouter = APIRouter()


@index_router.get("/", response_class=HTMLResponse)
async def index(templates: TemplateRenderer, current_user: CurrentUserOrNone):
    return templates.render(
        "index.jinja", UserContext(current_user=current_user)
    )


@index_router.get("/about", response_class=HTMLResponse)
async def about(templates: TemplateRenderer, current_user: CurrentUserOrNone):
    return templates.render(
        "about.jinja",
        UserContext(current_user=current_user),
    )


@index_router.get("/participants", response_class=HTMLResponse)
async def participants(
    templates: TemplateRenderer, current_user: CurrentUserOrNone
):
    return templates.render(
        "participants.jinja",
        UserContext(current_user=current_user),
    )


@index_router.get("/gallery", response_class=HTMLResponse)
async def gallery(
    templates: TemplateRenderer, current_user: CurrentUserOrNone
):
    return templates.render(
        "gallery.jinja",
        UserContext(current_user=current_user),
    )
