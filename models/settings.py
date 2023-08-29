from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_INITDB_DATABASE: str
    BOT_TOKEN: str
    ADMIN_TG: str

    model_config = SettingsConfigDict(env_file='.env.dev', env_file_encoding='utf-8')

settings = Settings()
