#!/usr/bin/env python3
import requests
import json
import datetime

WAZE_API_URL = "https://www.waze.com/live-map/api/georss"
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

def check_tpe_accidents():
    """Check TPE accidents and their UUIDs"""
    try:
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
            
            print(f"=== TPE/PIE ACCIDENT ANALYSIS ===")
            print(f"Found {len(accidents)} total accidents")
            print()
            
            tpe_accidents = []
            for accident in accidents:
                street = accident.get("street", "")
                country = accident.get("country", "")
                uuid = accident.get("uuid", "")
                
                if "TPE" in street or "PIE" in street or not street:
                    tpe_accidents.append({
                        'uuid': uuid,
                        'street': street,
                        'country': country,
                        'roadType': accident.get("roadType", ""),
                        'reportDescription': accident.get("reportDescription", "")
                    })
            
            print(f"TPE/PIE related accidents: {len(tpe_accidents)}")
            for i, acc in enumerate(tpe_accidents, 1):
                print(f"{i}. UUID: {acc['uuid']}")
                print(f"   Street: '{acc['street']}'")
                print(f"   Country: {acc['country']}")
                print(f"   RoadType: '{acc['roadType']}'")
                print(f"   Description: '{acc['reportDescription']}'")
                print()
                
            # Check for duplicate UUIDs
            uuids = [acc['uuid'] for acc in tpe_accidents]
            unique_uuids = set(uuids)
            if len(uuids) != len(unique_uuids):
                print("⚠️  DUPLICATE UUIDs FOUND!")
            else:
                print("✅ All UUIDs are unique")
                
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_tpe_accidents()