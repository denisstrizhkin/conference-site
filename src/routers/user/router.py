from typing import Annotated, Optional

from fastapi import APIRouter, status, Request, HTTPException, Form
from fastapi.responses import HTMLResponse

from src.db import Session
from src.depends import render_template
from src.routers.auth.depends import CurrentUser
from src.routers.files.repo import FileRepository
from src.routers.files.models import File

from .schemas import (
    UserFormContext,
    UsersContext,
    UserForm,
)
from .repo import UserRepository
from .models import ReportForm, UserRole

router = APIRouter(prefix="/user")


@router.get("/{user_id}", response_class=HTMLResponse)
async def get_account(
    user_id: int,
    request: Request,
    session: Session,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.admin:
        if current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user = await UserRepository(session).get_one_or_none(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    file: Optional[File] = None
    if user.form:
        file = await FileRepository(session).get_one(user.form.file_id)

    return render_template(
        request,
        "form/reg.jinja",
        UserFormContext(
            current_user=current_user, user=user, report_file=file
        ),
    )


@router.post("/{user_id}", response_class=HTMLResponse)
async def post_account(
    user_id: int,
    request: Request,
    session: Session,
    current_user: CurrentUser,
    form: Annotated[UserForm, Form()],
):
    if current_user.role != UserRole.admin:
        if current_user.id != user_id or form.role == UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user_repo = UserRepository(session)
    file_repo = FileRepository(session)
    user = await user_repo.get_one(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if user.form:
        await file_repo.delete(user.form.file_id)

    file: Optional[File] = None
    report_form: Optional[ReportForm] = None
    if form.report_name:
        content = await form.report_file.read()
        file = File(
            name=form.report_file.filename,
            type=form.report_file.content_type,
            content=content,
        )
        file = await file_repo.create(file)
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

    user = user.model_copy(
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
    user = await user_repo.update(user)

    return render_template(
        request,
        "form/reg.jinja",
        context=UserFormContext(
            current_user=current_user,
            user=user,
            report_file=file,
            message="Анкета сохранена.",
        ),
    )


@router.get("/", response_class=HTMLResponse)
async def get_users(
    request: Request,
    session: Session,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    users = await UserRepository(session).get()
    return render_template(
        request,
        "user/list.jinja",
        context=UsersContext(current_user=current_user, users=users),
    )
