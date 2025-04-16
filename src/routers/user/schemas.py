from typing_extensions import Self
from typing import Optional

from fastapi import UploadFile
from pydantic import BaseModel, model_validator

from src.routers.files import File
from src.schemas import BaseContext

from .models import User, UserRole, ReportType


class LoginForm(BaseModel):
    email: str
    password: str


class RegisterForm(LoginForm): ...


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
    report_name: Optional[str] = None
    report_type: Optional[ReportType] = None
    flag_bio_phys: bool = False
    flag_comp_sci: bool = False
    flag_math_phys: bool = False
    flag_med_phys: bool = False
    flag_nano_tech: bool = False
    flag_general_phys: bool = False
    flag_solid_body: bool = False
    flag_space_phys: bool = False
    report_file: Optional[UploadFile] = None


class UserContext(BaseContext):
    user: Optional[User] = None


class UsersContext(UserContext):
    users: list[User]


class UserFormContext(BaseContext):
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
                (UserRole.participant, "С докладом"),
            ]

        return self
