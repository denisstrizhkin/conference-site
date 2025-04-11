from typing import Annotated
import logging

from fastapi import APIRouter, status, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.schemas import BaseContext
from src.db import Session
from src.depends import Templates
from src.routers.files.repo import FileRepository
from src.routers.files.models import File

from .schemas import (
    UserFormContext,
    UsersContext,
    RegisterForm,
    LoginForm,
    UserForm,
)
from .repo import UserRepository
from .models import ReportForm, UserRole
from .auth import (
    create_access_token,
    PassHasher,
    CurrentUser,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user")


@router.get("/register", response_class=HTMLResponse)
async def register_form(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user/register.jinja",
        context=BaseContext().model_dump(),
    )


@router.post("/register")
async def register(
    request: Request,
    form: Annotated[RegisterForm, Form()],
    session: Session,
    templates: Templates,
):
    error: str | None = None
    try:
        await UserRepository(session).create(
            form.email, PassHasher.get_password_hash(form.password)
        )
    except IntegrityError as e:
        error = "Такой пользователь уже сущевствует"
        logger.error(e)
    except SQLAlchemyError as e:
        error = e._message()
        logger.error(e)

    if error is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/register.jinja",
            context=BaseContext(error=error).model_dump(),
        )

    return RedirectResponse(
        url="/user/login", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/login", response_class=HTMLResponse)
async def login_form(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user/login.jinja",
        context=BaseContext().model_dump(),
    )


@router.post("/login")
async def login(
    request: Request,
    form: Annotated[LoginForm, Form()],
    session: Session,
    templates: Templates,
):
    error: str | None = None
    try:
        user = await UserRepository(session).get_one(email=form.email)
    except SQLAlchemyError as e:
        error = e._message()
        logger.error(e)

    if user is None:
        error = "Такого пользователя не существует"
    if user and not PassHasher.verify_password(form.password, user.password):
        error = "Неправильная почта или пароль"

    if error is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context=BaseContext(error=error).model_dump(),
        )

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


@router.post("/logout")
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


@router.get("/{user_id}", response_class=HTMLResponse)
async def get_account(
    user_id: int,
    templates: Templates,
    request: Request,
    session: Session,
    current_user: CurrentUser,
):
    if current_user.id != user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user = await UserRepository(session).get_one(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    file: File | None = None
    if user.form:
        file = await FileRepository(session).get(user.form.file_id)

    return templates.TemplateResponse(
        request=request,
        name="form/reg.jinja",
        context=UserFormContext(user=user, report_file=file).model_dump(),
    )


@router.post("/{user_id}", response_class=HTMLResponse)
async def post_account(
    user_id: int,
    templates: Templates,
    request: Request,
    session: Session,
    current_user: CurrentUser,
    form: Annotated[UserForm, Form()],
):
    if current_user.id != user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if form.role == UserRole.admin and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user = await UserRepository(session).get_one(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    error: str | None = None
    try:
        report_form: ReportForm | None = None
        file: File | None = None
        if form.report_name:
            content = await form.report_file.read()
            file = await FileRepository(session).create(
                content=content,
                name=form.report_file.filename,
                type=form.report_file.content_type,
            )

            report_form = ReportForm(
                report_name=form.report_name,
                report_type=form.report_type,
                flag_bio_phys=form.flag_bio_phys,
                flag_comp_sci=form.flag_comp_sci,
                flag_math_phys=form.flag_math_phys,
                flag_med_phys=form.flag_med_phys,
                flag_nano_tech=form.flag_nano_tech,
                flag_general_phys=form.flag_general_phys,
                flag_solid_body=form.flag_solid_body,
                flag_space_phys=form.flag_space_phys,
                file_id=file.id,
            )

        updated_user = user.model_copy(
            update={
                "email": form.email,
                "role": form.role,
                "surname": form.surname,
                "name": form.name,
                "patronymic": form.patronymic,
                "organization": form.organization,
                "year": form.year,
                "contact": form.contact,
                "form": report_form,
            }
        )

        updated_user = await UserRepository(session).update(updated_user)
    except SQLAlchemyError as e:
        error = e._message()
        logger.error(e)

    if error:
        return templates.TemplateResponse(
            request=request,
            name="form/reg.jinja",
            context=UserFormContext(user=user, error=error).model_dump(),
        )

    return templates.TemplateResponse(
        request=request,
        name="form/reg.jinja",
        context=UserFormContext(
            user=updated_user, report_file=file, error=error
        ).model_dump(),
    )


@router.get("/", response_class=HTMLResponse)
async def get_users(
    templates: Templates,
    request: Request,
    session: Session,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    users = await UserRepository(session).get()
    return templates.TemplateResponse(
        request=request,
        name="user/list.jinja",
        context=UsersContext(user=current_user, users=users).model_dump(),
    )
