#!/usr/bin/env python3
"""Test script to upload document and monitor activity logging."""

import asyncio
import httpx
import json
from pathlib import Path

async def main():
    """Upload a document and monitor activity logs."""
    
    # Read test document
    doc_path = Path("DEMO_files_ for_testing/AI_vector_demo_hu.md")
    if not doc_path.exists():
        print(f"❌ Document not found: {doc_path}")
        return
    
    with open(doc_path, "rb") as f:
        content = f.read()
    
    # Upload document
    print(f"📤 Uploading {doc_path.name}...")
    
    async with httpx.AsyncClient() as client:
        # Upload
        files = {"file": (doc_path.name, content)}
        data = {"category": "ai"}
        
        response = await client.post(
            "http://localhost:8000/api/files/upload",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   {response.text}")
            return
        
        upload_result = response.json()
        print(f"✅ Upload started: {upload_result.get('upload_id')}")
        
        # Monitor activities
        print(f"\n📋 Activity Log (monitoring for 20 seconds)...\n")
        
        for i in range(20):
            await asyncio.sleep(1)
            
            # Fetch activities
            response = await client.get("http://localhost:8000/api/activities?count=100")
            if response.status_code == 200:
                activities = response.json().get("activities", [])
                
                # Display new activities
                if activities:
                    print(f"[{i+1}s] Got {len(activities)} activities:")
                    for activity in activities[-3:]:  # Show last 3
                        msg = activity.get("message", "")
                        atype = activity.get("type", "")
                        print(f"      {msg} ({atype})")
                else:
                    if i % 2 == 0:
                        print(f"[{i+1}s] Waiting for activities...")
        
        # Final activity log
        print(f"\n✅ Final Activity Log:")
        response = await client.get("http://localhost:8000/api/activities?count=100")
        if response.status_code == 200:
            activities = response.json().get("activities", [])
            for activity in activities:
                msg = activity.get("message", "")
                atype = activity.get("type", "")
                timestamp = activity.get("timestamp", 0)
                import datetime
                ts = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
                print(f"   {ts} | {msg} ({atype})")

if __name__ == "__main__":
    asyncio.run(main())
