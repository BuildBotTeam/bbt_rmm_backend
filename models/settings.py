from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_INITDB_DATABASE: str
    BOT_TOKEN: str
    HOST: str
    ADMIN_TG: str
    DB_ADMIN_USERNAME: str
    DB_ADMIN_EMAIL: str
    DB_ADMIN_PASSWORD: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
