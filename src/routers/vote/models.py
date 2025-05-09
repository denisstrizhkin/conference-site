from typing import Optional, Annotated

from enum import StrEnum, auto
from sqlmodel import SQLModel, Field, Column, Enum, String


class Reports(StrEnum):
    a = auto()
    b = auto()
    c = auto()
    d = auto()
    e = auto()


class Vote(SQLModel, table=True):
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
