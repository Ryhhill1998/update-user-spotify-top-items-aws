from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str
    db_name: str
    db_user: str
    db_pass: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
