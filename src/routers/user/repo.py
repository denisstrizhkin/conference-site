from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from src.routers.files.models import File
from src.routers.files.repo import FileRepository

from .models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_one(
        self, id: Optional[int] = None, email: Optional[str] = None
    ) -> Optional[User]:
        stmt = select(User)
        if id:
            stmt = stmt.where(User.id == id)
        if email:
            stmt = stmt.where(User.email == email)
        result = await self._session.execute(stmt)
        user: Optional[User] = result.scalar_one_or_none()
        if user is None:
            return None
        return User.model_validate(user)

    async def get(self) -> list[User]:
        stmt = select(User)
        result = await self._session.execute(stmt)
        return [User.model_validate(user) for user in result.scalars().all()]

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, password=hashed_password)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return User.model_validate(user)

    async def update(
        self, user: User, new_user: User, new_file: Optional[File]
    ) -> User:
        file_repo = FileRepository(self._session)
        if user.form:
            await file_repo.delete(user.form.file_id)
        if new_user.form:
            new_file = await file_repo.create(new_file)
            new_user = new_user.model_copy(
                update={
                    "form": new_user.form.model_copy(
                        update={"file_id": new_file.id}
                    )
                }
            )
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(**new_user.model_dump())
        )
        await self._session.execute(stmt)
        return await self.get_one(user.id)
