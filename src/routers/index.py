from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.depends import render_template
from src.routers.user.schemas import UserContext
from src.routers.auth.depends import CurrentUserOrNone

index_router: APIRouter = APIRouter()


@index_router.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: CurrentUserOrNone):
    return render_template(
        request,
        "index.jinja",
        UserContext(current_user=current_user),
    )


@index_router.get("/about", response_class=HTMLResponse)
async def about(request: Request, current_user: CurrentUserOrNone):
    return render_template(
        request,
        "about.jinja",
        UserContext(current_user=current_user),
    )


@index_router.get("/participants", response_class=HTMLResponse)
async def participants(request: Request, current_user: CurrentUserOrNone):
    return render_template(
        request,
        "participants.jinja",
        UserContext(current_user=current_user),
    )


@index_router.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request, current_user: CurrentUserOrNone):
    return render_template(
        request,
        "gallery.jinja",
        UserContext(current_user=current_user),
    )
