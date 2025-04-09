from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, ReportForm

from sqlmodel import select


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, email: str) -> User:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        user: User = result.one()[0]
        if user.form is None:
            return user
        return user.model_copy(update={"form": ReportForm(**user.form)})

    async def create(self, email: str, hashed_password: str):
        user = User(email=email, password=hashed_password)
        self._session.add(user)
        await self._session.commit()
