#!/usr/bin/env python3
"""Simple test runner for the Budapest Time API.

This script runs the FastAPI app in-process and issues a request to
`/api/budapest-time` using httpx's ASGI client support. It prints the
status code and response body. Exit code is 0 on success, 1 on failure.
"""
import asyncio
import sys

import httpx

from homework_01_api import app


async def main() -> int:
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        try:
            resp = await client.get("/api/budapest-time", timeout=15.0)
            print("Status:", resp.status_code)
            print("Body:")
            print(resp.text)
            resp.raise_for_status()
        except Exception as exc:
            print("Test failed:", exc, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
