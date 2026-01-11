import requests
import json

BASE_URL = "http://localhost:8000"

def test_list_meetings():
    print("Testing GET /meetings...")
    try:
        response = requests.get(f"{BASE_URL}/meetings")
        if response.status_code == 200:
            meetings = response.json()
            print(f"SUCCESS: Retrieved {len(meetings)} meetings.")
            for m in meetings:
                print(f" - ID: {m['id']}")
                print(f"   Meta: {m.get('metadata')}")
        else:
            print(f"FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")
    print("-" * 30)

def test_search_meetings(query):
    print(f"Testing GET /search?q={query}...")
    try:
        response = requests.get(f"{BASE_URL}/search", params={"q": query})
        if response.status_code == 200:
            results = response.json()
            print(f"SUCCESS: Found {len(results)} results.")
            for r in results:
                print(f" - ID: {r['id']}")
                print(f"   Score: {r.get('distance', 'N/A')}")
                print(f"   Snippet: {r.get('content', '')[:100]}...")
        else:
            print(f"FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")
    print("-" * 30)

def main():
    test_list_meetings()
    test_search_meetings("architecture")
    test_search_meetings("banana") # Should reasonably return nothing or low relevance

if __name__ == "__main__":
    main()
