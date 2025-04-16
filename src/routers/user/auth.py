from typing import Annotated, Optional
from datetime import datetime, timedelta

from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, Request, HTTPException, status
from pydantic import BaseModel, ValidationError

from src.db import Session
from src.settings import settings

from .models import User
from .repo import UserRepository


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
    to_encode = token.model_dump(mode="json")
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, settings.jwt_expire_minutes * 60


async def get_current_user(
    request: Request,
    session: Session,
) -> User:
    access_token = request.cookies.get("access_token")
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access token provided.",
        )

    try:
        payload = jwt.decode(
            access_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        token = Token.model_validate(payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode the token.",
        )

    user = await UserRepository(session).get_one(id=token.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist.",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_or_none(
    request: Request,
    session: Session,
) -> Optional[User]:
    try:
        return await get_current_user(request, session)
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


CurrentUserOrNone = Annotated[User, Depends(get_current_user_or_none)]
