"""Runtime configuration, loaded from environment / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Storage
    database_url: str = "postgresql://citybrain:citybrain@localhost:5433/citybrain"
    redis_url: str = "redis://localhost:6380/0"

    # Guardian
    guardian_url: str = "http://localhost:8001"
    trust_threshold: float = 0.7

    # Twin
    twin_url: str = "http://localhost:8002"

    # Redis Streams consumer
    consumer_group: str = "city-brain"
    consumer_name: str = "city-brain-1"
    sensor_stream: str = "sensors.readings"

    # Decision model (new in step B)
    model_path: str = "models/city_brain_v1.pkl"
    model_confidence_threshold: float = 0.6

    log_level: str = "INFO"


settings = Settings()