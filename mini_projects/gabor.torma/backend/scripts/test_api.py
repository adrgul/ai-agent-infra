import requests
import os
import sys

BASE_URL = "http://localhost:8000"

def test_file_upload(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Testing upload for: {filepath}")
    filename = os.path.basename(filepath)
    
    # Determine mime type roughly (optional, requests handles it usually)
    files = {'file': (filename, open(filepath, 'rb'))}
    
    try:
        response = requests.post(f"{BASE_URL}/process", files=files)
        if response.status_code == 200:
            print("SUCCESS")
            print(response.json())
        else:
            print(f"FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")
    print("-" * 30)

def main():
    # Wait for service availability (optional logic could go here)
    
    test_files = [
        "mock_data/sample.txt",
        "mock_data/sample.md",
        "mock_data/sample.srt",
        "mock_data/sample.docx"
    ]

    for f in test_files:
        test_file_upload(f)

if __name__ == "__main__":
    main()
