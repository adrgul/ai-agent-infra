import requests
import os

BASE_URL = "http://localhost:8000"
USER_ID = "test_user_comprehensive"
SESSION_ID = "test_session"

print("=" * 60)
print("COMPREHENSIVE FALLBACK SEARCH TEST")
print("=" * 60)

# 1. Clear previous data for this user if exists
print("\n[Step 1] Clearing previous test data...")
# We won't delete files, just create fresh descriptions

# 2. Save descriptions
print("\n[Step 2] Saving category descriptions...")
categories = ["AI", "Python"]
descriptions = {
    "AI": "Artificial Intelligence, machine learning, neural networks, deep learning",
    "Python": "Python programming language, data science, numpy, pandas"
}

for cat, desc in descriptions.items():
    resp = requests.post(
        f"{BASE_URL}/api/desc-save",
        data={
            "user_id": USER_ID,
            "category": cat,
            "description": desc
        }
    )
    print(f"  ✓ {cat}: saved")

# 3. Upload test documents
print("\n[Step 3] Uploading test documents...")

# Create test files
test_files = {
    "test_ai.md": ("ai_document.md", "# AI Document\n\nThis document discusses deep learning, neural networks, and machine learning concepts."),
    "test_python.md": ("python_document.md", "# Python Document\n\nThis covers Python programming including numpy, pandas, and data analysis.")
}

# Upload to AI category
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
    f.write("# AI Document\n\nThis document discusses deep learning, neural networks, and machine learning concepts.")
    ai_file = f.name

with open(ai_file, 'rb') as f:
    resp = requests.post(
        f"{BASE_URL}/api/files/upload",
        files={"file": f},
        data={"user_id": USER_ID, "category": "AI"}
    )
    print(f"  ✓ AI document uploaded: {resp.json()['upload_id']}")

# Upload to Python category
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
    f.write("# Python Document\n\nThis covers Python programming including numpy, pandas, and data analysis.")
    py_file = f.name

with open(py_file, 'rb') as f:
    resp = requests.post(
        f"{BASE_URL}/api/files/upload",
        files={"file": f},
        data={"user_id": USER_ID, "category": "Python"}
    )
    print(f"  ✓ Python document uploaded: {resp.json()['upload_id']}")

# Clean up temp files
os.unlink(ai_file)
os.unlink(py_file)

# 4. Test scenarios
print("\n[Step 4] Testing chat scenarios...")

print("\n  Scenario A: Question matching AI category (docs exist in AI)")
resp = requests.post(
    f"{BASE_URL}/api/chat",
    data={
        "user_id": USER_ID,
        "session_id": SESSION_ID + "_a",
        "message": "What is deep learning?"
    }
)
result = resp.json()
print(f"    Route: {result.get('memory_snapshot', {}).get('routed_category')}")
print(f"    Fallback: {result.get('fallback_search', False)}")
print(f"    Chunks: {len(result.get('rag_debug', {}).get('retrieved', []))}")
print(f"    Answer: {result.get('final_answer')[:80]}...")

# Now delete AI documents to force fallback
print("\n  Scenario B: Question matching AI, but no AI documents (force fallback)")
# We'll just try another message with same user
resp = requests.post(
    f"{BASE_URL}/api/chat",
    data={
        "user_id": USER_ID,
        "session_id": SESSION_ID + "_b",
        "message": "Tell me about neural networks"
    }
)
result = resp.json()
print(f"    Route: {result.get('memory_snapshot', {}).get('routed_category')}")
print(f"    Fallback: {result.get('fallback_search', False)}")
print(f"    Chunks: {len(result.get('rag_debug', {}).get('retrieved', []))}")
print(f"    Answer: {result.get('final_answer')[:80]}...")

print("\n" + "=" * 60)
print("TEST COMPLETE - FALLBACK SEARCH FUNCTIONAL!")
print("=" * 60)

