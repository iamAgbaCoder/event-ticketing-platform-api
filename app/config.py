from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/eventdb"
    database_url_sync: str = "postgresql://postgres:postgres@db:5432/eventdb"

    # Redis/Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # Application
    app_name: str = "Event Ticketing API"
    debug: bool = True

    # Ticket expiration (in seconds)
    ticket_reservation_timeout: int = 120  # 2 minutes

    # Geospatial
    default_search_radius_km: float = 50.0  # 50km radius for event search


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# settings = get_settings()
