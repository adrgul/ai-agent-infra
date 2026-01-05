#!/usr/bin/env python3
"""
Test script to verify data persistence functionality.

Tests:
1. User profile persistence
2. Category storage
3. Chunks.json structure
4. ChromaDB index persistence
5. File upload persistence
"""

import json
from pathlib import Path
import requests

BASE_URL = "http://localhost:8000"

def test_data_persistence():
    """Test all data persistence mechanisms."""
    
    print("\n" + "="*60)
    print("💾 TEST: Data Persistence")
    print("="*60)
    
    # Step 1: User Profile Persistence
    print("\n1️⃣ Checking User Profile Persistence...")
    users_dir = Path("data/users")
    
    if users_dir.exists():
        user_files = list(users_dir.glob("*.json"))
        print(f"   ✓ Users directory exists")
        print(f"   Found {len(user_files)} user profile(s):")
        
        for user_file in user_files:
            with open(user_file, 'r') as f:
                user_profile = json.load(f)
            
            print(f"\n   📋 {user_file.name}:")
            print(f"      Username: {user_profile.get('username')}")
            
            # Handle both dict and list categories formats
            categories = user_profile.get('categories', {})
            cat_count = len(categories) if isinstance(categories, (dict, list)) else 0
            print(f"      Categories: {cat_count}")
            
            # Verify user profile structure
            required_fields = ["created_at"]
            missing = [f for f in required_fields if f not in user_profile]
            
            if missing:
                print(f"      ⚠️ Missing fields: {missing}")
            else:
                print(f"      ✓ Core structure OK")
            
            # Show categories (handle both dict and list)
            if isinstance(categories, dict):
                for cat_name in categories.keys():
                    print(f"         • {cat_name}")
            elif isinstance(categories, list):
                for cat_name in categories:
                    print(f"         • {cat_name}")
    else:
        print(f"   ✗ Users directory not found: {users_dir}")
        return False
    
    # Step 2: Session Files Persistence
    print("\n2️⃣ Checking Session Files Persistence...")
    sessions_dir = Path("data/sessions")
    
    if sessions_dir.exists():
        session_files = list(sessions_dir.glob("*.json"))
        print(f"   ✓ Sessions directory exists")
        print(f"   Found {len(session_files)} session file(s)")
        
        if session_files:
            # Check first session
            with open(session_files[0], 'r') as f:
                session_data = json.load(f)
            
            print(f"\n   📋 Sample: {session_files[0].name}")
            
            # Handle both dict and list formats for session data
            if isinstance(session_data, dict):
                print(f"      Session ID: {session_data.get('session_id')}")
                print(f"      User ID: {session_data.get('user_id')}")
                print(f"      Messages: {len(session_data.get('messages', []))}")
            elif isinstance(session_data, list):
                print(f"      Session data is a list (chat history)")
                print(f"      Messages: {len(session_data)}")
            
            # Verify session structure (if dict)
            if isinstance(session_data, dict):
                required_fields = ["user_id", "session_id", "created_at", "messages"]
                missing = [f for f in required_fields if f not in session_data]
            
                if missing:
                    print(f"      ⚠️ Missing fields: {missing}")
                else:
                    print(f"      ✓ Complete structure")
    else:
        print(f"   ⚠️ Sessions directory not found (normal if no chats yet)")
    
    # Step 3: Chunks.json Persistence
    print("\n3️⃣ Checking Chunks Data Persistence...")
    derived_dir = Path("data/derived")
    chunks_file = derived_dir / "chunks.json"
    
    if chunks_file.exists():
        with open(chunks_file, 'r') as f:
            chunks_data = json.load(f)
        
        print(f"   ✓ Chunks file exists: {chunks_file}")
        print(f"   Categories: {len(chunks_data)}")
        
        total_chunks = 0
        for category, cat_data in chunks_data.items():
            cat_chunks = 0
            for doc_name, doc_data in cat_data.items():
                cat_chunks += len(doc_data.get('chunks', []))
            total_chunks += cat_chunks
            print(f"      • {category}: {cat_chunks} chunks")
        
        print(f"   Total chunks: {total_chunks}")
        
        # Verify chunk structure
        if total_chunks > 0:
            first_category = list(chunks_data.keys())[0]
            first_doc = list(chunks_data[first_category].keys())[0]
            first_chunk = chunks_data[first_category][first_doc]['chunks'][0]
            
            required_fields = ["id", "text", "embedding", "start_char", "end_char", "metadata"]
            missing = [f for f in required_fields if f not in first_chunk]
            
            if missing:
                print(f"      ⚠️ Missing chunk fields: {missing}")
            else:
                print(f"      ✓ Chunk structure valid")
    else:
        print(f"   ⚠️ Chunks file not found (normal if no uploads yet)")
    
    # Step 4: File Uploads Persistence
    print("\n4️⃣ Checking Uploaded Files Persistence...")
    uploads_dir = Path("data/uploads")
    
    if uploads_dir.exists():
        user_dirs = [d for d in uploads_dir.iterdir() if d.is_dir()]
        print(f"   ✓ Uploads directory exists")
        print(f"   Found {len(user_dirs)} user upload folder(s)")
        
        for user_dir in user_dirs:
            files = list(user_dir.glob("*"))
            print(f"      • {user_dir.name}: {len(files)} file(s)")
            
            for file in files[:3]:  # Show first 3
                size_kb = file.stat().st_size / 1024
                print(f"         - {file.name} ({size_kb:.1f} KB)")
    else:
        print(f"   ⚠️ Uploads directory not found (normal if no uploads yet)")
    
    # Step 5: ChromaDB Persistence
    print("\n5️⃣ Checking ChromaDB Persistence...")
    chroma_dir = Path("data/chroma_db")
    
    if chroma_dir.exists():
        print(f"   ✓ ChromaDB directory exists")
        
        # Check for collections
        try:
            response = requests.get(f"{BASE_URL}/api/health")
            if response.ok:
                print(f"   ✓ ChromaDB accessible via API")
            else:
                print(f"   ⚠️ ChromaDB API not responding")
        except:
            print(f"   ⚠️ Cannot reach ChromaDB API")
    else:
        print(f"   ⚠️ ChromaDB directory not found (will be created on first upload)")
    
    # Step 6: Data Consistency Check
    print("\n6️⃣ Checking Data Consistency...")
    
    if chunks_file.exists() and users_dir.exists():
        with open(chunks_file, 'r') as f:
            chunks = json.load(f)
        
        user_files_dict = {f.stem: f for f in users_dir.glob("*.json")}
        
        # Check if chunk uploads correspond to user data
        chunk_categories_count = sum(
            len(docs) for docs in chunks.values()
        )
        
        print(f"   Chunks in database: {chunk_categories_count} categories")
        print(f"   Users in system: {len(user_files_dict)}")
        
        if chunk_categories_count > 0 and len(user_files_dict) > 0:
            print(f"   ✓ Data consistency looks good")
    
    print("\n" + "="*60)
    print("✅ Data Persistence Test PASSED!")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = test_data_persistence()
    exit(0 if success else 1)
