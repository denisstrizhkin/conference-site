from typing import Annotated

from enum import StrEnum, auto
from sqlmodel import SQLModel, Field, UniqueConstraint, JSON, Column
from pydantic import BaseModel


class ReportType(StrEnum):
    original = auto()
    scipop = auto()


class ReportForm(BaseModel):
    report_name: str
    report_type: ReportType = Field(default=ReportType.original)

    flag_bio_phys: bool
    flag_comp_sci: bool
    flag_math_phys: bool
    flag_med_phys: bool
    flag_nano_tech: bool
    flag_general_phys: bool
    flag_solid_body: bool
    flag_space_phys: bool

    content: bytes
    content_type: str


class UserRole(StrEnum):
    admin = auto()
    basic = auto()
    participant = auto()
    viewer = auto()


class User(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    id: int = Field(default=None, primary_key=True)
    email: str = Field(default=None, nullable=False)
    password: str = Field(default=None, nullable=False)
    role: UserRole = Field(
        default=UserRole.basic,
        nullable=False,
        sa_column_kwargs={"server_default": UserRole.basic},
    )

    name: Annotated[str, Field(default=None, nullable=True)]
    surname: Annotated[str, Field(default=None, nullable=True)]
    patronymic: Annotated[str, Field(default=None, nullable=True)]
    organization: Annotated[str, Field(default=None, nullable=True)]
    year: Annotated[int, Field(default=None, nullable=True)]
    contact: Annotated[str, Field(default=None, nullable=True)]

    form: Annotated[
        ReportForm,
        Field(default=None, sa_column=Column(JSON, nullable=True)),
    ]
