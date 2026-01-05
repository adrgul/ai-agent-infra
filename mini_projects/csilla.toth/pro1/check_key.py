"""Health-check for OpenAI API key and client.

Usage:
  python check_key.py            # check .env and imports
  python check_key.py --api     # also attempt a lightweight API request (may consume quota)
  python check_key.py --show    # show the key (masked by default)
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def mask_key(k: str) -> str:
    if not k:
        return ""
    if len(k) <= 8:
        return k[0:2] + "..."
    return k[0:4] + "..." + k[-4:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", action="store_true", help="Perform a lightweight API call (may consume quota)")
    parser.add_argument("--show", action="store_true", help="Print the key (masked by default) to the console")
    args = parser.parse_args()

    if load_dotenv:
        load_dotenv()

    key = os.getenv("OPENAI_API_KEY")
    print("OPENAI_API_KEY present:", bool(key))
    if args.show:
        print("OPENAI_API_KEY:", mask_key(key))

    try:
        import openai
        print("openai import: OK")
    except Exception as exc:
        print("openai import failed:", exc)
        return 2

    if args.api:
        try:
            client = openai.OpenAI()
            # lightweight request: list models (may be rate-limited or consume quota)
            models = client.models.list()
            print("API call successful; models count:", len(getattr(models, 'data', []) or []))
        except Exception as exc:
            print("API call failed:", exc)
            return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
