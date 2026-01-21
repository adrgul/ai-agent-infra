#!/usr/bin/env python3
"""
Quick validation script to test the benchmark feature.
Run this after starting the application with ./start.sh
"""
import requests
import json
import time

API_URL = "http://localhost:8000"

def test_single_run():
    """Test normal single run (no repeat parameter)."""
    print("🧪 Test 1: Single run (no repeat parameter)")
    print("-" * 50)
    
    response = requests.post(
        f"{API_URL}/run",
        json={"user_input": "What is the capital of France?"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Answer: {data['answer'][:100]}")
        print(f"   Benchmark field present: {'benchmark' in data}")
        print(f"   Benchmark value: {data.get('benchmark')}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    print()


def test_benchmark_run(repeat: int, query: str):
    """Test benchmark run with repeat parameter."""
    print(f"🧪 Test: Benchmark with repeat={repeat}")
    print("-" * 50)
    print(f"Query: {query}")
    
    start_time = time.time()
    
    response = requests.post(
        f"{API_URL}/run?repeat={repeat}",
        json={"user_input": query}
    )
    
    total_time = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Answer: {data['answer'][:100]}")
        
        if 'benchmark' in data and data['benchmark']:
            bench = data['benchmark']
            print(f"\n📊 Benchmark Results:")
            print(f"   Repeat count: {bench['repeat']}")
            print(f"   Total time: {bench['total_time_seconds']}s")
            print(f"   Avg time/run: {bench['avg_time_per_run_seconds']}s")
            print(f"   Cache hits:")
            print(f"     - node_cache: {bench['cache_hits']['node_cache']}")
            print(f"     - embedding_cache: {bench['cache_hits']['embedding_cache']}")
            print(f"   Cache misses:")
            print(f"     - node_cache: {bench['cache_misses']['node_cache']}")
            print(f"     - embedding_cache: {bench['cache_misses']['embedding_cache']}")
            print(f"\n   Client-side total time: {total_time:.2f}s")
            
            # Calculate cache hit rate
            node_total = bench['cache_hits']['node_cache'] + bench['cache_misses']['node_cache']
            if node_total > 0:
                node_hit_rate = (bench['cache_hits']['node_cache'] / node_total) * 100
                print(f"   Node cache hit rate: {node_hit_rate:.1f}%")
        else:
            print("⚠️  No benchmark data in response!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    print()


def main():
    print("\n" + "=" * 60)
    print("🚀 Benchmark Feature Validation")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        health = requests.get(f"{API_URL}/healthz", timeout=2)
        if health.status_code == 200:
            print(f"✅ Server is running at {API_URL}")
            print()
        else:
            print(f"⚠️  Server responded with status {health.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to {API_URL}")
        print(f"   Make sure the application is running: ./start.sh")
        print(f"   Error: {e}")
        return
    
    # Run tests
    test_single_run()
    test_benchmark_run(5, "What is the capital of France?")
    test_benchmark_run(10, "Explain quantum computing in simple terms")
    
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print()
    print("💡 Tips:")
    print("   - Check application logs to see 'Benchmark run X/Y' messages")
    print("   - Cache hit rates should increase after first run")
    print("   - View metrics at: http://localhost:9090")
    print("   - View Grafana at: http://localhost:3000 (admin/admin)")
    print()


if __name__ == "__main__":
    main()
