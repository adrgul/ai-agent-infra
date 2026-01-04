#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test activity logging by uploading a document and checking activities.
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_upload_document():
    """Test document upload and activity logging."""
    
    print("\n" + "="*60)
    print("📄 TEST: Upload Document & Activity Logging")
    print("="*60)
    
    # Create test document
    test_content_str = """
    # Test Document
    
    This is a test document for activity logging.
    
    Machine Learning (ML) is a subset of Artificial Intelligence (AI) that focuses on the development of computer programs that can learn and improve from experience.
    
    Machine learning algorithms use computational methods to learn information directly from data without relying on a predetermined equation as a model.
    
    The performance of machine learning algorithms improves with increasing amounts of training data.
    
    Applications of Machine Learning:
    - Image recognition
    - Natural language processing
    - Recommendation systems
    - Autonomous vehicles
    - Healthcare diagnostics
    
    Deep Learning is a specialized subset of machine learning that uses artificial neural networks with multiple layers (hence deep).
    
    Neural networks are inspired by biological neurons in the human brain.
    
    Types of Neural Networks:
    - Convolutional Neural Networks (CNN) - for image processing
    - Recurrent Neural Networks (RNN) - for sequence data
    - Transformer Networks - for natural language processing
    
    Training a neural network involves:
    1. Forward pass: Input - Hidden layers - Output
    2. Calculate loss (error)
    3. Backward pass: Calculate gradients
    4. Update weights using optimization algorithm
    
    Common optimization algorithms:
    - Stochastic Gradient Descent (SGD)
    - Adam
    - RMSprop
    - Adagrad
    
    Hyperparameters are settings that must be configured before training:
    - Learning rate: Controls the step size during training
    - Batch size: Number of samples per gradient update
    - Number of epochs: Complete passes through the training data
    - Number of layers: Architecture of the network
    
    Overfitting occurs when a model learns the training data too well, including noise.
    Underfitting occurs when a model is too simple to capture underlying patterns.
    
    Regularization techniques to prevent overfitting:
    - L1 and L2 regularization
    - Dropout
    - Early stopping
    - Data augmentation
    - Cross-validation
    """
    test_content = test_content_str.encode('utf-8')
    
    # Step 1: Check initial activities
    print("\n1️⃣ Checking initial activities...")
    response = requests.get(f"{BASE_URL}/api/activities?count=100")
    if response.ok:
        activities = response.json().get("activities", [])
        print(f"   Initial activities: {len(activities)}")
    
    # Step 2: Upload document
    print("\n2️⃣ Uploading test document...")
    files = {
        'file': ('test_document.txt', test_content, 'text/plain'),
    }
    data = {
        'category': 'Machine Learning',
        'chunk_size_tokens': '900',
        'overlap_tokens': '150',
        'embedding_batch_size': '100'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/files/upload",
        files=files,
        data=data
    )
    
    if response.ok:
        upload_result = response.json()
        print(f"   ✅ Upload successful!")
        print(f"   Upload ID: {upload_result.get('upload_id')}")
        print(f"   Filename: {upload_result.get('filename')}")
    else:
        print(f"   ❌ Upload failed: {response.status_code}")
        print(f"   {response.text}")
        return
    
    # Step 3: Wait for background processing
    print("\n3️⃣ Waiting for background processing (15 seconds)...")
    for i in range(15):
        time.sleep(1)
        print(f"   ⏳ {i+1}s...", end="\r")
    print("\n")
    
    # Step 4: Fetch and display activities
    print("4️⃣ Fetching activities from backend...")
    response = requests.get(f"{BASE_URL}/api/activities?count=100")
    if response.ok:
        activities = response.json().get("activities", [])
        print(f"   Total activities: {len(activities)}\n")
        
        if activities:
            print("   📋 Activity Log:")
            print("   " + "-"*56)
            for i, activity in enumerate(activities[-20:], 1):  # Last 20
                timestamp = activity.get('timestamp', '?')
                message = activity.get('message', '?')
                activity_type = activity.get('type', '?')
                print(f"   {i:2d}. [{activity_type:10s}] {message}")
                if len(message) > 40:
                    print(f"       └→ {timestamp}")
            print("   " + "-"*56)
        else:
            print("   ❌ No activities recorded!")
    else:
        print(f"   ❌ Failed to fetch activities: {response.status_code}")
    
    # Step 5: Test chat
    print("\n5️⃣ Testing chat with question...")
    chat_data = {
        'user_id': 'test_user',
        'session_id': 'test_session',
        'message': 'Mi az a machine learning?'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data=chat_data
    )
    
    if response.ok:
        print(f"   ✅ Chat successful!")
        result = response.json()
        print(f"   Answer: {result.get('final_answer', '')[:100]}...")
    else:
        print(f"   ❌ Chat failed: {response.status_code}")
    
    # Step 6: Final activities
    print("\n6️⃣ Final activity log...")
    response = requests.get(f"{BASE_URL}/api/activities?count=100")
    if response.ok:
        activities = response.json().get("activities", [])
        print(f"   Total activities: {len(activities)}")
        
        # Show event types summary
        types_count = {}
        for activity in activities:
            atype = activity.get('type', 'unknown')
            types_count[atype] = types_count.get(atype, 0) + 1
        
        print("\n   📊 Activity Types Summary:")
        for atype, count in sorted(types_count.items()):
            print(f"      {atype:12s}: {count:3d}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)
    print(f"\n🌐 Open browser: {FRONTEND_URL}")
    print("   Click the 📋 Tevékenység button to see real-time activities!")
    print()

if __name__ == "__main__":
    test_upload_document()
