from typing_extensions import Self
from typing import Optional

from pydantic import model_validator

from src.routers.files import File
from src.schemas import BaseContext

from .models import User, UserRole


class UserContext(BaseContext):
    user: Optional[User] = None


class UserFormContext(BaseContext):
    user: User
    report_file: Optional[File] = None
    roles: list[tuple[UserRole, str]] = []

    @model_validator(mode="after")
    def set_roles(self) -> Self:
        if len(self.roles) > 0:
            return self

        if self.user == UserRole.admin:
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
