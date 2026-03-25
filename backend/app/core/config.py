from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Quantum Planet Simulator API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"


settings = Settings()

