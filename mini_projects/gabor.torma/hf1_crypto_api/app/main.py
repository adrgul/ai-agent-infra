import sys
import os

# Add the project root to the python path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.services import CoinGeckoService, CoinGeckoService
from app.cli import CryptoCLI

def main():
    """
    Main entry point.
    Follows DIP: Injects dependencies (Config, Service) into the CLI.

    Usage Instructions:
    -------------------
    1. Build the Docker image:
       docker build -t crypto-demo .

    2. Run the container with the env file:
       docker run -it --env-file .env crypto-demo

       # If you encounter DNS/Connection errors:
       docker run -it --env-file .env --dns 8.8.8.8 crypto-demo
    """
    # 1. Load Configuration
    config = Config.load()

    # 2. Initialize Service (Dependency Injection)
    # Switched to CoinGeckoService as requested
    price_service = CoinGeckoService(config)

    # 3. Initialize CLI with the service
    app = CryptoCLI(price_service)

    # 4. Run the application
    app.start()

if __name__ == "__main__":
    main()
