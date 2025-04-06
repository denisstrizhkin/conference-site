from typing import Annotated, Any
import logging

from fastapi import (
    APIRouter,
    status,
    Request,
    Form,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select, update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound

from src.db import AsyncSession
from src.depends import Templates
from .models import User, UserRole, ReportType
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
    session: AsyncSession,
    templates: Templates,
):
    user = User(email=email, password=PassHasher.get_password_hash(password))

    error: str | None = None
    try:
        async with session() as session:
            session.add(user)
            await session.commit()
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
    session: AsyncSession,
    templates: Templates,
):
    stmt = select(User).where(User.email == email)
    error: str | None = None
    try:
        async with session() as session:
            result = await session.execute(stmt)
            user = result.one()[0]

        if not PassHasher.verify_password(password, user.password):
            error = "Неправильная почта или пароль"
    except NoResultFound as e:
        error = "Такого пользователя не сущевствует"
        logger.error(e)
    except SQLAlchemyError as e:
        error = e._message()
        logger.error(e)

    if error is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU", "error": error},
        )

    token, expires = create_access_token(user)

    # Set cookie with token
    response = RedirectResponse(
        url="/user/account", status_code=status.HTTP_303_SEE_OTHER
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
            (UserRole.viewer, "Зритель"),
            (UserRole.participant, "Участник"),
        ]


def account_context(user: User, error: str | None = None) -> dict[Any, Any]:
    return {
        "title": "StudConfAU",
        "error": error,
        "user": user,
        "roles": generate_roles_list(user.role),
    }


@router.get("/account", response_class=HTMLResponse)
async def get_account(
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

    return templates.TemplateResponse(
        request=request,
        name="form/reg.jinja",
        context=account_context(current_user),
    )


@router.post("/account", response_class=HTMLResponse)
async def post_account(
    # Request stuff
    templates: Templates,
    request: Request,
    session: AsyncSession,
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
    flag_nano_tech: Annotated[bool, Form()] = False,
    flag_general_phys: Annotated[bool, Form()] = False,
    flag_solid_body: Annotated[bool, Form()] = False,
    flag_space_phys: Annotated[bool, Form()] = False,
):
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU"},
        )
    logger.error(current_user)

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
        }
    )

    error: str | None = None
    try:
        async with session() as session:
            stmt = (
                update(User)
                .where(User.id == updated_user.id)
                .values(**updated_user.model_dump())
            )
            await session.execute(stmt)
            await session.commit()
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
        context=account_context(updated_user, error),
    )


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
