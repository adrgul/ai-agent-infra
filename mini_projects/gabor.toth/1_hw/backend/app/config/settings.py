from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    openai_api_key: str = ""
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Dinamikus data_dir - működik bármelyik mappából
    data_dir: str = os.getenv(
        "DATA_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "data")
    )
    max_history_entries: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
