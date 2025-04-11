from typing import Annotated
import logging

import fastapi
from fastapi import APIRouter, status, Request, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.schemas import BaseContext
from src.db import Session
from src.depends import Templates
from src.routers.files.repo import FileRepository
from src.routers.files.models import File

from .schemas import UserFormContext, UsersContext
from .repo import UserRepository
from .models import User, ReportType, ReportForm, UserRole
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
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: Session,
    templates: Templates,
):
    error: str | None = None
    try:
        await UserRepository(session).create(
            email, PassHasher.get_password_hash(password)
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
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: Session,
    templates: Templates,
):
    error: str | None = None
    try:
        user = await UserRepository(session).get_one(email=email)
    except SQLAlchemyError as e:
        error = e._message()
        logger.error(e)

    if user is None:
        error = "Такого пользователя не существует"
    if user and not PassHasher.verify_password(password, user.password):
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
    # Request stuff
    user_id: int,
    templates: Templates,
    request: Request,
    session: Session,
    current_user: CurrentUser,
    # User
    role: Annotated[str, Form()],
    email: Annotated[str, Form()],
    surname: Annotated[str, Form()],
    name: Annotated[str, Form()],
    patronymic: Annotated[str, Form()],
    organization: Annotated[str, Form()],
    year: Annotated[int, Form()],
    contact: Annotated[str, Form()],
    # Report Form
    report_name: Annotated[str | None, Form()] = None,
    report_type: Annotated[ReportType | None, Form()] = None,
    flag_bio_phys: Annotated[bool, Form()] = False,
    flag_comp_sci: Annotated[bool, Form()] = False,
    flag_math_phys: Annotated[bool, Form()] = False,
    flag_med_phys: Annotated[bool, Form()] = False,
    flag_nano_tech: Annotated[bool, Form()] = False,
    flag_general_phys: Annotated[bool, Form()] = False,
    flag_solid_body: Annotated[bool, Form()] = False,
    flag_space_phys: Annotated[bool, Form()] = False,
    report_file: Annotated[UploadFile | None, fastapi.File(...)] = None,
):
    if current_user.id != user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if role == UserRole.admin and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user = await UserRepository(session).get_one(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    error: str | None = None
    try:
        report_form: ReportForm | None = None
        file: File | None = None
        if report_name:
            content = await report_file.read()
            file = await FileRepository(session).create(
                content=content,
                name=report_file.filename,
                type=report_file.content_type,
            )

            report_form = ReportForm(
                report_name=report_name,
                report_type=report_type,
                flag_bio_phys=flag_bio_phys,
                flag_comp_sci=flag_comp_sci,
                flag_math_phys=flag_math_phys,
                flag_med_phys=flag_med_phys,
                flag_nano_tech=flag_nano_tech,
                flag_general_phys=flag_general_phys,
                flag_solid_body=flag_solid_body,
                flag_space_phys=flag_space_phys,
                file_id=file.id,
            )

        updated_user = user.model_copy(
            update={
                "email": email,
                "role": role,
                "surname": surname,
                "name": name,
                "patronymic": patronymic,
                "organization": organization,
                "year": year,
                "contact": contact,
                "form": report_form,
            }
        )

        stmt = (
            update(User)
            .where(User.id == updated_user.id)
            .values(**updated_user.model_dump())
        )
        await session.execute(stmt)
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
        context=UsersContext(users=users).model_dump(),
    )
