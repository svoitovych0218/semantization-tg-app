from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    BOT_TOKEN: str
    WEBHOOK_URL: str
    ADMIN_KEY: str
    MINI_APP_URL: str

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
