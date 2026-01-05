# Crypto Price CLI

A minimal, SOLID-compliant Python CLI application to check cryptocurrency prices using the CoinGecko API.

## Project Structure

```
.
├── Dockerfile
├── requirements.txt
├── .env.example
└── app
    ├── __init__.py
    ├── main.py       # Entry point, wiring dependencies
    ├── config.py     # Configuration management
    ├── cli.py        # User interface logic
    └── services.py   # Business logic and API integration
```

## Architecture & SOLID Principles

This project demonstrates SOLID principles in Python:

- **SRP (Single Responsibility Principle)**:
  - `Config` handles configuration.
  - `CoinGeckoService` handles API requests.
  - `CryptoCLI` handles user interaction.
- **OCP (Open/Closed Principle)**:
  - `CryptoPriceProvider` is an abstract base class. New providers (e.g., Binance) can be added without modifying the CLI or App logic.
- **LSP (Liskov Substitution Principle)**:
  - `CoinGeckoService` can be substituted for any `CryptoPriceProvider`.
- **ISP (Interface Segregation Principle)**:
  - The `CryptoPriceProvider` interface is focused and minimal.
- **DIP (Dependency Inversion Principle)**:
  - `CryptoCLI` depends on the `CryptoPriceProvider` abstraction, not the concrete `CoinGeckoService`. Dependencies are injected in `main.py`.

## Installation & Usage

### Prerequisites

- Docker installed on your machine.
- Or Python 3.11+ if running locally.

### Running with Docker

1. **Build the Docker image:**

   ```bash
   docker build -t crypto-demo .
   ```

2. **Run the container:**

   ```bash
   docker run -it crypto-demo
   ```

   *Note: `-it` is required for interactive mode to accept user input.*

## Usage

Once the application is running, simply type the ID of the cryptocurrency you want to check (e.g., `bitcoin`, `ethereum`, `dogecoin`).

Type `exit` or `quit` to close the application.
