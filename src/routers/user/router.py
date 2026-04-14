from io import BytesIO
from typing import Annotated
import urllib

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from openpyxl import Workbook

from src.depends import TemplateRenderer
from src.routers.auth.depends import (
    allowed_id_or_roles,
    allowed_roles,
)
from src.controllers.user_controller import UserControllerDep, UserFilter
from src.routers.auth.depends import CurrentUser

from .schemas import (
    UserFormContext,
    UsersContext,
    UserForm,
)
from .models import UserRole

user_router = APIRouter(prefix="/user")


@user_router.get("/{user_id}", response_class=HTMLResponse)
async def get_account(
    user_id: int,
    templates: TemplateRenderer,
    user_controller: UserControllerDep,
    current_user: CurrentUser,
):
    allowed_id_or_roles(current_user, user_id, [UserRole.admin])
    user, file = await user_controller.get_user_with_file(UserFilter(id=user_id))
    return templates.render(
        "form/reg.jinja",
        UserFormContext(current_user=current_user, user=user, report_file=file),
    )


@user_router.post("/{user_id}", response_class=HTMLResponse)
async def post_account(
    user_id: int,
    templates: TemplateRenderer,
    user_controller: UserControllerDep,
    current_user: CurrentUser,
    form: Annotated[UserForm, Form()],
):
    allowed_id_or_roles(current_user, user_id, [UserRole.admin])
    user, file = await user_controller.update_from_user_form(current_user, form)
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
    user_controller: UserControllerDep,
    current_user: CurrentUser,
):
    allowed_roles(current_user, [UserRole.admin])
    users = await user_controller.get()
    return templates.render(
        "user/list.jinja",
        context=UsersContext(current_user=current_user, users=users),
    )


@user_router.post("/{user_id}/delete", response_class=HTMLResponse)
async def delete_user(
    user_id: int,
    templates: TemplateRenderer,
    user_controller: UserControllerDep,
    current_user: CurrentUser,
):
    allowed_roles(current_user, [UserRole.admin])
    user = await user_controller.delete(user_id)
    user_name = f"{user.surname or ''} {user.name or ''}".strip() or user.email
    users = await user_controller.get()
    return templates.render(
        "user/list.jinja",
        context=UsersContext(
            current_user=current_user,
            users=users,
            message=f"Пользователь удален {user_name}",
        ),
    )


# 3. Define the endpoint
@user_router.get("/excel/")
async def generate_excel(
    user_controller: UserControllerDep,
    current_user: CurrentUser,
):
    allowed_roles(current_user, [UserRole.admin])
    users = await user_controller.get()

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
        "Тип доклада",
        "Название доклада",
        "Предполагаемая тема",
        "Место работы",
        "Научный руководитель",
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
            "Классический"
            if user.form and user.form.form_type == "classical"
            else "Нелинейный"
            if user.form
            else "",
            user.form.report_name
            if user.form and user.form.form_type == "classical"
            else "",
            user.form.expected_topic
            if user.form and user.form.form_type == "nonlinear"
            else "",
            user.form.work_place
            if user.form and user.form.form_type == "nonlinear"
            else "",
            user.form.supervisor
            if user.form and user.form.form_type == "nonlinear"
            else "",
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
