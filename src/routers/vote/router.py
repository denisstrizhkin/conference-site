from typing import Annotated
import io
import base64

from fastapi import APIRouter, status, HTTPException, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import NoResultFound
import matplotlib.pyplot as plt

from src.logger import logger
from src.db import Session
from src.depends import TemplateRenderer
from src.routers.auth.depends import CurrentUserOrNone, CurrentUser
from src.routers.user.models import UserRole

from .schemas import VoteFormContext, VoteForm, VoteAdminContext, CodesForm
from .repo import VoteRepository
from .models import Vote, Reports


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
    image = get_vote_results_plot(votes)

    return templates.render(
        "vote/admin.jinja",
        VoteAdminContext(current_user=current_user, image=image),
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


def get_vote_results_plot(votes: list[Vote]) -> str:
    lables = list(map(str, Reports))
    cnt = dict(zip(lables, [0] * len(Reports)))
    for vote in votes:
        if vote.report:
            cnt[vote.report.value] += 1
    values = [cnt[lable] for lable in lables]
    plt.bar(lables, values)
    plt.title("Результаты голосования")
    with io.BytesIO() as buf:
        plt.savefig(buf, format="jpeg")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close()
    return f"data:image/jpeg;base64,{img_b64}"
