#!/usr/bin/env python3
"""
HF1 - 2 db API hívás:
1) Public API: GitHub Public API (Date header).
2) OpenAI API: Responses API (szöveg generálás a timestamp + user input alapján)

Futtatás példa:
  export OPENAI_API_KEY="..."
  python hf1_api_calls.py --timezone Europe/Budapest --note "Build elindítva"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))



PUBLIC_TIME_URL = "https://api.github.com/rate_limit"


def fetch_third_party_timestamp(timezone_name: str, timeout_s: int = 10) -> Dict[str, Any]:
    """
    3rd-party timestamp (demo HF1-hez).
    Source: GitHub Public API (Date header).
    """
    r = requests.get(
        PUBLIC_TIME_URL,
        timeout=timeout_s,
        headers={
            "User-Agent": "hf1/1.0",
            "Accept": "application/vnd.github+json",
        },
    )
    r.raise_for_status()

    date_hdr = r.headers.get("Date")
    if not date_hdr:
        raise RuntimeError("GitHub válaszban nincs Date header")

    dt_utc = parsedate_to_datetime(date_hdr).astimezone(timezone.utc)
    tz = ZoneInfo(timezone_name)
    dt_local = dt_utc.astimezone(tz)

    offset = dt_local.strftime("%z")          # +0100
    offset = offset[:3] + ":" + offset[3:]    # +01:00

    data = r.json()

    return {
        "source": "github_api_date_header",
        "datetime": dt_local.isoformat(),
        "timezone": timezone_name,
        "utc_offset": offset,
        "unixtime": int(dt_utc.timestamp()),
        "raw": {
            "date_header": date_hdr,
            "github_rate_limit": data.get("rate"),
        },
    }




def call_openai_responses(model: str, input_text: str) -> str:
    """
    OpenAI Responses API hívás a hivatalos Python SDK-n keresztül.
    """
    # Lazy import, hogy a public API rész OpenAI nélkül is fusson.
    from openai import OpenAI

    client = OpenAI()
    resp = client.responses.create(
        model=model,
        input=input_text,
    )


    # Stabil, ha elérhető:
    out_text = getattr(resp, "output_text", None)
    if out_text:
        return out_text.strip()

    # Fallback: első output_text content
    try:
        for item in resp.output:
            for c in item.content:
                if getattr(c, "type", "") == "output_text":
                    return c.text.strip()
    except Exception:
        pass

    return str(resp)[:2000]


def build_openai_prompt(ts: Dict[str, Any], note: str) -> str:
    """
    A user input: `note`. A public API-ból jön a timestamp.
    Kimenet: 1 sor, emberi olvasható "timestamp statement".
    """
    dt = ts.get("datetime")
    tz = ts.get("timezone")
    utc_offset = ts.get("utc_offset")
    unixtime = ts.get("unixtime")

    return (
        "Írj egyetlen rövid, magyar nyelvű sort, ami egy '3rd-party időbélyeg' nyilatkozat.\n"
        "Formátum: '<ISO_DATETIME> <TIMEZONE> (<UTC_OFFSET>) — <NOTE> — source=github_api_date_header unixtime=<UNIX>'\n"
        "Ne tegyél hozzá extra magyarázatot.\n\n"
        f"ISO_DATETIME: {dt}\n"
        f"TIMEZONE: {tz}\n"
        f"UTC_OFFSET: {utc_offset}\n"
        f"UNIX: {unixtime}\n"
        f"NOTE: {note}\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--timezone",
        default=os.getenv("TIMEZONE", "Europe/Budapest"),
        help="IANA timezone pl. Europe/Budapest",
    )
    ap.add_argument(
        "--note",
        required=True,
        help="User input (pl. 'Deploy elindítva')",
    )
    ap.add_argument(
        "--model",
        default=os.getenv("MODEL", "gpt-5-mini"),
        help="OpenAI model, pl. gpt-5-mini",
    )
    ap.add_argument(
        "--no-openai",
        action="store_true",
        help="Csak public API hívás (OpenAI nélkül)",
    )


    args = ap.parse_args()

    # 1) Public API
    ts = fetch_third_party_timestamp(args.timezone)

    result: Dict[str, Any] = {
        "public_api": ts
    }

    # 2) OpenAI API
    if not args.no_openai:
        if not os.getenv("OPENAI_API_KEY"):
            print("HIBA: nincs OPENAI_API_KEY. Tedd a .env fájlba.", file=sys.stderr)
            return 2

        prompt = build_openai_prompt(ts, args.note)
        out = call_openai_responses(args.model, prompt)
        result["openai_api"] = {
            "model": args.model,
            "output": out,
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
