#!/usr/bin/env python3
"""Test Waze API to check for over-filtering"""

import requests
import json
from datetime import datetime, timezone
import pytz

# Singapore timezone
SGT = pytz.timezone('Asia/Singapore')

def test_waze_api():
    print('=== TESTING WAZE API RESPONSE ===')
    
    waze_url = 'https://www.waze.com/live-map/api/georss'
    params = {
        'bottom': 1.1304753,
        'left': 103.6055424, 
        'right': 104.0945619,
        'top': 1.4764671,
        'env': 'row',
        'types': 'alerts,traffic'
    }

    print('Making Waze API request...')
    try:
        response = requests.get(waze_url, params=params, timeout=10)
        print(f'Status Code: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f'Total alerts found: {len(alerts)}')
            
            # Filter for accidents
            accidents = [alert for alert in alerts if alert.get('type') == 'ACCIDENT']
            print(f'Accidents found: {len(accidents)}')
            
            if accidents:
                print('\n=== ACCIDENT ANALYSIS ===')
                current_time = datetime.now(SGT)
                print(f"Current SGT time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                for i, acc in enumerate(accidents):
                    print(f'\nAccident {i+1}:')
                    print(f'  - Type: {acc.get("type")}')
                    print(f'  - Subtype: {acc.get("subtype")}') 
                    
                    location = acc.get("location", {})
                    print(f'  - Location: {location.get("y", "N/A")}, {location.get("x", "N/A")}')
                    print(f'  - Street: {acc.get("street", "N/A")}')
                    
                    # Check age
                    pub_millis = acc.get("pubMillis")
                    if pub_millis:
                        utc_time = datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
                        accident_time = utc_time.astimezone(SGT)
                        age_minutes = (current_time - accident_time).total_seconds() / 60
                        print(f'  - Timestamp: {accident_time.strftime("%Y-%m-%d %H:%M:%S SGT")}')
                        print(f'  - Age: {age_minutes:.1f} minutes')
                        print(f'  - Would be filtered (>15 min): {"YES" if age_minutes > 15 else "NO"}')
                    else:
                        print(f'  - Timestamp: MISSING')
                        print(f'  - Age: UNKNOWN (would be considered recent)')
                        
            else:
                print('\n=== NO ACCIDENTS FOUND ===')
                print('This explains why your monitor shows "Found 0 Waze accidents"')
                print('\nAvailable alert types:')
                types = set(alert.get('type') for alert in alerts)
                for alert_type in sorted(types):
                    count = len([a for a in alerts if a.get('type') == alert_type])
                    print(f'  - {alert_type}: {count} alerts')
                    
        else:
            print(f'API Error: {response.status_code} - {response.text[:200]}')
            
    except Exception as e:
        print(f'Request failed: {e}')

if __name__ == "__main__":
    test_waze_api()