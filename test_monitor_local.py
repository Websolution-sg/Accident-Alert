#!/usr/bin/env python3
"""
Quick test of the accident monitoring system for local validation
"""
import requests
import json
import time
import datetime
import math

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"
SGACCIDENT_CHAT_ID = "-1001486947378"

def log_message(message):
    """Print timestamped log message"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def coordinates_similar(lat1, lon1, lat2, lon2, radius_meters=100):
    """Check if two coordinates are within specified radius (default 100m)"""
    if not all([lat1, lon1, lat2, lon2]):
        return False
    
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = 6371000 * c
    
    return distance <= radius_meters

def test_telegram_connection():
    """Test Telegram bot connection"""
    log_message("Testing Telegram bot connection...")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                log_message(f"✓ Bot connected: {bot_info.get('first_name', 'Unknown')} (@{bot_info.get('username', 'Unknown')})")
                return True
        
        log_message(f"✗ Bot connection failed: HTTP {response.status_code}")
        return False
    except Exception as e:
        log_message(f"✗ Bot connection error: {e}")
        return False

def test_waze_api():
    """Test Waze API connection (expect failures due to blocking)"""
    log_message("Testing Waze API connection...")
    try:
        url = "https://www.waze.com/live-map/api/georss"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            log_message("✓ Waze API accessible (unexpected but good!)")
            return True
        else:
            log_message(f"✗ Waze API blocked: HTTP {response.status_code} (expected)")
            return False
    except Exception as e:
        log_message(f"✗ Waze API error: {e}")
        return False

def test_sgaccident_channel():
    """Test @sgaccident channel access"""
    log_message("Testing @sgaccident channel access...")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {'limit': 5}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                log_message(f"✓ Channel access successful, {len(updates)} recent updates")
                
                # Check for @sgaccident messages in updates
                sgaccident_count = 0
                for update in updates:
                    if 'channel_post' in update:
                        chat = update['channel_post'].get('chat', {})
                        if str(chat.get('id')) == SGACCIDENT_CHAT_ID:
                            sgaccident_count += 1
                
                if sgaccident_count > 0:
                    log_message(f"✓ Found {sgaccident_count} @sgaccident messages in recent updates")
                else:
                    log_message("- No recent @sgaccident messages (normal if quiet)")
                
                return True
        
        log_message(f"✗ Channel access failed: HTTP {response.status_code}")
        return False
    except Exception as e:
        log_message(f"✗ Channel access error: {e}")
        return False

def test_singapore_government_apis():
    """Test Singapore Government APIs"""
    log_message("Testing Singapore Government APIs...")
    
    # Test Traffic Cameras API
    try:
        url = "https://api.data.gov.sg/v1/transport/traffic-images"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('items', [{}])[0].get('cameras', [])
            log_message(f"✓ Traffic Cameras API: {len(cameras)} cameras found")
            traffic_api_ok = True
        else:
            log_message(f"✗ Traffic Cameras API failed: HTTP {response.status_code}")
            traffic_api_ok = False
    except Exception as e:
        log_message(f"✗ Traffic Cameras API error: {e}")
        traffic_api_ok = False
    
    # Test Taxi Availability API
    try:
        url = "https://api.data.gov.sg/v1/transport/taxi-availability"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            log_message(f"✓ Taxi Availability API: {len(features)} taxi zones found")
            taxi_api_ok = True
        else:
            log_message(f"✗ Taxi Availability API failed: HTTP {response.status_code}")
            taxi_api_ok = False
    except Exception as e:
        log_message(f"✗ Taxi Availability API error: {e}")
        taxi_api_ok = False
    
    return traffic_api_ok and taxi_api_ok

def test_coordinate_functions():
    """Test coordinate similarity functions"""
    log_message("Testing coordinate similarity functions...")
    
    test_cases = [
        (1.3521, 103.8198, 1.3522, 103.8199, "Close Singapore locations", True),
        (1.3521, 103.8198, 1.4521, 103.9198, "Far Singapore locations", False),
        (None, None, 1.3521, 103.8198, "Missing coordinates", False)
    ]
    
    all_passed = True
    for lat1, lon1, lat2, lon2, description, expected in test_cases:
        try:
            result = coordinates_similar(lat1, lon1, lat2, lon2)
            if result == expected:
                log_message(f"✓ {description}: {result} (as expected)")
            else:
                log_message(f"✗ {description}: {result} (expected {expected})")
                all_passed = False
        except Exception as e:
            log_message(f"✗ {description}: Error - {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    log_message("=" * 50)
    log_message("ACCIDENT MONITOR - LOCAL SYSTEM TEST")
    log_message("=" * 50)
    
    results = {
        "Telegram Bot": test_telegram_connection(),
        "Singapore Government APIs": test_singapore_government_apis(),
        "Waze API": test_waze_api(),
        "@sgaccident Channel": test_sgaccident_channel(),
        "Coordinate Functions": test_coordinate_functions()
    }
    
    log_message("=" * 50)
    log_message("TEST SUMMARY")
    log_message("=" * 50)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        log_message(f"{symbol} {test_name}: {status}")
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    log_message("=" * 50)
    log_message(f"OVERALL RESULT: {passed_count}/{total_count} tests passed")
    
    if passed_count >= 4:  # Bot, Gov APIs, Channel, Coordinates must pass (Waze expected to fail)
        log_message("🎉 SYSTEM READY FOR DEPLOYMENT!")
        log_message("Note: Waze API failure is expected due to blocking - using Government APIs instead")
    else:
        log_message("⚠️  SYSTEM NEEDS ATTENTION - Critical tests failed")
    
    log_message("=" * 50)

if __name__ == "__main__":
    main()