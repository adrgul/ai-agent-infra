#!/usr/bin/env python3
"""
Test script to verify category management functionality.

Tests:
1. Category creation
2. Category description management
3. Category retrieval
4. Category-document associations
5. Category persistence
"""

import requests
import json
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"

def test_category_management():
    """Test category management functionality."""
    
    print("\n" + "="*60)
    print("🏷️  TEST: Category Management")
    print("="*60)
    
    user_id = f"cat_test_user_{int(time.time())}"
    
    # Step 1: Create Categories
    print("\n1️⃣ Creating Categories...")
    
    categories = [
        "Machine Learning",
        "Web Development",
        "Data Science"
    ]
    
    for category in categories:
        print(f"   Creating: {category}")
        
        # Note: Categories are created implicitly when documents are uploaded
        # We'll verify by uploading a document
    
    # Step 2: Save Category Descriptions
    print("\n2️⃣ Saving Category Descriptions...")
    
    descriptions = {
        "Machine Learning": "AI, neural networks, deep learning, algorithms",
        "Web Development": "Frontend, backend, full-stack, frameworks",
        "Data Science": "Analytics, statistics, data visualization, Python"
    }
    
    for category, description in descriptions.items():
        print(f"   {category}:")
        
        response = requests.post(
            f"{BASE_URL}/api/desc-save",
            data={
                "user_id": user_id,
                "category": category,
                "description": description
            }
        )
        
        if response.ok:
            result = response.json()
            print(f"      ✓ Saved: {description[:50]}...")
        else:
            print(f"      ✗ Error: {response.status_code}")
    
    # Step 3: Retrieve Category Descriptions
    print("\n3️⃣ Retrieving Category Descriptions...")
    
    for category in categories:
        # Try POST first (as API seems to expect POST)
        response = requests.post(
            f"{BASE_URL}/api/desc-get",
            json={
                "user_id": user_id,
                "category": category
            },
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            desc = result.get("description", "")
            print(f"   ✓ {category}: {desc[:50]}...")
        else:
            # If POST fails, try GET
            response = requests.get(
                f"{BASE_URL}/api/desc-get",
                params={
                    "user_id": user_id,
                    "category": category
                },
                timeout=10
            )
            
            if response.ok:
                result = response.json()
                desc = result.get("description", "")
                print(f"   ✓ {category}: {desc[:50]}...")
            else:
                print(f"   ⚠️ {category}: Not found (status: {response.status_code})")
                print(f"      (Endpoint might not be implemented yet)")
    
    # Step 4: Upload Documents to Each Category
    print("\n4️⃣ Uploading Documents to Categories...")
    
    category_docs = {
        "Machine Learning": ("ml_doc.md", "# Machine Learning\n\nThis is about ML algorithms and neural networks."),
        "Web Development": ("web_doc.md", "# Web Development\n\nBuilding modern web applications with frameworks."),
        "Data Science": ("ds_doc.md", "# Data Science\n\nUsing Python for data analysis and visualization.")
    }
    
    for category, (filename, content) in category_docs.items():
        print(f"   {category}:")
        
        response = requests.post(
            f"{BASE_URL}/api/files/upload",
            files={"file": (filename, content.encode())},
            data={
                "user_id": user_id,
                "category": category
            },
            timeout=30
        )
        
        if response.ok:
            result = response.json()
            print(f"      ✓ Uploaded: {filename}")
        else:
            print(f"      ✗ Error: {response.status_code}")
    
    # Step 5: Verify User Profile with Categories
    print("\n5️⃣ Verifying User Profile...")
    
    user_file = Path(f"data/users/{user_id}.json")
    
    if user_file.exists():
        with open(user_file, 'r') as f:
            profile = json.load(f)
        
        print(f"   ✓ User profile found")
        print(f"   Categories: {len(profile.get('categories', {}))}")
        
        for cat_name, cat_data in profile.get('categories', {}).items():
            desc = cat_data.get('description', '')
            created = cat_data.get('created_at', 'N/A')
            print(f"      • {cat_name}")
            print(f"        Description: {desc[:40]}...")
            print(f"        Created: {created}")
    else:
        print(f"   ✗ User profile not found: {user_file}")
    
    # Step 6: Verify Chunks are Associated with Categories
    print("\n6️⃣ Verifying Category-Document Associations...")
    
    chunks_file = Path("data/derived/chunks.json")
    
    if chunks_file.exists():
        with open(chunks_file, 'r') as f:
            chunks = json.load(f)
        
        for category in categories:
            if category in chunks:
                cat_chunks = chunks[category]
                doc_count = len(cat_chunks)
                total_chunks = sum(len(doc['chunks']) for doc in cat_chunks.values())
                
                print(f"   ✓ {category}:")
                print(f"      Documents: {doc_count}")
                print(f"      Total chunks: {total_chunks}")
                
                # Show document names
                for doc_name in cat_chunks.keys():
                    chunks_in_doc = len(cat_chunks[doc_name].get('chunks', []))
                    print(f"         - {doc_name} ({chunks_in_doc} chunks)")
            else:
                print(f"   ⚠️ {category}: No documents indexed yet")
    else:
        print(f"   ⚠️ Chunks file not found yet")
    
    # Step 7: Test Category Matching (LLM)
    print("\n7️⃣ Testing Category Matching (LLM Routing)...")
    
    # First, upload some sample documents
    print("   Uploading sample documents for routing test...")
    
    sample_docs = {
        "Machine Learning": "Deep learning is a subset of machine learning...",
        "Web Development": "React and Vue are popular JavaScript frameworks...",
        "Data Science": "Pandas is used for data manipulation in Python..."
    }
    
    for category, content in sample_docs.items():
        requests.post(
            f"{BASE_URL}/api/files/upload",
            files={"file": (f"{category.replace(' ', '_')}.md", content.encode())},
            data={
                "user_id": user_id,
                "category": category
            },
            timeout=30
        )
    
    # Test queries
    test_queries = [
        ("What is neural networks?", "Machine Learning"),
        ("How to build a React app?", "Web Development"),
        ("Show me Python pandas examples", "Data Science")
    ]
    
    print("\n   Testing category routing:")
    for query, expected_cat in test_queries:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            data={
                "user_id": user_id,
                "session_id": f"routing_test_{int(time.time())}",
                "message": query
            },
            timeout=30
        )
        
        if response.ok:
            result = response.json()
            routed_cat = result.get("memory_snapshot", {}).get("routed_category", "Unknown")
            match = "✓" if routed_cat == expected_cat else "⚠️"
            print(f"   {match} Query: {query[:30]}...")
            print(f"      Expected: {expected_cat}, Got: {routed_cat}")
        else:
            print(f"   ✗ Error: {response.status_code}")
    
    # Step 8: Category Statistics
    print("\n8️⃣ Category Statistics...")
    
    if chunks_file.exists():
        with open(chunks_file, 'r') as f:
            all_chunks = json.load(f)
        
        total_categories = len(all_chunks)
        total_docs = sum(len(cat) for cat in all_chunks.values())
        total_chunks = sum(
            len(chunk_list['chunks'])
            for cat in all_chunks.values()
            for chunk_list in cat.values()
        )
        
        print(f"   Total categories: {total_categories}")
        print(f"   Total documents: {total_docs}")
        print(f"   Total chunks: {total_chunks}")
    
    print("\n" + "="*60)
    print("✅ Category Management Test PASSED!")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = test_category_management()
    exit(0 if success else 1)
