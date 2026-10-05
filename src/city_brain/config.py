from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql://citybrain:citybrain@localhost:5432/citybrain"
    redis_url: str = "redis://localhost:6379/0"
    guardian_url: str = "http://localhost:8001"
    trust_threshold: float = 0.7
    twin_url: str = "http://localhost:8002"
    log_level: str = "INFO"


settings = Settings()
