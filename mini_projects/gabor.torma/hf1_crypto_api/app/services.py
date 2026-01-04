from abc import ABC, abstractmethod
import requests
from typing import Optional
from app.config import Config

class CryptoPriceProvider(ABC):
    """
    Abstract Base Class for Crypto Price Providers.
    Follows OCP: New providers can be added without changing the consumer code.
    Follows ISP: Clients only see the methods they need.
    """
    @abstractmethod
    def get_price(self, crypto_id: str) -> Optional[float]:
        """Fetches the current price of the cryptocurrency in USD."""
        pass

class CoinGeckoService(CryptoPriceProvider):
    """
    Concrete implementation using CoinGecko API.
    Follows LSP: Can be substituted for any CryptoPriceProvider.
    Follows SRP: Responsible only for fetching data from CoinGecko.
    """
    def __init__(self, config: Config):
        self.api_url = config.API_URL
        self.timeout = config.TIMEOUT

    def get_price(self, crypto_id: str) -> Optional[float]:
        try:
            # CoinGecko expects lowercase ids, e.g., 'bitcoin'
            clean_id = crypto_id.lower().strip()
            url = f"{self.api_url}/{clean_id}"
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            price_usd = data.get("data", {}).get("priceUsd")
            
            if price_usd:
                return float(price_usd)
            return None
            
        except requests.RequestException as e:
            # In a real app, we might log this
            print(f"Error fetching price: {e}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Error parsing response: {e}")
            return None

class CoinGeckoService(CryptoPriceProvider):
    """
    Concrete implementation using CoinGecko API.
    Follows LSP: Can be substituted for any CryptoPriceProvider.
    """
    def __init__(self, config: Config):
        self.api_url = config.API_URL
        self.timeout = config.TIMEOUT

    def get_price(self, crypto_id: str) -> Optional[float]:
        try:
            clean_id = crypto_id.lower().strip()
            # CoinGecko uses query parameters: ?ids=bitcoin&vs_currencies=usd
            params = {
                "ids": clean_id,
                "vs_currencies": "usd"
            }
            
            response = requests.get(self.api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            # Response format: {"bitcoin": {"usd": 12345.67}}
            if clean_id in data and "usd" in data[clean_id]:
                return float(data[clean_id]["usd"])
            return None
            
        except requests.RequestException as e:
            print(f"Error fetching price: {e}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Error parsing response: {e}")
            return None
