from enum import StrEnum, auto
from typing import Annotated

from sqlmodel import Column, Enum, Field, SQLModel, String, UniqueConstraint


class Reports(StrEnum):
    a = auto()
    b = auto()
    c = auto()
    d = auto()
    e = auto()
    f = auto()
    g = auto()
    h = auto()
    i = auto()
    j = auto()
    k = auto()
    l = auto()


class Vote(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("code", name="uq_vote_code"),)

    id: Annotated[int | None, Field(default=None, primary_key=True)]
    code: Annotated[
        str,
        Field(sa_column=Column(String(50), nullable=False)),
    ]
    report: Annotated[
        Reports | None,
        Field(
            default=None,
            sa_column=Column(Enum(Reports), nullable=True),
        ),
    ]
