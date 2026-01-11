import requests
import os
import sys
import json

BASE_URL = "http://localhost:8000"

def test_rag_processing(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Testing RAG Processing with: {filepath}")
    filename = os.path.basename(filepath)
    
    files = {'file': (filename, open(filepath, 'rb'))}
    
    try:
        response = requests.post(f"{BASE_URL}/process", files=files)
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS")
            print("Summary Snippet:", data.get("summary")[:100] + "...")
            print("-" * 20)
            print("Tasks Count:", len(data.get("tasks", [])))
            print("Notes Count:", len(data.get("notes", [])))
        else:
            print(f"FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")
    print("=" * 30)

def main():
    # Use the long architecture meeting for a good test of RAG and summarization
    test_file = "mock_data/meeting_4_long_architecture.txt"
    # If not found (running from backend dir?), try adjusting path
    if not os.path.exists(test_file):
        if os.path.exists(f"../{test_file}"):
            test_file = f"../{test_file}"

    test_rag_processing(test_file)

if __name__ == "__main__":
    main()
