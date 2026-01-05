You are an expert Python backend engineer and software architect.
Generate a minimal but clean new project that calls OPENAI API to summarize input text up to 20 words and make and print a set of person's names.

The code MUST follow SOLID principles (Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion) in a pragmatic, lightweight way. Use small, focused classes and clear abstractions.

Goal
-----
Create a small Python CLI app in that:
1. Reads an OpenAI API key from a `.env` file.
2. Lets the user type free-text prompts in a terminal loop till user types only 'exit' or 'quit'
3. For each prompt:
   - Create a summarization extract using the OpenAI API.
   - Prints out a short summarization to the terminal up to 20 words.
   - make and print out a list of names of persons was mentioned in the input text.

Project structure
------------------
Create the following files:

- `requirements.txt`
- `app/main.py`
- `app/config.py`
- `app/summarizer.py`
- `app/lister.py`
- `app/cli.py`
- `.env.example`  (template for the real `.env`)

SOLID & architecture guidelines
-------------------------------
Design the code according to SOLID principles:

1. Single Responsibility Principle
   - Each class/module should have one clear responsibility:
     - `Config` for configuration loading.
     - `SummarizeService` for extract generation.
     - `ListParticipants` for creating a distinct list of persons name.     
     - `CLI` layer for user interaction.

2. Open/Closed Principle
   - Define small interfaces / abstract base classes where it makes sense:
   - The core app should depend on these abstractions, so we can swap implementations (e.g., different embedding provider or vector DB) without changing the app logic.

3. Liskov Substitution Principle
   - Concrete implementations must be drop-in replacements for the corresponding interface / ABC without breaking behavior.

4. Interface Segregation Principle
   - Keep interfaces small and focused
5. Dependency Inversion Principle
   - High-level logic (the application / CLI) should depend on abstractions, not concrete classes:
   - Configuration (e.g. choosing OpenAI model, DB path) should be outside the core logic, in `config.py` or `main.py`.

Python & dependencies
----------------------
- Use Python 3.11 (or 3.10+) 
- Use `openai` for calling the API.

Environment variables
----------------------
- The real API key must NOT be hard-coded.
- In `config.py`, load variables from `.env` using `python-dotenv`.
- Expect `OPENAI_API_KEY` in the `.env`.
- `.env.example` should contain:
    OPENAI_API_KEY=your_openai_api_key_here

Embeddings logic
-----------------
- Use one of the current OpenAI embedding models, for example `text-embedding-3-small`.
- Implement an `EmbeddingService` abstraction (e.g. via an abstract base class or protocol) with:
    - `get_embedding(text: str) -> List[float]`
- Implement `OpenAIEmbeddingService(EmbeddingService)` that:
    - uses the OpenAI Embeddings API,
    - returns the embedding vector,
    - handles basic errors (print/log an error and continue if the API fails).

Vector DB logic
----------------
- Implement a `VectorStore` abstraction with methods like:
    - `add(id: str, text: str, embedding: List[float]) -> None`
    - `similarity_search(embedding: List[float], k: int) -> List[Tuple[str, float, str]]`
      (id, score, text or similar)
- Implement `ChromaVectorStore(VectorStore)` using ChromaDB:
    - On startup, create or load a persistent collection, e.g.:
        - path: `./chroma_db`
        - collection name: `prompts`
    - For each user prompt:
        - generate an ID (e.g. UUID string),
        - add the text + embedding to the collection.
    - After inserting, run a similarity search on the same collection to find the k nearest neighbors (e.g. k=3) to the current embedding.
    - Return the matched texts and similarity scores/distances.

CLI behavior and application orchestration
-------------------------------------------
- Implement a high-level `EmbeddingApp` class that:
    - Receives an `EmbeddingService` and `VectorStore` via constructor injection.
    - Has a method like `process_query(text: str, k: int = 3)` that:
        1) gets the embedding of the input text,
        2) stores it in the vector DB,
        3) performs a similarity search,
        4) returns the results in a structured form.

- Implement `CLI` logic in `app/cli.py` or within `main.py` using the `EmbeddingApp`:
    - When the app starts, print a short intro explaining what it does.
    - Enter an infinite loop:
        - Prompt the user: `Enter a prompt (or 'exit' to quit): `
        - If the user types `exit`, gracefully terminate.
        - Otherwise:
            - Call `EmbeddingApp.process_query(...)`.
            - Print a nicely formatted result, for example:

              ```
              Stored prompt and retrieved nearest neighbors:
              1. (distance=0.000) "the current text itself..."
              2. (distance=0.123) "previous similar text..."
              3. (distance=0.456) "another somewhat related text..."
              ```



Developer instructions
-----------------------
Add short usage instructions as comments (or docstring) in `app/main.py`:

- How to copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`.
- How to build the Docker image, e.g.:
    - `docker build -t embedding-demo .`
- How to run the container with the env file:
    - `docker run -it --env-file .env embedding-demo`

Code style
-----------
- Use clear function boundaries and small classes that follow SOLID.
- Add type hints and minimal docstrings for public methods.
- Keep the code as simple and educational as possible: this is for teaching embeddings + vector DB basics and SOLID design in a Python/Docker setting.

Now generate all the mentioned files with full, working code.



