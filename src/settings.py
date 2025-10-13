from typing import Type
from pathlib import Path
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    echo_sql: bool
    show_docs: bool
    db_uri: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data.db'}"
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int

    model_config = SettingsConfigDict(
        toml_file=BASE_DIR / "settings.toml",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
