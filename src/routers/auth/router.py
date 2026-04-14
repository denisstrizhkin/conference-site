from typing import Annotated

from fastapi import APIRouter, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from src.controllers.user_controller import (
    UserControllerDep,
    UserFilter,
    UserNew,
)
from src.depends import TemplateRenderer
from src.schemas import BaseContext
from src.settings import settings

from .depends import (
    PassHasher,
    create_access_token,
)
from .schemas import (
    LoginForm,
    RegisterForm,
)

auth_router = APIRouter(prefix="/auth")


@auth_router.get("/register", response_class=HTMLResponse)
async def register_form(templates: TemplateRenderer):
    return templates.render(
        "auth/register.jinja",
    )


@auth_router.post("/register", response_class=HTMLResponse)
async def register(
    templates: TemplateRenderer,
    form: Annotated[RegisterForm, Form()],
    user_controller: UserControllerDep,
):
    try:
        await user_controller.create(
            UserNew(
                email=form.email,
                password=PassHasher.get_password_hash(form.password),
            )
        )
    except IntegrityError:
        return templates.render(
            "auth/register.jinja",
            BaseContext(error="Такой пользователь уже сущевствует."),
        )

    return RedirectResponse(
        url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
    )


@auth_router.get("/login", response_class=HTMLResponse)
async def login_form(templates: TemplateRenderer):
    return templates.render(
        "auth/login.jinja",
    )


@auth_router.post("/login", response_class=HTMLResponse)
async def login(
    templates: TemplateRenderer,
    form: Annotated[LoginForm, Form()],
    user_controller: UserControllerDep,
):
    def error_response(error: str) -> HTMLResponse:
        return templates.render(
            "auth/login.jinja",
            BaseContext(error=error),
        )

    user = await user_controller.get_one_or_none(UserFilter(email=form.email))
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
        secure=settings.secure_cookies,
        samesite="lax",
    )

    return response


@auth_router.post("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    # Remove the access token cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )

    return response
