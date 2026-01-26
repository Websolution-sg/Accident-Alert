#!/usr/bin/env python3
import requests
import json
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

def check_current_accidents():
    """Check what accidents would be processed right now"""
    print("=== CURRENT ACCIDENTS STATUS ===")
    print(f"Timestamp: {datetime.datetime.now()}")
    print()
    
    try:
        # Load processed accidents
        with open('processed_accidents.json', 'r') as f:
            processed_data = json.load(f)
            waze_processed = set(processed_data.get('waze_accidents', []))
        print(f"Already processed: {len(waze_processed)} Waze accidents")
        
        # Get current accidents
        params = {
            "top": SINGAPORE_BOUNDS["north"],
            "bottom": SINGAPORE_BOUNDS["south"],
            "left": SINGAPORE_BOUNDS["west"],
            "right": SINGAPORE_BOUNDS["east"],
            "env": "row",
            "types": "alerts"
        }
        
        response = requests.get(WAZE_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            accidents = [alert for alert in alerts if alert.get("type") == "ACCIDENT"]
            
            print(f"Live accidents found: {len(accidents)}")
            print()
            
            new_count = 0
            for i, accident in enumerate(accidents, 1):
                uuid = accident.get("uuid", "")
                street = accident.get("street", "")
                country = accident.get("country", "")
                
                status = "NEW" if uuid not in waze_processed else "PROCESSED"
                if status == "NEW":
                    new_count += 1
                
                print(f"{i}. {status}: {street} ({country})")
                print(f"   UUID: {uuid}")
                
                # Check if it would pass filters
                if not street:
                    print("   ❌ FILTERED: Empty street")
                elif country not in ['SG', 'SN']:
                    print(f"   ❌ FILTERED: Wrong country ({country})")
                else:
                    print("   ✅ WOULD PROCESS")
                print()
            
            print(f"Summary: {new_count} new accidents would be processed")
            
        else:
            print(f"API Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_current_accidents()