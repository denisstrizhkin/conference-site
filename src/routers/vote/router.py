from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import NoResultFound

from src.logger import logger
from src.db import Session
from src.depends import TemplateRenderer
from src.routers.auth.depends import CurrentUserOrNone, CurrentUser
from src.routers.user.models import UserRole

from .schemas import VoteFormContext, VoteForm, VoteAdminContext, CodesForm
from .repo import VoteRepository

import matplotlib.pyplot as plt
import io
import base64


vote_router = APIRouter(prefix="/vote")


@vote_router.get("/", response_class=HTMLResponse)
async def get_vote(
    templates: TemplateRenderer, current_user: CurrentUserOrNone
):
    return templates.render(
        "vote/index.jinja",
        VoteFormContext(current_user=current_user),
    )


@vote_router.post("/", response_class=HTMLResponse)
async def post_vote(
    templates: TemplateRenderer,
    current_user: CurrentUserOrNone,
    session: Session,
    form: Annotated[VoteForm, Form()],
):
    try:
        vote = await VoteRepository(session).update(form.code, form.report)
    except NoResultFound:
        return templates.render(
            "vote/index.jinja",
            VoteFormContext(
                current_user=current_user,
                selected=form.report,
                error="Такого кода несуществует.",
            ),
        )

    return templates.render(
        "vote/index.jinja",
        VoteFormContext(
            current_user=current_user,
            selected=vote.report,
            message="Голос учтен.",
        ),
    )


@vote_router.get("/admin", response_class=HTMLResponse)
async def get_admin(
    templates: TemplateRenderer,
    current_user: CurrentUser,
    session: Session,
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    votes = await VoteRepository(session).get()
    logger.info(votes)

    img = "data:image/png;base64," + get_pic(votes)

    return templates.render(
        "vote/admin.jinja", VoteAdminContext(current_user=current_user, image=img)
    )


@vote_router.post("/admin", response_class=HTMLResponse)
async def post_admin(
    templates: TemplateRenderer,
    current_user: CurrentUser,
    session: Session,
    codes_form: Annotated[CodesForm, Form()],
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    data = await codes_form.codes_file.read()
    codes_s = data.decode("utf8").strip()
    codes = [code.strip() for code in codes_s.split()]

    vote_repo = VoteRepository(session)
    for code in codes:
        await vote_repo.create(code)

    votes = await vote_repo.get()
    logger.info(votes)

    return templates.render(
        "vote/admin.jinja",
        VoteAdminContext(
            current_user=current_user,
            message="Коды голосования перезаданы.",
        ),
    )


def get_pic(votes):
    print(votes)
    categories = ["A", "B", "C", "D", "E"]
    vals = [0, 0, 0, 0, 0]
    for vote in votes:
        if vote.report is None:
            continue
        if vote.report.value == "a":
            vals[0] += 1
        elif vote.report.value == "b":
            vals[1] += 1
        elif vote.report.value == "c":
            vals[2] += 1
        elif vote.report.value == "d":
            vals[3] += 1
        elif vote.report.value == "e":
            vals[4] += 1
    plt.bar(categories, vals)
    plt.title("Результаты голосования")

    buf = io.BytesIO()
    plt.savefig(buf, format="jpg")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    buf.close
    return img
