from typing import Annotated

from fastapi import APIRouter, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from src.routers.user.repo import UserRepository
from src.schemas import BaseContext
from src.db import Session
from src.depends import Templates

from .schemas import (
    RegisterForm,
    LoginForm,
)
from .depends import (
    create_access_token,
    PassHasher,
)

router = APIRouter(prefix="/auth")


@router.get("/register", response_class=HTMLResponse)
async def register_form(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/register.jinja",
        context=BaseContext().model_dump(),
    )


@router.post("/register", response_class=HTMLResponse | RedirectResponse)
async def register(
    request: Request,
    form: Annotated[RegisterForm, Form()],
    session: Session,
    templates: Templates,
):
    try:
        await UserRepository(session).create(
            form.email, PassHasher.get_password_hash(form.password)
        )
    except IntegrityError:
        return templates.TemplateResponse(
            request=request,
            name="user/register.jinja",
            context=BaseContext(
                error="Такой пользователь уже сущевствует."
            ).model_dump(),
        )

    return RedirectResponse(
        url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/login", response_class=HTMLResponse)
async def login_form(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user/login.jinja",
        context=BaseContext().model_dump(),
    )


@router.post("/login", response_class=HTMLResponse | RedirectResponse)
async def login(
    request: Request,
    form: Annotated[LoginForm, Form()],
    session: Session,
    templates: Templates,
):
    def error_response(error: str) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.jinja",
            context=BaseContext(error=error).model_dump(),
        )

    user = await UserRepository(session).get_one_or_none(email=form.email)
    if user is None:
        return error_response("Такого пользователя не существует.")
    if not PassHasher.verify_password(form.password, user.password):
        return error_response("Неправильная почта или пароль.")

    token, expires = create_access_token(user.id)

    # Set cookie with token
    response = RedirectResponse(
        url=f"/user/{user.id}", status_code=status.HTTP_303_SEE_OTHER
    )
    response.set_cookie(
        key="access_token",
        value=f"{token}",
        httponly=True,
        max_age=expires,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
    )

    return response


@router.post("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    # Remove the access token cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,  # For HTTPS
        samesite="lax",
    )

    return response
