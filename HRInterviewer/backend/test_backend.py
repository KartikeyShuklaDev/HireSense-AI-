"""
Test backend resilience: Check if /start endpoint returns 400 on rapid calls
"""
import requests
import time
import sys

BASE_URL = "http://localhost:5000"

def test_backend():
    print("\n🧪 Testing HR Interview Backend Resilience\n")
    
    # Test 1: Check if backend is running
    print("1️⃣ Checking if backend is alive...")
    try:
        resp = requests.get(f"{BASE_URL}/")
        print(f"   ✅ GET /  → {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Backend not running: {e}")
        return

    # Test 2: First interview start
    print("\n2️⃣ First POST /api/interview/start...")
    try:
        resp = requests.post(f"{BASE_URL}/api/interview/start")
        print(f"   Response: {resp.status_code}")
        print(f"   Body: {resp.json()}")
        if resp.status_code == 200:
            print("   ✅ Interview started successfully")
        else:
            print(f"   ❌ Unexpected status: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Wait a bit for the interview thread to start
    print("\n   ⏳ Waiting 3 seconds for interview thread to initialize...")
    time.sleep(3)

    # Test 3: Check status while running
    print("\n3️⃣ GET /api/interview/status (while running)...")
    try:
        resp = requests.get(f"{BASE_URL}/api/interview/status")
        print(f"   ✅ Status: {resp.status_code}")
        data = resp.json()
        print(f"   - Running: {data.get('is_running')}")
        print(f"   - Stage: {data.get('stage')}")
        print(f"   - Status: {data.get('status')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Try to start another interview while one is running
    print("\n4️⃣ Second POST /api/interview/start (should be 400)...")
    try:
        resp = requests.post(f"{BASE_URL}/api/interview/start")
        print(f"   Response: {resp.status_code}")
        if resp.status_code == 400:
            print("   ✅ Correctly rejected (already running)")
        else:
            print(f"   ⚠ Unexpected status: {resp.status_code}")
        print(f"   Body: {resp.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 5: End interview
    print("\n5️⃣ POST /api/interview/end...")
    try:
        resp = requests.post(f"{BASE_URL}/api/interview/end")
        print(f"   ✅ Status: {resp.status_code}")
        print(f"   Body: {resp.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 6: History
    print("\n6️⃣ GET /api/interview/history...")
    try:
        resp = requests.get(f"{BASE_URL}/api/interview/history?limit=5")
        print(f"   ✅ Status: {resp.status_code}")
        data = resp.json()
        items = data.get("items", [])
        print(f"   Found {len(items)} past interviews")
        if items:
            print(f"   Latest: {items[0].get('name')} - Score: {items[0].get('avg_score')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n✅ Backend test complete!\n")

if __name__ == "__main__":
    test_backend()
