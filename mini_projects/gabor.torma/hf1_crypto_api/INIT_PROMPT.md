You are an expert Python backend engineer and software architect.
Generate a minimal but clean example project that demonstrates external API request.

The code MUST follow SOLID principles (Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion) in a pragmatic, lightweight way. Use small, focused classes and clear abstractions.

Goal
-----
Create a small Python CLI app that show crypto currency price:
1. Lets the user type crypto name prompts in a terminal loop.
2. For each prompt:
   - Getting the current price of the crypto. 
   - Prints the current price and scores back to the terminal.

Project structure
------------------
Create the following files:

- `Dockerfile`
- `requirements.txt`
- `app/main.py`
- `app/config.py`
- `app/cli.py`

SOLID & architecture guidelines
-------------------------------
Design the code according to SOLID principles:

1. Single Responsibility Principle
   - Each class/module should have one clear responsibility:
     - `Config` for configuration loading.
     - `CrytoApp` (or similar) to orchestrate the workflow.
     - `CLI` layer for user interaction.

2. Open/Closed Principle
   - Define small interfaces / abstract base classes where it makes sense:
     - e.g. an `CrytoApp` interface / ABC.
   - The core app (`CrytoApp`) should depend on these abstractions, so we can swap implementations

3. Liskov Substitution Principle
   - Concrete implementations must be drop-in replacements for the corresponding interface / ABC without breaking behavior.

4. Interface Segregation Principle

5. Dependency Inversion Principle
   - High-level logic (the application / CLI) should depend on abstractions, not concrete classes:
     - Pass `CrytoApp` via constructor injection.
   - Configuration (e.g. choosing OpenAI model, DB path) should be outside the core logic, in `config.py` or `main.py`.

Python & dependencies
----------------------
- Use Python 3.11 (or 3.10+) in the Docker image (official slim image is fine).
- Use `python-dotenv` to load environment variables from `.env`.

`requirements.txt` should include at least:
- `python-dotenv`

Environment variables
----------------------
- The real API key must NOT be hard-coded.
- In `config.py`, load variables from `.env` using `python-dotenv`.

Dockerfile
-----------
- Based on an official Python image (e.g. `python:3.11-slim`).
- Copy the project files into the container.
- Install dependencies from `requirements.txt`.
- Use a working directory like `/app`.
- Ensure the `./chroma_db` directory is created and writable.
- Set `ENTRYPOINT` or `CMD` so that running the container starts the CLI, e.g.:
    `CMD ["python", "-m", "app.main"]`

Developer instructions
-----------------------
Add short usage instructions as comments (or docstring) in `app/main.py`:

- How to build the Docker image, e.g.:
    - `docker build -t crypto-demo .`
- How to run the container with the env file:
    - `docker run -it crypto-demo`

Code style
-----------
- Use clear function boundaries and small classes that follow SOLID.
- Add type hints and minimal docstrings for public methods.
- Keep the code as simple and educational as possible: this is for teaching embeddings + vector DB basics and SOLID design in a Python/Docker setting.

Documenation
------------
Generate a clean and detailed installing and runing guide inro readme.md

Now generate all the mentioned files with full, working code.

