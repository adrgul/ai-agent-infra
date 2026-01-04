#!/usr/bin/env python3
"""
Simple API call example (Python, uses `requests`).

Replace the `API_URL` / `API_TOKEN` environment variables or edit the placeholders below.
"""
import os
import json
import requests

API_URL = os.environ.get("API_URL", "https://api.example.com/resource")
API_TOKEN = os.environ.get("API_TOKEN", "YOUR_TOKEN")

def post_example(data=None):
    if data is None:
        data = {"name": "Adam", "age": 30}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if API_TOKEN and API_TOKEN != "YOUR_TOKEN":
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    resp = requests.post(API_URL, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    # attempt to return JSON, fall back to text
    try:
        return resp.json()
    except ValueError:
        return resp.text

if __name__ == "__main__":
    sample = {"name": "Adam", "age": 30}
    print(f"Posting to: {API_URL}")
    try:
        result = post_example(sample)
        print("Response:")
        print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else result)
    except requests.HTTPError as e:
        print("HTTP error:", e)
        if e.response is not None:
            print(e.response.status_code, e.response.text)
    except Exception as e:
        print("Error:", e)
