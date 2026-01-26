#!/usr/bin/env python3

import requests
import json

def test_waze_api():
    print("Testing Waze API access...")
    
    WAZE_API_URL = "https://www.waze.com/live-map/api/georss"
    SINGAPORE_BOUNDS = {
        "north": 1.4784,
        "south": 1.1496,
        "east": 104.0853,
        "west": 103.6065
    }
    
    # Test 1: Current parameters
    print("\n1. Testing with current parameters...")
    params = {
        "top": SINGAPORE_BOUNDS["north"],
        "bottom": SINGAPORE_BOUNDS["south"],
        "left": SINGAPORE_BOUNDS["west"],
        "right": SINGAPORE_BOUNDS["east"],
        "env": "row",
        "types": "alerts"
    }
    
    try:
        response = requests.get(WAZE_API_URL, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            accidents = [a for a in alerts if a.get("type") == "ACCIDENT"]
            print(f"   Found {len(accidents)} accidents")
        else:
            print(f"   Error Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: With User-Agent header
    print("\n2. Testing with User-Agent header...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(WAZE_API_URL, params=params, headers=headers, timeout=30)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            accidents = [a for a in alerts if a.get("type") == "ACCIDENT"]
            print(f"   Found {len(accidents)} accidents")
        else:
            print(f"   Error Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Different endpoint format
    print("\n3. Testing alternative URL format...")
    alt_url = "https://www.waze.com/live-map/api/georss"
    try:
        response = requests.get(alt_url, params=params, headers=headers, timeout=30)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            accidents = [a for a in alerts if a.get("type") == "ACCIDENT"]
            print(f"   Found {len(accidents)} accidents")
        else:
            print(f"   Error Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_waze_api()