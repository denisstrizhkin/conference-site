from io import BytesIO
from typing import Annotated, Optional
import urllib

from fastapi import APIRouter, status, HTTPException, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from openpyxl import Workbook

from src.db import Session
from src.depends import TemplateRenderer
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

user_router = APIRouter(prefix="/user")


@user_router.get("/{user_id}", response_class=HTMLResponse)
async def get_account(
    user_id: int,
    templates: TemplateRenderer,
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

    return templates.render(
        "form/reg.jinja",
        UserFormContext(
            current_user=current_user, user=user, report_file=file
        ),
    )


@user_router.post("/{user_id}", response_class=HTMLResponse)
async def post_account(
    user_id: int,
    templates: TemplateRenderer,
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

    return templates.render(
        "form/reg.jinja",
        context=UserFormContext(
            current_user=current_user,
            user=user,
            report_file=file,
            message="Анкета сохранена.",
        ),
    )


@user_router.get("/", response_class=HTMLResponse)
async def get_users(
    templates: TemplateRenderer,
    session: Session,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    users = await UserRepository(session).get()
    return templates.render(
        "user/list.jinja",
        context=UsersContext(current_user=current_user, users=users),
    )


# 3. Define the endpoint
@user_router.get("/excel/")
async def generate_excel(
    session: Session,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    users = await UserRepository(session).get()

    # Create a new Excel workbook and select the active sheet
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Участники конференции"  # Set a title for the sheet

    headers = [
        "Логин",
        "Роль",
        "Контактная информация",
        "Имя",
        "Фамилия",
        "Отчество",
        "Организация",
        "Год обучения",
        "Название доклада",
    ]

    # Write headers to the first row
    sheet.append(headers)

    # Write data rows
    for user in users:
        if user.role == UserRole.basic:
            continue

        # Extract values in the order of headers
        row_data = [
            user.email,
            "Докладчик" if user.role == UserRole.participant else "Зритель",
            user.contact,
            user.name,
            user.surname,
            user.patronymic,
            user.organization,
            user.year,
            user.form.report_name if user.form else "",
        ]

        # Append the row data to the sheet
        sheet.append(row_data)

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    file_name = urllib.parse.quote(
        "Участники 2025 студенческой конференции.xlsx".encode("utf8")
    )
    # Return the buffer content as a StreamingResponse
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{file_name}",
        },  # Suggest a filename for download
    )
