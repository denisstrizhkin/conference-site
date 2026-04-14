from enum import StrEnum, auto
from typing import Annotated

from pydantic import BaseModel
from sqlmodel import JSON, Column, Field, SQLModel, UniqueConstraint


class ReportType(StrEnum):
    original = auto()
    scipop = auto()


class ReportFormType(StrEnum):
    classical = auto()
    nonlinear = auto()


class ReportForm(BaseModel):
    form_type: ReportFormType = Field(default=ReportFormType.classical)

    report_name: str | None = None
    report_type: ReportType | None = None

    flag_bio_phys: bool
    flag_comp_sci: bool
    flag_math_phys: bool
    flag_med_phys: bool
    flag_nano_tech: bool
    flag_general_phys: bool
    flag_solid_body: bool
    flag_space_phys: bool

    file_id: int | None = None

    work_place: str | None = None
    supervisor: str | None = None
    expected_topic: str | None = None


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

    name: Annotated[str | None, Field(default=None, nullable=True)]
    surname: Annotated[str | None, Field(default=None, nullable=True)]
    patronymic: Annotated[str | None, Field(default=None, nullable=True)]
    organization: Annotated[str | None, Field(default=None, nullable=True)]
    year: Annotated[int | None, Field(default=None, nullable=True)]
    contact: Annotated[str | None, Field(default=None, nullable=True)]

    form: Annotated[
        ReportForm | None,
        Field(default=None, sa_column=Column(JSON, nullable=True)),
    ]
