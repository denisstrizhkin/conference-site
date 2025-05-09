from typing import Annotated

from fastapi import APIRouter, status, Request, HTTPException, Form
from fastapi.responses import HTMLResponse

from src.db import Session
from src.depends import TemplateRenderer
from src.routers.auth.depends import CurrentUserOrNone, CurrentUser
from src.routers.user.models import UserRole

from .schemas import VoteFormContext, VoteForm


vote_router = APIRouter(prefix="/vote")


@vote_router.get("/", response_class=HTMLResponse)
async def get_vote(
    templates: TemplateRenderer, current_user: CurrentUserOrNone
):
    return templates.render(
        "vote/vote.jinja",
        VoteFormContext(current_user=current_user),
    )


@vote_router.post("/", response_class=HTMLResponse)
async def post_vote(
    templates: TemplateRenderer,
    current_user: CurrentUserOrNone,
    session: Session,
    form: Annotated[VoteForm, Form()],
):
    return templates.render(
        "vote/vote.jinja",
        VoteFormContext(current_user=current_user),
    )


@vote_router.get("/admin", response_class=HTMLResponse)
async def get_admin(request: Request, current_user: CurrentUser):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@vote_router.post("/admin", response_class=HTMLResponse)
async def post_admin(request: Request, current_user: CurrentUser):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
