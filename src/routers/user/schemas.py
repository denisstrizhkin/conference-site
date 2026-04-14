from typing_extensions import Self
from typing import Optional

from fastapi import UploadFile
from pydantic import BaseModel, model_validator

from src.routers.files.models import File
from src.schemas import BaseContext

from .models import User, UserRole, ReportType, ReportFormType


class UserForm(BaseModel):
    # User data
    role: UserRole
    email: str
    surname: str
    name: str
    patronymic: Optional[str] = None
    organization: str
    year: int
    contact: str

    # Report Form
    form_type: Optional[ReportFormType] = None

    # Classical fields
    report_name: Optional[str] = None
    report_type: Optional[ReportType] = None

    # Common flags
    flag_bio_phys: bool = False
    flag_comp_sci: bool = False
    flag_math_phys: bool = False
    flag_med_phys: bool = False
    flag_nano_tech: bool = False
    flag_general_phys: bool = False
    flag_solid_body: bool = False
    flag_space_phys: bool = False
    report_file: Optional[UploadFile] = None

    # Nonlinear fields
    work_place: Optional[str] = None
    supervisor: Optional[str] = None
    expected_topic: Optional[str] = None

    @model_validator(mode="after")
    def validate_form_type_fields(self) -> Self:
        if self.role == UserRole.participant:
            if self.form_type == ReportFormType.classical:
                self.work_place = None
                self.supervisor = None
                self.expected_topic = None
            elif self.form_type == ReportFormType.nonlinear:
                self.report_name = None
                self.report_type = None
        else:
            self.form_type = None
            self.report_name = None
            self.report_type = None
            self.work_place = None
            self.supervisor = None
            self.expected_topic = None
        return self


class UserContext(BaseContext):
    current_user: Optional[User] = None


class UsersContext(UserContext):
    users: list[User]


class UserFormContext(BaseContext):
    current_user: User
    user: User
    report_file: Optional[File] = None
    roles: list[tuple[UserRole, str]] = []

    @model_validator(mode="after")
    def set_roles(self) -> Self:
        if len(self.roles) > 0:
            return self

        if self.user.role == UserRole.admin:
            self.roles = [
                (UserRole.admin, "Админ"),
            ]
        else:
            self.roles = [
                (UserRole.basic, "Не участвую"),
                (UserRole.viewer, "Без доклада"),
                (UserRole.participant, "Доклад"),
            ]

        return self
