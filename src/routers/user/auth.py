from typing import Annotated
from datetime import datetime, timedelta
import json
import logging

from jose import jwt, JWTError
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from .models import User
from src.db import AsyncSession
from src.settings import settings

oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    user: User
    expires: datetime


def create_access_token(user: User) -> tuple[str, datetime]:
    expires = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode = Token(user=user, expires=expires).model_dump_json()
    to_encode = json.loads(to_encode)
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, expires


def decode_token(token: str) -> User:
    return User(id=0, email="rika@example.com", password="huika")


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
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        logging.info(payload)
        user = payload.user
    except JWTError as e:
        logging.error(e)
        return None

    try:
        stmt = select(User).where(
            User.email == user.email, User.password == user.password
        )
        async with session() as session:
            result = await session.execute(stmt)
            user = result.first()
    except SQLAlchemyError as e:
        logging.error(e)
        return None

    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]
