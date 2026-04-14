from sqlmodel import Field, SQLModel


class File(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(default=None, nullable=False)
    type: str = Field(default=None, nullable=False)
    content: bytes = Field(default=None, nullable=False)
