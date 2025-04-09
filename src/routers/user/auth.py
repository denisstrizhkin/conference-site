from typing import Annotated
from datetime import datetime, timedelta
import json
import logging

from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, Request
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from src.db import Session
from src.settings import settings

from .models import User
from .repo import UserRepository

logger = logging.getLogger(__name__)


class PassHasher:
    _context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return PassHasher._context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return PassHasher._context.hash(password)


class Token(BaseModel):
    email: str
    expires: datetime


def create_access_token(email: str) -> tuple[str, int]:
    expires = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    token = Token(email=email, expires=expires)
    to_encode = token.model_dump_json()
    to_encode = json.loads(to_encode)
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, settings.jwt_expire_minutes * 60


async def get_current_user(
    request: Request,
    session: Session,
) -> User | None:
    access_token = request.cookies.get("access_token")
    if access_token is None:
        logger.error("no access token provided")
        return None

    try:
        payload = jwt.decode(
            access_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        token = Token(**payload)
    except JWTError as e:
        logger.error(e)
        return None

    try:
        user = await UserRepository(session).get(token.email)
    except SQLAlchemyError as e:
        logger.error(e)
        return None

    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]
