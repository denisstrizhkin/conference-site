from typing import Annotated, Optional

from fastapi import APIRouter, status, Request, HTTPException, Form
from fastapi.responses import HTMLResponse

from src.db import Session
from src.depends import render_template
from src.routers.auth.depends import CurrentUserOrNone

from .schemas import VoteFormContext


vote_router = APIRouter(prefix="/vote")


@vote_router.get("/", response_class=HTMLResponse)
async def vote(request: Request, current_user: CurrentUserOrNone):
    return render_template(
        request,
        "vote.jinja",
        VoteFormContext(),
    )
