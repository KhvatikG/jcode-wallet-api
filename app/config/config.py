from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv('.env')


class Settings(BaseSettings):
    """
    Конфигурация приложения
    """

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    DB_POOL_SIZE: int = 500
    DB_MAX_OVERFLOW: int = 500
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800


    # Загрузка переменных окружения из файла .env
    model_config = SettingsConfigDict(
        env_file='../../.env'
    )

    @property
    def get_db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# Экземпляр конфигурации
settings = Settings()
