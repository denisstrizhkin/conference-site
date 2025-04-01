from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(default=None, nullable=False)
    password: str = Field(default=None, nullable=False)
