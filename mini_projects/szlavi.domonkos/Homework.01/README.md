# Budapest Time API (Homework 01)

Simple FastAPI application that fetches the current time for the `Europe/Budapest` timezone from worldtimeapi.org and exposes a small HTTP API.

**Highlights**
- **Purpose**: Demo FastAPI usage, external HTTP calls, and Pydantic response models.
- **Source file**: `homework_01_api.py`

**Requirements**
- Python 3.11+


# Budapest Time API (Homework 01)

Lightweight FastAPI project that demonstrates calling an external time API (worldtimeapi.org) to obtain current time information for the `Europe/Budapest` timezone and exposing a small HTTP interface.

**Repository snapshot**

This project lives under the `mini_projects/szlavi.domonkos/Homework.01` folder and contains the following files:

- `homework_01_api.py` — Main FastAPI application (ASGI) with endpoints and Pydantic response models.
- `run_test.py` — Small in-process test script that uses `httpx.AsyncClient` to call the ASGI app.
- `requirements.txt` — Dependency list for quick setup.
- `README.md` — This document.

**Project file structure**

```
mini_projects/szlavi.domonkos/Homework.01/
├─ homework_01_api.py       # FastAPI app, endpoints, models
├─ run_test.py              # In-process test script using httpx ASGI client
├─ requirements.txt         # Listed dependencies
└─ README.md                # Project documentation
```

Components and responsibilities

- FastAPI application (`homework_01_api.py`):
  - Defines the FastAPI `app` with metadata (title, description, version).
  - Provides three endpoints:
    - `GET /api/budapest-time` — a validated `TimeResponse` with `timezone`, `datetime`, `utc_datetime`, and `utc_offset`.
    - `GET /api/budapest-time/raw` — returns the raw JSON payload from the upstream API.
    - `GET /health` — simple health check returning `{"status": "healthy"}`.
  - Uses `httpx.AsyncClient` to call `https://worldtimeapi.org/api/timezone/Europe/Budapest` with a 10s timeout and maps common errors to appropriate HTTP status codes.

- Test runner (`run_test.py`):
  - Runs the ASGI app in-process (no network server required) using `httpx.AsyncClient(app=app, base_url="http://testserver")`.
  - Prints status code and response body; exits with non-zero code on failure.

API details

- GET /api/budapest-time
  - Description: Returns a compact, validated JSON response with Budapest timezone and UTC-formatted datetime.
  - Response model: `TimeResponse` (Pydantic)
  - Success example (200):

```json
{
  "timezone": "Europe/Budapest",
  "datetime": "2024-12-23T15:30:45.123456+01:00",
  "utc_datetime": "2024-12-23T14:30:45.123456Z",
  "utc_offset": "+01:00"
}
```

- GET /api/budapest-time/raw
  - Description: Proxy endpoint returning the upstream JSON without transformation. Useful for debugging.

- GET /health
  - Description: Health check for the service. Returns `{"status":"healthy"}`.

Error handling and timeouts

- Timeout: External requests use a 10s timeout. Timeouts are returned as HTTP 504.
- Upstream HTTP errors (non-2xx) are mapped to HTTP 502.
- Parsing errors or unexpected conditions return HTTP 500.

Setup and run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server (development):

```bash
uvicorn homework_01_api:app --reload --host 0.0.0.0 --port 8000
```

Run the in-process test (no server required):

```bash
python3 run_test.py
```

Notes and suggestions

- The app relies on `worldtimeapi.org` as a free public data source. For production usage consider a resilient strategy (caching, retries, rate-limiting).
- The `run_test.py` script is intentionally small — for more comprehensive testing add `pytest`-based tests and mock the upstream HTTP calls (e.g., with `respx`).

Credits

Created as a homework/demo project to illustrate building a small FastAPI service and testing it in-process.
