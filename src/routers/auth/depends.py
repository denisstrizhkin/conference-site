from datetime import datetime, timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import ValidationError

from src.controllers.user_controller import UserControllerDep, UserFilter
from src.routers.user.models import User, UserRole
from src.settings import settings

from .models import Token


class PassHasher:
    ph = PasswordHasher()

    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        try:
            PassHasher.ph.verify(hash, password)
            return True
        except VerifyMismatchError:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        return PassHasher.ph.hash(password)


def create_access_token(id: int) -> tuple[str, int]:
    expires = datetime.utcnow() + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    token = Token(id=id, expires=expires)
    to_encode = token.model_dump(mode="json")
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, settings.jwt_expire_minutes * 60


async def get_current_user(
    request: Request,
    user_controller: UserControllerDep,
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
    except (JWTError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode the token.",
        ) from err
    user = await user_controller.get_one_or_none(UserFilter(id=token.id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist.",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_or_none(
    request: Request,
    user_controller: UserControllerDep,
) -> User | None:
    try:
        return await get_current_user(request, user_controller)
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


CurrentUserOrNone = Annotated[User, Depends(get_current_user_or_none)]


def allowed_id_or_roles(
    current_user: User, user_id: int | None, roles: list[UserRole]
):
    is_allowed = current_user.role in roles or current_user.id == user_id
    if not is_allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


def allowed_id(current_user: User, user_id: int):
    allowed_id_or_roles(current_user, user_id, [])


def allowed_roles(current_user: User, roles: list[UserRole]):
    allowed_id_or_roles(current_user, None, roles)
