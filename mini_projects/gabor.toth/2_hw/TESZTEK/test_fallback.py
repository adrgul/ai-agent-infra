import requests
import json

BASE_URL = "http://localhost:8000"

# First, let's save descriptions for two categories
print("1. Saving category descriptions...")

# Save AI description
resp = requests.post(
    f"{BASE_URL}/api/desc-save",
    data={
        "user_id": "user1",
        "category": "AI",
        "description": "Mesterséges intelligencia, machine learning, deep learning"
    }
)
print(f"   AI: {resp.json()}")

# Save Python description
resp = requests.post(
    f"{BASE_URL}/api/desc-save",
    data={
        "user_id": "user1",
        "category": "Python",
        "description": "Python programozási nyelv"
    }
)
print(f"   Python: {resp.json()}")

# Now let's upload a document ONLY to Python category
print("\n2. Uploading file only to Python category...")
with open("test_rag.md", "rb") as f:
    files = {
        "file": f,
    }
    data = {
        "user_id": "user1",
        "category": "Python"
    }
    resp = requests.post(f"{BASE_URL}/api/files/upload", files=files, data=data)
    print(f"   Upload: {resp.json()}")

# Now test: ask a question that would match AI category but we have no documents there
print("\n3. Sending question that should match AI category (but no docs there)...")
resp = requests.post(
    f"{BASE_URL}/api/chat",
    data={
        "user_id": "user1",
        "session_id": "session1",
        "message": "Mi az a deep learning?"
    }
)
result = resp.json()
print(f"\n   Response:")
if result.get('final_answer'):
    print(f"   - final_answer: {result.get('final_answer')[:150]}...")
    print(f"   - fallback_search: {result.get('fallback_search')}")
    print(f"   - routed_category: {result.get('memory_snapshot', {}).get('routed_category')}")
    print(f"   - Retrieved chunks: {len(result.get('rag_debug', {}).get('retrieved', []))}")
else:
    print(f"   - Error: {result}")

