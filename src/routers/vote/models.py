from typing import Optional, Annotated

from enum import StrEnum, auto
from sqlmodel import SQLModel, Field, Column, Enum, String, UniqueConstraint


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

    id: Annotated[Optional[int], Field(default=None, primary_key=True)]
    code: Annotated[
        str,
        Field(sa_column=Column(String(50), nullable=False)),
    ]
    report: Annotated[
        Optional[Reports],
        Field(
            default=None,
            sa_column=Column(Enum(Reports), nullable=True),
        ),
    ]
