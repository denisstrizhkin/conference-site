from typing import Annotated
import logging

from fastapi import (
    APIRouter,
    status,
    Request,
    Form,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from src.db import AsyncSession
from src.depends import Templates
from .models import User
from .auth import create_access_token, CurrentUser, PassHasher

router = APIRouter(prefix="/user")


@router.get("/register", response_class=HTMLResponse)
async def register_form(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user/register.jinja",
        context={"title": "StudConfAU"},
    )


@router.post("/register")
async def register(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: AsyncSession,
    templates: Templates,
):
    user = User(email=email, password=PassHasher.get_password_hash(password))
    try:
        async with session() as session:
            session.add(user)
            await session.commit()
    except SQLAlchemyError as e:
        error = e._message()
        logging.error(e)
        return templates.TemplateResponse(
            request=request,
            name="user/register.jinja",
            context={"title": "StudConfAU", "error": error},
        )

    return RedirectResponse(
        url="/user/login", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/login", response_class=HTMLResponse)
async def login_form(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user/login.jinja",
        context={"title": "StudConfAU"},
    )


@router.post("/login")
async def login(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: AsyncSession,
    templates: Templates,
):
    stmt = select(User).where(User.email == email)
    error: str | None = None
    try:
        async with session() as session:
            result = await session.execute(stmt)
            user = result.one()[0]
    except SQLAlchemyError as e:
        error = e._message()
        logging.error(e)

    if not PassHasher.verify_password(password, user.password):
        error = "Wrong email or password"

    if error is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU", "error": error},
        )

    token, expires = create_access_token(user)

    # Set cookie with token
    response = RedirectResponse(
        url="/user", status_code=status.HTTP_303_SEE_OTHER
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=expires,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
    )

    return response


@router.post("/logout")
async def logout_user():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    # Remove the access token cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,  # For HTTPS
        samesite="lax",
    )

    return response


@router.get("/", response_class=HTMLResponse)
async def get_users(
    templates: Templates,
    request: Request,
    session: AsyncSession,
    current_user: CurrentUser,
):
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU"},
        )

    async with session() as session:
        result = await session.execute(select(User))
    users = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="user/list.jinja",
        context={"title": "StudConfAU", "users": users},
    )
