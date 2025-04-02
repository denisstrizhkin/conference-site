from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select

from src.db import AsyncSession
from src.depends import Templates
from .models import User

router = APIRouter()


@router.get("/register", response_class=HTMLResponse)
async def register(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request, name="user/register.jinja", context={"title": "StudConfAU"}
    )


@router.post("/register")
async def create_user(
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: AsyncSession,
):
    user = User(email=email, password=password)
    async with session() as session:
        session.add(user)
        await session.commit()
    return RedirectResponse(url="/user/register", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse)
async def get_users(templates: Templates, request: Request, session: AsyncSession):
    async with session() as session:
        result = await session.execute(select(User))
    users = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="user/list.jinja",
        context={"title": "StudConfAU", "users": users},
    )
