from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "AgentFlow API"
    secret_key: str = "change_me"
    openapi_url: str = "/openapi.json"
    database_url: str
    redis_url: str
    qdrant_url: str
    r2r_base_url: str = "http://localhost:7272"
    r2r_api_key: str | None = None

@lru_cache()
def get_settings() -> Settings:
    return Settings()
