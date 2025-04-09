from typing import Annotated, Any
import logging

import fastapi
from fastapi import (
    APIRouter,
    status,
    Request,
    Form,
    UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select, update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.db import Session
from src.depends import Templates
from src.routers.files.repo import FileRepository
from src.routers.files.models import File

from .repo import UserRepository
from .models import User, UserRole, ReportType, ReportForm
from .auth import create_access_token, CurrentUser, PassHasher

logger = logging.getLogger(__name__)

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
    session: Session,
    templates: Templates,
):
    error: str | None = None
    try:
        user = await UserRepository(session).get(email)
    except SQLAlchemyError as e:
        error = e._message()
        logger.error(e)

    if user is None:
        error = "Такого пользователя не сущевствует"
    if user and not PassHasher.verify_password(password, user.password):
        error = "Неправильная почта или пароль"

    if error is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU", "error": error},
        )

    token, expires = create_access_token(user.email)

    # Set cookie with token
    response = RedirectResponse(
        url="/user/account", status_code=status.HTTP_303_SEE_OTHER
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


def generate_roles_list(current_role: UserRole) -> list[tuple[UserRole, str]]:
    if current_role == UserRole.admin:
        return [
            (UserRole.admin, "Админ"),
        ]
    else:
        return [
            (UserRole.basic, "Не учавствую"),
            (UserRole.viewer, "Без доклада"),
            (UserRole.participant, "С докладом"),
        ]


def account_context(
    user: User, report_file: File | None = None, error: str | None = None
) -> dict[Any, Any]:
    return {
        "title": "StudConfAU",
        "error": error,
        "user": user,
        "report_file": report_file,
        "roles": generate_roles_list(user.role),
    }


@router.get("/account", response_class=HTMLResponse)
async def get_account(
    templates: Templates,
    request: Request,
    session: Session,
    current_user: CurrentUser,
):
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU"},
        )

    file: File | None = None
    if current_user.form:
        file = await FileRepository(session).get(current_user.form.file_id)

    return templates.TemplateResponse(
        request=request,
        name="form/reg.jinja",
        context=account_context(current_user, file),
    )


@router.post("/account", response_class=HTMLResponse)
async def post_account(
    # Request stuff
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
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU"},
        )
    logger.error(current_user)

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

        updated_user = current_user.model_copy(
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
            context=account_context(current_user, error),
        )

    return templates.TemplateResponse(
        request=request,
        name="form/reg.jinja",
        context=account_context(updated_user, file, error),
    )


@router.get("/", response_class=HTMLResponse)
async def get_users(
    templates: Templates,
    request: Request,
    session: Session,
    current_user: CurrentUser,
):
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU"},
        )

    result = await session.execute(select(User))
    users = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="user/list.jinja",
        context={"title": "StudConfAU", "users": users},
    )
