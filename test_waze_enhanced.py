#!/usr/bin/env python3
"""
Enhanced Waze API test with different approaches
"""
import requests
import json
import time
import random

def test_waze_with_session():
    """Test Waze API using a session with more realistic browser behavior"""
    
    session = requests.Session()
    
    # First, visit the main Waze page to get cookies
    print("🔍 Getting Waze session...")
    try:
        session.get('https://www.waze.com/', timeout=10)
        print("✅ Got Waze homepage")
    except Exception as e:
        print(f"❌ Failed to get homepage: {e}")
        return False
    
    # Wait a bit to simulate human behavior
    time.sleep(random.uniform(1, 3))
    
    # Now try the API with better headers and session
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.waze.com/live-map',
        'Origin': 'https://www.waze.com',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    # Singapore bounding box
    params = {
        'bottom': '1.1304753',
        'left': '103.6055424', 
        'right': '104.0945619',
        'top': '1.4764671',
        'env': 'row',
        'types': 'alerts,traffic'
    }
    
    print("🔍 Testing Waze API with session and enhanced headers...")
    try:
        response = session.get(
            'https://www.waze.com/live-map/api/georss', 
            params=params, 
            headers=headers, 
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"✅ Success! Retrieved {len(alerts)} alerts")
            
            accidents = [alert for alert in alerts 
                        if alert.get('type', '').upper() in ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR']]
            print(f"Found {len(accidents)} accidents")
            
            if accidents:
                print("Sample accidents:")
                for i, acc in enumerate(accidents[:3]):
                    street = acc.get('street', 'Unknown')
                    location = acc.get('location', {})
                    print(f"  {i+1}. {street} at {location.get('y', 0):.4f}, {location.get('x', 0):.4f}")
            
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_alternative_waze_endpoints():
    """Test alternative Waze endpoints"""
    
    endpoints = [
        {
            'url': 'https://www.waze.com/live-map/api/georss',
            'name': 'GeoRSS API (current)'
        },
        {
            'url': 'https://www.waze.com/row-rtserver/web/TGeoRSS',
            'name': 'Alternative GeoRSS'
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing {endpoint['name']}: {endpoint['url']}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.waze.com/',
            'Accept': 'application/json, text/plain, */*'
        }
        
        params = {
            'bottom': '1.1304753',
            'left': '103.6055424', 
            'right': '104.0945619',
            'top': '1.4764671',
            'env': 'row'
        }
        
        try:
            response = requests.get(endpoint['url'], params=params, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    alerts = data.get('alerts', [])
                    print(f"  ✅ Success! {len(alerts)} alerts")
                    return True
                except json.JSONDecodeError:
                    print(f"  ❌ Invalid JSON response")
            else:
                print(f"  ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return False

def main():
    print("=" * 60)
    print("🚗 ENHANCED WAZE API TESTING")
    print("=" * 60)
    
    # Test with session
    success1 = test_waze_with_session()
    
    print("\n" + "=" * 60)
    
    # Test alternative endpoints
    success2 = test_alternative_waze_endpoints()
    
    print("\n" + "=" * 60)
    
    if success1 or success2:
        print("🎉 At least one approach worked!")
        print("You can now run the main monitoring system.")
    else:
        print("⚠️  All Waze API approaches failed.")
        print("This might be due to:")
        print("  • Rate limiting")
        print("  • IP-based blocking")
        print("  • Changed API requirements")
        print("  • Temporary service issues")
        print("\nThe Telegram monitoring will still work for @sgaccident!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()