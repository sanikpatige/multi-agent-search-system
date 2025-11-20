#!/usr/bin/env python3
"""
Test script for Multi-Agent Search System
"""

import requests
import json
import time
from datetime import datetime


API_URL = "http://localhost:8000"


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)


def print_result(result):
    """Pretty print search result"""
    print(f"\n[{result['rank']}] {result['title']}")
    print(f"    Source: {result['source']} | Score: {result['relevance_score']}")
    print(f"    URL: {result['url']}")
    print(f"    Snippet: {result['snippet'][:100]}...")


def test_simple_search():
    """Test simple search"""
    print_header("Test 1: Simple Search")
    
    data = {
        "query": "Python programming tutorial",
        "max_results": 5,
        "enable_analysis": True,
        "include_synthesis": True
    }
    
    print(f"\nQuery: {data['query']}")
    print("Executing search...")
    
    try:
        response = requests.post(f"{API_URL}/search", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Search completed!")
            print(f"   Found: {len(result['results'])} results")
            print(f"   Time: {result['agent_metrics']['total_time_ms']}ms")
            
            # Show top 3 results
            print("\nTop 3 Results:")
            for r in result['results'][:3]:
                print_result(r)
            
            # Show synthesis
            if result.get('synthesis'):
                print(f"\n📝 Synthesis:")
                print(f"   Summary: {result['synthesis']['summary'][:150]}...")
                print(f"   Confidence: {result['synthesis']['confidence']}")
                print(f"   Key Points:")
                for point in result['synthesis']['key_points'][:3]:
                    print(f"      • {point}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_advanced_search():
    """Test advanced search with analysis"""
    print_header("Test 2: Advanced Search with Full Analysis")
    
    data = {
        "query": "latest developments in quantum computing",
        "max_results": 10,
        "enable_analysis": True,
        "include_synthesis": True
    }
    
    print(f"\nQuery: {data['query']}")
    print("Executing advanced search...")
    
    try:
        response = requests.post(f"{API_URL}/search", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Search completed!")
            
            # Agent metrics
            metrics = result['agent_metrics']
            print(f"\n⏱️  Agent Performance:")
            print(f"   Query Processing: {metrics['query_processing_ms']}ms")
            print(f"   Search Execution: {metrics['search_execution_ms']}ms")
            print(f"   Synthesis: {metrics['synthesis_ms']}ms")
            print(f"   Total Time: {metrics['total_time_ms']}ms")
            print(f"   Agents Used: {', '.join(metrics['agents_used'])}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_cache():
    """Test caching functionality"""
    print_header("Test 3: Cache Test (Same Query Twice)")
    
    data = {
        "query": "machine learning basics",
        "max_results": 5
    }
    
    print(f"\nQuery: {data['query']}")
    
    # First search
    print("\n1st search (should be slow - not cached)...")
    start = time.time()
    response1 = requests.post(f"{API_URL}/search", json=data, timeout=60)
    time1 = (time.time() - start) * 1000
    
    # Second search (should be faster - cached)
    print("\n2nd search (should be fast - cached)...")
    start = time.time()
    response2 = requests.post(f"{API_URL}/search", json=data, timeout=60)
    time2 = (time.time() - start) * 1000
    
    if response1.status_code == 200 and response2.status_code == 200:
        result1 = response1.json()
        result2 = response2.json()
        
        print(f"\n✅ Cache Test Results:")
        print(f"   1st search time: {time1:.2f}ms (cached: {result1.get('cached', False)})")
        print(f"   2nd search time: {time2:.2f}ms (cached: {result2.get('cached', False)})")
        print(f"   Speedup: {time1/time2:.2f}x faster")
        
        return True
    else:
        print(f"❌ Cache test failed")
        return False


def test_agent_status():
    """Test agent status endpoint"""
    print_header("Test 4: Agent Status Check")
    
    try:
        response = requests.get(f"{API_URL}/agents/status")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n🤖 Agent Status:")
            for agent in data['agents']:
                print(f"\n   {agent['name']}:")
                print(f"      Status: {agent['status']}")
                print(f"      Tasks Completed: {agent['tasks_completed']}")
                print(f"      Avg Execution: {agent['avg_execution_time_ms']}ms")
            
            print(f"\n📊 Orchestrator:")
            orch = data['orchestrator_status']
            print(f"   Total Searches: {orch['total_searches']}")
            print(f"   Success Rate: {orch['success_rate']}%")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_metrics():
    """Test metrics endpoint"""
    print_header("Test 5: System Metrics")
    
    try:
        response = requests.get(f"{API_URL}/metrics")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📈 System Metrics:")
            print(f"   Uptime: {data['uptime_seconds']:.2f}s")
            print(f"   Total Searches: {data['total_searches']}")
            print(f"   Searches/min: {data['searches_per_minute']:.2f}")
            print(f"   Errors: {data['error_count']}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" 🧪 Multi-Agent Search System - Test Suite")
    print("="*70)
    print("\nMake sure the API server is running (python app.py)")
    print("Press Enter to start tests or Ctrl+C to cancel...")
    input()
    
    tests = [
        ("Simple Search", test_simple_search),
        ("Advanced Search", test_advanced_search),
        ("Cache Test", test_cache),
        ("Agent Status", test_agent_status),
        ("System Metrics", test_metrics)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            time.sleep(2)  # Brief pause between tests
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    print()
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n{'='*70}\n")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
