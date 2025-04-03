from typing import Annotated
import logging

from fastapi import (
    APIRouter,
    status,
    Request,
    Form,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from src.db import AsyncSession
from src.depends import Templates
from .models import User
from .auth import create_access_token, CurrentUser

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
    user = User(email=email, password=password)
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
    stmt = select(User).where(User.email == email, User.password == password)
    async with session() as session:
        result = await session.execute(stmt)
        user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad email or password",
        )
    logging.info(user)

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


@router.get("/", response_class=HTMLResponse)
async def get_users(
    templates: Templates,
    request: Request,
    session: AsyncSession,
    current_user: CurrentUser,
):
    logging.info(current_user)
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
