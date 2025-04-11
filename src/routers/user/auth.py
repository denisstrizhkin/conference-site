from typing import Annotated, Optional
from datetime import datetime, timedelta
import json
import logging

from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, Request, HTTPException, status
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
    id: int
    expires: datetime


def create_access_token(id: int) -> tuple[str, int]:
    expires = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    token = Token(id=id, expires=expires)
    to_encode = token.model_dump_json()
    to_encode = json.loads(to_encode)
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, settings.jwt_expire_minutes * 60


async def get_current_user_or_none(
    request: Request,
    session: Session,
) -> Optional[User]:
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
        user = await UserRepository(session).get(token.id)
    except SQLAlchemyError as e:
        logger.error(e)
        return None

    return user


CurrentUserOrNone = Annotated[Optional[User], Depends(get_current_user_or_none)]


async def get_current_user(
    request: Request, session: Session, current_user: CurrentUserOrNone
) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
