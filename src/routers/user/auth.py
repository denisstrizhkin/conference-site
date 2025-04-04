from typing import Annotated
from datetime import datetime, timedelta
import json
import logging

from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, Request
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from .models import User
from src.db import AsyncSession
from src.settings import settings


class PassHasher:
    _context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return PassHasher._context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return PassHasher._context.hash(password)


class Token(BaseModel):
    user: User
    expires: datetime


def create_access_token(user: User) -> tuple[str, datetime]:
    expires = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    token = Token(user=user, expires=expires)
    to_encode = token.model_dump_json()
    to_encode = json.loads(to_encode)
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, expires


async def get_current_user(
    request: Request,
    session: AsyncSession,
) -> User | None:
    token = request.cookies.get("access_token")
    if token is None:
        logging.error("no access token provided")
        return None

    try:
        payload = jwt.decode(
            token[7:], settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        token = Token(**payload)
        user = token.user
    except JWTError as e:
        logging.error(e)
        return None

    logging.error(user)
    try:
        stmt = select(User).where(User.email == user.email)
        async with session() as session:
            result = await session.execute(stmt)
            user = result.one()[0]
    except SQLAlchemyError as e:
        logging.error(e)
        return None

    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]
