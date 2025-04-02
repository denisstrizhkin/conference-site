from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from .models import User

oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")


def decode_token(token: str) -> User:
    return User(id=0, email="rika@example.com", password="huika")


async def get_current_user(token: Annotated[str, Depends(oauth2_schema)]) -> User:
    user = decode_token(token)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
