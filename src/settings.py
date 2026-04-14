import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Self, get_type_hints

BASE_DIR = Path(__file__).parent.parent


def get_env_file(name: str) -> str | None:
    value_path = os.environ.get(f"{name}_FILE")
    if value_path is None:
        return None
    with open(value_path) as f:
        return f.read().strip()


def get_env(name: str) -> str | None:
    value = get_env_file(name)
    if value is None:
        return os.environ.get(name)
    return value


def get_env_var[T](
    name: str, cast_type: type[T] = str, default: T | None = None
) -> T:
    value = get_env(name)
    if value is None and default is None:
        raise ValueError(f"Environment variable {name} is not set")
    if value is None:
        return default
    if cast_type is bool:
        if value == "True":
            return True
        if value == "False":
            return False
        raise ValueError(f"Invalid boolean value: {value}")
    return cast_type(value)


@dataclass(frozen=True)
class Settings:
    jwt_secret: str = "123456"
    admin_password: str = "password"
    echo_sql: bool = True
    show_docs: bool = True
    secure_cookies: bool = False
    db_uri: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data.db'}"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    @classmethod
    def load(cls) -> Self:
        hints = get_type_hints(cls)
        args = dict()
        for field in fields(cls):
            name = field.name.upper()
            value = get_env_var(name, hints[field.name], field.default)
            args[field.name] = value
        return cls(**args)


settings = Settings.load()

if __name__ == "__main__":
    print(settings)
