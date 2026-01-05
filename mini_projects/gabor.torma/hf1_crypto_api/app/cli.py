import sys
from app.services import CryptoPriceProvider

class CryptoCLI:
    """
    Handles user interaction.
    Follows SRP: Responsible only for UI/CLI logic.
    Follows DIP: Depends on the CryptoPriceProvider abstraction, not a concrete class.
    """
    def __init__(self, price_provider: CryptoPriceProvider):
        self.price_provider = price_provider

    def start(self):
        print("Welcome to the Crypto Price Checker!")
        print("Type a cryptocurrency ID (e.g., 'bitcoin', 'ethereum') to get the price.")
        print("Type 'exit' or 'quit' to stop.")
        print("-" * 50)

        while True:
            try:
                user_input = input("\nEnter crypto ID: ").strip()
                
                if user_input.lower() in ('exit', 'quit'):
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue

                self._handle_request(user_input)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                sys.exit(0)

    def _handle_request(self, crypto_id: str):
        print(f"Fetching price for '{crypto_id}'...")
        price = self.price_provider.get_price(crypto_id)
        
        if price is not None:
            print(f"Current price of {crypto_id}: ${price:,.2f}")
        else:
            print(f"Could not find price for '{crypto_id}'. Please check the ID and try again.")
