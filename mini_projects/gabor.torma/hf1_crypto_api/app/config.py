import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """
    Application configuration.
    Follows SRP: Responsible only for providing configuration values.
    """
    API_URL: str = os.getenv("API_URL", "https://api.coingecko.com/api/v3/simple/price")
    API_KEY: str = os.getenv("API_KEY", "")  # Optional for some public APIs, but good practice to have
    TIMEOUT: int = int(os.getenv("TIMEOUT", "10"))

    @classmethod
    def load(cls) -> "Config":
        return cls()
