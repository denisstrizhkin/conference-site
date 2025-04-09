from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, ReportForm

from sqlmodel import select


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        user: User = result.scalar_one_or_none()
        if user and user.form:
            return user.model_copy(update={"form": ReportForm(**user.form)})
        return user

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, password=hashed_password)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user
