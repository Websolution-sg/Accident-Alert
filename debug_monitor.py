#!/usr/bin/env python3
import requests
import json
import time
import datetime

# Configuration  
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"
WAZE_API_URL = "https://www.waze.com/live-map/api/georss"
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

def test_waze_api():
    """Test Waze API connection"""
    try:
        print("Testing Waze API...")
        params = {
            "top": SINGAPORE_BOUNDS["north"],
            "bottom": SINGAPORE_BOUNDS["south"],
            "left": SINGAPORE_BOUNDS["west"],
            "right": SINGAPORE_BOUNDS["east"],
            "env": "row",
            "types": "alerts"
        }
        
        response = requests.get(WAZE_API_URL, params=params, timeout=10)
        print(f"Waze API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            accidents = [alert for alert in alerts if alert.get("type") == "ACCIDENT"]
            print(f"Found {len(accidents)} accidents total")
            
            for accident in accidents:
                location = accident.get("location", {})
                street = accident.get("street", "")
                city = accident.get("city", "")
                country = accident.get("country", "")
                print(f"  - {street} ({city}, {country})")
                
            return True
        return False
    except Exception as e:
        print(f"Waze API Error: {e}")
        return False

def test_telegram_api():
    """Test Telegram bot API"""
    try:
        print("Testing Telegram API...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        print(f"Telegram API Status: {response.status_code}")
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"Bot: {bot_info.get('result', {}).get('username', 'Unknown')}")
            return True
        return False
    except Exception as e:
        print(f"Telegram API Error: {e}")
        return False

if __name__ == "__main__":
    print("=== DEBUGGING ACCIDENT MONITOR ===")
    print(f"Timestamp: {datetime.datetime.now()}")
    print()
    
    # Test APIs
    waze_ok = test_waze_api()
    print()
    telegram_ok = test_telegram_api()
    
    print()
    print("=== SUMMARY ===")
    print(f"Waze API: {'✅ OK' if waze_ok else '❌ FAILED'}")
    print(f"Telegram API: {'✅ OK' if telegram_ok else '❌ FAILED'}")