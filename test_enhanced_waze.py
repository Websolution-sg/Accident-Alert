#!/usr/bin/env python3
"""Test enhanced Waze API with anti-blocking features"""
import requests
import random
import time
import json

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]

WAZE_ENDPOINTS = [
    'https://www.waze.com/live-map/api/georss',
    'https://www.waze.com/row-partnerhub-api/georss',
    'https://www.waze.com/partnerhub-api/georss',
    'https://www.waze.com/rtserver/web/TGeoRSS'
]

def test_waze_endpoint(url, params, headers):
    """Test a specific Waze endpoint"""
    print(f"Testing endpoint: {url}")
    print(f"User-Agent: {headers.get('User-Agent', '')[:50]}...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Content Length: {len(response.text)}")
            if 'singapore' in response.text.lower() or 'accident' in response.text.lower():
                print("✓ Found relevant accident data")
                return True
            else:
                print("? Response received but no accident data found")
        elif response.status_code == 403:
            print("✗ 403 Forbidden - Access blocked")
        elif response.status_code == 429:
            print("✗ 429 Too Many Requests - Rate limited")
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request error: {e}")
    
    return False

def main():
    """Test all Waze endpoints with different strategies"""
    print("Testing Enhanced Waze API Anti-Blocking")
    print("=" * 50)
    
    # Singapore coordinates
    params = {
        'bottom': '1.1304',
        'top': '1.4784',
        'left': '103.5000',
        'right': '104.1000',
        'env': 'row',
        'types': 'alerts'
    }
    
    success_count = 0
    total_tests = 0
    
    for i, endpoint in enumerate(WAZE_ENDPOINTS):
        print(f"\n--- Test {i+1}/4: Endpoint Strategy ---")
        
        # Use different user agent for each endpoint
        user_agent = USER_AGENTS[i % len(USER_AGENTS)]
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        if test_waze_endpoint(endpoint, params, headers):
            success_count += 1
        total_tests += 1
        
        # Wait between tests to avoid detection
        if i < len(WAZE_ENDPOINTS) - 1:
            wait_time = random.randint(3, 8)
            print(f"Waiting {wait_time} seconds before next test...")
            time.sleep(wait_time)
    
    print(f"\n{'='*50}")
    print(f"Test Results: {success_count}/{total_tests} endpoints successful")
    
    if success_count > 0:
        print("✓ At least one endpoint is working - anti-blocking partially effective")
    else:
        print("✗ All endpoints blocked - need additional measures")
        print("\nRecommendations:")
        print("1. Consider using a VPN or proxy service")
        print("2. Try accessing from different IP ranges")
        print("3. Implement longer delays between requests")
        print("4. Look for alternative traffic data sources")

if __name__ == "__main__":
    main()